"""Pagina 2 — Eveniment și scenarii.

Alegi un eveniment, o categorie, stocul, prețul și perioada. Pagina arată cererea estimată
în trei scenarii (scăzut / de bază / ridicat) și stocul recomandat."""

import pandas as pd
import streamlit as st

import common
import i18n
import model
from common import t

data = common.get_data()
fitted = common.get_model()
bt = common.get_backtest()
lines = common.get_lines()
today = common.reference_date()
lang = common.lang()

weekly_cat = bt["weekly_category"]
bands = model.scenario_bands(weekly_cat)
widening = model.event_widening(weekly_cat)
sigma_cat = model.error_sigma(weekly_cat, "category")

st.title(t("p2.title"))

# --- Inputuri -----------------------------------------------------------------
events = model.upcoming_events(data["factors"], today)
options = [t("p2.no_event")] + [
    t("p2.event_option", event=common.label("event", e.event), start=common.fmt_date(e.start),
      end=common.fmt_date(e.end))
    for e in events.itertuples()]
choice = st.selectbox(t("p2.event"), range(len(options)), format_func=lambda i: options[i],
                      index=1 if len(options) > 1 else 0, key="p2_event")
if choice == 0:
    event_name, default_start, default_days = "", today, 14
else:
    ev = events.iloc[choice - 1]
    event_name, default_start, default_days = ev["event"], ev["start"], int(ev["days"])

category = st.selectbox(t("p2.category"), model.CATEGORIES, format_func=lambda c: common.label("category", c),
                        key="p2_category")
category_label = common.label("category", category)

# Valorile implicite vin din CSV: stocul curent al categoriei și prețul mediu realizat în ultimele 90 de zile
cat_stock = int(data["products"].loc[data["products"]["category"] == category, "stock_units"].sum())
recent = lines[(lines["category"] == category) & (lines["order_date"] > today - pd.Timedelta(days=90))]
avg_price = float(recent["value_ron"].sum() / recent["quantity"].sum())

c1, c2 = st.columns(2)
stock_now = c1.number_input(t("p2.stock"), min_value=0, value=cat_stock, step=10, help=t("p2.stock_help"))
price = c2.number_input(t("p2.price"), min_value=0.0, value=round(avg_price, 2), step=1.0, format="%.2f",
                        help=t("p2.price_help"))
last_day = data["factors"]["date"].max()
c3, c4 = st.columns(2)
start = c3.date_input(t("p2.start"), value=default_start.date(), min_value=today.date(),
                      max_value=last_day.date(), format=i18n.DATE_INPUT_FORMAT[lang])
days = c4.number_input(t("p2.days"), min_value=1, max_value=60, value=default_days)
service = st.select_slider(t("p2.service"), options=[0.90, 0.95, 0.98], value=0.95,
                           format_func=lambda x: common.fmt_pct(x, 0))

res = model.event_scenarios(fitted, data, bands, widening, sigma_cat, category,
                            pd.Timestamp(start), int(days), event_name, service)
if res["days_covered"] < days:
    st.warning(t("p2.calendar_warning", date=common.fmt_date(last_day), n=res["days_covered"]))

# --- Cererea în trei scenarii -------------------------------------------------
st.subheader(t("p2.demand_header"))
st.caption(t("p2.demand_caption", category=category_label, start=common.fmt_date(start), days=res["days_covered"]))
for label_key, key, help_text in [
    ("p2.metric_low", "low", t("p2.help_mult", m=common.fmt_num(res["low_mult"], 2))),
    ("p2.metric_base", "base", t("p2.help_base")),
    ("p2.metric_high", "high", t("p2.help_mult", m=common.fmt_num(res["high_mult"], 2))),
]:
    col_a, col_b = st.columns(2)
    col_a.metric(t(label_key), t("common.units", n=common.fmt_num(res[key])), help=help_text)
    col_b.metric(t("p2.value"), common.fmt_ron(res[key] * price))

if event_name:
    uplift = res["base"] / res["no_event"] - 1 if res["no_event"] else 0
    st.info(t("p2.uplift", event=common.label("event", event_name),
              pct=("+" if uplift >= 0 else "") + common.fmt_pct(uplift),
              a=common.fmt_num(res["no_event"]), b=common.fmt_num(res["base"])))

# Graficul: coloanele primesc nume traduse, ca legenda să fie în limba aleasă
series = [common.label("scenario", code) for code in ["low", "base", "high"]]
daily = (res["daily"]
         .rename(columns={code: common.label("scenario", code) for code in ["low", "base", "high"]})
         .reset_index())
common.time_chart(daily, "date", series, t("p2.axis_date"), t("p2.axis_daily"))

# --- Stocul -------------------------------------------------------------------
st.subheader(t("p2.stock_header"))
s1, s2 = st.columns(2)
s1.metric(t("p2.safety_stock"), t("common.units", n=common.fmt_num(res["safety_stock"])))
s2.metric(t("p2.recommended"), t("common.units", n=common.fmt_num(res["recommended_stock"])),
          help=t("p2.recommended_help"))
gap = stock_now - res["recommended_stock"]
if gap < 0:
    st.error(t("p2.shortage_msg", units=common.fmt_num(-gap), value=common.fmt_ron(-gap * price),
               date=common.fmt_date(start)))
elif stock_now > res["high"] + res["safety_stock"]:
    extra = stock_now - res["recommended_stock"]
    st.warning(t("p2.excess_msg", units=common.fmt_num(extra), value=common.fmt_ron(extra * price)))
else:
    st.success(t("p2.ok_msg", units=common.fmt_num(gap)))

with st.expander(t("p2.sources_header")):
    widen_text = t("p2.sources_widen", w=common.fmt_num(res["widening"], 2)) if event_name else ""
    st.markdown(t("p2.sources_md", category=category_label.lower(), widen=widen_text,
                  z=common.fmt_num(model.z_score(service), 2), service=common.fmt_pct(service, 0),
                  sigma=common.fmt_num(sigma_cat[category] * res["widening"], 1)))
    if event_name:
        ef = fitted["event_factors"]
        ef = ef[(ef["event"] == event_name) & (ef["category"] == category)]
        st.markdown(t("p2.multipliers_title", event=common.label("event", event_name),
                      category=category_label.lower()))
        st.dataframe(
            pd.DataFrame({
                t("p2.col_ctype"): ef["customer_type"].map(lambda c: common.label("customer_type", c)),
                t("p2.col_mult"): [common.fmt_num(v, 2) for v in ef["event_factor"]],
            }),
            hide_index=True,
        )
