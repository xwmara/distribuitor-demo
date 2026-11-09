"""Pagina de start: problema și ciclul Predict → Decide → Act."""

import streamlit as st

import common
from common import t

data = common.get_data()
orders = data["orders"]
today = common.reference_date()

st.title(t("home.title"))
st.caption(t("home.caption"))
st.markdown(t("home.problem_md"))

st.subheader(t("home.cycle_header"))
steps = [
    (":material/insights:", "home.step_predict_title", "home.step_predict_text"),
    (":material/rule:", "home.step_decide_title", "home.step_decide_text"),
    (":material/bolt:", "home.step_act_title", "home.step_act_text"),
]
for icon, title_key, text_key in steps:
    with st.container(border=True):
        st.markdown(f"**{icon} {t(title_key)}**")
        st.write(t(text_key))

st.subheader(t("home.data_header"))
c1, c2 = st.columns(2)
c1.metric(t("home.metric_customers"), len(data["customers"]))
c2.metric(t("home.metric_products"), len(data["products"]))
c3, c4 = st.columns(2)
c3.metric(t("home.metric_orders"), common.fmt_num(orders["order_id"].nunique()))
c4.metric(t("home.metric_months"), round((orders["order_date"].max() - orders["order_date"].min()).days / 30.4))
st.caption(t("home.history_caption", start=common.fmt_date(orders["order_date"].min()),
             end=common.fmt_date(orders["order_date"].max()), today=common.fmt_date(today)))

st.subheader(t("home.pages_header"))
st.page_link("app_pages/p1_client.py", label=t("home.link_client"), icon=":material/person_search:")
st.page_link("app_pages/p2_scenarii.py", label=t("home.link_scenarios"), icon=":material/event:")
st.page_link("app_pages/p3_decide.py", label=t("home.link_decide"), icon=":material/checklist:")
st.page_link("app_pages/p4_acuratete.py", label=t("home.link_accuracy"), icon=":material/query_stats:")
