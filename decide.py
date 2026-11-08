"""
decide.py — transformă prognoza în acțiuni (pasul "Decide" din ciclul Predict → Decide → Act).

Regulile sunt simple și explicite, ca un om să le poată verifica:
1. Produs cu stocul sub punctul de recomandă         → "Comandă acum la furnizor"
2. Client care va comanda curând un produs fără stoc → avertizare pe client
3. Client care a depășit clar ritmul obișnuit        → "Contactează clientul"
4. Produs cu stoc pentru prea multe zile             → "Suprastoc"
5. Eveniment care începe în orizontul de planificare → "Pregătește evenimentul"
"""

import pandas as pd

import model

PRIORITY_ORDER = {"Ridicată": 0, "Medie": 1, "Scăzută": 2}


def fmt_date(d) -> str:
    return pd.Timestamp(d).strftime("%d.%m.%Y")


def fmt_num(x, decimals: int = 0) -> str:
    """1234.5 → '1.234,5' (format românesc)."""
    s = f"{x:,.{decimals}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def join_ro(items: list) -> str:
    """['a', 'b', 'c'] → 'a, b și c'."""
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " și " + items[-1]


def when(days: int) -> str:
    return "azi" if days == 0 else "mâine" if days == 1 else f"peste {days} zile"


def build_actions(fitted: dict, data: dict, stock: pd.DataFrame, today: pd.Timestamp,
                  horizon_days: int) -> list:
    """Întoarce o listă de acțiuni: dict(priority, kind, title, text)."""
    actions = []
    customers = data["customers"].set_index("customer_id")
    baseline = fitted["baseline"].merge(data["products"][["product_id", "product_name"]], on="product_id")

    # 1. Produse cu risc de lipsă
    shortage = stock[stock["status"] == "Lipsă"].sort_values("shortage_risk", ascending=False)
    for p in shortage.itertuples(index=False):
        actions.append({
            "priority": "Ridicată" if p.shortage_risk >= 0.30 else "Medie",
            "kind": "Comandă la furnizor",
            "title": f"Comandă acum la furnizor: {p.product_name}",
            "text": (f"Stoc: {fmt_num(p.stock_units)} ({p.unit}). Cererea estimată până sosește marfa "
                     f"({p.lead_time_days} zile): {fmt_num(p.demand_lead)}, plus stoc de siguranță "
                     f"{fmt_num(p.safety_stock)}. Risc de lipsă: {p.shortage_risk:.0%}. "
                     f"Recomandat: {fmt_num(p.order_qty)} ({p.unit}), acoperă {p.lead_time_days} + "
                     f"{horizon_days} zile."),
        })

    # 2. Clienți care vor comanda un produs fără stoc suficient ÎNAINTE să poată ajunge
    #    marfa nouă de la furnizor (comanda clientului cade în timpul de livrare).
    upcoming = model.upcoming_orders(fitted, today, horizon_days).drop_duplicates("customer_id")
    for o in upcoming.itertuples(index=False):
        basket = baseline[(baseline["customer_id"] == o.customer_id) & (baseline["frequency"] >= 0.5)]
        hit = basket.merge(shortage[["product_id", "lead_time_days"]], on="product_id")
        hit = hit[o.days_until < hit["lead_time_days"]]
        if hit.empty:
            continue
        parts = [f"{cat.lower()} ({', '.join(names)})"
                 for cat, names in hit.groupby("category")["product_name"].apply(list).items()]
        name = customers.loc[o.customer_id, "customer_name"]
        actions.append({
            "priority": "Ridicată" if o.days_until <= 3 else "Medie",
            "kind": "Client",
            "title": f"{name}: comandă estimată {when(o.days_until)}",
            "text": (f"Clientul {name} comandă de obicei la ~{o.interval_days:g} zile. Următoarea comandă "
                     f"estimată: {fmt_date(o.order_date)}. Stoc insuficient la {join_ro(parts)}, iar marfa nouă "
                     f"ajunge în {int(hit['lead_time_days'].max())} zile de la comandă: comandă acum la "
                     f"furnizor și confirmă cu clientul cantitățile."),
        })

    # 3. Clienți care au depășit clar ritmul obișnuit (posibil pierduți către concurență)
    for r in fitted["rhythm"].itertuples(index=False):
        days_since = (today - r.last_order_date).days
        if days_since > max(1.5 * r.interval_days, r.interval_days + 2):
            name = customers.loc[r.customer_id, "customer_name"]
            actions.append({
                "priority": "Medie",
                "kind": "Client",
                "title": f"Contactează clientul: {name}",
                "text": (f"Nu a mai comandat de {days_since} zile, deși comandă de obicei la "
                         f"~{r.interval_days:g} zile (ultima comandă: {fmt_date(r.last_order_date)}). "
                         f"Un telefon acum poate salva comanda."),
            })

    # 4. Suprastoc
    excess = stock[stock["status"] == "Exces"].sort_values("days_of_cover", ascending=False)
    for p in excess.itertuples(index=False):
        buyers = baseline[baseline["product_id"] == p.product_id].assign(
            weight=lambda d: d["typical_qty"] * d["frequency"]).nlargest(3, "weight")
        buyer_names = ", ".join(customers.loc[buyers["customer_id"], "customer_name"])
        actions.append({
            "priority": "Medie" if p.category == "Lactate" else "Scăzută",
            "kind": "Suprastoc",
            "title": f"Suprastoc: {p.product_name}",
            "text": (f"Stoc: {fmt_num(p.stock_units)} = ~{fmt_num(p.days_of_cover)} zile de vânzări "
                     f"(prag: {p.excess_threshold_days} zile pentru {p.category.lower()}). "
                     f"~{fmt_num(p.excess_units)} ({p.unit}) peste prag. Nu reaproviziona; propune o ofertă "
                     f"clienților care îl cumpără des: {buyer_names}."),
        })

    # 5. Evenimente care încep în curând
    events = model.upcoming_events(data["factors"], today)
    limit = today + pd.Timedelta(days=horizon_days + int(data["products"]["lead_time_days"].max()))
    ef = fitted["event_factors"]
    for e in events[events["start"] <= limit].itertuples(index=False):
        rows = ef[ef["event"] == e.event]
        detail = "; ".join(
            f"{ctype}: " + ", ".join(f"{r.category.lower()} ×{fmt_num(r.event_factor, 2)}"
                                     for r in rows[rows["customer_type"] == ctype].itertuples())
            for ctype in sorted(rows["customer_type"].unique()))
        actions.append({
            "priority": "Medie",
            "kind": "Eveniment",
            "title": f"Pregătește evenimentul: {e.event} ({fmt_date(e.start)} – {fmt_date(e.end)})",
            "text": (f"Începe {when((e.start - today).days)}. Multiplicatori estimați din istoric: {detail}. "
                     f"Verifică scenariile pe pagina „Eveniment și scenarii”."),
        })

    return sorted(actions, key=lambda a: PRIORITY_ORDER[a["priority"]])
