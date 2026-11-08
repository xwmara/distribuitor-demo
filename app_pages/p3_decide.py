"""Pagina 3 — Decide (și primul pas din Act).

Compară cererea estimată cu stocul și transformă rezultatul în acțiuni concrete:
comandă la furnizor, contactează clientul, gestionează suprastocul, pregătește evenimentul."""

import pandas as pd
import streamlit as st

import common
import decide
import model

data = common.get_data()
fitted = common.get_model()
bt = common.get_backtest()
today = common.reference_date()

st.title("Decide: acțiuni recomandate")
st.caption(f"„Azi” în demo: {common.fmt_date(today)}")

c1, c2 = st.columns(2)
horizon = c1.select_slider("Orizont de planificare", options=[7, 14, 21, 28], value=14,
                           format_func=lambda d: f"{d} zile")
service = c2.select_slider("Nivel de serviciu", options=[0.90, 0.95, 0.98], value=0.95,
                           format_func=lambda x: f"{x:.0%}")

sigma = model.error_sigma(bt["weekly_product"], "product_id")
stock = model.stock_check(fitted, data, today, horizon, sigma, service)
actions = decide.build_actions(fitted, data, stock, today, horizon)

m1, m2, m3 = st.columns(3)
m1.metric("Acțiuni", len(actions))
m2.metric("Risc de lipsă", int((stock["status"] == "Lipsă").sum()), help="Produse sub punctul de recomandă.")
m3.metric("Exces", int((stock["status"] == "Exces").sum()), help="Produse cu prea multe zile de stoc.")

# --- Lista de acțiuni ---------------------------------------------------------
kinds = ["Comandă la furnizor", "Client", "Suprastoc", "Eveniment"]
selected = st.pills("Filtru", kinds, selection_mode="multi", default=kinds)
icons = {"Ridicată": ":red[●]", "Medie": ":orange[●]", "Scăzută": ":gray[●]"}
shown = [a for a in actions if a["kind"] in (selected or [])]
if not shown:
    st.write("Nicio acțiune pentru filtrul ales.")
for a in shown:
    with st.container(border=True):
        st.markdown(f"**{a['title']}**")
        st.write(a["text"])
        st.caption(f"{icons[a['priority']]} Prioritate {a['priority'].lower()} · {a['kind']}")

# --- Act: draft de comandă la furnizor ----------------------------------------
st.subheader("Act")
to_order = stock[(stock["status"] == "Lipsă") & (stock["order_qty"] > 0)]
st.write("Într-un sistem real, acest pas ar trimite automat comanda la furnizor sau un mesaj clientului. "
         "Aici generăm doar un fișier draft, pe care îl verifică un om.")
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
    f"Descarcă draftul de comandă la furnizor ({len(po)} produse, {common.fmt_ron(po['value_ron'].sum())})",
    data=po.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"draft_comanda_furnizor_{today:%Y-%m-%d}.csv",
    mime="text/csv",
    disabled=po.empty,
    icon=":material/download:",
)

# --- Detaliu pe produse -------------------------------------------------------
with st.expander("Stoc vs. cerere, pe produse"):
    view = stock.sort_values(["status", "shortage_risk"], ascending=[True, False])
    st.dataframe(
        pd.DataFrame({
            "Produs": view["product_name"],
            "Stoc": view["stock_units"],
            "Necesar": view["reorder_point"].round().astype(int),
            "Status": view["status"] + " · " + (view["shortage_risk"] * 100).round().astype(int).astype(str) + "%",
        }),
        hide_index=True, width="stretch",
        column_config={
            "Necesar": st.column_config.NumberColumn(
                help="Punct de recomandă = cererea în timpul livrării de la furnizor + stocul de siguranță."),
            "Status": st.column_config.TextColumn(help="Status și riscul de lipsă în timpul livrării."),
        },
    )
    st.caption("Risc de lipsă = probabilitatea ca cererea din timpul livrării să depășească stocul "
               "(distribuție normală, cu abaterea standard a erorilor din perioada de test). "
               f"Exces = stoc peste {', '.join(f'{d} zile la {c.lower()}' for c, d in model.EXCESS_DAYS.items())} "
               "(regulă de business demonstrativă).")
