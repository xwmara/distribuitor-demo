"""
generate_data.py: generează datele SIMULATE ale proiectului.

"Distribuitor Demo SRL" este o firmă fictivă. Nimic din acest fișier nu provine
de la o companie reală: clienții, produsele, prețurile și comenzile sunt
create de un generator aleator cu seed fix (rezultatul este mereu același).

Ce produce (în folderul data/):
  customers.csv         25 de clienți (18 Horeca, 7 retail), fiecare cu ritmul lui de comandă
  products.csv          30 de produse în 3 categorii, cu preț, stoc curent și timp de livrare
  orders.csv            24 de luni de comenzi (o linie = un produs dintr-o comandă)
  external_factors.csv  factori externi pe zile: sezon, post, temperatură, evenimente

La final rulează export_powerbi.py, care scrie fișierele pentru Power BI în data/powerbi/.

Rulare:  python generate_data.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

HISTORY_START = pd.Timestamp("2024-11-01")
HISTORY_END = pd.Timestamp("2026-10-31")  # 24 de luni de istoric
FACTORS_END = pd.Timestamp("2027-05-31")  # factorii externi acoperă și perioada prognozată

# Paștele ortodox (data fixă pe ani, ca să nu complicăm codul cu un algoritm de calcul)
ORTHODOX_EASTER = {2025: "2025-04-20", 2026: "2026-04-12", 2027: "2027-05-02"}

SEASON_BY_MONTH = {
    12: "iarnă", 1: "iarnă", 2: "iarnă",
    3: "primăvară", 4: "primăvară", 5: "primăvară",
    6: "vară", 7: "vară", 8: "vară",
    9: "toamnă", 10: "toamnă", 11: "toamnă",
}

CITIES = ["București", "Cluj-Napoca", "Brașov", "Sibiu", "Iași", "Timișoara"]

# Tipuri de clienți. "interval" = la câte zile comandă (min, max);
# "size" = cât de mare e clientul față de unul mediu; "code" = ce produse i se potrivesc.
SEGMENTS = {
    "Restaurant": {
        "type": "Horeca", "interval": (3, 6), "size": (0.9, 1.5), "code": "R",
        "names": ["Bistro Castanul", "Restaurant Moara Veche", "Trattoria Pădurea",
                  "Restaurant Hanul Verde", "Bistro Strada Mare", "Restaurant Grădina cu Tei",
                  "Pizzeria Cuptorul", "Restaurant Malul Lacului"],
    },
    "Cafenea": {
        "type": "Horeca", "interval": (2, 4), "size": (0.6, 1.0), "code": "C",
        "names": ["Cafeneaua Boabe Calde", "Café Colț de Carte", "Cafeneaua Ceașca Albastră",
                  "Cafeneaua Piața Mică", "Café Fereastra"],
    },
    "Hotel": {
        "type": "Horeca", "interval": (5, 8), "size": (1.3, 2.2), "code": None,  # cumpără de toate
        "names": ["Hotel Panorama", "Hotel Brazii", "Pensiunea Valea Însorită",
                  "Hotel Central Parc", "Hotel Lacul Albastru"],
    },
    "Magazin": {
        "type": "Retail", "interval": (6, 11), "size": (1.5, 2.5), "code": None,  # cumpără de toate
        "names": ["Minimarket La Colț", "Magazinul Familiei", "Alimentara Cartier 3",
                  "Minimarket Stejarul", "Magazin Mixt Nord", "Alimentara Bulevard",
                  "Minimarket Răsărit"],
    },
}

# Produse: nume, categorie, unitate, preț (RON), cantitate tipică pe comandă,
# pentru cine se potrivește (R = restaurant, C = cafenea; hotelurile și magazinele iau orice).
PRODUCTS = [
    ("Cartofi prăjiți congelați 2,5 kg", "Congelate", "pungă", 32.0, 10, "R"),
    ("Legume mexicane congelate 1 kg", "Congelate", "pungă", 14.5, 6, "R"),
    ("Mazăre congelată 1 kg", "Congelate", "pungă", 11.0, 5, "R"),
    ("Pizza margherita congelată (bax 6)", "Congelate", "bax", 96.0, 3, "RC"),
    ("Croissant cu unt congelat (bax 40)", "Congelate", "bax", 138.0, 2, "C"),
    ("Înghețată vanilie 5 L", "Congelate", "cutie", 85.0, 2, "RC"),
    ("Înghețată ciocolată 5 L", "Congelate", "cutie", 89.0, 2, "RC"),
    ("File de pește congelat 1 kg", "Congelate", "pungă", 46.0, 5, "R"),
    ("Chiftele de vită congelate 2 kg", "Congelate", "pungă", 68.0, 3, "R"),
    ("Clătite congelate (bax 20)", "Congelate", "bax", 54.0, 2, "C"),
    ("Lapte 3,5% 1 L", "Lactate", "litru", 7.2, 24, "RC"),
    ("Smântână 20% 1 kg", "Lactate", "găleată", 19.5, 6, "R"),
    ("Brânză telemea 1 kg", "Lactate", "kg", 34.0, 5, "R"),
    ("Cașcaval 1 kg", "Lactate", "kg", 42.0, 5, "RC"),
    ("Mozzarella 1 kg", "Lactate", "kg", 38.0, 6, "R"),
    ("Unt 82% 1 kg", "Lactate", "kg", 48.0, 3, "RC"),
    ("Iaurt natural 1 kg", "Lactate", "găleată", 12.5, 6, "RC"),
    ("Frișcă lichidă 1 L", "Lactate", "litru", 21.0, 6, "RC"),
    ("Brânză de vaci 1 kg", "Lactate", "kg", 22.0, 4, "R"),
    ("Lapte pentru barista 1 L", "Lactate", "litru", 8.9, 30, "C"),
    ("Apă plată 0,5 L (bax 12)", "Băuturi", "bax", 18.0, 10, "RC"),
    ("Apă minerală 0,5 L (bax 12)", "Băuturi", "bax", 19.0, 10, "RC"),
    ("Suc de portocale 1 L", "Băuturi", "litru", 9.5, 12, "RC"),
    ("Limonadă 0,33 L (bax 24)", "Băuturi", "bax", 72.0, 3, "RC"),
    ("Cola 0,33 L (bax 24)", "Băuturi", "bax", 66.0, 4, "RC"),
    ("Cafea boabe 1 kg", "Băuturi", "kg", 95.0, 4, "RC"),
    ("Ceai negru (100 plicuri)", "Băuturi", "cutie", 28.0, 2, "C"),
    ("Bere fără alcool 0,5 L (bax 20)", "Băuturi", "bax", 84.0, 2, "R"),
    ("Vin alb sec 0,75 L", "Băuturi", "sticlă", 29.0, 12, "R"),
    ("Sirop de soc 1 L", "Băuturi", "sticlă", 24.0, 3, "C"),
]

# Timpul de livrare de la furnizor, în zile (min, max), pe categorie
LEAD_TIME_DAYS = {"Congelate": (5, 7), "Lactate": (2, 3), "Băuturi": (3, 5)}

# --- Regulile "ascunse" ale simulării --------------------------------------
# Generatorul folosește aceste efecte ca să creeze istoricul. Modelul (model.py)
# NU le citește: el le re-estimează doar din CSV-uri, ca într-un caz real.
EVENT_EFFECT = {
    ("Black Friday", "Retail"): {"Congelate": 1.40, "Lactate": 1.15, "Băuturi": 1.50},
    ("Black Friday", "Horeca"): {"Congelate": 1.05, "Lactate": 1.00, "Băuturi": 1.10},
    ("Crăciun", "Retail"): {"Congelate": 1.45, "Lactate": 1.35, "Băuturi": 1.80},
    ("Crăciun", "Horeca"): {"Congelate": 1.30, "Lactate": 1.20, "Băuturi": 1.55},
    ("Paște", "Retail"): {"Congelate": 1.25, "Lactate": 1.60, "Băuturi": 1.35},
    ("Paște", "Horeca"): {"Congelate": 1.20, "Lactate": 1.40, "Băuturi": 1.25},
}
FASTING_EFFECT = {  # în post scad lactatele; congelatele (pește, legume) cresc puțin
    ("Horeca", "Lactate"): 0.72, ("Retail", "Lactate"): 0.85,
    ("Horeca", "Congelate"): 1.06, ("Retail", "Congelate"): 1.04,
}
P_SKIP_ORDER = 0.02    # clientul sare peste o comandă (a cumpărat din altă parte)
P_LOST = 0.03          # comandă primită, dar nelivrată (pierdută)
P_LATE = 0.06          # comandă livrată cu întârziere
NOISE_SIGMA = 0.18     # zgomotul cantităților (log-normal)
TREND_PER_YEAR = 0.03  # creștere ușoară a volumelor de la an la an

EVENT_YEAR_SPREAD = 0.35  # fiecare an, efectul unui eveniment e mai slab sau mai puternic (±35%)

# Câte "zile de vânzări" (media ultimelor 8 săptămâni) are fiecare produs în stoc azi,
# în ordinea P01..P30. Amestec intenționat: câteva produse cu prea puțin stoc și câteva
# cu prea mult în fiecare categorie, ca pagina Decide să aibă ce arăta.
STOCK_COVER_DAYS = [
    4, 20, 25, 75, 30, 25, 15, 5, 22, 28,  # congelate
    12, 30, 8, 10, 2, 9, 35, 14, 10, 12,   # lactate
    18, 25, 4, 30, 12, 20, 14, 3, 60, 22,  # băuturi
]


def mark_period(df, column, start, end, label):
    """Scrie `label` în coloana `column` pentru zilele dintre start și end (inclusiv)."""
    mask = (df["date"] >= pd.Timestamp(start)) & (df["date"] <= pd.Timestamp(end))
    df.loc[mask, column] = label


def second_friday_of_november(year):
    """Black Friday în acest demo = a doua vineri din noiembrie."""
    nov1 = pd.Timestamp(year=year, month=11, day=1)
    first_friday = nov1 + pd.Timedelta(days=(4 - nov1.weekday()) % 7)
    return first_friday + pd.Timedelta(days=7)


def build_external_factors(rng):
    """Un rând pe zi: sezon, post, eveniment și temperatură (toate simulate)."""
    df = pd.DataFrame({"date": pd.date_range(HISTORY_START, FACTORS_END, freq="D")})
    df["season"] = df["date"].dt.month.map(SEASON_BY_MONTH)

    # Perioade de post (calendar ortodox, simplificat)
    df["fasting_period"] = ""
    for year in range(HISTORY_START.year, FACTORS_END.year + 1):
        mark_period(df, "fasting_period", f"{year}-08-01", f"{year}-08-14", "Postul Adormirii Maicii Domnului")
        mark_period(df, "fasting_period", f"{year}-11-15", f"{year}-12-24", "Postul Crăciunului")
        if year in ORTHODOX_EASTER:
            easter = pd.Timestamp(ORTHODOX_EASTER[year])
            mark_period(df, "fasting_period", easter - pd.Timedelta(days=48),
                        easter - pd.Timedelta(days=1), "Postul Paștelui")
    df["is_fasting"] = df["fasting_period"] != ""

    # Evenimente comerciale: ferestrele în care clienții cumpără mai mult
    df["event"] = ""
    for year in range(HISTORY_START.year, FACTORS_END.year + 1):
        bf = second_friday_of_november(year)
        mark_period(df, "event", bf - pd.Timedelta(days=5), bf + pd.Timedelta(days=2), "Black Friday")
        mark_period(df, "event", f"{year}-12-10", f"{year}-12-24", "Crăciun")
        if year in ORTHODOX_EASTER:
            easter = pd.Timestamp(ORTHODOX_EASTER[year])
            mark_period(df, "event", easter - pd.Timedelta(days=10), easter - pd.Timedelta(days=1), "Paște")

    # Temperatura: o curbă sezonieră (minim în ianuarie, maxim în iulie) + zgomot
    # care "ține minte" ziua precedentă (zilele calde vin în serii).
    day_of_year = df["date"].dt.dayofyear.to_numpy()
    seasonal_normal = 11 + 12 * np.sin(2 * np.pi * (day_of_year - 105) / 365.25)
    noise = np.zeros(len(df))
    for i in range(1, len(df)):
        noise[i] = 0.7 * noise[i - 1] + rng.normal(0, 2.0)
    is_history = df["date"] <= HISTORY_END
    # Pentru viitor folosim doar normala sezonieră (o "prognoză meteo" simulată, fără zgomot)
    df["temperature_c"] = np.where(is_history, seasonal_normal + noise, seasonal_normal).round(1)
    df["temperature_type"] = np.where(is_history, "istoric simulat", "normală sezonieră")
    return df


def build_customers(rng):
    rows = []
    for segment, cfg in SEGMENTS.items():
        low, high = cfg["interval"]
        for name in cfg["names"]:
            rows.append({
                "customer_name": name,
                "customer_type": cfg["type"],
                "segment": segment,
                "city": str(rng.choice(CITIES)),
                "order_every_days": int(rng.integers(low, high + 1)),
                "size": float(rng.uniform(*cfg["size"])),  # folosit doar la generare
            })
    df = pd.DataFrame(rows)
    df.insert(0, "customer_id", [f"C{i:02d}" for i in range(1, len(df) + 1)])
    return df


def build_products(rng):
    df = pd.DataFrame(PRODUCTS, columns=["product_name", "category", "unit", "price_ron", "typical_qty", "fits"])
    df.insert(0, "product_id", [f"P{i:02d}" for i in range(1, len(df) + 1)])
    df["lead_time_days"] = [int(rng.integers(lo, hi + 1)) for lo, hi in df["category"].map(LEAD_TIME_DAYS)]
    return df


def true_multiplier(day, customer_type, segment, category, product_name, event_strength):
    """Efectul total al zilei asupra cantității (regulile ascunse ale simulării).
    event_strength = cât de "puternic" e evenimentul în acel an (1,0 = efectul obișnuit)."""
    mult = 1.0
    temp = day["temperature_c"]
    if category == "Băuturi":  # la cald se beau mai multe băuturi
        mult *= float(np.clip(1 + 0.02 * (temp - 12), 0.75, 1.45))
    if "Înghețată" in product_name:  # înghețata depinde puternic de temperatură
        mult *= float(np.clip(1 + 0.05 * (temp - 12), 0.35, 2.0))
    if segment == "Hotel" and day["season"] == "vară":  # sezon turistic
        mult *= 1.20
    if day["is_fasting"]:
        mult *= FASTING_EFFECT.get((customer_type, category), 1.0)
    if day["event"]:
        effect = EVENT_EFFECT[(day["event"], customer_type)][category]
        mult *= 1 + (effect - 1) * event_strength
    return mult


def build_orders(customers, products, factors, rng):
    factors_by_day = factors.set_index("date").to_dict("index")
    # Intensitatea fiecărui eveniment, pe an (ex.: Crăciunul 2025 mai slab decât cel din 2024)
    event_strength = {
        (event, year): float(rng.uniform(1 - EVENT_YEAR_SPREAD, 1 + EVENT_YEAR_SPREAD))
        for event in ["Black Friday", "Crăciun", "Paște"]
        for year in range(HISTORY_START.year, HISTORY_END.year + 1)
    }
    rows = []
    order_no = 0

    for cust in customers.itertuples(index=False):
        # 1) "Coșul" clientului: ce produse cumpără și cât de des apare fiecare pe comandă
        code = SEGMENTS[cust.segment]["code"]
        candidates = products if code is None else products[products["fits"].str.contains(code)]
        n_products = min(len(candidates), int(rng.integers(6, 11)))
        chosen = rng.choice(candidates.index.to_numpy(), size=n_products, replace=False)
        basket = []
        for idx in chosen:
            p = products.loc[idx]
            basket.append({
                "product_id": p["product_id"], "product_name": p["product_name"],
                "category": p["category"], "price": p["price_ron"],
                "base_qty": p["typical_qty"] * cust.size * rng.lognormal(0, 0.25),
                "p_include": rng.uniform(0.6, 0.95),
            })

        # 2) Comenzile, una după alta, la ritmul clientului (± o zi)
        day = HISTORY_START + pd.Timedelta(days=int(rng.integers(0, cust.order_every_days)))
        while day <= HISTORY_END:
            if rng.random() >= P_SKIP_ORDER:
                order_no += 1
                r = rng.random()
                if r < P_LOST:
                    status, delay = "pierdută", 0
                elif r < P_LOST + P_LATE:
                    status, delay = "întârziată", int(rng.integers(1, 4))
                else:
                    status, delay = "livrată", 0

                ctx = factors_by_day[day]
                trend = 1 + TREND_PER_YEAR * (day - HISTORY_START).days / 365
                order_lines = [p for p in basket if rng.random() < p["p_include"]] or [basket[0]]
                strength = event_strength.get((ctx["event"], day.year), 1.0)
                for p in order_lines:
                    mult = true_multiplier(ctx, cust.customer_type, cust.segment, p["category"],
                                           p["product_name"], strength)
                    qty = p["base_qty"] * mult * trend * rng.lognormal(0, NOISE_SIGMA)
                    rows.append({
                        "order_id": f"O{order_no:06d}",
                        "order_date": day,
                        "customer_id": cust.customer_id,
                        "product_id": p["product_id"],
                        "quantity": max(1, int(round(qty))),
                        "unit_price_ron": p["price"],
                        "status": status,
                        "delivery_delay_days": delay,
                    })
            step = cust.order_every_days + int(rng.choice([-1, 0, 0, 0, 1]))
            day += pd.Timedelta(days=max(1, step))

    return pd.DataFrame(rows)


def add_current_stock(products, orders):
    """Stocul de azi = vânzările medii zilnice din ultimele 8 săptămâni × un număr de zile."""
    recent = orders[orders["order_date"] > HISTORY_END - pd.Timedelta(days=56)]
    avg_daily = recent.groupby("product_id")["quantity"].sum() / 56
    products = products.copy()
    products["stock_units"] = [
        int(round(avg_daily.get(pid, 0) * days)) for pid, days in zip(products["product_id"], STOCK_COVER_DAYS)
    ]
    return products


def main():
    rng = np.random.default_rng(SEED)
    DATA_DIR.mkdir(exist_ok=True)

    factors = build_external_factors(rng)
    customers = build_customers(rng)
    products = build_products(rng)
    orders = build_orders(customers, products, factors, rng)
    products = add_current_stock(products, orders)

    # Salvăm doar coloanele utile aplicației; datele în format ISO (AAAA-LL-ZZ)
    customers.drop(columns=["size"]).to_csv(DATA_DIR / "customers.csv", index=False)
    products[["product_id", "product_name", "category", "unit", "price_ron", "stock_units", "lead_time_days"]] \
        .to_csv(DATA_DIR / "products.csv", index=False)
    orders.assign(order_date=orders["order_date"].dt.strftime("%Y-%m-%d")) \
        .to_csv(DATA_DIR / "orders.csv", index=False)
    factors.assign(date=factors["date"].dt.strftime("%Y-%m-%d")) \
        .to_csv(DATA_DIR / "external_factors.csv", index=False)

    # Mesajele din consolă sunt fără diacritice (consola Windows nu le afișează mereu corect)
    print(f"Clienti: {len(customers)} ({(customers['customer_type'] == 'Horeca').sum()} Horeca, "
          f"{(customers['customer_type'] == 'Retail').sum()} retail)")
    print(f"Produse: {len(products)}")
    print(f"Comenzi: {orders['order_id'].nunique()} ({len(orders)} linii), "
          f"{orders['order_date'].min():%Y-%m-%d} - {orders['order_date'].max():%Y-%m-%d}")
    print(f"Factori externi: {len(factors)} zile, pana la {factors['date'].max():%Y-%m-%d}")

    # Exportul pentru Power BI folosește modelul, deci rulează după ce datele există
    import export_powerbi
    export_powerbi.main()


if __name__ == "__main__":
    main()
