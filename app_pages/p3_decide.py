"""Pagina 3: Decide (și primul pas din Act).

Compară cererea estimată cu stocul și transformă rezultatul în acțiuni concrete:
comandă la furnizor, contactează clientul, gestionează suprastocul, pregătește evenimentul."""

import pandas as pd
import streamlit as st

import common
import decide
import model
from common import t

data = common.get_data()
fitted = common.get_model()
bt = common.get_backtest()
today = common.reference_date()

st.title(t("p3.title"))
st.caption(t("common.today", date=common.fmt_date(today)))

c1, c2 = st.columns(2)
horizon = c1.select_slider(t("p3.horizon"), options=[7, 14, 21, 28], value=14,
                           format_func=lambda d: t("p3.days_fmt", n=d))
service = c2.select_slider(t("p3.service"), options=[0.90, 0.95, 0.98], value=0.95,
                           format_func=lambda x: common.fmt_pct(x, 0))

sigma = model.error_sigma(bt["weekly_product"], "product_id")
stock = model.stock_check(fitted, data, today, horizon, sigma, service)
actions = decide.build_actions(fitted, data, stock, today, horizon, common.lang())

m1, m2, m3 = st.columns(3)
m1.metric(t("p3.metric_actions"), len(actions))
m2.metric(t("p3.metric_shortage"), int((stock["status"] == "Lipsă").sum()), help=t("p3.metric_shortage_help"))
m3.metric(t("p3.metric_excess"), int((stock["status"] == "Exces").sum()), help=t("p3.metric_excess_help"))

# --- Lista de acțiuni ---------------------------------------------------------
kinds = ["supplier", "customer", "overstock", "event"]
selected = st.pills(t("p3.filter"), kinds, selection_mode="multi", default=kinds,
                    format_func=lambda k: common.label("kind", k))
dots = {"high": ":red[●]", "medium": ":orange[●]", "low": ":gray[●]"}
shown = [a for a in actions if a["kind"] in (selected or [])]
if not shown:
    st.write(t("p3.no_actions"))
for a in shown:
    with st.container(border=True):
        st.markdown(f"**{a['title']}**")
        st.write(a["text"])
        priority = common.label("priority", a["priority"])
        st.caption(f"{dots[a['priority']]} " + t("p3.priority_caption",
                                                  priority=priority if common.lang() == "en" else priority.lower(),
                                                  kind=common.label("kind", a["kind"])))

# --- Act: draft de comandă la furnizor ----------------------------------------
st.subheader(t("p3.act_header"))
to_order = stock[(stock["status"] == "Lipsă") & (stock["order_qty"] > 0)]
st.write(t("p3.act_text"))
po = pd.DataFrame({
    "created_on": today.strftime("%Y-%m-%d"),
    "product_id": to_order["product_id"],
    "product_name": to_order["product_name"],
    "unit": to_order["unit"],
    "quantity": to_order["order_qty"].astype(int),
    "unit_price_ron": to_order["price_ron"],
    "value_ron": (to_order["order_qty"] * to_order["price_ron"]).round(2),
})
st.download_button(
    t("p3.download", n=len(po), value=common.fmt_ron(po["value_ron"].sum())),
    data=po.to_csv(index=False).encode("utf-8-sig"),
    file_name=t("p3.download_file", date=today.strftime("%Y-%m-%d")),
    mime="text/csv",
    disabled=po.empty,
    icon=":material/download:",
)

# --- Detaliu pe produse -------------------------------------------------------
with st.expander(t("p3.table_header")):
    view = stock.sort_values(["status", "shortage_risk"], ascending=[True, False])
    col_needed, col_status = t("p3.col_needed"), t("p3.col_status")
    st.dataframe(
        pd.DataFrame({
            t("p3.col_product"): view["product_name"],
            t("p3.col_stock"): view["stock_units"],
            col_needed: view["reorder_point"].round().astype(int),
            col_status: [f"{common.label('stock_status', s)} · {common.fmt_pct(r, 0)}"
                         for s, r in zip(view["status"], view["shortage_risk"])],
        }),
        hide_index=True, width="stretch",
        column_config={
            col_needed: st.column_config.NumberColumn(help=t("p3.col_needed_help")),
            col_status: st.column_config.TextColumn(help=t("p3.col_status_help")),
        },
    )
    rules = ", ".join(t("p3.excess_rule_item", days=d, category=common.label("category", c).lower())
                      for c, d in model.EXCESS_DAYS.items())
    st.caption(t("p3.table_caption", rules=rules))
