"""Pagina 1 — Predicția pe client (Predict).

Alegi un client și vezi: ritmul lui de comandă, istoricul și următoarea comandă estimată
(data, produsele și cantitățile)."""

import pandas as pd
import streamlit as st

import common
import model

data = common.get_data()
fitted = common.get_model()
lines = common.get_lines()
today = common.reference_date()

st.title("Predicția pe client")
st.caption(f"„Azi” în demo: {common.fmt_date(today)}")

# --- Alegerea clientului ------------------------------------------------------
customers = data["customers"].sort_values("customer_name")
labels = dict(zip(customers["customer_id"],
                  customers["customer_name"] + " · " + customers["segment"] + ", " + customers["city"]))
customer_id = st.selectbox("Client", customers["customer_id"], format_func=labels.get)
cust = customers.set_index("customer_id").loc[customer_id]
pred = model.predict_next_order(fitted, data, customer_id, today)

# --- Ritmul -------------------------------------------------------------------
st.subheader("Ritmul de comandă")
c1, c2 = st.columns(2)
c1.metric("Ritm calculat din istoric", f"la ~{pred['interval_days']:g} zile",
          help="Mediana zilelor dintre două comenzi consecutive.")
c2.metric("Ritm din fișa clientului", f"la {cust['order_every_days']} zile",
          help="Valoarea din customers.csv, pentru comparație.")
c3, c4 = st.columns(2)
c3.metric("Ultima comandă", common.fmt_date(pred["last_order_date"]))
c4.metric("Următoarea comandă estimată", common.fmt_date(pred["date"]))
if pred["overdue_days"] > 0:
    st.warning(f"Comanda era așteptată pe {common.fmt_date(pred['expected_date'])}; "
               f"clientul a întârziat {pred['overdue_days']} zile față de ritmul lui. Estimăm comanda azi.")

# --- Următoarea comandă -------------------------------------------------------
st.subheader("Următoarea comandă estimată")
basket = pred["basket"]
day = basket.iloc[0]
context = [f"temperatură estimată {common.fmt_num(day['temperature_c'], 1)}°C"]
if day["is_fasting"]:
    context.append("perioadă de post")
if day["event"]:
    context.append(f"eveniment: {day['event']}")
st.caption(f"{common.fmt_date(pred['date'])}: " + ", ".join(context))

likely = basket[basket["frequency"] >= 0.5]
occasional = basket[basket["frequency"] < 0.5]


def basket_table(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "Produs": df["product_name"],
        "Cantitate": df["estimated_qty"].round().clip(lower=1).astype(int).astype(str) + " " + df["unit"],
        "Probabilitate": (df["frequency"] * 100).round().astype(int),
    })


st.dataframe(
    basket_table(likely), hide_index=True, width="stretch",
    column_config={"Probabilitate": st.column_config.ProgressColumn(
        "Probabilitate", help="În câte comenzi din 100 (ultimele 180 de zile) a apărut produsul.",
        format="%d%%", min_value=0, max_value=100)},
)
st.metric("Valoare estimată (produsele probabile)", common.fmt_ron(likely["estimated_value_ron"].sum()))
if not occasional.empty:
    with st.expander(f"Produse cumpărate ocazional ({len(occasional)})"):
        st.dataframe(basket_table(occasional), hide_index=True, width="stretch",
                     column_config={"Probabilitate": st.column_config.NumberColumn(format="%d%%")})

with st.expander("Cum s-a calculat cantitatea"):
    ex = likely.iloc[0] if not likely.empty else basket.iloc[0]
    st.markdown(
        f"""
**Cantitate estimată = cantitate tipică × multiplicator eveniment × factor extern**

Exemplu pentru *{ex['product_name']}*:

- cantitate tipică într-o zi normală (ultimele 180 de zile): **{common.fmt_num(ex['typical_qty'], 2)}**
- multiplicator eveniment: **×{common.fmt_num(ex['event_factor'], 2)}** {f"({ex['event']})" if ex['event'] else "(niciun eveniment)"}
- factor extern = temperatură ×{common.fmt_num(ex['temp_factor'], 2)} · post ×{common.fmt_num(ex['post_factor'], 2)}
  = **×{common.fmt_num(ex['external_factor'], 2)}**

Rezultat: {common.fmt_num(ex['typical_qty'], 2)} × {common.fmt_num(ex['event_factor'], 2)} ×
{common.fmt_num(ex['external_factor'], 2)} = **{common.fmt_num(ex['estimated_qty'], 1)} {ex['unit']}**
(rotunjit: {max(1, round(ex['estimated_qty']))}).

Data = ultima comandă + ritmul calculat ({common.fmt_date(pred['last_order_date'])} + {round(pred['interval_days'])} zile).
"""
    )

# --- Istoricul ----------------------------------------------------------------
st.subheader("Istoricul comenzilor")
cl = lines[lines["customer_id"] == customer_id]
orders = (cl.groupby(["order_id", "order_date", "status"])
          .agg(value_ron=("value_ron", "sum"), n_products=("product_id", "nunique"))
          .reset_index().sort_values("order_date"))
orders["gap_days"] = orders["order_date"].diff().dt.days

monthly = (orders.assign(month=orders["order_date"].dt.to_period("M").dt.to_timestamp())
           .groupby("month")["value_ron"].sum().reset_index())
st.markdown("**Valoarea comenzilor pe lună (RON)**")
st.bar_chart(monthly, x="month", y="value_ron", x_label="Luna", y_label="RON", height=240)

st.markdown("**Zile între două comenzi**")
st.line_chart(orders.dropna(subset=["gap_days"]), x="order_date", y="gap_days",
              x_label="Data comenzii", y_label="Zile", height=200)

counts = orders["status"].value_counts()
st.caption(f"{len(orders)} comenzi în 24 de luni: "
           + ", ".join(f"{counts.get(s, 0)} {s}" for s in ["livrată", "întârziată", "pierdută"])
           + ". Comenzile pierdute contează ca cerere (clientul a cerut marfa).")

last = orders.tail(8).iloc[::-1]
st.dataframe(
    pd.DataFrame({
        "Data": last["order_date"].dt.strftime("%d.%m.%Y"),
        "Valoare": last["value_ron"].map(common.fmt_ron),
        "Status": last["status"],
    }),
    hide_index=True, width="stretch",
)
