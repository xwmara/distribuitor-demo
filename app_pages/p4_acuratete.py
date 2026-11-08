"""Pagina 4 — Acuratețea prognozei.

Modelul este antrenat doar pe prima parte a istoricului și comparat cu comenzile
din perioada următoare (pe care nu le-a văzut). Eroarea se măsoară cu MAPE."""

import pandas as pd
import streamlit as st

import common
import model

bt = common.get_backtest()
weekly = bt["weekly_category"]

st.title("Acuratețea prognozei")
st.caption(f"Antrenare: {common.fmt_date(bt['train_start'])} – {common.fmt_date(bt['train_end'])}. "
           f"Test: {common.fmt_date(bt['test_start'])} – {common.fmt_date(bt['test_end'])} "
           f"({weekly['week_start'].nunique()} săptămâni complete, comparate pe categorii).")

overall = model.mape(weekly)
by_cat = model.mape_by(weekly, "category")
st.metric("MAPE total (săptămânal, pe categorie)", common.fmt_pct(overall),
          help="Media lui |real − prognoză| / real, pe toate săptămânile și categoriile din test.")
cols = st.columns(3)
for col, cat in zip(cols, model.CATEGORIES):
    col.metric(cat, common.fmt_pct(by_cat[cat]))

# --- Prognoză vs. real --------------------------------------------------------
st.subheader("Prognoză vs. comenzi reale simulate")
category = st.radio("Categorie", model.CATEGORIES, horizontal=True)
w = weekly[weekly["category"] == category]
chart = w[["week_start", "forecast", "actual"]].rename(
    columns={"week_start": "Săptămâna", "forecast": "Prognoză", "actual": "Real"})
st.line_chart(chart, x="Săptămâna", y=["Prognoză", "Real"], y_label="Unități / săptămână", height=280)

# --- Eroarea pe tip de săptămână ----------------------------------------------
st.subheader("Eroarea pe tip de săptămână")
by_type = model.mape_by(weekly, "week_type")
counts = weekly.groupby("week_type")["week_start"].nunique()
type_cols = st.columns(len(by_type))
for col, (wtype, value) in zip(type_cols, by_type.items()):
    col.metric(f"{wtype.capitalize()} ({counts[wtype]} săpt.)", common.fmt_pct(value))

# --- Când lărgim intervalul ---------------------------------------------------
st.subheader("Când trebuie lărgit intervalul")
widening = model.event_widening(weekly)
by_week = weekly.groupby("week_start")["abs_pct_error"].mean()
rolling = by_week.rolling(4).mean().dropna()
recent_mape = float(rolling.iloc[-1])

notes = []
if widening > 1:
    notes.append(f"**Evenimente**: eroarea a fost {common.fmt_pct(by_type['eveniment'])} în săptămânile cu eveniment, "
                 f"față de {common.fmt_pct(by_type['normală'])} în cele normale. Pentru evenimente, banda dintre "
                 f"scenariul scăzut și cel ridicat se lărgește ×{common.fmt_num(widening, 2)}.")
else:
    notes.append("**Evenimente**: în perioada de test, eroarea la evenimente nu a fost mai mare decât în "
                 "săptămânile normale, deci banda rămâne aceeași.")
if recent_mape > 1.5 * overall:
    notes.append(f"**Eroare recentă**: MAPE pe ultimele 4 săptămâni este {common.fmt_pct(recent_mape)}, "
                 f"peste 1,5 × media ({common.fmt_pct(1.5 * overall)}). Lărgește intervalul și reantrenează modelul.")
else:
    notes.append(f"**Eroare recentă**: MAPE pe ultimele 4 săptămâni este {common.fmt_pct(recent_mape)}, "
                 f"sub pragul de alertă de 1,5 × media ({common.fmt_pct(1.5 * overall)}). Banda actuală e suficientă.")
for n in notes:
    st.markdown(f"- {n}")
st.info(
    "Regula generală: lărgește intervalul când (1) urmează un eveniment, mai ales unul văzut doar o dată "
    "în istoric; (2) eroarea pe ultimele 4 săptămâni depășește 1,5 × media; (3) clientul sau produsul are "
    "istoric scurt; (4) condițiile ies din ce a văzut modelul (temperaturi extreme, client nou, preț schimbat).",
    icon=":material/tips_and_updates:",
)

bands = model.scenario_bands(weekly)
st.markdown("**Benzile scenariilor** (percentilele 10 și 90 ale erorii, pe categorie)")
st.dataframe(
    pd.DataFrame({
        "Categorie": bands.index,
        "Scăzut": ("× " + bands["low_mult"].round(2).astype(str)).values,
        "Ridicat": ("× " + bands["high_mult"].round(2).astype(str)).values,
    }),
    hide_index=True, width="stretch",
)

with st.expander("Cele mai mari 5 erori"):
    worst = weekly.nlargest(5, "abs_pct_error")
    st.dataframe(
        pd.DataFrame({
            "Săptămâna": worst["week_start"].dt.strftime("%d.%m.%Y"),
            "Categorie": worst["category"],
            "Real / Prognoză": worst["actual"].round().astype(int).astype(str) + " / "
                               + worst["forecast"].round().astype(int).astype(str),
            "Eroare": (worst["abs_pct_error"] * 100).round(1).astype(str) + "%",
        }),
        hide_index=True, width="stretch",
    )
    st.caption("Tipul săptămânii: " + ", ".join(
        f"{common.fmt_date(r.week_start)} = {r.week_type}{' (' + r.event_name + ')' if r.event_name else ''}"
        for r in worst.itertuples()))
