"""
model.py — modelul demonstrativ de prognoză (fără machine learning).

IDEEA, PE SCURT
---------------
Pentru fiecare pereche (client, produs):

    cantitate_estimată = cantitate_tipică          # ritmul istoric al clientului
                       × multiplicator_eveniment   # Black Friday / Crăciun / Paște
                       × factor_extern             # temperatură × post

- cantitate_tipică  = cât ia clientul de obicei pe o comandă într-o zi "normală"
                      (fără eveniment, fără post), calculată din ultimele 180 de zile.
- ritmul clientului = mediana zilelor dintre două comenzi consecutive.
- multiplicatorii   = rapoarte simple calculate din istoric, pe tip de client și categorie.
                      Ex.: dacă în zilele de Crăciun retailul a luat băuturi de 1,7 ori mai
                      mult decât în zilele normale, multiplicatorul este 1,7.

Cererea pe zi (folosită pentru stoc):
    cerere_zilnică = cantitate_estimată × frecvența produsului pe comandă ÷ intervalul clientului

Tot aici: eroarea prognozei (MAPE) pe o perioadă de test, cele trei scenarii
(scăzut / de bază / ridicat) și stocul de siguranță.

Toate numerele se calculează din CSV-urile din data/. Singurii parametri scriși de mână
sunt regulile de business de mai jos (pragurile de exces, nivelul de serviciu), marcate ca atare.
"""

from math import sqrt
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"

KEYS = ["customer_type", "category"]  # nivelul la care estimăm multiplicatorii
CATEGORIES = ["Congelate", "Lactate", "Băuturi"]
TEMP_BINS = [-np.inf, 5, 12, 20, np.inf]
TEMP_LABELS = ["sub 5°C", "5–12°C", "12–20°C", "peste 20°C"]
RECENT_DAYS = 180                    # fereastra pentru cantitatea tipică (nivelul recent)
BACKTEST_TRAIN_END = "2025-11-30"    # antrenăm până aici, testăm pe ce urmează

# Reguli de business (parametri demonstrativi, nu rezultate din date):
# peste câte zile de vânzări considerăm stocul "exces", în funcție de cât de perisabil e produsul.
EXCESS_DAYS = {"Congelate": 60, "Lactate": 21, "Băuturi": 45}


# =============================================================================
# 1. Date
# =============================================================================
def load_data(data_dir: Path = DATA_DIR) -> dict:
    """Citește cele patru CSV-uri. Căile sunt relative la acest fișier."""
    customers = pd.read_csv(data_dir / "customers.csv")
    products = pd.read_csv(data_dir / "products.csv")
    orders = pd.read_csv(data_dir / "orders.csv", parse_dates=["order_date"])
    factors = pd.read_csv(data_dir / "external_factors.csv", parse_dates=["date"])
    factors["event"] = factors["event"].fillna("")
    factors["fasting_period"] = factors["fasting_period"].fillna("")
    return {"customers": customers, "products": products, "orders": orders, "factors": factors}


def reference_date(data: dict) -> pd.Timestamp:
    """'Azi' în demonstrație = ziua de după ultima comandă din istoric."""
    return data["orders"]["order_date"].max() + pd.Timedelta(days=1)


def temperature_band(temps: pd.Series) -> pd.Series:
    return pd.cut(temps, bins=TEMP_BINS, labels=TEMP_LABELS, right=False).astype(str)


def prepare_lines(data: dict) -> pd.DataFrame:
    """Liniile de comandă îmbogățite cu tipul clientului, categoria și factorii zilei."""
    lines = (
        data["orders"]
        .merge(data["customers"][["customer_id", "customer_name", "customer_type", "segment"]], on="customer_id")
        .merge(data["products"][["product_id", "product_name", "category", "unit"]], on="product_id")
        .merge(data["factors"][["date", "temperature_c", "is_fasting", "event"]],
               left_on="order_date", right_on="date", how="left")
        .drop(columns="date")
    )
    lines["temp_band"] = temperature_band(lines["temperature_c"])
    lines["value_ron"] = lines["quantity"] * lines["unit_price_ron"]
    return lines


# =============================================================================
# 2. Antrenare: ritm, multiplicatori, cantitate tipică
# =============================================================================
def customer_rhythm(lines: pd.DataFrame) -> pd.DataFrame:
    """Ritmul fiecărui client = mediana zilelor dintre două comenzi."""
    orders = lines[["customer_id", "order_date"]].drop_duplicates().sort_values(["customer_id", "order_date"])
    orders["gap_days"] = orders.groupby("customer_id")["order_date"].diff().dt.days
    return (
        orders.groupby("customer_id")
        .agg(interval_days=("gap_days", "median"),
             n_orders=("order_date", "size"),
             last_order_date=("order_date", "max"))
        .reset_index()
    )


def _ratio_to_normal(lines, mask, group_cols, value_col, name):
    """Media lui `value_col` pe grupurile selectate de `mask`,
    împărțită la media din zilele normale (fără eveniment și fără post)."""
    normal_level = lines[lines["is_normal"]].groupby(KEYS)[value_col].mean().rename("normal_level")
    table = lines[mask].groupby(group_cols)[value_col].mean().rename(name).reset_index()
    table = table.merge(normal_level.reset_index(), on=KEYS)
    table[name] = table[name] / table["normal_level"]
    return table.drop(columns="normal_level")


def _attach(lines, table, on, name):
    """Adaugă factorul din `table` pe fiecare linie (1,0 dacă lipsește)."""
    lines = lines.merge(table, on=on, how="left")
    lines[name] = lines[name].fillna(1.0)
    return lines


def fit_model(data: dict, train_end=None, recent_days: int = RECENT_DAYS) -> dict:
    """Calculează toate componentele modelului din istoricul de până la `train_end`."""
    lines = prepare_lines(data)
    if train_end is not None:
        lines = lines[lines["order_date"] <= pd.Timestamp(train_end)]
    lines = lines.reset_index(drop=True)
    fitted_until = lines["order_date"].max()

    # Pasul 1 — ritmul clientului
    rhythm = customer_rhythm(lines)

    # Pasul 2 — "indicele" fiecărei linii: cantitatea împărțită la media clientului
    # pentru acel produs. Așa putem compara un restaurant mic cu un hotel mare.
    lines["index"] = lines["quantity"] / lines.groupby(["customer_id", "product_id"])["quantity"].transform("mean")
    lines["is_normal"] = (lines["event"] == "") & ~lines["is_fasting"]
    lines["adjusted"] = lines["index"]

    # 2a. Temperatura: indicele mediu pe fiecare bandă de temperatură, în zilele normale
    temp_factors = _ratio_to_normal(lines, lines["is_normal"], KEYS + ["temp_band"], "adjusted", "temp_factor")
    lines = _attach(lines, temp_factors, KEYS + ["temp_band"], "temp_factor")
    lines["adjusted"] = lines["adjusted"] / lines["temp_factor"]

    # 2b. Postul: zile de post fără eveniment, după ce am scos efectul temperaturii
    post_mask = lines["is_fasting"] & (lines["event"] == "")
    post_factors = _ratio_to_normal(lines, post_mask, KEYS, "adjusted", "post_factor")
    lines = _attach(lines, post_factors, KEYS, "post_factor")
    lines["post_factor"] = np.where(lines["is_fasting"], lines["post_factor"], 1.0)
    lines["adjusted"] = lines["adjusted"] / lines["post_factor"]

    # 2c. Evenimentele: ce rămâne după ce am scos temperatura și postul
    event_factors = _ratio_to_normal(lines, lines["event"] != "", ["event"] + KEYS, "adjusted", "event_factor")
    lines = _attach(lines, event_factors, ["event"] + KEYS, "event_factor")

    # Pasul 3 — cantitatea tipică: cantitatea "curățată" de efectele zilei, pe ultimele N zile
    lines["qty_normal"] = lines["quantity"] / (lines["temp_factor"] * lines["post_factor"] * lines["event_factor"])
    recent = lines[lines["order_date"] > fitted_until - pd.Timedelta(days=recent_days)]
    n_recent = recent.groupby("customer_id")["order_id"].nunique().rename("n_recent_orders").reset_index()
    baseline = (
        recent.groupby(["customer_id", "customer_type", "product_id", "category"])
        .agg(typical_qty=("qty_normal", "mean"), n_orders_with_product=("order_id", "nunique"))
        .reset_index()
        .merge(n_recent, on="customer_id")
    )
    # frecvența = în câte comenzi din 100 apare produsul
    baseline["frequency"] = baseline["n_orders_with_product"] / baseline["n_recent_orders"]

    return {
        "fitted_until": fitted_until,
        "rhythm": rhythm,
        "temp_factors": temp_factors,
        "post_factors": post_factors,
        "event_factors": event_factors,
        "baseline": baseline,
    }


# =============================================================================
# 3. Prognoză
# =============================================================================
def factor_grid(model: dict, factors: pd.DataFrame, start, end, event_override=None) -> pd.DataFrame:
    """Pentru fiecare zi și fiecare (tip client, categorie): factorul extern și multiplicatorul de eveniment.
    event_override: None = evenimentele din calendar; "" = fără eveniment; "Crăciun" = forțează un eveniment."""
    days = factors[(factors["date"] >= start) & (factors["date"] <= end)]
    days = days[["date", "temperature_c", "is_fasting", "event"]].copy()
    if event_override is not None:
        days["event"] = event_override
    days["temp_band"] = temperature_band(days["temperature_c"])

    combos = model["baseline"][KEYS].drop_duplicates()
    grid = days.merge(combos, how="cross")
    grid = grid.merge(model["temp_factors"], on=KEYS + ["temp_band"], how="left")
    grid = grid.merge(model["post_factors"], on=KEYS, how="left")
    grid = grid.merge(model["event_factors"], on=["event"] + KEYS, how="left")
    grid["temp_factor"] = grid["temp_factor"].fillna(1.0)
    grid["post_factor"] = np.where(grid["is_fasting"], grid["post_factor"].fillna(1.0), 1.0)
    grid["event_factor"] = grid["event_factor"].fillna(1.0)
    grid["external_factor"] = grid["temp_factor"] * grid["post_factor"]
    return grid


def daily_demand(model: dict, factors: pd.DataFrame, start, end, event_override=None) -> pd.DataFrame:
    """Cererea estimată pe zi, client și produs:
    cantitate_tipică × frecvență ÷ interval × multiplicator_eveniment × factor_extern."""
    grid = factor_grid(model, factors, start, end, event_override)
    pairs = model["baseline"].merge(model["rhythm"][["customer_id", "interval_days"]], on="customer_id")
    pairs["per_day"] = pairs["typical_qty"] * pairs["frequency"] / pairs["interval_days"]
    demand = pairs.merge(grid[["date", "event"] + KEYS + ["event_factor", "external_factor"]], on=KEYS)
    demand["forecast"] = demand["per_day"] * demand["event_factor"] * demand["external_factor"]
    return demand[["date", "customer_id", "customer_type", "product_id", "category", "event", "forecast"]]


def predict_next_order(model: dict, data: dict, customer_id: str, today: pd.Timestamp) -> dict:
    """Următoarea comandă a unui client: data (ultima comandă + ritm) și coșul estimat."""
    r = model["rhythm"].set_index("customer_id").loc[customer_id]
    step = max(1, int(round(r["interval_days"])))
    expected = r["last_order_date"] + pd.Timedelta(days=step)
    overdue_days = max(0, (today - expected).days)
    order_date = max(expected, today)  # dacă a întârziat, ne așteptăm să comande azi

    grid = factor_grid(model, data["factors"], order_date, order_date)
    cols = KEYS + ["event", "temperature_c", "is_fasting", "temp_factor", "post_factor",
                   "event_factor", "external_factor"]
    basket = model["baseline"][model["baseline"]["customer_id"] == customer_id].merge(grid[cols], on=KEYS)
    basket["estimated_qty"] = basket["typical_qty"] * basket["event_factor"] * basket["external_factor"]
    basket = basket.merge(data["products"][["product_id", "product_name", "unit", "price_ron"]], on="product_id")
    basket["estimated_value_ron"] = basket["estimated_qty"].round().clip(lower=1) * basket["price_ron"]
    return {
        "date": order_date,
        "expected_date": expected,
        "overdue_days": overdue_days,
        "interval_days": float(r["interval_days"]),
        "last_order_date": r["last_order_date"],
        "basket": basket.sort_values(["frequency", "estimated_value_ron"], ascending=False),
    }


def upcoming_orders(model: dict, today: pd.Timestamp, horizon_days: int) -> pd.DataFrame:
    """Toate comenzile estimate ale clienților în următoarele `horizon_days` zile."""
    end = today + pd.Timedelta(days=horizon_days - 1)
    rows = []
    for r in model["rhythm"].itertuples(index=False):
        step = max(1, int(round(r.interval_days)))
        expected = r.last_order_date + pd.Timedelta(days=step)
        overdue = max(0, (today - expected).days)
        day = max(expected, today)
        first = True
        while day <= end:
            rows.append({"customer_id": r.customer_id, "order_date": day,
                         "days_until": (day - today).days, "overdue_days": overdue if first else 0,
                         "interval_days": r.interval_days})
            first = False
            day += pd.Timedelta(days=step)
    return pd.DataFrame(rows).sort_values(["order_date", "customer_id"]).reset_index(drop=True)


def upcoming_events(factors: pd.DataFrame, today: pd.Timestamp) -> pd.DataFrame:
    """Ferestrele de eveniment din calendar, de azi încolo (eveniment, început, sfârșit, zile)."""
    f = factors[(factors["date"] >= today) & (factors["event"] != "")].sort_values("date")
    new_block = (f["event"] != f["event"].shift()) | (f["date"].diff().dt.days != 1)
    f = f.assign(block=new_block.cumsum())
    return (
        f.groupby("block")
        .agg(event=("event", "first"), start=("date", "min"), end=("date", "max"), days=("date", "size"))
        .reset_index(drop=True)
    )


# =============================================================================
# 4. Acuratețe: testăm modelul pe luni pe care nu le-a văzut
# =============================================================================
def _week_start(dates: pd.Series) -> pd.Series:
    """Lunea săptămânii din care face parte fiecare dată."""
    return dates - pd.to_timedelta(dates.dt.weekday, unit="D")


def _compare(forecast, actual, keys):
    f = forecast.groupby(keys)["forecast"].sum()
    a = actual.groupby(keys)["quantity"].sum().rename("actual")
    out = pd.concat([f, a], axis=1).fillna(0.0).reset_index()
    out["error"] = out["actual"] - out["forecast"]
    return out


def backtest(data: dict, train_end=BACKTEST_TRAIN_END) -> dict:
    """Antrenează modelul până la `train_end` și compară prognoza cu comenzile reale simulate
    din perioada următoare, pe săptămâni. Comenzile pierdute contează: au fost cerere reală."""
    train_end = pd.Timestamp(train_end)
    test_start = train_end + pd.Timedelta(days=1)
    test_end = data["orders"]["order_date"].max()

    fitted = fit_model(data, train_end=train_end)
    forecast = daily_demand(fitted, data["factors"], test_start, test_end)
    lines = prepare_lines(data)
    actual = lines[(lines["order_date"] >= test_start) & (lines["order_date"] <= test_end)]

    forecast = forecast.assign(week_start=_week_start(forecast["date"]))
    actual = actual.assign(week_start=_week_start(actual["order_date"]))

    # Tipul săptămânii: cu eveniment, de post sau normală
    f = data["factors"].assign(week_start=_week_start(data["factors"]["date"]),
                               has_event=data["factors"]["event"] != "")
    weeks = f.groupby("week_start").agg(has_event=("has_event", "max"), fasting_days=("is_fasting", "sum"))
    weeks["week_type"] = np.select([weeks["has_event"], weeks["fasting_days"] >= 4],
                                   ["eveniment", "post"], "normală")
    week_event = (f[f["has_event"]].groupby("week_start")["event"].first().rename("event_name"))

    def keep_full_weeks(df):
        full = (df["week_start"] >= test_start) & (df["week_start"] + pd.Timedelta(days=6) <= test_end)
        df = df[full].merge(weeks[["week_type"]].reset_index(), on="week_start", how="left")
        return df.merge(week_event.reset_index(), on="week_start", how="left").fillna({"event_name": ""})

    weekly_category = keep_full_weeks(_compare(forecast, actual, ["week_start", "category"]))
    weekly_category["abs_pct_error"] = weekly_category["error"].abs() / weekly_category["actual"]
    weekly_category["pct_error"] = weekly_category["error"] / weekly_category["forecast"]
    weekly_product = keep_full_weeks(_compare(forecast, actual, ["week_start", "product_id", "category"]))

    return {
        "train_start": lines["order_date"].min(),
        "train_end": train_end,
        "test_start": test_start,
        "test_end": test_end,
        "weekly_category": weekly_category,
        "weekly_product": weekly_product,
    }


def mape(weekly: pd.DataFrame) -> float:
    """MAPE = media erorilor procentuale absolute |real − prognoză| / real."""
    return float(weekly["abs_pct_error"].mean())


def mape_by(weekly: pd.DataFrame, column: str) -> pd.Series:
    return weekly.groupby(column)["abs_pct_error"].mean()


def scenario_bands(weekly_category: pd.DataFrame, low_q: float = 0.10, high_q: float = 0.90) -> pd.DataFrame:
    """Scenariile vin din erorile trecute: dacă în 10% din săptămâni realul a fost cu 12% sub prognoză,
    scenariul scăzut = prognoza × 0,88. Analog pentru scenariul ridicat (percentila 90)."""
    q = weekly_category.groupby("category")["pct_error"].quantile([low_q, high_q]).unstack()
    return pd.DataFrame({
        "low_mult": (1 + q[low_q]).clip(upper=1.0),
        "high_mult": (1 + q[high_q]).clip(lower=1.0),
    })


def event_widening(weekly_category: pd.DataFrame) -> float:
    """De câte ori e mai mare eroarea în săptămânile cu eveniment decât în cele normale (minim 1)."""
    by_type = mape_by(weekly_category, "week_type")
    if "eveniment" not in by_type.index or "normală" not in by_type.index:
        return 1.0
    return max(1.0, float(by_type["eveniment"] / by_type["normală"]))


def scenario_multipliers(bands: pd.DataFrame, category: str, widening: float = 1.0) -> tuple:
    """(multiplicator scăzut, multiplicator ridicat), lărgite cu `widening` pentru evenimente."""
    low = 1 - (1 - bands.loc[category, "low_mult"]) * widening
    high = 1 + (bands.loc[category, "high_mult"] - 1) * widening
    return max(0.0, float(low)), float(high)


def error_sigma(weekly: pd.DataFrame, key: str) -> pd.Series:
    """Abaterea standard a erorii săptămânale (în unități), pe produs sau pe categorie."""
    return weekly.groupby(key)["error"].std()


def z_score(service_level: float) -> float:
    return NormalDist().inv_cdf(service_level)


def safety_stock(sigma_week: float, days: float, service_level: float = 0.95) -> float:
    """Stoc de siguranță = z × σ_eroare_săptămânală × √(zile / 7)."""
    return z_score(service_level) * sigma_week * sqrt(max(days, 0) / 7)


# =============================================================================
# 5. Stoc: ce avem vs. ce estimăm că se va cere
# =============================================================================
def stock_check(model: dict, data: dict, today: pd.Timestamp, horizon_days: int,
                sigma_week_by_product: pd.Series, service_level: float = 0.95) -> pd.DataFrame:
    """Pentru fiecare produs: cererea în timpul livrării de la furnizor, stocul de siguranță,
    riscul de lipsă, zilele de acoperire și cantitatea recomandată de comandat."""
    products = data["products"].copy()
    max_days = int(products["lead_time_days"].max()) + horizon_days + 30
    fc = daily_demand(model, data["factors"], today, today + pd.Timedelta(days=max_days))
    daily = fc.groupby(["product_id", "date"])["forecast"].sum().reset_index()
    daily["day"] = (daily["date"] - today).dt.days
    daily = daily.merge(products[["product_id", "lead_time_days"]], on="product_id")

    # Cererea pe trei ferestre: cât durează livrarea, livrare + orizont, următoarele 30 de zile
    daily["in_lead"] = daily["forecast"] * (daily["day"] < daily["lead_time_days"])
    daily["in_cover"] = daily["forecast"] * (daily["day"] < daily["lead_time_days"] + horizon_days)
    daily["in_30"] = daily["forecast"] * (daily["day"] < 30)
    sums = daily.groupby("product_id")[["in_lead", "in_cover", "in_30"]].sum()
    sums.columns = ["demand_lead", "demand_cover", "demand_30d"]
    df = products.merge(sums.reset_index(), on="product_id", how="left").fillna(
        {"demand_lead": 0.0, "demand_cover": 0.0, "demand_30d": 0.0})

    sigma = df["product_id"].map(sigma_week_by_product).fillna(0.0)
    df["sigma_lead"] = sigma * np.sqrt(df["lead_time_days"] / 7)
    df["safety_stock"] = z_score(service_level) * df["sigma_lead"]
    df["reorder_point"] = df["demand_lead"] + df["safety_stock"]

    # Risc de lipsă = probabilitatea ca cererea din timpul livrării să depășească stocul
    z = (df["stock_units"] - df["demand_lead"]) / df["sigma_lead"].replace(0, np.nan)
    df["shortage_risk"] = [1 - NormalDist().cdf(v) if pd.notna(v) else 0.0 for v in z]

    avg_daily = df["demand_30d"] / 30
    df["days_of_cover"] = df["stock_units"] / avg_daily.replace(0, np.nan)
    df["excess_threshold_days"] = df["category"].map(EXCESS_DAYS)
    df["order_qty"] = np.ceil((df["demand_cover"] + df["safety_stock"] - df["stock_units"]).clip(lower=0))
    df["excess_units"] = (df["stock_units"] - df["excess_threshold_days"] * avg_daily).clip(lower=0).round()

    df["status"] = np.select(
        [df["stock_units"] < df["reorder_point"], df["days_of_cover"] > df["excess_threshold_days"]],
        ["Lipsă", "Exces"], "OK")
    return df


def event_scenarios(model: dict, data: dict, bands: pd.DataFrame, widening: float,
                    sigma_week_by_category: pd.Series, category: str, start: pd.Timestamp,
                    days: int, event: str, service_level: float = 0.95) -> dict:
    """Cererea pe o categorie într-o perioadă, în trei scenarii, plus stocul recomandat.
    `event` se aplică pe toate zilele perioadei ("" = fără eveniment)."""
    end = start + pd.Timedelta(days=days - 1)
    with_event = daily_demand(model, data["factors"], start, end, event_override=event)
    without = daily_demand(model, data["factors"], start, end, event_override="")
    daily = with_event[with_event["category"] == category].groupby("date")["forecast"].sum()
    daily_no_event = without[without["category"] == category].groupby("date")["forecast"].sum()

    w = widening if event else 1.0
    low_mult, high_mult = scenario_multipliers(bands, category, w)
    sigma = float(sigma_week_by_category.get(category, 0.0)) * w
    base = float(daily.sum())
    ss = safety_stock(sigma, len(daily), service_level)
    return {
        "days_covered": len(daily),
        "daily": pd.DataFrame({"low": daily * low_mult, "base": daily, "high": daily * high_mult}),
        "low": base * low_mult, "base": base, "high": base * high_mult,
        "low_mult": low_mult, "high_mult": high_mult, "widening": w,
        "no_event": float(daily_no_event.sum()),
        "safety_stock": ss,
        "recommended_stock": base + ss,
    }
