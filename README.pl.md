# E-Commerce Performance & Attribution Engine

Moduł analityczny badający efektywność kampanii płatnych i bezpłatnych w sklepie internetowym w okresie **08.05–05.08.2026**. Projekt powstał, aby rozwiązać realny problem biznesowy: **jak nie przepalać budżetu reklamowego, opierając się na mylącym modelu Last-Click oraz gdzie w procesie zakupowym faktycznie uciekają klienci**.

Projekt łączy czyszczenie surowych logów GA4, kalkulację wskaźników rentowności (ROAS, CPA, AOV), analizę kohortową opóźnienia decyzji zakupowej oraz gotowy skrypt generujący interaktywny dashboard zarządczy w HTML.

> **Uwaga dotycząca danych:**  
> Analiza bazuje na rzeczywistych danych transakcyjnych i logach behawioralnych pochodzących z funkcjonującego sklepu internetowego. Wszystkie wrażliwe dane biznesowe oraz wolumeny przychodowe zostały poddane procedurze anonimizacji i standaryzacji (skalowanie metryk), co pozwoliło na pełne zachowanie realnych zależności, proporcji oraz wzorców konwersji przy zachowaniu poufności.



<br>



<!-- 📸 MIEJSCE NA ZDJĘCIE 1: GŁÓWNY HERO DASHBOARD -->
<!-- Zrób pełnoekranowy zrzut wygenerowanego pliku executive_summary_report.html otwartego w przeglądarce. Powinno być widać kafelki KPI na samej górze oraz początek tabeli podsumowującej. -->
![Pulpit Zarządczy - Executive Summary](docs/img/dashboard_hero.png)



<br>


## 1. Problem Biznesowy

W e-commerce opieranie budżetów wyłącznie na standardowym raporcie Last-Touch z Google Analytics prowadzi do trzech kosztownych błędów:
1. **Błędna ocena kampanii wizerunkowych i prospectingowych:** Kampanie sprowadzające nowych klientów są wyłączane, bo „nie domykają sprzedaży bezpośrednio”, a ruch organiczny i bezpośredni zbiera darmowe laury za zamówienia, których sam nie zainicjował.
2. **Niewidoczne przepalanie budżetu:** Kampanie generujące ogromny ruch wyglądają dobrze w raportach zasięgowych, ale po nałożeniu kosztów okazują się nierentowne (wysoki CPA, niski koszyk).
3. **Brak wiedzy o tempie zakupu:** Bez analizy kohortowej marketingu nie wiadomo, czy remarketing ma trwać 3 dni, 7 dni czy miesiąc.

**Cel projektu:** Odpowiedzieć na pytania: które kampanie skalować, które uciąć natychmiast, dlaczego klienci porzucają koszyki i jak rozkłada się konwersja w czasie.



<br>



## 2. Przepływ Danych (Workflow)

```text
Surowe dane z GA4 i koszty reklam (CSV)
       ↓
Czyszczenie danych, normalizacja nazw i wydzielenie Ceneo
       ↓
Modelowanie atrybucji (First-Touch vs Last-Touch)
       ↓
Integracja kosztów mediowych i wyliczenie ROAS, CPA, AOV, ARPU
       ↓
Analiza kohortowa opóźnienia zakupu (Day 0 vs D1-3 vs D4-7 vs >7)
       ↓
Diagnostyka 5-etapowego lejka zakupowego (Analiza Drop-off)
       ↓
Segmentacja kampanii i rekomendacje budżetowe
       ↓
Generowanie samodzielnego raportu HTML z wykresami Plotly
```

<br>


## 3. Dane i Przygotowanie Zbioru

Pipeline integruje 6 plików z danymi eksportowanymi z GA4 oraz systemów reklamowych (Ceneo, Google Ads):
* `sales_performance.csv` – transakcje i przychody w modelu Last-Touch.
* `first_touch_users.csv` – pierwsze źródła wizyt nowych użytkowników.
* `traffic_and_revenue.csv` – wolumeny użytkowników, transakcji i przychodu.
* `campaign_costs.csv` – realne wydatki reklamowe na kampanie.
* `funnel_events.csv` – zdarzenia lejka: `session_start`, `view_item`, `add_to_cart`, `begin_checkout`, `purchase`.
* `cohort_analysis_campaigns.csv` & `cohort_analysis_sources.csv` – dzienne interwały powrotów i zakupów.

### 1) Czyszczenie Danych
* **Wydzielenie Ceneo z ruchu referral:** Ceneo w GA4 wpada domyślnie jako zwykły odsyłacz (`referral`). Ponieważ to kanał płatny za klik (CPC), został odseparowany od darmowych poleceń, aby nie fałszować rentowności.
* **Standaryzacja braków i `(not set)`:** Puste wartości i ucięte parametry UTM zunifikowano do postaci `Not set (not set)`.
* **Usuwanie duplikatów systemowych GA4:** Oczyszczono zbiory kohortowe z wierszy sumarycznych `RESERVED` oraz zdublowanych rekordów z drugiego zakresu dat.

### 2) Inżynieria Wskaźników
* **Delta Atrybucji:** Różnica między przychodem zainicjowanym (First-Touch) a domkniętym (Last-Touch).
* **Zgodność Modeli (Match %):** Pokazuje, na ile dany kanał domyka sprzedaż w tym samym źródle, w którym ją zaczął.
* **ROAS & CPA:**
  $$\text{ROAS} = \frac{\text{Przychód}}{\text{Koszt}}, \quad \text{CPA} = \frac{\text{Koszt}}{\text{Liczba Transakcji}}$$
* **Wycinek kohortowy:** Przeliczenie skumulowanych transakcji w GA4 na faktyczny, inkrementalny przyrost sprzedaży w dniach: **Day 0** (ten sam dzień), **Days 1–3**, **Days 4–7** i **Powyżej 7 dni**.

### 3) Przestrzeń Zmiennych i Podział Źródeł
* **Ruch bezpłatny:** `(direct)`, `(organic)`, `(referral)`, `Shopping Free Listings`, `(ai-assistant)`, `Not set (not set)`.
* **Kampanie płatne:** `ceneo / referral`, `Milwaukee - Search`, `Milwaukee-Ogrod-Shopping`, `PMax Distar`, `(cross-network)`, `adbox_ceneo`, `Distar rabat`, `aku`.

### 4) Macierz Kwalifikacji Kampanii
* **Core / High-Value:** Wysoki koszyk (AOV $\ge$ 500 PLN) i wysoki zwrot na usera (ARPU powyżej mediany).
* **Strong Conversion:** Stabilna konwersja (CR $\ge$ 2.0%).
* **Low AOV:** Zamówienia drobne, wymagające cross-sellingu.
* **Needs Audit:** Kampanie bez ani jednej transakcji.


<br>


## 4. Ewaluacja i Zestawienie Źródeł

Zbiorcze zestawienie efektywności wszystkich analizowanych źródeł ruchu:

| Źródło / Kampania | Użytkownicy | Transakcje | Przychód (PLN) | ROAS | CPA (PLN) | AOV (PLN) | CR % | Transakcje Day 0 | Zgodność FT/LT | Status / Rekomendacja |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **ceneo / referral** | 3 831 | 87 | 105 711,99 | **12,31** | **98,72** | 1 215,08 | 2,27% | 72,7% | 100,0% | **Top Performer (Skalować)** |
| **Milwaukee - Search** | 4 338 | 45 | 43 398,90 | **3,63** | **265,86** | 964,42 | 1,04% | 73,5% | 90,7% | **Utrzymać + Optymalizować CRO** |
| **(direct)** | 1 234 | 39 | 38 064,50 | — | — | 976,01 | 3,16% | 84,6% | 96,2% | **Utrzymać (Baza powracająca)** |
| **(organic)** | 2 630 | 26 | 23 214,10 | — | — | 892,85 | 0,99% | 76,9% | 80,6% | **Utrzymać (Domyka paid ads)** |
| **Milwaukee-Ogrod-Shopping** | 13 783 | 62 | 12 921,38 | **1,08** | **208,41** | 208,41 | 0,45% | 80,0% | 98,0% | **Przepalanie (Uciąć budżet o 50%)** |
| **PMax \| Distar** | 470 | 14 | 5 152,00 | **3,65** | **100,51** | 368,00 | 2,98% | 85,7% | 97,5% | **Skalować (Wdrożyć cross-sell)** |
| **Not set (not set)** | 135 | 11 | 9 845,20 | — | — | 895,02 | 8,15% | 81,8% | 92,1% | **Audyt techniczny tagów UTM** |
| **(ai-assistant)** | 37 | 2 | 2 031,80 | — | — | 1 015,90 | 5,41% | 50,0% | 100,0% | **Nowy trend (Monitorować)** |
| **Shopping Free Listings** | 22 | 2 | 484,00 | — | — | 242,00 | 8,89% | 50,0% | 100,0% | **Optymalizować feed produktowy** |
| **(cross-network)** | 312 | 1 | 296,00 | **0,52** | **296,00** | 296,00 | 0,32% | 100,0% | 100,0% | **Wstrzymać / Zmienić strukturę** |
| **adbox_ceneo** | 14 | 0 | 0,00 | **0,00** | — | 0,00 | 0,00% | — | — | **Wyłączyć natychmiast** |
| **Distar rabat** | 3 | 0 | 0,00 | **0,00** | — | 0,00 | 0,00% | — | — | **Wyłączyć natychmiast** |
| **aku** | 3 | 0 | 0,00 | **0,00** | — | 0,00 | 0,00% | — | — | **Wyłączyć natychmiast** |

### Kluczowe Wnioski Biznesowe
1. **Ceneo to filar rentowności sklepu:** 105,7k PLN przychodu, wysoki koszyk (1 215 PLN) i znakomity ROAS 12,31. Ruch z porównywarki wie, po co przychodzi – 72,7% kupuje od razu, a reszta traktuje sklep jako bazę odniesienia i wraca w ciągu tygodnia.
2. **Dramatyczna nieefektywność `Milwaukee-Ogrod`:** Kampania ściągnęła ponad połowę całego ruchu sklepu (13,7k wizyt) i zjadła rekordowy budżet (12,9k PLN), dając ledwo próg rentowności (ROAS 1,08). CPA na poziomie 208 PLN przy koszyku 208 PLN oznacza realną stratę po odliczeniu kosztu towaru i logistyki.
3. **Synergia Paid Search z SEO:** Płatna kampania `Milwaukee Search` inicjuje duży ruch u nowych klientów (o 4,4k PLN więcej w First-Touch niż w Last-Touch). Z kolei Organic Search domyka o 4,5k PLN więcej w Last-Touch. Wniosek: użytkownicy widzą reklamę płatną, szukają opinii, a potem wpisują nazwę sklepu w Google i kupują organicznie.
4. **Wysoki potencjał ruchu z asystentów AI:** Źródło `(ai-assistant)` miało tylko 37 wizyt, ale wygenerowało 2 zakupy na łączną kwotę ponad 2 000 PLN (CR = 5,41%, AOV > 1 000 PLN). To bardzo obiecujący kanał wczesnego etapu.

### Symulacja Reallokacji Budżetu
* Obcięcie budżetu `Milwaukee-Ogrod` o 50% uwalnia ok. **6 460 PLN**.
* Przeniesienie 70% tej kwoty na Ceneo (podniesienie stawek CPC na marżowych produktach) i 30% na PMax Distar pozwala podnieść całościowy ROAS konta z **4,12 do ponad 6,50** bez straty wolumenu sprzedaży.


<br>


## 5. Wykresy i Analityka Wizualna

### 1) Rentowność Kampanii Płatnych: ROAS vs CPA
Wykres bąbelkowy zestawiający koszt pozyskania klienta (CPA) z mnożnikiem zwrotu z reklamy (ROAS). Wielkość bąbla odzwierciedla wolumen przychodu.

<!-- 📸 MIEJSCE NA ZDJĘCIE 2: WYKRES BĄBELKOWY ROAS VS CPA -->
![Rentowność Kampanii Płatnych](docs/img/chart_roas_vs_cpa.png)

* **Wniosek:** Kampanie w lewym górnym rogu (Ceneo) przynoszą wysoki zysk niskim kosztem. Kampanie w prawym dolnym rogu (`Milwaukee-Ogrod`, `cross-network`) drenują budżet.

### 2) Czas do Zakupu: Analiza Kohortowa Latencji
Poziomy wykres skumulowany pokazujący, ile dni upływa od pierwszej wizyty do zakupu w poszczególnych źródłach.

<!-- 📸 MIEJSCE NA ZDJĘCIE 3: WYKRES KOHORTOWY -->
![Dystrybucja Czasu do Zakupu](docs/img/chart_cohort_latency.png)

* **Wniosek:** **88,5% klientów kupuje tego samego dnia (Day 0)**. Użytkownicy rozważający zakup dłużej potrzebują maksymalnie 1–7 dni (20–27% transakcji na Ceneo i Searchu). Remarketing dłuższy niż 7 dni nie ma uzasadnienia ekonomicznego.

### 3) 5-Etapowy Lejek Zakupowy (Gdzie Uciekają Klienci)
Wykres lejkowy zdarzeń e-commerce z interaktywnym przełącznikiem kampanii.

<!-- 📸 MIEJSCE NA ZDJĘCIE 4: LEJEK ZAKUPOWY -->
![Lejek Konwersji Zakupowej](docs/img/chart_purchase_funnel.png)

* **Główny problem e-commerce:** Na etapie przejścia z `begin_checkout` do `purchase` odpada aż **76,5% użytkowników** (tylko 23,5% finalizuje zamówienie). Klienci dodają produkty do koszyka i wchodzą w formularz, po czym rezygnują – wskazuje to na brak preferowanych metod płatności, wymóg rejestracji lub niespodziewane koszty dostawy.



<br>



## 6. Stos Technologiczny

* **Język i biblioteki bazowe:** Python 3.10+, Pandas, NumPy
* **Wizualizacja danych:** Plotly Express, Plotly Graph Objects
* **Frontend raportu:** Samodzielny szablon HTML5/CSS3 (Dark Mode, Flexbox, CSS Grid) zintegrowany z silnikiem Plotly.js – otwiera się lokalnie w przeglądarce bez konieczności stawiania serwera.


<br>



## 7. Struktura Projektu

```text
ecommerce-analytics/
├── docs/
│   └── img/
│       ├── dashboard_hero.png        # Zrzut całego dashboardu zarządczego
│       ├── chart_roas_vs_cpa.png     # Wykres ROAS vs CPA dla kampanii płatnych
│       ├── chart_cohort_latency.png  # Wykres kohortowy czasu do zakupu
│       └── chart_purchase_funnel.png # Wykres 5-etapowego lejka zakupowego
├── sales_performance.csv             # Transakcje Last-Touch
├── first_touch_users.csv             # Ruch First-Touch
├── traffic_and_revenue.csv           # Dane zbiorcze o ruchu
├── campaign_costs.csv                # Koszty reklamowe
├── funnel_events.csv                 # Zdarzenia na ścieżce zakupu
├── cohort_analysis_campaigns.csv     # Kohorty per kampania
├── cohort_analysis_sources.csv       # Kohorty per źródło
├── 01_attribution_model.py           # Skrypt 1: Porównanie First vs Last Touch
├── 02_campaign_matrix.py             # Skrypt 2: Macierz efektywności (CR vs AOV)
├── 03_funnel_and_roas.py             # Skrypt 3: Analiza lejka i ROAS
├── 04_cohort_latency.py              # Skrypt 4: Analiza czasu konwersji
├── 05_executive_report.py            # Skrypt 5: Główny generator raportu HTML
├── requirements.txt                  # Wymagane biblioteki Pythona
└── README.md                         # Dokumentacja projektu
```


<br>




## 8. Jak Uruchomić Projekt

### Wymagania Wstępne
* Zainstalowany Python 3.10 lub nowszy
* Pliki z danymi (`.csv`) umieszczone w głównym katalogu projektu

### 1. Klonowanie repozytorium
```bash
git clone https://github.com/laura-szczerbowska/ecommerce-analytics.git
cd ecommerce-analytics
```

### 2. Środowisko wirtualne i instalacja zależności
# Utworzenie środowiska wirtualnego
python -m venv .venv

# Aktywacja środowiska (Linux/macOS):
source .venv/bin/activate

# Aktywacja środowiska (Windows PowerShell):
.\.venv\Scripts\Activate.ps1

# Instalacja wymaganych pakietów
pip install -r requirements.txt



<br>



### 3. Generowanie dashboardu zarządczego
python 05_executive_report.py
Skrypt przetworzy pliki CSV, obliczy wskaźniki, wygeneruje gotowy plik executive_summary_report.html i automatycznie otworzy go w domyślnej przeglądarce.

## 9. Kierunki Dalszego Rozwoju
* Algorytmiczny model atrybucji (Markov Chains / Shapley): Przejście z modeli heurystycznych na probabilistyczny model łańcuchów Markowa dla wielokanałowych ścieżek zakupowych.
* Integracja z Google BigQuery: Bezpośrednie pobieranie danych ze strumienia zdarzeń GA4 bez konieczności ręcznego eksportu plików CSV.
* Automatyczny alert wahań CPA: Skrypt powiadamiający zespół (np. na Slacku), gdy koszt pozyskania transakcji (CPA) wzrośnie o ponad 30% tydzień do tygodnia.


<br>


## 10. Podsumowanie i Rekomendacje dla Zarządu
* Wdrożenie wniosków z analizy pozwala na natychmiastowe oszczędności i wzrost rentowności:
* Natychmiastowe cięcie kosztów: Obcięcie budżetu nierentownej kampanii Milwaukee-Ogrod o 50% oraz wyłączenie zerowych kampanii (adbox_ceneo, aku, Distar rabat) zatrzymuje marnowanie ponad 7 000 PLN kwartalnie.
* Doinwestowanie Ceneo: Ruch z porównywarki generuje 12-krotny zwrot (ROAS 12,31). Należy zabezpieczyć budżet i podnieść stawki na najlepiej konwertujące produkty, aby nie tracić wyświetleń przez wyczerpane saldo.
* Naprawa checkoutu priorytetem przed zwiększaniem ruchu: Sprowadzanie nowego ruchu przy porzucalności kasy na poziomie 76,5% to marnowanie budżetu. Wdrożenie płatności BLIK jednym kliknięciem oraz zakupów bez rejestracji podniesie zyski szybciej niż jakakolwiek nowa kampania reklamowa.
* Skrócenie okna remarketingu: Kampanie remarketingowe powinny skupić się na pierwszych 7 dniach od wizyty – po tym czasie szansa na domknięcie zakupu drastycznie spada.
