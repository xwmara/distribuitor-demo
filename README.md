# Distribuitor Demo SRL: B2B order forecasting demo

A small Streamlit app showing the **Predict → Decide → Act** cycle for a fictional B2B food
distributor: predict when each customer will order and how much, compare that with stock,
and turn the result into concrete actions (order from the supplier now, call a customer,
handle overstock).

> **Simulated data, demo model.** It does not represent the model of any real company.
> "Distribuitor Demo SRL", its customers, products, prices and orders are all invented.
> The model is a transparent rule-based calculation (no machine learning).

## What is simulated

Everything in `data/` is produced by `generate_data.py` with a fixed random seed (42):

| File | Content |
|---|---|
| `data/customers.csv` | 25 fictional customers: 18 HoReCa (restaurants, cafés, hotels) and 7 small retail shops, each with its own ordering rhythm |
| `data/products.csv` | 30 products in 3 categories (frozen, dairy, beverages) with price, current stock and supplier lead time |
| `data/orders.csv` | 24 months of order lines (Nov 2024 – Oct 2026) with seasonality (Christmas, Easter, fasting periods, summer), noise, a slight trend, and some lost or late orders |
| `data/external_factors.csv` | One row per day: season, Orthodox fasting period, simulated temperature and event windows (Black Friday, Christmas, Easter), extended to May 2027 for forecasting |

The model never reads the generator's hidden effects. It re-estimates everything from the CSV files.

## The model (in `model.py`)

```
estimated quantity = typical quantity of the customer for that product
                   × event multiplier (event, customer type, category)
                   × external factor  (temperature band × fasting)
```

- **Customer rhythm**: median number of days between consecutive orders.
- **Multipliers**: simple ratios from history (e.g. retail beverage volume in Christmas windows ÷ volume on normal days).
- **Accuracy**: trained until 30 Nov 2025, tested on Dec 2025 – Oct 2026, measured with weekly MAPE per category.
- **Scenarios**: low / base / high from the 10th and 90th percentile of past forecast errors, widened for events when event weeks were less accurate.
- **Safety stock**: `z × σ(weekly forecast error) × √(days / 7)`.

## App pages

The app is bilingual (Romanian / English): use the language switch in the sidebar, or open it with `?lang=en` in the URL. All interface text lives in `i18n.py`.


0. **Start**: the problem (stock-outs, overstock, reactive ordering) and the Predict → Decide → Act cycle.
1. **Customer prediction**: order history, rhythm, and the next estimated order (date, products, quantities).
2. **Event & scenarios**: pick an event, category, stock, price and date; see demand in three scenarios and the recommended stock.
3. **Decide**: a prioritised action list with shortage/overstock risk, plus a downloadable draft purchase order.
4. **Forecast accuracy**: forecast vs. simulated actuals, MAPE, and a note on when to widen the interval.

## Run locally

Requires Python 3.11+ (pandas 3 needs 3.11 or newer).

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The data is already in `data/`, so the app starts right away. To regenerate it
(same result every time, thanks to the fixed seed):

```bash
python generate_data.py
```

This also rewrites the Power BI exports.

## Power BI exports

`data/powerbi/` contains four CSV files (UTF-8 with BOM, ISO dates `YYYY-MM-DD`):

| File | Content |
|---|---|
| `orders_history.csv` | Historical order lines with customer and product attributes |
| `forecast_scenarios.csv` | Daily forecast per product for the next 90 days, in low / base / high scenarios |
| `stock_vs_demand.csv` | Current stock vs. expected demand, safety stock, shortage risk and suggested order per product |
| `forecast_error.csv` | Weekly forecast vs. actual per category over the test period, with error metrics |

To regenerate only the exports: `python export_powerbi.py`.

## Deploy on Streamlit Community Cloud

1. Push this folder to a GitHub repository (including `data/`).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub and click **Create app**.
3. Pick the repository and branch, and set **Main file path** to `app.py`.
4. Under **Advanced settings**, choose Python 3.12 (or newer).
5. Click **Deploy**. No secrets or API keys are needed.

All file paths are relative to the source files (`pathlib`), so the app behaves the same locally and in the cloud.

## Project structure

```
app.py               entry point, navigation, disclaimer on every page
common.py            cached data/model loading, current language, formatting and chart helpers
i18n.py              all interface texts in Romanian and English, plus number/date formatting per language
model.py             the forecasting model, accuracy, scenarios, safety stock, stock check
decide.py            rules that turn the forecast into actions
generate_data.py     simulated data generator (fixed seed)
export_powerbi.py    Power BI CSV exports
app_pages/           the five pages
data/                simulated CSV data (+ data/powerbi/ exports)
PROJECT_NOTES.md     detailed notes (in Romanian)
```
