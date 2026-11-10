"""
common.py: lucruri folosite de toate paginile:
- încărcarea datelor și calculul modelului cu st.cache_data (se fac o singură dată, apoi din cache);
- limba aleasă (st.session_state["lang"]) și scurtături pentru textele din i18n.py;
- formatarea numerelor și a datelor în limba aleasă.
"""

import altair as alt
import pandas as pd
import streamlit as st

import i18n
import model

# Formatul datelor pe axele graficelor: numeric, ca să nu apară nume de luni în engleză în versiunea RO
AXIS_DATE_FORMAT = {"ro": "%d.%m.%y", "en": "%Y-%m-%d"}
AXIS_MONTH_FORMAT = {"ro": "%m.%Y", "en": "%Y-%m"}
TOOLTIP_DATE_FORMAT = {"ro": "%d.%m.%Y", "en": "%Y-%m-%d"}


@st.cache_data(show_spinner=False)
def get_data() -> dict:
    return model.load_data()


@st.cache_data(show_spinner=False)
def get_model() -> dict:
    """Modelul antrenat pe tot istoricul (folosit pentru prognozele de azi încolo)."""
    return model.fit_model(get_data())


@st.cache_data(show_spinner=False)
def get_backtest() -> dict:
    """Modelul antrenat doar pe prima parte a istoricului și testat pe restul."""
    return model.backtest(get_data())


@st.cache_data(show_spinner=False)
def get_rolling_backtest() -> dict:
    """Backtest pe ferestre succesive: model reantrenat lunar + baseline naiv."""
    return model.rolling_backtest(get_data())


@st.cache_data(show_spinner=False)
def get_lines() -> pd.DataFrame:
    return model.prepare_lines(get_data())


def reference_date() -> pd.Timestamp:
    return model.reference_date(get_data())


# --- Limba -------------------------------------------------------------------
def lang() -> str:
    """Limba aleasă în sidebar (implicit română). Selectorul e în app.py, cu key="lang"."""
    return st.session_state.get("lang", i18n.DEFAULT_LANG)


def t(key: str, **kwargs) -> str:
    return i18n.t(key, lang(), **kwargs)


def label(group: str, value) -> str:
    return i18n.label(group, value, lang())


def show_disclaimer():
    st.info(t("app.disclaimer"), icon=":material/info:")


# --- Grafice -------------------------------------------------------------------
def time_chart(df: pd.DataFrame, x: str, y_cols: list, x_title: str, y_title: str,
               kind: str = "line", height: int = 260, monthly: bool = False):
    """Grafic în timp (linie sau bare) cu titluri și formatul datelor în limba aleasă.
    `y_cols` = coloanele de desenat; numele lor apar în legendă."""
    long = df.melt(id_vars=[x], value_vars=y_cols, var_name="series", value_name="value").rename(columns={x: "x"})
    axis_fmt = (AXIS_MONTH_FORMAT if monthly else AXIS_DATE_FORMAT)[lang()]
    tip_fmt = AXIS_MONTH_FORMAT[lang()] if monthly else TOOLTIP_DATE_FORMAT[lang()]
    base = alt.Chart(long)
    mark = base.mark_bar() if kind == "bar" else base.mark_line()
    encoding = {
        "x": alt.X("x:T", title=x_title, axis=alt.Axis(format=axis_fmt, labelAngle=0)),
        "y": alt.Y("value:Q", title=y_title),
        "tooltip": [alt.Tooltip("x:T", title=x_title, format=tip_fmt),
                    alt.Tooltip("series:N", title=""),
                    alt.Tooltip("value:Q", title=y_title, format=",.0f")],
    }
    if len(y_cols) > 1:  # legenda doar când sunt mai multe serii
        encoding["color"] = alt.Color("series:N", sort=y_cols, legend=alt.Legend(orient="bottom", title=None))
    st.altair_chart(mark.encode(**encoding).properties(height=height), width="stretch")


# --- Formatare în limba aleasă -------------------------------------------------
def fmt_num(x, decimals: int = 0) -> str:
    return i18n.fmt_num(x, lang(), decimals)


def fmt_days(x) -> str:
    return i18n.fmt_days(x, lang())


def fmt_ron(x) -> str:
    return i18n.fmt_ron(x, lang())


def fmt_pct(x, decimals: int = 1) -> str:
    return i18n.fmt_pct(x, lang(), decimals)


def fmt_date(d) -> str:
    return i18n.fmt_date(d, lang())
