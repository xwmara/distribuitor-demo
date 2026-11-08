"""Pagina de start: problema și ciclul Predict → Decide → Act."""

import streamlit as st

import common

data = common.get_data()
orders = data["orders"]
today = common.reference_date()

st.title("Distribuitor Demo SRL")
st.caption("Demo: prognoza comenzilor clienților B2B și acțiuni recomandate")

st.markdown(
    """
**Problema.** Un distribuitor de alimente servește restaurante, cafenele, hoteluri și magazine mici.
Fără prognoză, lucrează reactiv: află ce trebuie abia când vine comanda.

- **Lipsă de stoc**: clientul cere, produsul nu e pe raft, comanda se pierde sau pleacă la concurență.
- **Suprastoc**: bani blocați în marfă, iar la lactate risc de expirare.
- **Comenzi reactive**: comanda la furnizor se face târziu, de obicei după ce a apărut problema.

**Ideea.** Mare parte din cerere se poate anticipa: fiecare client comandă într-un ritm,
iar evenimentele (Black Friday, Crăciun, Paște), postul și temperatura o mută previzibil.
"""
)

st.subheader("Ciclul Predict → Decide → Act")
steps = [
    (":material/insights: Predict",
     "Estimează când comandă fiecare client și ce cantități, pornind de la ritmul lui istoric, "
     "ajustat cu evenimente și factori externi."),
    (":material/rule: Decide",
     "Compară cererea estimată cu stocul: unde e risc de lipsă, unde e exces și ce trebuie comandat."),
    (":material/bolt: Act",
     "Transformă deciziile în acțiuni: comandă la furnizor, telefon la client, ofertă pentru stocul în exces."),
]
for title, text in steps:
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.write(text)

st.subheader("Ce date are demo-ul")
c1, c2 = st.columns(2)
c1.metric("Clienți", len(data["customers"]))
c2.metric("Produse", len(data["products"]))
c3, c4 = st.columns(2)
c3.metric("Comenzi în istoric", common.fmt_num(orders["order_id"].nunique()))
c4.metric("Luni de istoric", round((orders["order_date"].max() - orders["order_date"].min()).days / 30.4))
st.caption(
    f"Istoric: {common.fmt_date(orders['order_date'].min())} – {common.fmt_date(orders['order_date'].max())}. "
    f"„Azi” în demo: {common.fmt_date(today)} (ziua de după ultima comandă din istoric)."
)

st.subheader("Paginile")
st.page_link("app_pages/p1_client.py", label="1. Predicția pe client", icon=":material/person_search:")
st.page_link("app_pages/p2_scenarii.py", label="2. Eveniment și scenarii", icon=":material/event:")
st.page_link("app_pages/p3_decide.py", label="3. Decide: acțiuni recomandate", icon=":material/checklist:")
st.page_link("app_pages/p4_acuratete.py", label="4. Acuratețea prognozei", icon=":material/query_stats:")
