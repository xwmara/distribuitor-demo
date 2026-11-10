"""
app.py: punctul de intrare al aplicației Streamlit.

Rulare: streamlit run app.py

- Definește paginile cu st.navigation (titlurile în limba aleasă).
- Pune selectorul de limbă în sidebar. Are key="lang", deci alegerea rămâne în
  st.session_state când treci de la o pagină la alta. Limba inițială poate veni
  și din link (?lang=en).
- Codul de aici rulează înaintea fiecărei pagini, deci mesajul despre datele
  simulate apare sus, pe toate paginile.
"""

import streamlit as st

import common
import i18n

st.set_page_config(
    page_title=common.t("app.page_title"),
    page_icon=":material/local_shipping:",
    layout="centered",  # coloană îngustă: se citește bine și pe telefon
)

# La prima deschidere, limba poate veni din link: ...streamlit.app/?lang=en
if "lang" not in st.session_state and st.query_params.get("lang") in i18n.LANGUAGES:
    st.session_state["lang"] = st.query_params["lang"]

t = common.t
pages = [
    st.Page("app_pages/home.py", title=t("nav.home"), icon=":material/home:", default=True),
    st.Page("app_pages/p1_client.py", title=t("nav.client"), icon=":material/person_search:", url_path="client"),
    st.Page("app_pages/p2_scenarii.py", title=t("nav.scenarios"), icon=":material/event:", url_path="scenarii"),
    st.Page("app_pages/p3_decide.py", title=t("nav.decide"), icon=":material/checklist:", url_path="decide"),
    st.Page("app_pages/p4_acuratete.py", title=t("nav.accuracy"), icon=":material/query_stats:",
            url_path="acuratete"),
]

page = st.navigation(pages)

st.sidebar.radio(
    t("app.language"),
    options=list(i18n.LANGUAGES),
    format_func=i18n.LANGUAGES.get,
    key="lang",
    horizontal=True,
)
st.sidebar.caption(t("app.disclaimer"))

common.show_disclaimer()
page.run()
