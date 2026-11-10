"""Pagina 4: Acuratețea prognozei.

Modelul este antrenat doar pe prima parte a istoricului și comparat cu comenzile
din perioada următoare (pe care nu le-a văzut). Eroarea se măsoară cu MAPE."""

import pandas as pd
import streamlit as st

import common
import model
from common import t

bt = common.get_backtest()
weekly = bt["weekly_category"]

st.title(t("p4.title"))
st.caption(t("p4.caption", train_start=common.fmt_date(bt["train_start"]), train_end=common.fmt_date(bt["train_end"]),
             test_start=common.fmt_date(bt["test_start"]), test_end=common.fmt_date(bt["test_end"]),
             n=weekly["week_start"].nunique()))

overall = model.mape(weekly)
by_cat = model.mape_by(weekly, "category")
top1, top2 = st.columns(2)
top1.metric(t("p4.mape_total"), common.fmt_pct(overall), help=t("p4.mape_total_help"))
top2.metric(t("p4.wape_total"), common.fmt_pct(model.wape(weekly)), help=t("p4.wape_total_help"))
cols = st.columns(3)
for col, cat in zip(cols, model.CATEGORIES):
    col.metric(common.label("category", cat), common.fmt_pct(by_cat[cat]))

# --- Prognoză vs. real --------------------------------------------------------
st.subheader(t("p4.fc_header"))
category = st.radio(t("p4.category"), model.CATEGORIES, horizontal=True,
                    format_func=lambda c: common.label("category", c), key="p4_category")
s_fc, s_act = t("p4.series_forecast"), t("p4.series_actual")
chart = (weekly[weekly["category"] == category][["week_start", "forecast", "actual"]]
         .rename(columns={"forecast": s_fc, "actual": s_act}))
common.time_chart(chart, "week_start", [s_fc, s_act], t("p4.axis_week"), t("p4.axis_units_week"), height=280)

# --- Eroarea pe tip de săptămână ----------------------------------------------
st.subheader(t("p4.type_header"))
by_type = model.mape_by(weekly, "week_type")
counts = weekly.groupby("week_type")["week_start"].nunique()
type_cols = st.columns(len(by_type))
for col, (wtype, value) in zip(type_cols, by_type.items()):
    col.metric(t("p4.type_metric", type=common.label("week_type", wtype), n=counts[wtype]), common.fmt_pct(value))

# --- Când lărgim intervalul ---------------------------------------------------
st.subheader(t("p4.widen_header"))
widening = model.event_widening(weekly)
by_week = weekly.groupby("week_start")["abs_pct_error"].mean()
recent_mape = float(by_week.rolling(4).mean().dropna().iloc[-1])

if widening > 1:
    notes = [t("p4.note_event_widen", event=common.fmt_pct(by_type["eveniment"]),
               normal=common.fmt_pct(by_type["normală"]), w=common.fmt_num(widening, 2))]
else:
    notes = [t("p4.note_event_same")]
recent_key = "p4.note_recent_high" if recent_mape > 1.5 * overall else "p4.note_recent_ok"
notes.append(t(recent_key, recent=common.fmt_pct(recent_mape), limit=common.fmt_pct(1.5 * overall)))
for n in notes:
    st.markdown(f"- {n}")
st.info(t("p4.rule_info"), icon=":material/tips_and_updates:")

bands = model.scenario_bands(weekly)
st.markdown(t("p4.bands_title"))
st.dataframe(
    pd.DataFrame({
        t("p4.col_category"): [common.label("category", c) for c in bands.index],
        t("p4.col_low"): [f"× {common.fmt_num(v, 2)}" for v in bands["low_mult"]],
        t("p4.col_high"): [f"× {common.fmt_num(v, 2)}" for v in bands["high_mult"]],
    }),
    hide_index=True, width="stretch",
)

# --- Verificări suplimentare: reantrenare lunară, baseline naiv, banda fără privit în viitor ---
st.subheader(t("p4.checks_header"))
rb = common.get_rolling_backtest()
rw = rb["weekly"]
st.caption(t("p4.checks_caption", n=rw["week_start"].nunique(), origins=rb["n_origins"], weeks=rb["baseline_weeks"]))
rolling_wape, baseline_wape = model.wape(rw), model.wape(rw, "baseline_error")
st.dataframe(
    pd.DataFrame({
        t("p4.col_method"): [t("p4.method_static", date=common.fmt_date(bt["train_end"])),
                             t("p4.method_rolling"),
                             t("p4.method_baseline", weeks=rb["baseline_weeks"])],
        t("p4.col_mape"): [common.fmt_pct(overall), common.fmt_pct(model.mape(rw)),
                           common.fmt_pct(rw["baseline_abs_pct_error"].mean())],
        t("p4.col_wape"): [common.fmt_pct(model.wape(weekly)), common.fmt_pct(rolling_wape),
                           common.fmt_pct(baseline_wape)],
    }),
    hide_index=True, width="stretch",
)
st.markdown(f"- {t('p4.vs_baseline', pct=common.fmt_pct(1 - rolling_wape / baseline_wape, 0))}")
cov = rb["coverage"]
st.markdown(f"- {t('p4.coverage', pct=common.fmt_pct(cov['inside_band'].mean(), 0), n=cov['week_start'].nunique())}")

with st.expander(t("p4.worst_header")):
    worst = weekly.nlargest(5, "abs_pct_error")
    st.dataframe(
        pd.DataFrame({
            t("p4.col_week"): [common.fmt_date(d) for d in worst["week_start"]],
            t("p4.col_category"): [common.label("category", c) for c in worst["category"]],
            t("p4.col_actual_fc"): [f"{common.fmt_num(a)} / {common.fmt_num(f)}"
                                    for a, f in zip(worst["actual"], worst["forecast"])],
            t("p4.col_error"): [common.fmt_pct(e) for e in worst["abs_pct_error"]],
        }),
        hide_index=True, width="stretch",
    )
    items = ", ".join(
        f"{common.fmt_date(r.week_start)} = {common.label('week_type', r.week_type).lower()}"
        + (f" ({common.label('event', r.event_name)})" if r.event_name else "")
        for r in worst.itertuples())
    st.caption(t("p4.week_type_caption", items=items))
