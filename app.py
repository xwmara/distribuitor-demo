"""
app.py — punctul de intrare al aplicației Streamlit.

Rulare: streamlit run app.py

Definește paginile cu st.navigation. Codul de aici rulează înaintea fiecărei pagini,
deci mesajul despre datele simulate apare sus, pe toate paginile.
"""

import streamlit as st

import common

st.set_page_config(
    page_title="Distribuitor Demo SRL · prognoză B2B",
    page_icon=":material/local_shipping:",
    layout="centered",  # coloană îngustă: se citește bine și pe telefon
)

pages = [
    st.Page("app_pages/home.py", title="Start", icon=":material/home:", default=True),
    st.Page("app_pages/p1_client.py", title="1. Predicția pe client",
            icon=":material/person_search:", url_path="client"),
    st.Page("app_pages/p2_scenarii.py", title="2. Eveniment și scenarii",
            icon=":material/event:", url_path="scenarii"),
    st.Page("app_pages/p3_decide.py", title="3. Decide",
            icon=":material/checklist:", url_path="decide"),
    st.Page("app_pages/p4_acuratete.py", title="4. Acuratețea prognozei",
            icon=":material/query_stats:", url_path="acuratete"),
]

page = st.navigation(pages)
common.show_disclaimer()
st.sidebar.caption(common.DISCLAIMER)
page.run()
