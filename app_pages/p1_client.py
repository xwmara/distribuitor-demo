"""Pagina 1 — Predicția pe client (Predict).

Alegi un client și vezi: ritmul lui de comandă, istoricul și următoarea comandă estimată
(data, produsele și cantitățile)."""

import pandas as pd
import streamlit as st

import common
import model
from common import t

data = common.get_data()
fitted = common.get_model()
lines = common.get_lines()
today = common.reference_date()

st.title(t("p1.title"))
st.caption(t("common.today", date=common.fmt_date(today)))

# --- Alegerea clientului ------------------------------------------------------
customers = data["customers"].sort_values("customer_name")
labels = {
    c.customer_id: f"{c.customer_name} · {common.label('segment', c.segment)}, {c.city}"
    for c in customers.itertuples()
}
customer_id = st.selectbox(t("p1.customer"), customers["customer_id"], format_func=labels.get)
cust = customers.set_index("customer_id").loc[customer_id]
pred = model.predict_next_order(fitted, data, customer_id, today)

# --- Ritmul -------------------------------------------------------------------
st.subheader(t("p1.rhythm_header"))
c1, c2 = st.columns(2)
c1.metric(t("p1.rhythm_calc"), t("p1.rhythm_calc_value", n=common.fmt_days(pred["interval_days"])),
          help=t("p1.rhythm_calc_help"))
c2.metric(t("p1.rhythm_card"), t("p1.rhythm_card_value", n=cust["order_every_days"]), help=t("p1.rhythm_card_help"))
c3, c4 = st.columns(2)
c3.metric(t("p1.last_order"), common.fmt_date(pred["last_order_date"]))
c4.metric(t("p1.next_order"), common.fmt_date(pred["date"]))
if pred["overdue_days"] > 0:
    st.warning(t("p1.overdue", date=common.fmt_date(pred["expected_date"]), n=pred["overdue_days"]))

# --- Următoarea comandă -------------------------------------------------------
st.subheader(t("p1.next_header"))
basket = pred["basket"]
day = basket.iloc[0]
context = [t("p1.ctx_temp", t=common.fmt_num(day["temperature_c"], 1))]
if day["is_fasting"]:
    context.append(t("p1.ctx_fasting"))
if day["event"]:
    context.append(t("p1.ctx_event", event=common.label("event", day["event"])))
st.caption(f"{common.fmt_date(pred['date'])}: " + ", ".join(context))

likely = basket[basket["frequency"] >= 0.5]
occasional = basket[basket["frequency"] < 0.5]
col_product, col_qty, col_prob = t("p1.col_product"), t("p1.col_qty"), t("p1.col_prob")


def basket_table(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        col_product: df["product_name"],
        col_qty: [f"{max(1, round(q))} {common.label('unit', u)}" for q, u in zip(df["estimated_qty"], df["unit"])],
        col_prob: (df["frequency"] * 100).round().astype(int),
    })


st.dataframe(
    basket_table(likely), hide_index=True, width="stretch",
    column_config={col_prob: st.column_config.ProgressColumn(
        col_prob, help=t("p1.col_prob_help"), format="%d%%", min_value=0, max_value=100)},
)
st.metric(t("p1.est_value"), common.fmt_ron(likely["estimated_value_ron"].sum()))
if not occasional.empty:
    with st.expander(t("p1.occasional", n=len(occasional))):
        st.dataframe(basket_table(occasional), hide_index=True, width="stretch",
                     column_config={col_prob: st.column_config.NumberColumn(format="%d%%")})

with st.expander(t("p1.how_header")):
    ex = likely.iloc[0] if not likely.empty else basket.iloc[0]
    event_note = (t("p1.event_note", event=common.label("event", ex["event"])) if ex["event"]
                  else t("p1.no_event"))
    st.markdown(t(
        "p1.how_md",
        product=ex["product_name"],
        typical=common.fmt_num(ex["typical_qty"], 2),
        event_factor=common.fmt_num(ex["event_factor"], 2),
        event_note=event_note,
        temp_factor=common.fmt_num(ex["temp_factor"], 2),
        post_factor=common.fmt_num(ex["post_factor"], 2),
        external=common.fmt_num(ex["external_factor"], 2),
        qty=common.fmt_num(ex["estimated_qty"], 1),
        unit=common.label("unit", ex["unit"]),
        rounded=max(1, round(ex["estimated_qty"])),
        last=common.fmt_date(pred["last_order_date"]),
        interval=round(pred["interval_days"]),
    ))

# --- Istoricul ----------------------------------------------------------------
st.subheader(t("p1.history_header"))
cl = lines[lines["customer_id"] == customer_id]
orders = (cl.groupby(["order_id", "order_date", "status"])
          .agg(value_ron=("value_ron", "sum"), n_products=("product_id", "nunique"))
          .reset_index().sort_values("order_date"))
orders["gap_days"] = orders["order_date"].diff().dt.days

monthly = (orders.assign(month=orders["order_date"].dt.to_period("M").dt.to_timestamp())
           .groupby("month")["value_ron"].sum().reset_index())
st.markdown(f"**{t('p1.monthly_title')}**")
common.time_chart(monthly, "month", ["value_ron"], t("p1.axis_month"), t("p1.axis_ron"),
                  kind="bar", height=240, monthly=True)

gaps = orders.dropna(subset=["gap_days"])[["order_date", "gap_days"]]
st.markdown(f"**{t('p1.gap_title')}**")
common.time_chart(gaps, "order_date", ["gap_days"], t("p1.axis_order_date"), t("p1.axis_days"), height=200)

counts = orders["status"].value_counts()
parts = ", ".join(f"{common.label('status_many', s)}: {common.fmt_num(counts.get(s, 0))}"
                  for s in ["livrată", "întârziată", "pierdută"])
st.caption(t("p1.status_caption", n=common.fmt_num(len(orders)), parts=parts))

last = orders.tail(8).iloc[::-1]
st.dataframe(
    pd.DataFrame({
        t("p1.col_date"): [common.fmt_date(d) for d in last["order_date"]],
        t("p1.col_value"): last["value_ron"].map(common.fmt_ron),
        t("p1.col_status"): last["status"].map(lambda s: common.label("status", s)),
    }),
    hide_index=True, width="stretch",
)
