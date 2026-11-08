"""
common.py — lucruri folosite de toate paginile:
- încărcarea datelor și calculul modelului cu st.cache_data (se fac o singură dată, apoi din cache);
- mesajul obligatoriu despre datele simulate;
- formatarea numerelor și a datelor în stil românesc.
"""

import pandas as pd
import streamlit as st

import model

DISCLAIMER = "Date simulate, model demonstrativ. Nu reprezintă modelul vreunei companii reale."


@st.cache_data(show_spinner="Se încarcă datele simulate…")
def get_data() -> dict:
    return model.load_data()


@st.cache_data(show_spinner="Se calculează modelul…")
def get_model() -> dict:
    """Modelul antrenat pe tot istoricul (folosit pentru prognozele de azi încolo)."""
    return model.fit_model(get_data())


@st.cache_data(show_spinner="Se testează prognoza pe perioada de test…")
def get_backtest() -> dict:
    """Modelul antrenat doar pe prima parte a istoricului și testat pe restul."""
    return model.backtest(get_data())


@st.cache_data
def get_lines() -> pd.DataFrame:
    return model.prepare_lines(get_data())


def reference_date() -> pd.Timestamp:
    return model.reference_date(get_data())


def show_disclaimer():
    st.info(DISCLAIMER, icon=":material/info:")


def fmt_num(x, decimals: int = 0) -> str:
    """1234.5 → '1.234,5'."""
    s = f"{x:,.{decimals}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_ron(x) -> str:
    return f"{fmt_num(x)} RON"


def fmt_pct(x, decimals: int = 1) -> str:
    return f"{fmt_num(100 * x, decimals)}%"


def fmt_date(d) -> str:
    return pd.Timestamp(d).strftime("%d.%m.%Y")
