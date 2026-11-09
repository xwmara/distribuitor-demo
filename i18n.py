"""
i18n.py — toate textele aplicației, în română (ro) și engleză (en).

- TEXTS: textele interfeței, grupate în ordinea paginilor (app → start → 1 → 2 → 3 → acțiuni → 4).
  Câmpurile între acolade, ex. {date}, se completează la afișare.
- LABELS: traducerea la afișare a valorilor din CSV-uri (categorii, evenimente, statusuri, unități).
  Datele din CSV rămân neschimbate; numele clienților și ale produselor nu se traduc.
- Funcții de formatare: RO = 1.234,5 și zz.ll.aaaa; EN = 1,234.5 și aaaa-ll-zz.

Fișierul nu depinde de Streamlit, deci poate fi folosit și din decide.py sau din teste.
"""

import pandas as pd

LANGUAGES = {"ro": "Română", "en": "English"}
DEFAULT_LANG = "ro"
DATE_INPUT_FORMAT = {"ro": "DD.MM.YYYY", "en": "YYYY-MM-DD"}

TEXTS = {
    # ------------------------------------------------------------------ app.py (comun tuturor paginilor)
    "app.page_title": {"ro": "Distribuitor Demo SRL · prognoză B2B",
                       "en": "Distribuitor Demo SRL · B2B forecasting"},
    "app.disclaimer": {"ro": "Date simulate, model demonstrativ. Nu reprezintă modelul vreunei companii reale.",
                       "en": "Simulated data, demonstration model. Does not represent any real company's model."},
    "app.language": {"ro": "Limba", "en": "Language"},
    "nav.home": {"ro": "Start", "en": "Home"},
    "nav.client": {"ro": "1. Predicția pe client", "en": "1. Customer forecast"},
    "nav.scenarios": {"ro": "2. Eveniment și scenarii", "en": "2. Events & scenarios"},
    "nav.decide": {"ro": "3. Decide", "en": "3. Decide"},
    "nav.accuracy": {"ro": "4. Acuratețea prognozei", "en": "4. Forecast accuracy"},
    "common.today": {"ro": "„Azi” în demo: {date}", "en": "“Today” in this demo: {date}"},
    "common.units": {"ro": "{n} unități", "en": "{n} units"},

    # ------------------------------------------------------------------ Start (home.py)
    "home.title": {"ro": "Distribuitor Demo SRL", "en": "Distribuitor Demo SRL"},
    "home.caption": {"ro": "Demo: prognoza comenzilor clienților B2B și acțiuni recomandate",
                     "en": "Demo: forecasting B2B customer orders and recommending actions"},
    "home.problem_md": {
        "ro": (
            "**Problema.** Un distribuitor de alimente servește restaurante, cafenele, hoteluri și magazine mici. "
            "Fără prognoză, lucrează reactiv: află ce trebuie abia când vine comanda.\n\n"
            "- **Lipsă de stoc**: clientul cere, produsul nu e pe raft, comanda se pierde sau pleacă la concurență.\n"
            "- **Suprastoc**: bani blocați în marfă, iar la lactate risc de expirare.\n"
            "- **Comenzi reactive**: comanda la furnizor se face târziu, de obicei după ce a apărut problema.\n\n"
            "**Ideea.** Mare parte din cerere se poate anticipa: fiecare client comandă într-un ritm, "
            "iar evenimentele (Black Friday, Crăciun, Paște), postul și temperatura o mută previzibil."
        ),
        "en": (
            "**The problem.** A food distributor supplies restaurants, cafés, hotels and small shops. "
            "Without a forecast it works reactively: it only learns what is needed when the order arrives.\n\n"
            "- **Stock-outs**: the customer asks, the product is not on the shelf, and the order is lost "
            "or goes to a competitor.\n"
            "- **Overstock**: cash tied up in goods and, for dairy, a risk of expiry.\n"
            "- **Reactive ordering**: supplier orders go out late, usually after the problem has appeared.\n\n"
            "**The idea.** Much of the demand can be anticipated: every customer orders at their own rhythm, "
            "and events (Black Friday, Christmas, Easter), fasting periods and temperature shift it predictably."
        ),
    },
    "home.cycle_header": {"ro": "Ciclul Predict → Decide → Act", "en": "The Predict → Decide → Act cycle"},
    "home.step_predict_title": {"ro": "Predict", "en": "Predict"},
    "home.step_predict_text": {
        "ro": "Estimează când comandă fiecare client și ce cantități, pornind de la ritmul lui istoric, "
              "ajustat cu evenimente și factori externi.",
        "en": "Estimate when each customer will order and how much, starting from their historical rhythm "
              "and adjusting for events and external factors."},
    "home.step_decide_title": {"ro": "Decide", "en": "Decide"},
    "home.step_decide_text": {
        "ro": "Compară cererea estimată cu stocul: unde e risc de lipsă, unde e exces și ce trebuie comandat.",
        "en": "Compare expected demand with stock: where a stock-out is likely, where there is overstock, "
              "and what needs ordering."},
    "home.step_act_title": {"ro": "Act", "en": "Act"},
    "home.step_act_text": {
        "ro": "Transformă deciziile în acțiuni: comandă la furnizor, telefon la client, ofertă pentru stocul în exces.",
        "en": "Turn decisions into actions: a supplier order, a call to a customer, an offer to clear overstock."},
    "home.data_header": {"ro": "Ce date are demo-ul", "en": "What data the demo uses"},
    "home.metric_customers": {"ro": "Clienți", "en": "Customers"},
    "home.metric_products": {"ro": "Produse", "en": "Products"},
    "home.metric_orders": {"ro": "Comenzi în istoric", "en": "Orders in history"},
    "home.metric_months": {"ro": "Luni de istoric", "en": "Months of history"},
    "home.history_caption": {
        "ro": "Istoric: {start} – {end}. „Azi” în demo: {today} (ziua de după ultima comandă din istoric).",
        "en": "History: {start} – {end}. “Today” in this demo: {today} (the day after the last order in the history)."},
    "home.pages_header": {"ro": "Paginile", "en": "Pages"},
    "home.link_client": {"ro": "1. Predicția pe client", "en": "1. Customer forecast"},
    "home.link_scenarios": {"ro": "2. Eveniment și scenarii", "en": "2. Events & scenarios"},
    "home.link_decide": {"ro": "3. Decide: acțiuni recomandate", "en": "3. Decide: recommended actions"},
    "home.link_accuracy": {"ro": "4. Acuratețea prognozei", "en": "4. Forecast accuracy"},

    # ------------------------------------------------------------------ 1. Predicția pe client (p1_client.py)
    "p1.title": {"ro": "Predicția pe client", "en": "Customer forecast"},
    "p1.customer": {"ro": "Client", "en": "Customer"},
    "p1.rhythm_header": {"ro": "Ritmul de comandă", "en": "Ordering rhythm"},
    "p1.rhythm_calc": {"ro": "Ritm calculat din istoric", "en": "Rhythm from history"},
    "p1.rhythm_calc_help": {"ro": "Mediana zilelor dintre două comenzi consecutive.",
                            "en": "Median number of days between two consecutive orders."},
    "p1.rhythm_calc_value": {"ro": "la ~{n} zile", "en": "every ~{n} days"},
    "p1.rhythm_card": {"ro": "Ritm din fișa clientului", "en": "Rhythm on customer record"},
    "p1.rhythm_card_help": {"ro": "Valoarea din customers.csv, pentru comparație.",
                            "en": "The value in customers.csv, for comparison."},
    "p1.rhythm_card_value": {"ro": "la {n} zile", "en": "every {n} days"},
    "p1.last_order": {"ro": "Ultima comandă", "en": "Last order"},
    "p1.next_order": {"ro": "Următoarea comandă estimată", "en": "Next expected order"},
    "p1.overdue": {
        "ro": "Comanda era așteptată pe {date}; clientul a întârziat {n} zile față de ritmul lui. Estimăm comanda azi.",
        "en": "The order was expected on {date}; the customer is {n} days behind their usual rhythm. "
              "We expect the order today."},
    "p1.next_header": {"ro": "Următoarea comandă estimată", "en": "Next expected order"},
    "p1.ctx_temp": {"ro": "temperatură estimată {t}°C", "en": "expected temperature {t}°C"},
    "p1.ctx_fasting": {"ro": "perioadă de post", "en": "fasting period"},
    "p1.ctx_event": {"ro": "eveniment: {event}", "en": "event: {event}"},
    "p1.col_product": {"ro": "Produs", "en": "Product"},
    "p1.col_qty": {"ro": "Cantitate", "en": "Quantity"},
    "p1.col_prob": {"ro": "Probabilitate", "en": "Likelihood"},
    "p1.col_prob_help": {"ro": "În câte comenzi din 100 (ultimele 180 de zile) a apărut produsul.",
                         "en": "In how many orders out of 100 (last 180 days) the product appeared."},
    "p1.est_value": {"ro": "Valoare estimată (produsele probabile)", "en": "Estimated value (likely products)"},
    "p1.occasional": {"ro": "Produse cumpărate ocazional ({n})", "en": "Occasional products ({n})"},
    "p1.how_header": {"ro": "Cum s-a calculat cantitatea", "en": "How the quantity was calculated"},
    "p1.how_md": {
        "ro": (
            "**Cantitate estimată = cantitate tipică × multiplicator eveniment × factor extern**\n\n"
            "Exemplu pentru *{product}*:\n\n"
            "- cantitate tipică într-o zi normală (ultimele 180 de zile): **{typical}**\n"
            "- multiplicator eveniment: **×{event_factor}** {event_note}\n"
            "- factor extern = temperatură ×{temp_factor} · post ×{post_factor} = **×{external}**\n\n"
            "Rezultat: {typical} × {event_factor} × {external} = **{qty} {unit}** (rotunjit: {rounded}).\n\n"
            "Data = ultima comandă + ritmul calculat ({last} + {interval} zile)."
        ),
        "en": (
            "**Estimated quantity = typical quantity × event multiplier × external factor**\n\n"
            "Example for *{product}*:\n\n"
            "- typical quantity on a normal day (last 180 days): **{typical}**\n"
            "- event multiplier: **×{event_factor}** {event_note}\n"
            "- external factor = temperature ×{temp_factor} · fasting ×{post_factor} = **×{external}**\n\n"
            "Result: {typical} × {event_factor} × {external} = **{qty} {unit}** (rounded: {rounded}).\n\n"
            "Date = last order + calculated rhythm ({last} + {interval} days)."
        ),
    },
    "p1.event_note": {"ro": "({event})", "en": "({event})"},
    "p1.no_event": {"ro": "(niciun eveniment)", "en": "(no event)"},
    "p1.history_header": {"ro": "Istoricul comenzilor", "en": "Order history"},
    "p1.monthly_title": {"ro": "Valoarea comenzilor pe lună (RON)", "en": "Order value per month (RON)"},
    "p1.axis_month": {"ro": "Luna", "en": "Month"},
    "p1.axis_ron": {"ro": "RON", "en": "RON"},
    "p1.gap_title": {"ro": "Zile între două comenzi", "en": "Days between two orders"},
    "p1.axis_order_date": {"ro": "Data comenzii", "en": "Order date"},
    "p1.axis_days": {"ro": "Zile", "en": "Days"},
    "p1.status_caption": {
        "ro": "{n} comenzi în 24 de luni ({parts}). Comenzile pierdute contează ca cerere (clientul a cerut marfa).",
        "en": "{n} orders in 24 months ({parts}). Lost orders still count as demand (the customer asked for the goods)."},
    "p1.col_date": {"ro": "Data", "en": "Date"},
    "p1.col_value": {"ro": "Valoare", "en": "Value"},
    "p1.col_status": {"ro": "Status", "en": "Status"},

    # ------------------------------------------------------------------ 2. Eveniment și scenarii (p2_scenarii.py)
    "p2.title": {"ro": "Eveniment și scenarii", "en": "Events & scenarios"},
    "p2.event": {"ro": "Eveniment", "en": "Event"},
    "p2.no_event": {"ro": "Fără eveniment (perioadă normală)", "en": "No event (normal period)"},
    "p2.event_option": {"ro": "{event} ({start} – {end})", "en": "{event} ({start} – {end})"},
    "p2.category": {"ro": "Categorie", "en": "Category"},
    "p2.stock": {"ro": "Stoc curent (unități)", "en": "Current stock (units)"},
    "p2.stock_help": {"ro": "Implicit: suma stocurilor din products.csv pentru categorie.",
                      "en": "Default: total stock of the category in products.csv."},
    "p2.price": {"ro": "Preț mediu (RON / unitate)", "en": "Average price (RON / unit)"},
    "p2.price_help": {"ro": "Implicit: prețul mediu realizat în ultimele 90 de zile.",
                      "en": "Default: average price achieved over the last 90 days."},
    "p2.start": {"ro": "Data de început", "en": "Start date"},
    "p2.days": {"ro": "Număr de zile", "en": "Number of days"},
    "p2.service": {"ro": "Nivel de serviciu (pentru stocul de siguranță)", "en": "Service level (for safety stock)"},
    "p2.calendar_warning": {
        "ro": "Calendarul de factori externi se oprește la {date}; calculul acoperă doar {n} zile.",
        "en": "The external-factor calendar ends on {date}; the calculation covers only {n} days."},
    "p2.demand_header": {"ro": "Cererea estimată", "en": "Expected demand"},
    "p2.demand_caption": {
        "ro": "{category}, {start} + {days} zile, toți clienții. Unitățile sunt un amestec de ambalaje (pungi, baxuri, litri…).",
        "en": "{category}, {start} + {days} days, all customers. Units are a mix of pack types (bags, cases, litres…)."},
    "p2.metric_low": {"ro": "Scenariu scăzut", "en": "Low scenario"},
    "p2.metric_base": {"ro": "Scenariu de bază", "en": "Base scenario"},
    "p2.metric_high": {"ro": "Scenariu ridicat", "en": "High scenario"},
    "p2.help_mult": {"ro": "Prognoza × {m}", "en": "Forecast × {m}"},
    "p2.help_base": {"ro": "Prognoza modelului", "en": "The model's forecast"},
    "p2.value": {"ro": "Valoare", "en": "Value"},
    "p2.uplift": {
        "ro": "Față de aceeași perioadă fără {event}: {pct} ({a} → {b} unități).",
        "en": "Compared with the same period without {event}: {pct} ({a} → {b} units)."},
    "p2.axis_date": {"ro": "Data", "en": "Date"},
    "p2.axis_daily": {"ro": "Unități pe zi", "en": "Units per day"},
    "p2.stock_header": {"ro": "Stocul recomandat", "en": "Recommended stock"},
    "p2.safety_stock": {"ro": "Stoc de siguranță", "en": "Safety stock"},
    "p2.recommended": {"ro": "Stoc recomandat", "en": "Recommended stock"},
    "p2.recommended_help": {"ro": "Cererea de bază + stocul de siguranță.", "en": "Base demand + safety stock."},
    "p2.shortage_msg": {
        "ro": "Stoc insuficient: lipsesc ~{units} unități (~{value}). Comandă la furnizor înainte de {date}.",
        "en": "Not enough stock: ~{units} units short (~{value}). Order from the supplier before {date}."},
    "p2.excess_msg": {
        "ro": "Risc de exces: ~{units} unități peste recomandat (~{value} blocați în stoc). "
              "Stocul depășește chiar și scenariul ridicat.",
        "en": "Overstock risk: ~{units} units above the recommendation (~{value} tied up in stock). "
              "Stock exceeds even the high scenario."},
    "p2.ok_msg": {
        "ro": "Stocul acoperă scenariul de bază plus stocul de siguranță (rezervă: {units} unități).",
        "en": "Stock covers the base scenario plus safety stock (buffer: {units} units)."},
    "p2.sources_header": {"ro": "De unde vin cifrele", "en": "Where the numbers come from"},
    "p2.sources_md": {
        "ro": (
            "- **Scenariul de bază**: suma cererii zilnice estimate de model pentru toți clienții "
            "(cantitate tipică × frecvență ÷ ritm × multiplicator eveniment × factor extern).\n"
            "- **Scăzut / ridicat**: percentilele 10 și 90 ale erorilor săptămânale din perioada de test, "
            "pentru {category}. {widen}\n"
            "- **Stoc de siguranță** = z ({z} pentru {service}) × σ eroare săptămânală ({sigma} unități) × √(zile / 7)."
        ),
        "en": (
            "- **Base scenario**: total daily demand forecast by the model for all customers "
            "(typical quantity × frequency ÷ rhythm × event multiplier × external factor).\n"
            "- **Low / high**: 10th and 90th percentiles of weekly errors in the test period, "
            "for {category}. {widen}\n"
            "- **Safety stock** = z ({z} for {service}) × σ of weekly error ({sigma} units) × √(days / 7)."
        ),
    },
    "p2.sources_widen": {
        "ro": "Pentru evenimente, banda e lărgită ×{w} (eroarea a fost mai mare în săptămânile cu eveniment).",
        "en": "For events the band is widened ×{w} (errors were larger in event weeks)."},
    "p2.multipliers_title": {"ro": "Multiplicatorii estimați din istoric pentru {event}, {category}:",
                             "en": "Multipliers estimated from history for {event}, {category}:"},
    "p2.col_ctype": {"ro": "Tip client", "en": "Customer type"},
    "p2.col_mult": {"ro": "Multiplicator", "en": "Multiplier"},

    # ------------------------------------------------------------------ 3. Decide (p3_decide.py)
    "p3.title": {"ro": "Decide: acțiuni recomandate", "en": "Decide: recommended actions"},
    "p3.horizon": {"ro": "Orizont de planificare", "en": "Planning horizon"},
    "p3.days_fmt": {"ro": "{n} zile", "en": "{n} days"},
    "p3.service": {"ro": "Nivel de serviciu", "en": "Service level"},
    "p3.metric_actions": {"ro": "Acțiuni", "en": "Actions"},
    "p3.metric_shortage": {"ro": "Risc de lipsă", "en": "Stock-out risk"},
    "p3.metric_shortage_help": {"ro": "Produse sub punctul de recomandă.", "en": "Products below their reorder point."},
    "p3.metric_excess": {"ro": "Exces", "en": "Overstock"},
    "p3.metric_excess_help": {"ro": "Produse cu prea multe zile de stoc.", "en": "Products with too many days of stock."},
    "p3.filter": {"ro": "Filtru", "en": "Filter"},
    "p3.no_actions": {"ro": "Nicio acțiune pentru filtrul ales.", "en": "No actions for the selected filter."},
    "p3.priority_caption": {"ro": "Prioritate {priority} · {kind}", "en": "{priority} priority · {kind}"},
    "p3.act_header": {"ro": "Act", "en": "Act"},
    "p3.act_text": {
        "ro": "Într-un sistem real, acest pas ar trimite automat comanda la furnizor sau un mesaj clientului. "
              "Aici generăm doar un fișier draft, pe care îl verifică un om.",
        "en": "In a real system this step would send the supplier order or a customer message automatically. "
              "Here we only generate a draft file for a person to review."},
    "p3.download": {"ro": "Descarcă draftul de comandă la furnizor ({n} produse, {value})",
                    "en": "Download the draft supplier order ({n} products, {value})"},
    "p3.download_file": {"ro": "draft_comanda_furnizor_{date}.csv", "en": "draft_supplier_order_{date}.csv"},
    "p3.table_header": {"ro": "Stoc vs. cerere, pe produse", "en": "Stock vs. demand, by product"},
    "p3.col_product": {"ro": "Produs", "en": "Product"},
    "p3.col_stock": {"ro": "Stoc", "en": "Stock"},
    "p3.col_needed": {"ro": "Necesar", "en": "Needed"},
    "p3.col_needed_help": {
        "ro": "Punct de recomandă = cererea în timpul livrării de la furnizor + stocul de siguranță.",
        "en": "Reorder point = demand during the supplier lead time + safety stock."},
    "p3.col_status": {"ro": "Status", "en": "Status"},
    "p3.col_status_help": {"ro": "Status și riscul de lipsă în timpul livrării.",
                           "en": "Status and stock-out risk during the lead time."},
    "p3.table_caption": {
        "ro": "Risc de lipsă = probabilitatea ca cererea din timpul livrării să depășească stocul "
              "(distribuție normală, cu abaterea standard a erorilor din perioada de test). "
              "Exces = stoc peste {rules} (regulă de business demonstrativă).",
        "en": "Stock-out risk = probability that demand during the lead time exceeds stock "
              "(normal distribution, using the standard deviation of test-period errors). "
              "Overstock = stock above {rules} (demonstration business rule)."},
    "p3.excess_rule_item": {"ro": "{days} zile la {category}", "en": "{days} days for {category}"},

    # ------------------------------------------------------------------ Acțiuni generate de decide.py
    "act.supplier_title": {"ro": "Comandă acum la furnizor: {product}", "en": "Order from the supplier now: {product}"},
    "act.supplier_text": {
        "ro": "Stoc: {stock} ({unit}). Cererea estimată până sosește marfa ({lead} zile): {demand}, plus stoc de "
              "siguranță {ss}. Risc de lipsă: {risk}. Recomandat: {qty} ({unit}), acoperă {lead} + {horizon} zile.",
        "en": "Stock: {stock} ({unit}). Expected demand until the delivery arrives ({lead} days): {demand}, plus "
              "safety stock of {ss}. Stock-out risk: {risk}. Suggested order: {qty} ({unit}), covering "
              "{lead} + {horizon} days."},
    "act.customer_title": {"ro": "{name}: comandă estimată {when}", "en": "{name}: order expected {when}"},
    "act.customer_text": {
        "ro": "Clientul {name} comandă de obicei la ~{interval} zile. Următoarea comandă estimată: {date}. "
              "Stoc insuficient la {items}, iar marfa nouă ajunge în {lead} zile de la comandă: comandă acum la "
              "furnizor și confirmă cu clientul cantitățile.",
        "en": "{name} usually orders every ~{interval} days. Next order expected: {date}. Stock is short for "
              "{items}, and new supply takes {lead} days to arrive: order from the supplier now and confirm "
              "quantities with the customer."},
    "act.item": {"ro": "{category} ({products})", "en": "{category} ({products})"},
    "act.and": {"ro": " și ", "en": " and "},
    "act.when_today": {"ro": "azi", "en": "today"},
    "act.when_tomorrow": {"ro": "mâine", "en": "tomorrow"},
    "act.when_days": {"ro": "peste {n} zile", "en": "in {n} days"},
    "act.contact_title": {"ro": "Contactează clientul: {name}", "en": "Contact the customer: {name}"},
    "act.contact_text": {
        "ro": "Nu a mai comandat de {days} zile, deși comandă de obicei la ~{interval} zile "
              "(ultima comandă: {last}). Un telefon acum poate salva comanda.",
        "en": "No order for {days} days, although they usually order every ~{interval} days "
              "(last order: {last}). A call now could save the order."},
    "act.overstock_title": {"ro": "Suprastoc: {product}", "en": "Overstock: {product}"},
    "act.overstock_text": {
        "ro": "Stoc: {stock} = ~{cover} zile de vânzări (prag: {threshold} zile pentru {category}). "
              "~{excess} ({unit}) peste prag. Nu reaproviziona; propune o ofertă clienților care îl cumpără des: "
              "{buyers}.",
        "en": "Stock: {stock} = ~{cover} days of sales (threshold: {threshold} days for {category}). "
              "~{excess} ({unit}) above the threshold. Do not reorder; offer a deal to the customers who buy it "
              "most: {buyers}."},
    "act.event_title": {"ro": "Pregătește evenimentul: {event} ({start} – {end})",
                        "en": "Prepare for the event: {event} ({start} – {end})"},
    "act.event_text": {
        "ro": "Începe {when}. Multiplicatori estimați din istoric: {detail}. "
              "Verifică scenariile pe pagina „Eveniment și scenarii”.",
        "en": "Starts {when}. Multipliers estimated from history: {detail}. "
              "Check the scenarios on the “Events & scenarios” page."},
    "act.event_detail_item": {"ro": "{category} ×{mult}", "en": "{category} ×{mult}"},

    # ------------------------------------------------------------------ 4. Acuratețea prognozei (p4_acuratete.py)
    "p4.title": {"ro": "Acuratețea prognozei", "en": "Forecast accuracy"},
    "p4.caption": {
        "ro": "Antrenare: {train_start} – {train_end}. Test: {test_start} – {test_end} "
              "({n} săptămâni complete, comparate pe categorii).",
        "en": "Training: {train_start} – {train_end}. Test: {test_start} – {test_end} "
              "({n} full weeks, compared by category)."},
    "p4.mape_total": {"ro": "MAPE total (săptămânal, pe categorie)", "en": "Overall MAPE (weekly, by category)"},
    "p4.mape_total_help": {
        "ro": "Media lui |real − prognoză| / real, pe toate săptămânile și categoriile din test.",
        "en": "Average of |actual − forecast| / actual over all test weeks and categories."},
    "p4.fc_header": {"ro": "Prognoză vs. comenzi reale simulate", "en": "Forecast vs. simulated actual orders"},
    "p4.category": {"ro": "Categorie", "en": "Category"},
    "p4.series_forecast": {"ro": "Prognoză", "en": "Forecast"},
    "p4.series_actual": {"ro": "Real", "en": "Actual"},
    "p4.axis_week": {"ro": "Săptămâna", "en": "Week"},
    "p4.axis_units_week": {"ro": "Unități / săptămână", "en": "Units / week"},
    "p4.type_header": {"ro": "Eroarea pe tip de săptămână", "en": "Error by type of week"},
    "p4.type_metric": {"ro": "{type} ({n} săpt.)", "en": "{type} ({n} wks)"},
    "p4.widen_header": {"ro": "Când trebuie lărgit intervalul", "en": "When to widen the interval"},
    "p4.note_event_widen": {
        "ro": "**Evenimente**: eroarea a fost {event} în săptămânile cu eveniment, față de {normal} în cele normale. "
              "Pentru evenimente, banda dintre scenariul scăzut și cel ridicat se lărgește ×{w}.",
        "en": "**Events**: the error was {event} in event weeks versus {normal} in normal weeks. "
              "For events, the band between the low and high scenarios is widened ×{w}."},
    "p4.note_event_same": {
        "ro": "**Evenimente**: în perioada de test, eroarea la evenimente nu a fost mai mare decât în săptămânile "
              "normale, deci banda rămâne aceeași.",
        "en": "**Events**: in the test period, event weeks were no less accurate than normal weeks, "
              "so the band stays the same."},
    "p4.note_recent_high": {
        "ro": "**Eroare recentă**: MAPE pe ultimele 4 săptămâni este {recent}, peste 1,5 × media ({limit}). "
              "Lărgește intervalul și reantrenează modelul.",
        "en": "**Recent error**: MAPE over the last 4 weeks is {recent}, above 1.5 × the average ({limit}). "
              "Widen the interval and retrain the model."},
    "p4.note_recent_ok": {
        "ro": "**Eroare recentă**: MAPE pe ultimele 4 săptămâni este {recent}, sub pragul de alertă de "
              "1,5 × media ({limit}). Banda actuală e suficientă.",
        "en": "**Recent error**: MAPE over the last 4 weeks is {recent}, below the alert threshold of "
              "1.5 × the average ({limit}). The current band is sufficient."},
    "p4.rule_info": {
        "ro": "Regula generală: lărgește intervalul când (1) urmează un eveniment, mai ales unul văzut doar o dată "
              "în istoric; (2) eroarea pe ultimele 4 săptămâni depășește 1,5 × media; (3) clientul sau produsul are "
              "istoric scurt; (4) condițiile ies din ce a văzut modelul (temperaturi extreme, client nou, preț schimbat).",
        "en": "General rule: widen the interval when (1) an event is coming, especially one seen only once in the "
              "history; (2) the error over the last 4 weeks exceeds 1.5 × the average; (3) the customer or product "
              "has a short history; (4) conditions fall outside what the model has seen (extreme temperatures, "
              "a new customer, a price change)."},
    "p4.bands_title": {"ro": "**Benzile scenariilor** (percentilele 10 și 90 ale erorii, pe categorie)",
                       "en": "**Scenario bands** (10th and 90th percentiles of the error, by category)"},
    "p4.col_category": {"ro": "Categorie", "en": "Category"},
    "p4.col_low": {"ro": "Scăzut", "en": "Low"},
    "p4.col_high": {"ro": "Ridicat", "en": "High"},
    "p4.worst_header": {"ro": "Cele mai mari 5 erori", "en": "The 5 largest errors"},
    "p4.col_week": {"ro": "Săptămâna", "en": "Week"},
    "p4.col_actual_fc": {"ro": "Real / Prognoză", "en": "Actual / Forecast"},
    "p4.col_error": {"ro": "Eroare", "en": "Error"},
    "p4.week_type_caption": {"ro": "Tipul săptămânii: {items}", "en": "Type of week: {items}"},
}

# Valori din CSV-uri / din model, traduse doar la afișare
LABELS = {
    "category": {
        "Congelate": {"ro": "Congelate", "en": "Frozen"},
        "Lactate": {"ro": "Lactate", "en": "Dairy"},
        "Băuturi": {"ro": "Băuturi", "en": "Beverages"},
    },
    "event": {
        "Black Friday": {"ro": "Black Friday", "en": "Black Friday"},
        "Crăciun": {"ro": "Crăciun", "en": "Christmas"},
        "Paște": {"ro": "Paște", "en": "Easter"},
    },
    "scenario": {
        "low": {"ro": "Scăzut", "en": "Low"},
        "base": {"ro": "De bază", "en": "Base"},
        "high": {"ro": "Ridicat", "en": "High"},
    },
    "status": {
        "livrată": {"ro": "livrată", "en": "delivered"},
        "întârziată": {"ro": "întârziată", "en": "late"},
        "pierdută": {"ro": "pierdută", "en": "lost"},
    },
    "status_many": {
        "livrată": {"ro": "livrate", "en": "delivered"},
        "întârziată": {"ro": "întârziate", "en": "late"},
        "pierdută": {"ro": "pierdute", "en": "lost"},
    },
    "stock_status": {
        "Lipsă": {"ro": "Lipsă", "en": "Shortage"},
        "Exces": {"ro": "Exces", "en": "Overstock"},
        "OK": {"ro": "OK", "en": "OK"},
    },
    "week_type": {
        "eveniment": {"ro": "Eveniment", "en": "Event"},
        "post": {"ro": "Post", "en": "Fasting"},
        "normală": {"ro": "Normală", "en": "Normal"},
    },
    "customer_type": {
        "Horeca": {"ro": "Horeca", "en": "HoReCa"},
        "Retail": {"ro": "Retail", "en": "Retail"},
    },
    "segment": {
        "Restaurant": {"ro": "Restaurant", "en": "Restaurant"},
        "Cafenea": {"ro": "Cafenea", "en": "Café"},
        "Hotel": {"ro": "Hotel", "en": "Hotel"},
        "Magazin": {"ro": "Magazin", "en": "Shop"},
    },
    "unit": {
        "pungă": {"ro": "pungă", "en": "bag"},
        "bax": {"ro": "bax", "en": "case"},
        "cutie": {"ro": "cutie", "en": "box"},
        "litru": {"ro": "litru", "en": "litre"},
        "găleată": {"ro": "găleată", "en": "tub"},
        "kg": {"ro": "kg", "en": "kg"},
        "sticlă": {"ro": "sticlă", "en": "bottle"},
    },
    "priority": {
        "high": {"ro": "Ridicată", "en": "High"},
        "medium": {"ro": "Medie", "en": "Medium"},
        "low": {"ro": "Scăzută", "en": "Low"},
    },
    "kind": {
        "supplier": {"ro": "Comandă la furnizor", "en": "Supplier order"},
        "customer": {"ro": "Client", "en": "Customer"},
        "overstock": {"ro": "Suprastoc", "en": "Overstock"},
        "event": {"ro": "Eveniment", "en": "Event"},
    },
}


# ---------------------------------------------------------------------------- funcții
def t(key: str, lang: str, **kwargs) -> str:
    """Textul pentru `key` în limba `lang`, cu câmpurile {…} completate."""
    text = TEXTS[key][lang]
    return text.format(**kwargs) if kwargs else text


def label(group: str, value, lang: str) -> str:
    """Traducerea unei valori din date (ex. categoria „Lactate” → „Dairy”). Dacă lipsește, rămâne neschimbată."""
    return LABELS.get(group, {}).get(value, {}).get(lang, value)


def fmt_num(x, lang: str, decimals: int = 0) -> str:
    """RO: 1.234,5   EN: 1,234.5"""
    s = f"{x:,.{decimals}f}"
    if lang == "ro":
        s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s


def fmt_days(x, lang: str) -> str:
    """Un interval în zile: fără zecimale dacă e întreg (4), altfel cu una (4,5 / 4.5)."""
    return fmt_num(x, lang, 0 if float(x).is_integer() else 1)


def fmt_pct(x, lang: str, decimals: int = 1) -> str:
    return f"{fmt_num(100 * x, lang, decimals)}%"


def fmt_ron(x, lang: str) -> str:
    return f"{fmt_num(x, lang)} RON"


def fmt_date(d, lang: str) -> str:
    """RO: 01.11.2026   EN: 2026-11-01"""
    return pd.Timestamp(d).strftime("%d.%m.%Y" if lang == "ro" else "%Y-%m-%d")


def join_list(items: list, lang: str) -> str:
    """['a', 'b', 'c'] → 'a, b și c' (RO) / 'a, b and c' (EN)."""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + t("act.and", lang) + items[-1]
