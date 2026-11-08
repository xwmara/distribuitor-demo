"""Pagina 2 — Eveniment și scenarii.

Alegi un eveniment, o categorie, stocul, prețul și perioada. Pagina arată cererea estimată
în trei scenarii (scăzut / de bază / ridicat) și stocul recomandat."""

import pandas as pd
import streamlit as st

import common
import model

data = common.get_data()
fitted = common.get_model()
bt = common.get_backtest()
lines = common.get_lines()
today = common.reference_date()

weekly_cat = bt["weekly_category"]
bands = model.scenario_bands(weekly_cat)
widening = model.event_widening(weekly_cat)
sigma_cat = model.error_sigma(weekly_cat, "category")

st.title("Eveniment și scenarii")

# --- Inputuri -----------------------------------------------------------------
events = model.upcoming_events(data["factors"], today)
options = ["Fără eveniment (perioadă normală)"] + [
    f"{e.event} ({common.fmt_date(e.start)} – {common.fmt_date(e.end)})" for e in events.itertuples()]
choice = st.selectbox("Eveniment", range(len(options)), format_func=lambda i: options[i],
                      index=1 if len(options) > 1 else 0)
if choice == 0:
    event_name, default_start, default_days = "", today, 14
else:
    ev = events.iloc[choice - 1]
    event_name, default_start, default_days = ev["event"], ev["start"], int(ev["days"])

category = st.selectbox("Categorie", model.CATEGORIES)

# Valorile implicite vin din CSV: stocul curent al categoriei și prețul mediu realizat în ultimele 90 de zile
cat_stock = int(data["products"].loc[data["products"]["category"] == category, "stock_units"].sum())
recent = lines[(lines["category"] == category) & (lines["order_date"] > today - pd.Timedelta(days=90))]
avg_price = float(recent["value_ron"].sum() / recent["quantity"].sum())

c1, c2 = st.columns(2)
stock_now = c1.number_input("Stoc curent (unități)", min_value=0, value=cat_stock, step=10,
                            help="Implicit: suma stocurilor din products.csv pentru categorie.")
price = c2.number_input("Preț mediu (RON / unitate)", min_value=0.0, value=round(avg_price, 2), step=1.0,
                        format="%.2f", help="Implicit: prețul mediu realizat în ultimele 90 de zile.")
last_day = data["factors"]["date"].max()
c3, c4 = st.columns(2)
start = c3.date_input("Data de început", value=default_start.date(), min_value=today.date(),
                      max_value=last_day.date(), format="DD.MM.YYYY")
days = c4.number_input("Număr de zile", min_value=1, max_value=60, value=default_days)
service = st.select_slider("Nivel de serviciu (pentru stocul de siguranță)", options=[0.90, 0.95, 0.98],
                           value=0.95, format_func=lambda x: f"{x:.0%}")

res = model.event_scenarios(fitted, data, bands, widening, sigma_cat, category,
                            pd.Timestamp(start), int(days), event_name, service)
if res["days_covered"] < days:
    st.warning(f"Calendarul de factori externi se oprește la {common.fmt_date(last_day)}; "
               f"calculul acoperă doar {res['days_covered']} zile.")

# --- Cererea în trei scenarii -------------------------------------------------
st.subheader("Cererea estimată")
st.caption(f"{category}, {common.fmt_date(start)} + {res['days_covered']} zile, toți clienții. "
           "Unitățile sunt un amestec de ambalaje (pungi, baxuri, litri…).")
for label, key, help_text in [
    ("Scenariu scăzut", "low", f"Prognoza × {common.fmt_num(res['low_mult'], 2)}"),
    ("Scenariu de bază", "base", "Prognoza modelului"),
    ("Scenariu ridicat", "high", f"Prognoza × {common.fmt_num(res['high_mult'], 2)}"),
]:
    col_a, col_b = st.columns(2)
    col_a.metric(label, f"{common.fmt_num(res[key])} unități", help=help_text)
    col_b.metric("Valoare", common.fmt_ron(res[key] * price))

if event_name:
    uplift = res["base"] / res["no_event"] - 1 if res["no_event"] else 0
    st.info(f"Față de aceeași perioadă fără {event_name}: {'+' if uplift >= 0 else ''}{common.fmt_pct(uplift)} "
            f"({common.fmt_num(res['no_event'])} → {common.fmt_num(res['base'])} unități).")

daily = res["daily"].reset_index().rename(columns={"date": "Data"})
st.line_chart(daily, x="Data", y=["Scăzut", "De bază", "Ridicat"], y_label="Unități pe zi", height=260)

# --- Stocul -------------------------------------------------------------------
st.subheader("Stocul recomandat")
s1, s2 = st.columns(2)
s1.metric("Stoc de siguranță", f"{common.fmt_num(res['safety_stock'])} unități")
s2.metric("Stoc recomandat", f"{common.fmt_num(res['recommended_stock'])} unități",
          help="Cererea de bază + stocul de siguranță.")
gap = stock_now - res["recommended_stock"]
if gap < 0:
    st.error(f"Stoc insuficient: lipsesc ~{common.fmt_num(-gap)} unități "
             f"(~{common.fmt_ron(-gap * price)}). Comandă la furnizor înainte de {common.fmt_date(start)}.")
elif stock_now > res["high"] + res["safety_stock"]:
    extra = stock_now - res["recommended_stock"]
    st.warning(f"Risc de exces: ~{common.fmt_num(extra)} unități peste recomandat "
               f"(~{common.fmt_ron(extra * price)} blocați în stoc). Stocul depășește chiar și scenariul ridicat.")
else:
    st.success(f"Stocul acoperă scenariul de bază plus stocul de siguranță "
               f"(rezervă: {common.fmt_num(gap)} unități).")

with st.expander("De unde vin cifrele"):
    st.markdown(
        f"""
- **Scenariul de bază**: suma cererii zilnice estimate de model pentru toți clienții
  (cantitate tipică × frecvență ÷ ritm × multiplicator eveniment × factor extern).
- **Scăzut / ridicat**: percentilele 10 și 90 ale erorilor săptămânale din perioada de test, pentru {category.lower()}.
  {"Pentru evenimente, banda e lărgită ×" + common.fmt_num(res['widening'], 2) + " (eroarea a fost mai mare în săptămânile cu eveniment)." if event_name else ""}
- **Stoc de siguranță** = z ({common.fmt_num(model.z_score(service), 2)} pentru {service:.0%}) × σ eroare săptămânală
  ({common.fmt_num(sigma_cat[category] * res['widening'], 1)} unități) × √(zile / 7).
"""
    )
    if event_name:
        ef = fitted["event_factors"]
        ef = ef[(ef["event"] == event_name) & (ef["category"] == category)]
        st.markdown(f"**Multiplicatorii estimați din istoric pentru {event_name}, {category.lower()}:**")
        st.dataframe(
            pd.DataFrame({"Tip client": ef["customer_type"], "Multiplicator": ef["event_factor"].round(2)}),
            hide_index=True,
        )
