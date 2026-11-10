"""
export_powerbi.py: scrie patru CSV-uri pentru Power BI în data/powerbi/.

  orders_history.csv       comenzile istorice (o linie = un produs dintr-o comandă)
  forecast_scenarios.csv   prognoza zilnică pe produs, următoarele 90 de zile, în 3 scenarii
  stock_vs_demand.csv      stocul curent vs. cererea estimată, pe produs
  forecast_error.csv       prognoză vs. real pe săptămâni și categorii (perioada de test)

Datele sunt în format ISO (AAAA-LL-ZZ). Fișierele au BOM UTF-8 ca diacriticele
să apară corect și în Excel, nu doar în Power BI.

Rulare: python export_powerbi.py  (rulează automat și la final în generate_data.py)
"""

import pandas as pd

import model

OUT_DIR = model.DATA_DIR / "powerbi"
FORECAST_DAYS = 90
SERVICE_LEVEL = 0.95
HORIZON_DAYS = 14


def iso(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series).dt.strftime("%Y-%m-%d")


def save(df: pd.DataFrame, name: str):
    df.to_csv(OUT_DIR / name, index=False, encoding="utf-8-sig")
    print(f"  {name}: {len(df)} randuri")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = model.load_data()
    fitted = model.fit_model(data)
    bt = model.backtest(data)
    today = model.reference_date(data)
    weekly_cat = bt["weekly_category"]
    bands = model.scenario_bands(weekly_cat)
    widening = model.event_widening(weekly_cat)
    print("Export Power BI:")

    # 1. Comenzile istorice
    lines = model.prepare_lines(data)
    history = lines.assign(order_date=iso(lines["order_date"]))[[
        "order_id", "order_date", "customer_id", "customer_name", "customer_type", "segment",
        "product_id", "product_name", "category", "unit", "quantity", "unit_price_ron", "value_ron",
        "status", "delivery_delay_days"]]
    save(history, "orders_history.csv")

    # 2. Prognoza pe scenarii (zilnic, pe produs)
    fc = model.daily_demand(fitted, data["factors"], today, today + pd.Timedelta(days=FORECAST_DAYS - 1))
    daily = fc.groupby(["date", "product_id", "category", "event"])["forecast"].sum().reset_index()
    low_high = daily.apply(
        lambda r: model.scenario_multipliers(bands, r["category"], widening if r["event"] else 1.0),
        axis=1, result_type="expand")
    daily["forecast_low"] = (daily["forecast"] * low_high[0]).round(2)
    daily["forecast_base"] = daily["forecast"].round(2)
    daily["forecast_high"] = (daily["forecast"] * low_high[1]).round(2)
    daily = daily.merge(data["products"][["product_id", "product_name"]], on="product_id")
    daily["week_start"] = iso(daily["date"] - pd.to_timedelta(daily["date"].dt.weekday, unit="D"))
    daily["date"] = iso(daily["date"])
    save(daily[["date", "week_start", "product_id", "product_name", "category", "event",
                "forecast_low", "forecast_base", "forecast_high"]], "forecast_scenarios.csv")

    # 3. Stoc vs. cerere estimată
    sigma = model.error_sigma(bt["weekly_product"], "product_id")
    stock = model.stock_check(fitted, data, today, HORIZON_DAYS, sigma, SERVICE_LEVEL)
    stock.insert(0, "snapshot_date", today.strftime("%Y-%m-%d"))
    cols = ["snapshot_date", "product_id", "product_name", "category", "unit", "price_ron", "stock_units",
            "lead_time_days", "demand_lead", "demand_cover", "demand_30d", "safety_stock", "reorder_point",
            "shortage_risk", "days_of_cover", "order_qty", "excess_units", "status"]
    save(stock[cols].round(3), "stock_vs_demand.csv")

    # 4. Eroarea prognozei pe perioada de test
    err = weekly_cat.assign(week_start=iso(weekly_cat["week_start"]))
    save(err[["week_start", "category", "week_type", "event_name", "forecast", "actual", "error",
              "abs_pct_error", "pct_error"]].round(4), "forecast_error.csv")


if __name__ == "__main__":
    main()
