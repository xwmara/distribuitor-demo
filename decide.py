"""
decide.py: transformă prognoza în acțiuni (pasul "Decide" din ciclul Predict → Decide → Act).

Regulile sunt simple și explicite, ca un om să le poată verifica:
1. Produs cu stocul sub punctul de recomandă         → "Comandă acum la furnizor"
2. Client care va comanda curând un produs fără stoc → avertizare pe client
3. Client care a depășit clar ritmul obișnuit        → "Contactează clientul"
4. Produs cu stoc pentru prea multe zile             → "Suprastoc"
5. Eveniment care începe în orizontul de planificare → "Pregătește evenimentul"

Textele vin din șabloanele din i18n.py, în limba cerută (lang = "ro" sau "en").
Prioritatea și tipul acțiunii sunt coduri ("high", "supplier"…), traduse la afișare.
"""

import pandas as pd

import i18n
import model

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def build_actions(fitted: dict, data: dict, stock: pd.DataFrame, today: pd.Timestamp,
                  horizon_days: int, lang: str = i18n.DEFAULT_LANG) -> list:
    """Întoarce o listă de acțiuni: dict(priority, kind, title, text)."""

    # Scurtături pentru texte și formatare în limba cerută
    def t(key, **kw):
        return i18n.t(key, lang, **kw)

    def num(x, decimals=0):
        return i18n.fmt_num(x, lang, decimals)

    def date(d):
        return i18n.fmt_date(d, lang)

    def cat(c):
        return i18n.label("category", c, lang).lower()

    def unit(u):
        return i18n.label("unit", u, lang)

    def when(days):
        if days == 0:
            return t("act.when_today")
        if days == 1:
            return t("act.when_tomorrow")
        return t("act.when_days", n=days)

    actions = []
    customers = data["customers"].set_index("customer_id")
    baseline = fitted["baseline"].merge(data["products"][["product_id", "product_name"]], on="product_id")

    # 1. Produse cu risc de lipsă
    shortage = stock[stock["status"] == "Lipsă"].sort_values("shortage_risk", ascending=False)
    for p in shortage.itertuples(index=False):
        actions.append({
            "priority": "high" if p.shortage_risk >= 0.30 else "medium",
            "kind": "supplier",
            "title": t("act.supplier_title", product=p.product_name),
            "text": t("act.supplier_text", stock=num(p.stock_units), unit=unit(p.unit), lead=p.lead_time_days,
                      demand=num(p.demand_lead), ss=num(p.safety_stock),
                      risk=i18n.fmt_pct(p.shortage_risk, lang, 0), qty=num(p.order_qty), horizon=horizon_days),
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
        items = [t("act.item", category=cat(c), products=", ".join(names))
                 for c, names in hit.groupby("category")["product_name"].apply(list).items()]
        name = customers.loc[o.customer_id, "customer_name"]
        actions.append({
            "priority": "high" if o.days_until <= 3 else "medium",
            "kind": "customer",
            "title": t("act.customer_title", name=name, when=when(o.days_until)),
            "text": t("act.customer_text", name=name, interval=i18n.fmt_days(o.interval_days, lang), date=date(o.order_date),
                      items=i18n.join_list(items, lang), lead=int(hit["lead_time_days"].max())),
        })

    # 3. Clienți care au depășit clar ritmul obișnuit (posibil pierduți către concurență)
    for r in fitted["rhythm"].itertuples(index=False):
        days_since = (today - r.last_order_date).days
        if days_since > max(1.5 * r.interval_days, r.interval_days + 2):
            name = customers.loc[r.customer_id, "customer_name"]
            actions.append({
                "priority": "medium",
                "kind": "customer",
                "title": t("act.contact_title", name=name),
                "text": t("act.contact_text", days=days_since, interval=i18n.fmt_days(r.interval_days, lang),
                          last=date(r.last_order_date)),
            })

    # 4. Suprastoc
    excess = stock[stock["status"] == "Exces"].sort_values("days_of_cover", ascending=False)
    for p in excess.itertuples(index=False):
        buyers = baseline[baseline["product_id"] == p.product_id].assign(
            weight=lambda d: d["typical_qty"] * d["frequency"]).nlargest(3, "weight")
        actions.append({
            "priority": "medium" if p.category == "Lactate" else "low",
            "kind": "overstock",
            "title": t("act.overstock_title", product=p.product_name),
            "text": t("act.overstock_text", stock=num(p.stock_units), cover=num(p.days_of_cover),
                      threshold=p.excess_threshold_days, category=cat(p.category), excess=num(p.excess_units),
                      unit=unit(p.unit), buyers=", ".join(customers.loc[buyers["customer_id"], "customer_name"])),
        })

    # 5. Evenimente care încep în curând
    events = model.upcoming_events(data["factors"], today)
    limit = today + pd.Timedelta(days=horizon_days + int(data["products"]["lead_time_days"].max()))
    ef = fitted["event_factors"]
    for e in events[events["start"] <= limit].itertuples(index=False):
        rows = ef[ef["event"] == e.event]
        detail = "; ".join(
            f"{i18n.label('customer_type', ctype, lang)}: " + ", ".join(
                t("act.event_detail_item", category=cat(r.category), mult=num(r.event_factor, 2))
                for r in rows[rows["customer_type"] == ctype].itertuples())
            for ctype in sorted(rows["customer_type"].unique()))
        actions.append({
            "priority": "medium",
            "kind": "event",
            "title": t("act.event_title", event=i18n.label("event", e.event, lang),
                       start=date(e.start), end=date(e.end)),
            "text": t("act.event_text", when=when((e.start - today).days), detail=detail),
        })

    return sorted(actions, key=lambda a: PRIORITY_ORDER[a["priority"]])
