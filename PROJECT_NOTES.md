# PROJECT_NOTES: Distribuitor Demo SRL

> Date simulate, model demonstrativ. Nu reprezintă modelul vreunei companii reale.

Note pentru prezentarea proiectului la interviu. Toate cifrele de mai jos provin din CSV-urile
generate cu seed 42 (le obții identic rulând `python generate_data.py`).

---

## 1. Structura proiectului

| Fișier | Ce face |
|---|---|
| `app.py` | Punctul de intrare. Setează pagina (layout îngust, bun pe telefon), definește cele 5 pagini cu `st.navigation` și afișează mesajul „Date simulate…” deasupra fiecărei pagini. |
| `i18n.py` | Toate textele interfeței, în română și engleză, ordonate pe pagini, plus traducerea la afișare a valorilor din CSV (categorii, evenimente, statusuri, unități) și formatarea pe limbă (RO 1.234,5 și 01.11.2026; EN 1,234.5 și 2026-11-01). |
| `common.py` | Încărcarea datelor, a modelului și a backtestului cu `st.cache_data`, deci se calculează o singură dată per server. Conține și mesajul obligatoriu și formatarea românească (1.234,5; 01.11.2026). |
| `model.py` | Modelul: citirea datelor, ritmul clienților, multiplicatorii (temperatură, post, eveniment), cantitatea tipică, prognoza zilnică, următoarea comandă, backtestul, MAPE, scenariile, stocul de siguranță și verificarea stocului. Nu depinde de Streamlit, deci se poate testa separat. |
| `decide.py` | Regulile care transformă prognoza în acțiuni: comandă la furnizor, alertă pe client, client care a întârziat, suprastoc, eveniment care se apropie. |
| `generate_data.py` | Generatorul de date simulate (seed fix). La final pornește exportul Power BI. |
| `export_powerbi.py` | Scrie cele 4 CSV-uri pentru Power BI în `data/powerbi/`. |
| `app_pages/home.py` | Pagina de start. |
| `app_pages/p1_client.py` | Pagina 1: predicția pe client. |
| `app_pages/p2_scenarii.py` | Pagina 2: eveniment și scenarii. |
| `app_pages/p3_decide.py` | Pagina 3: Decide (+ Act). |
| `app_pages/p4_acuratete.py` | Pagina 4: acuratețea prognozei. |
| `data/*.csv` | Datele simulate: `customers`, `products`, `orders`, `external_factors`. |
| `data/powerbi/*.csv` | Exporturile: `orders_history`, `forecast_scenarios`, `stock_vs_demand`, `forecast_error`. |
| `requirements.txt` | `streamlit`, `pandas`, `numpy`, cu versiuni fixate. |
| `README.md` | Descrierea în engleză, rularea locală și publicarea pe Streamlit Community Cloud. |
| `.gitignore` | Ignoră cache-urile Python, mediile virtuale, secretele Streamlit și fișierele de editor. `data/` intră intenționat în git. |

Fluxul datelor: `generate_data.py` → `data/*.csv` → `model.py` (calcule) → `decide.py` (reguli) → paginile din `app_pages/`.

---

## 2. Ce face fiecare pagină

**Limba**: selector RO / EN în sidebar (păstrat între pagini prin `st.session_state`), sau link cu `?lang=en`. Acțiunile din `decide.py` se generează din șabloane traduse; numele clienților și ale produselor rămân neschimbate.

**Start (`home.py`)**
- Problema: lipsa de stoc, suprastocul și comenzile reactive.
- Ciclul Predict → Decide → Act, în trei carduri.
- Cifre din CSV: 25 clienți, 30 produse, 3.519 comenzi, 24 luni.
- „Azi” în demo: 01.11.2026, ziua de după ultima comandă din istoric.
- Linkuri către cele 4 pagini.

**1. Predicția pe client (`p1_client.py`)**
- Selector de client (nume, segment, oraș).
- Ritmul calculat din istoric (mediana zilelor dintre comenzi), comparat cu ritmul din fișa clientului.
- Data ultimei comenzi și data următoarei comenzi estimate. Dacă clientul a depășit ritmul, apare un avertisment.
- Coșul estimat: produs, cantitate și probabilitate (bară de progres). Produsele ocazionale (sub 50%) sunt separate într-un expander.
- Valoarea estimată a comenzii.
- Expander „Cum s-a calculat”: formula aplicată pas cu pas pe primul produs.
- Istoric: valoarea comenzilor pe lună (bar chart), zilele dintre comenzi (line chart), numărul de comenzi livrate, întârziate și pierdute, ultimele 8 comenzi.

**2. Eveniment și scenarii (`p2_scenarii.py`)**
- Selector de eveniment, cu ferestrele viitoare din calendar: Black Friday 08–15.11.2026, Crăciun 10–24.12.2026, Paște 22.04–01.05.2027, plus „Fără eveniment”.
- Inputuri: categorie, stoc curent, preț mediu, dată de început, număr de zile și nivel de serviciu (90/95/98%).
- Valorile implicite vin din CSV: stocul categoriei e suma din `products.csv`, iar prețul e media realizată în ultimele 90 de zile.
- Rezultat: cererea în scenariile scăzut / de bază / ridicat, în unități și RON, și creșterea față de aceeași perioadă fără eveniment.
- Grafic zilnic cu cele trei scenarii.
- Stoc de siguranță, stoc recomandat și verdict față de stocul introdus: lipsă (cu valoarea în RON), exces (bani blocați) sau OK.
- Expander cu sursa fiecărei cifre și multiplicatorii estimați pentru eveniment, pe tip de client.

**3. Decide (`p3_decide.py`)**
- Orizont de planificare (7–28 zile) și nivel de serviciu.
- Contoare: numărul de acțiuni, produse cu risc de lipsă și produse în exces.
- Lista de acțiuni ca și carduri, ordonate după prioritate și filtrabile după tip:
  - *Comandă la furnizor*: stoc, cerere în timpul livrării, stoc de siguranță, risc de lipsă și cantitatea recomandată.
  - *Client*, de exemplu: „Clientul Hotel Panorama comandă de obicei la ~5 zile. Următoarea comandă estimată: 05.11.2026. Stoc insuficient la congelate (Cartofi prăjiți…, File de pește…), iar marfa nouă ajunge în 7 zile: comandă acum la furnizor.” Alerta apare doar dacă clientul comandă înainte să poată ajunge marfa nouă.
  - *Contactează clientul*: clientul a depășit clar ritmul obișnuit (peste 1,5 × intervalul).
  - *Suprastoc*: zile de stoc peste prag, plus clienții cărora li se poate propune o ofertă.
  - *Eveniment*: un eveniment începe în orizont; se afișează multiplicatorii estimați.
- **Act**: descarcă un CSV „draft comandă la furnizor” pentru produsele cu risc de lipsă.
- Expander cu tabelul stoc vs. necesar pe produse (4 coloane, potrivit pentru telefon).

**4. Acuratețea prognozei (`p4_acuratete.py`)**
- Perioada de antrenare (01.11.2024–30.11.2025) și perioada de test (01.12.2025–31.10.2026, 47 de săptămâni complete).
- MAPE total: **11,0%**, WAPE total: **11,0%**. MAPE pe categorii: congelate 8,6%, lactate 14,4%, băuturi 10,0%.
- Grafic prognoză vs. real, pe săptămâni, pentru categoria aleasă.
- MAPE pe tip de săptămână: eveniment 12,0%, normală 10,9%, post 10,9%.
- Nota „Când trebuie lărgit intervalul”, calculată din date:
  - eroarea la evenimente e mai mare, deci banda se lărgește ×1,10;
  - verificarea erorii pe ultimele 4 săptămâni față de pragul de 1,5 × media;
  - regula generală: evenimente rare, eroare recentă mare, istoric scurt, condiții noi.
- Tabelul benzilor de scenariu și cele mai mari 5 erori.
- **Verificări suplimentare** (`model.rolling_backtest`), pe aceleași 47 de săptămâni:
  - model reantrenat lunar (11 reantrenări, fiecare prezice doar luna următoare): MAPE 11,4%, WAPE 11,1%. Rezultatul e stabil;
  - baseline naiv (media reală a ultimelor 4 săptămâni dinaintea lunii): MAPE 18,6%, WAPE 17,9%. Modelul are cu **38%** mai puțină eroare (WAPE);
  - banda scenariilor calibrată doar pe lunile anterioare a cuprins realul în **78%** din 38 de săptămâni (ținta pentru P10–P90: 80%).

---

## 3. Formula modelului, cu un exemplu numeric

```
cantitate_estimată = cantitate_tipică × multiplicator_eveniment × factor_extern
factor_extern      = factor_temperatură × factor_post
cerere_zilnică     = cantitate_estimată × frecvența_produsului ÷ intervalul_clientului
```

Cum se calculează fiecare termen (în `fit_model`):
1. **Indice** pe fiecare linie de comandă = cantitate ÷ media clientului pentru acel produs. Așa putem compara clienți mici cu clienți mari.
2. **Factor temperatură**: indicele mediu pe fiecare bandă de temperatură (<5, 5–12, 12–20, >20°C) ÷ indicele mediu din zilele normale, pe tip client × categorie.
3. **Factor post**: după scoaterea efectului temperaturii, media din zilele de post (fără eveniment) ÷ media din zilele normale.
4. **Multiplicator eveniment**: după scoaterea temperaturii și a postului, media din ferestrele de eveniment ÷ media din zilele normale.
5. **Cantitate tipică**: media cantităților „curățate” de factori, pe ultimele 180 de zile.
6. **Ritm**: mediana zilelor dintre comenzi. **Frecvență**: în ce proporție din comenzi apare produsul.

Efectele se scot pe rând (temperatură → post → eveniment) pentru că se suprapun. De exemplu, fereastra de Crăciun cade în Postul Crăciunului.

**Exemplu**: Minimarket La Colț (retail), Suc de portocale 1 L, o comandă în 13.11.2026 (Black Friday):

| Termen | Valoare | De unde |
|---|---|---|
| Cantitate tipică | 37,38 L | media ultimelor 180 de zile, curățată de factori |
| Multiplicator Black Friday (retail, băuturi) | ×1,287 | estimat din Black Friday 2024 și 2025 |
| Factor temperatură (5,2°C → banda 5–12°C) | ×0,935 | retail, băuturi |
| Factor post | ×1,000 | 13.11 nu e zi de post (postul începe pe 15.11) |
| **Cantitate estimată** | 37,38 × 1,287 × 0,935 = **44,98 ≈ 45 L** | |
| Frecvență / ritm | 0,80 / 9 zile | |
| Cerere zilnică medie | 44,98 × 0,80 ÷ 9 = **4,0 L/zi** | folosită la stoc |

Pentru comparație, generatorul a folosit pentru Black Friday la retail/băuturi un efect de 1,50, cu o intensitate care variază de la an la an. Modelul a estimat 1,29 din cele două apariții din istoric. Diferența arată exact de ce banda se lărgește la evenimente.

**Scenarii** (băuturi): percentilele 10 și 90 ale erorii săptămânale din test dau ×0,863 și ×1,138. Pentru evenimente banda se lărgește ×1,10, deci devine ×0,849 și ×1,152.

**Stoc de siguranță** (băuturi, 14 zile, nivel de serviciu 95%):
z = 1,645; σ eroare săptămânală = 85,8 unități → 1,645 × 85,8 × √(14/7) ≈ **200 unități**.

**Risc de lipsă** (pagina Decide): probabilitatea ca cererea din timpul livrării să depășească stocul.
Se calculează ca 1 − Φ((stoc − cerere_livrare) ÷ σ_livrare), cu σ_livrare = σ_săptămânal × √(zile_livrare / 7).

---

## 4. Ce e simulat și ce limite are

**Simulat (tot):**
- Clienții, produsele, prețurile, stocurile și timpii de livrare.
- Comenzile, cu ritm propriu ±1 zi, cantități cu zgomot log-normal (σ = 0,18) și trend de +3% pe an.
- 2% comenzi sărite, 3% pierdute și 6% întârziate.
- Efectele de eveniment, post, temperatură și sezon turistic la hoteluri.
- Temperatura: istoric simulat; pentru viitor, doar normala sezonieră.
- Stocul curent: setat intenționat ca să existe și lipsă, și exces.

**Limite:**
- Datele sunt curate: fără erori de introducere, fără clienți noi sau pierduți definitiv, fără schimbări de preț și fără promoții proprii.
- Fiecare eveniment apare de 1–2 ori în istoricul de antrenare, deci multiplicatorii sunt incerți.
- Multiplicatorii sunt pe tip de client × categorie, nu pe client × produs. Efectele specifice, ca înghețata vara sau hotelurile vara, sunt doar parțial prinse.
- Cererea pe zi e o medie (cantitate × frecvență ÷ interval). Modelul nu știe în ce zi exactă vine fiecare comandă, de aceea MAPE se măsoară pe săptămână.
- Trendul nu e modelat explicit. E compensat parțial de fereastra recentă de 180 de zile.
- Benzile de scenariu și σ folosite în aplicație sunt calibrate pe perioada de test. Le-am verificat și fără privit în viitor (backtest pe ferestre succesive): acoperire 78%, față de ținta de 80%.
- Testul acoperă un singur an, deci fiecare eveniment (Crăciun, Paște) a fost testat o singură dată.
- Unitățile pe categorie sunt un amestec de ambalaje (pungi, baxuri, litri), acceptabil doar pentru demo.
- Pragurile de exces (60 / 21 / 45 de zile) și nivelul de serviciu sunt reguli de business alese de mână, nu rezultate din date.
- Pasul „Act” doar generează un CSV. Nu trimite nimic nicăieri.

---

## 5. Întrebări tehnice probabile, cu răspunsuri scurte

**1. De ce nu ai folosit machine learning?**
Scopul e un model pe care îl poate explica oricine din business, iar fiecare cifră se poate urmări până la CSV. Cu 25 de clienți și 2 ani de date, un model complex ar învăța zgomotul. Modelul simplu e un baseline bun. Un model ML, de exemplu gradient boosting pe aceleași variabile, ar trebui să-l bată în backtest ca să merite complexitatea.

**2. Cum eviți data leakage în evaluare?**
Modelul de test e antrenat strict până la 30.11.2025. Ritmul, multiplicatorii și cantitatea tipică se calculează doar din acea perioadă, apoi prognoza se compară cu dec. 2025 – oct. 2026. În plus, backtestul pe ferestre succesive reantrenează modelul la începutul fiecărei luni, doar cu datele de până atunci, și verifică benzile scenariilor calibrate doar pe lunile anterioare (acoperire 78%, țintă 80%).

**3. De ce MAPE săptămânal pe categorie, nu pe fiecare comandă?**
Pe linie de comandă, realul e des 0 sau foarte mic, iar MAPE devine infinit sau instabil. Agregat pe săptămână, eroarea de „ziua exactă” dispare și rămâne ce contează pentru stoc. Aplicația raportează și WAPE (eroarea totală ÷ volumul total, 11,0%), care nu explodează la valori mici. Ca reper, un baseline naiv are WAPE 17,9%.

**4. Ce faci cu un client sau un produs nou (cold start)?**
Fără istoric nu există ritm sau cantitate tipică. Folosești media segmentului (de exemplu, „cafenea din Cluj”) până la primele 5–8 comenzi, apoi treci treptat pe datele clientului. Banda de scenariu trebuie lărgită în perioada asta.

**5. Cum ar arăta în producție și cum scalează?**
Calculele sunt vectorizate în pandas (merge-uri, groupby), iar backtestul procesează ~65.000 de rânduri (client × produs × zi) în sub o secundă. `st.cache_data` le face o singură dată per server. În producție, antrenarea și prognoza ar rula ca job programat (zilnic sau săptămânal), cu rezultatele salvate într-o bază de date. Aplicația doar le citește. Pasul „Act” ar trimite comenzi în ERP sau mesaje către agenții de vânzări, cu aprobare umană peste un prag de valoare.
