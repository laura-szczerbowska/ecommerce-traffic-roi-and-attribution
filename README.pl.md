<div align="right">
  <a href="./README.md">English</a> | <strong>Polski</strong>
</div>

# Wielokanałowa Analiza Efektywności Kampanii i Modeli Atrybucji w E-Commerce

Moduł analityczny badający efektywność kampanii płatnych i źródeł bezpłatnych w sklepie internetowym w okresie **08.05-05.08.2026**. Rozwiązuje on konkretny problem: pokazuje, jak skuteczniej wydawać budżet bez opierania się wyłącznie na 'Last Touch' oraz w których momentach procesu klienci rezygnują z zakupu.”

Projekt łączy czyszczenie surowych logów GA4, kalkulację wskaźników rentowności (ROAS, CPA, AOV), analizę kohortową opóźnienia decyzji zakupowej oraz gotowy skrypt generujący interaktywny dashboard zarządczy w HTML.

> **Uwaga dotycząca danych:**  
> Analiza bazuje na rzeczywistych danych transakcyjnych i logach behawioralnych pochodzących z funkcjonującego sklepu internetowego. Wszystkie wrażliwe dane biznesowe oraz wolumeny przychodowe zostały poddane procedurze anonimizacji i standaryzacji, co pozwoliło na pełne zachowanie realnych zależności, proporcji oraz wzorców konwersji przy zachowaniu poufności.


<br>



<br>







https://github.com/user-attachments/assets/7549c1da-bbde-4963-a660-0bac8d8346fd






<br>


<br>


## 1. Problem Biznesowy

W e-commerce opieranie budżetów wyłącznie na standardowym raporcie Last-Touch z Google Analytics prowadzi do trzech kosztownych błędów:
1. **Błędna ocena kampanii wizerunkowych i prospectingowych:** Kampanie sprowadzające nowych klientów są wyłączane, ponieważ „nie domykają sprzedaży bezpośrednio”, a ruch organiczny i bezpośredni zbiera darmowe laury za zamówienia, których sam nie zainicjował.
2. **Niewidoczne przepalanie budżetu:** Kampanie generujące ogromny ruch wyglądają dobrze w raportach zasięgowych, ale po nałożeniu kosztów okazują się nierentowne (wysoki CPA, niski koszyk).
3. **Brak wiedzy o tempie zakupu:** Bez analizy kohortowej marketingu nie wiadomo, czy remarketing ma trwać 3 dni, 7 dni czy miesiąc.

**Cel projektu:** Odpowiedzieć na pytania: które kampanie skalować, które uciąć natychmiast, dlaczego klienci porzucają koszyki i jak rozkłada się konwersja w czasie.



<br>



## 2. Przepływ Danych (Workflow)

```text
Surowe dane z GA4 i koszty kampanii
       ↓
Czyszczenie danych, normalizacja nazw i wydzielenie Comparison Engine z ogólnego 'refferal'
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

Pipeline integruje 6 plików z danymi eksportowanymi z GA4 oraz koszty płatnych kampanii:
* `sales_performance.csv` - transakcje i przychody w modelu Last-Touch.
* `first_touch_users.csv` - pierwsze źródła wizyt nowych użytkowników.
* `traffic_and_revenue.csv` - wolumeny użytkowników, transakcji i przychodu.
* `campaign_costs.csv` - realne wydatki reklamowe na kampanie.
* `funnel_events.csv` - zdarzenia lejka: `session_start`, `view_item`, `add_to_cart`, `begin_checkout`, `purchase`.
* `cohort_analysis_campaigns.csv` & `cohort_analysis_sources.csv` - dzienne interwały powrotów i zakupów.


<br>



### 1) Czyszczenie Danych
* **Wydzielenie Comparison Engine z ruchu referral:** Comparison Engine w GA4 wpada domyślnie jako zwykły odsyłacz (`referral`). Ponieważ to kanał płatny za klik (CPC), został odseparowany od darmowych poleceń, aby nie fałszować rentowności.
* **Standaryzacja braków i `(not set)`:** Puste wartości i ucięte parametry UTM zunifikowano do postaci `Not set (not set)`.
* **Usuwanie duplikatów systemowych GA4:** Oczyszczono zbiory kohortowe z wierszy sumarycznych `RESERVED` oraz zdublowanych rekordów z drugiego zakresu dat.


<br>


### 2) Inżynieria Wskaźników

- **Delta Atrybucji:** Różnica między przychodem zainicjowanym (First-Touch) a domkniętym (Last-Touch):


<br>


$$
\Delta \text{Przychód} = \text{Przychód}_{\text{FT}} - \text{Przychód}_{\text{LT}}
$$


<br>


- **Zgodność Modeli (Match Rate):** Pokazuje, na ile dany kanał domyka sprzedaż w tym samym źródle, w którym ją zaczął:


<br>


$$
\text{Match Rate} = \frac{\min(\text{Przychód}_{\text{FT}}, \text{Przychód}_{\text{LT}})}{\max(\text{Przychód}_{\text{FT}}, \text{Przychód}_{\text{LT}})} \times 100
$$


<br>


- **Wskaźniki Rentowności Mediów (ROAS & CPA):**


<br>


$$
\text{ROAS} = \frac{\text{Przychód}}{\text{Koszt}}, \quad \text{CPA} = \frac{\text{Koszt}}{\text{Liczba Transakcji}}
$$


<br>


- **Wycinek kohortowy:** Przeliczenie skumulowanych transakcji w GA4 na faktyczny, inkrementalny przyrost sprzedaży w dniach: **Day 0 (ten sam dzień)**, **Days 1-3**, **Days 4-7** i **Powyżej 7 dni**.


<br>


### 3) Przestrzeń Zmiennych i Podział Źródeł
* **Ruch bezpłatny:** `(direct)`, `(organic)`, `(referral)`, `Shopping Free Listings`, `(ai-assistant)`, `Not set (not set)`.
* **Kampanie płatne:** `comparison_engine / referral`, `PowerBrand – ElectroStore – Search Website`, `PowerBrand-Shopping`, `PMax | DiamondTools`, `(cross-network)`, `adbox_comparison`, `DiamondTools discount`, `aku`.


<br>


### 4) Macierz Kwalifikacji Kampanii
* **Core / High-Value:** Wysoki koszyk (AOV $\ge$ 500 PLN) i wysoki zwrot na usera (ARPU powyżej mediany).
* **Strong Conversion:** Stabilna konwersja (CR $\ge$ 2.0%).
* **Low AOV:** Zamówienia drobne, wymagające cross-sellingu.
* **Needs Audit:** Kampanie bez ani jednej transakcji.


<br>


## 4. Ewaluacja i Zestawienie Źródeł

Zbiorcze zestawienie efektywności wszystkich analizowanych źródeł ruchu:

| Source / Campaign | Users | Trans. | Revenue (PLN) | ROAS | CPA (PLN) | CR % | Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Comparison Engine / referral** | 3 831 | 87 | 105 711.99 | 12.31 | 98.72 | 2.27% | **Protect & Fund** |
| **PowerBrand – ElectroStore – Search Website** | 4 338 | 45 | 43 398.90 | 3.63 | 265.86 | 1.04% | **Maintain & Optimize** |
| **(direct)** | 1 234 | 39 | 38 064.50 | — | — | 3.16% | **Leverage & Retain** |
| **(organic)** | 2 630 | 26 | 23 214.10 | — | — | 0.99% | **Leverage & Retain** |
| **PowerBrand-Shopping** | 13 783 | 62 | 12 921.38 | 1.08 | 208.41 | 0.45% | **Audit & Restructure** |
| **PMax DiamondTools** | 470 | 14 | 5 152.00 | 3.65 | 100.51 | 2.98% | **Maintain & Optimize** |
| **Not set (not set)** | 135 | 11 | 9 845.20 | — | — | 8.15% | **Audit & Restructure** |
| **(ai-assistant)** | 37 | 2 | 2 031.80 | — | — | 5.41% | **Leverage & Retain** |
| **Shopping Free Listings** | 22 | 2 | 484.00 | — | — | 8.89% | **Leverage & Retain** |
| **(cross-network)** | 312 | 1 | 296.00 | 0.52 | 296.00 | 0.32% | **Audit & Restructure** |
| **Zero-conversion paid (3 campaigns)** | 20 | 0 | 0.00 | 0.00 | — | 0.00% | **Pause / Cut Spend** |

*\*Obejmuje: `adbox_comparison`, `DiamondTools discount`, `aku`.*


<br>



### Kluczowe Wnioski Biznesowe

1) **Comparison Engine to filar rentowności sklepu:** 105,7k PLN przychodu, wysoki koszyk (1215 PLN) i najwyższy ROAS 12,31. Ruch z porównywarki przychodzi z określoną intencją - 72,7% użytkowników dokonuje zakupu od razu, a pozostała część traktuje sklep jako bazę odniesienia i wraca w ciągu tygodnia.
  
2) **Dramatyczna nieefektywność `PowerBrand-Shopping`:** Kampania ściągnęła ponad połowę całego ruchu sklepu (13,7k wizyt) i pochłonęła rekordowy budżet (12,9k PLN), dając ledwo próg rentowności (ROAS 1,08). CPA na poziomie 208 PLN przy koszyku 208 PLN oznacza realną stratę po odliczeniu kosztu towaru i logistyki.

3) **Synergia Paid Search z SEO:** Płatna kampania `PowerBrand – ElectroStore – Search Website` inicjuje duży ruch u nowych klientów (o 4,4k PLN więcej w First-Touch niż w Last-Touch). Z kolei Organic Search domyka o 4,5k PLN więcej w Last-Touch. Można więć stwierdzić, że użytkownicy widzą reklamę płatną, szukają opinii, a potem wpisują nazwę sklepu w Google i kupują organicznie.

4) **Wysoki potencjał ruchu z asystentów AI:** Źródło `(ai-assistant)` pomimo tego, że miało tylko 37 wizyt, wygenerowało 2 zakupy na łączną kwotę ponad 2 000 PLN (CR = 5,41%, AOV > 1 000 PLN). To bardzo obiecujący kanał wczesnego etapu.


<br>


### Symulacja Realokacji Budżetu

- Obcięcie budżetu `PowerBrand-Shopping` o 50% uwalnia ok. **6 460 PLN**.

  
- Przeniesienie 70% tej kwoty na Comparison Engine (podniesienie stawek CPC na marżowych produktach) i 30% na PMax DiamondTools pozwala podnieść całościowy ROAS konta z **4,12 do ponad 6,50** bez straty wolumenu sprzedaży.


<br>


## 5. Wykresy i Analityka Wizualna

### 1) Rentowność Kampanii Płatnych: ROAS vs CPA
Wykres bąbelkowy zestawiający koszt pozyskania klienta (CPA) z mnożnikiem zwrotu z reklamy (ROAS). Wielkość bąbla odzwierciedla wolumen przychodu.


<br>


<img width="1535" height="737" alt="image" src="https://github.com/user-attachments/assets/3e9926dc-3a98-4134-a1c0-7929f57dfec6" />



<br>


<br>


**Wniosek:** Kampanie w lewym górnym rogu (Comparison Engine) przynoszą wysoki zysk niskim kosztem. Kampanie w prawym dolnym rogu (`PowerBrand-Shopping`, `cross-network`) drenują budżet.


<br>


### 2) Czas do Zakupu: Analiza Kohortowa Latencji
Poziomy wykres skumulowany pokazujący, ile dni upływa od pierwszej wizyty do zakupu w poszczególnych źródłach.


<br>


<img width="1517" height="853" alt="image" src="https://github.com/user-attachments/assets/61eb1e1e-7865-4922-ab90-fa89d6a1221c" />



<br>


<br>


**Wniosek:** **88,5% klientów sklepu internetowego kupuje tego samego dnia (Day 0)**. Użytkownicy rozważający zakup dłużej potrzebują maksymalnie 1-7 dni (20-27% transakcji na Comparison Engine i Searchu). Nie ma sensu prowadzić remarketingu dłużej niż 7 dni.


<br>


### 3) 5-Etapowy Lejek Zakupowy (Gdzie Uciekają Klienci)
Wykres lejkowy zdarzeń e-commerce z interaktywnym przełącznikiem kampanii.


<br>


<img width="1485" height="706" alt="image" src="https://github.com/user-attachments/assets/04f9121b-9d34-4d7e-8fcb-c48377723063" />



<br>


<br>


**Główny problem e-commerce:** Na etapie przejścia z `begin_checkout` do `purchase` odpada aż **76,5% użytkowników** (tylko 23,5% finalizuje zamówienie). Klienci dodają produkty do koszyka i wchodzą w formularz, po czym rezygnują - wskazuje to na brak preferowanych metod płatności, wymóg rejestracji lub niespodziewane koszty dostawy.



<br>



## 6. Stos Technologiczny

- **Język i biblioteki bazowe:** Python 3.10+, Pandas, NumPy
- **Wizualizacja danych:** Plotly Express, Plotly Graph Objects
- **Frontend raportu:** Samodzielny szablon HTML5/CSS3 zintegrowany z silnikiem Plotly.js - otwiera się lokalnie w przeglądarce bez konieczności stawiania serwera.


<br>



## 7. Struktura Projektu

```text
ecommerce-analytics/
├── data/
│   ├── sales_performance.csv              # Transakcje Last-Touch
│   ├── first_touch_users.csv              # Ruch First-Touch
│   ├── traffic_and_revenue.csv            # Dane zbiorcze o ruchu
│   ├── campaign_costs.csv                 # Koszty reklamowe
│   ├── funnel_events.csv                  # Zdarzenia na ścieżce zakupu
│   ├── cohort_analysis_campaigns.csv      # Kohorty per kampania
│   └── cohort_analysis_sources.csv        # Kohorty per źródło
├── 01_attribution_model.py                # Skrypt 1: Porównanie First vs Last Touch
├── 02_campaign_matrix.py                  # Skrypt 2: Macierz efektywności (CR vs AOV)
├── 03_funnel_and_roas.py                  # Skrypt 3: Analiza lejka i ROAS
├── 04_cohort_latency.py                   # Skrypt 4: Analiza czasu konwersji
├── 05_executive_report.py                 # Skrypt 5: Główny generator raportu HTML
├── executive_summary_report.html          # Interaktywny dashboard zarządczy (wygenerowany raport html)
├── requirements.txt                       # Wymagane biblioteki Pythona
├── README.md                              # Dokumentacja w języku angielskim
└── README.pl.md                           # Dokumentacja w języku polskim

```


<br>


## 8. Jak Uruchomić Projekt

#### 1) Klonowanie repozytorium
```bash
git clone https://github.com/laura-szczerbowska/ecommerce-analytics.git
cd ecommerce-analytics
```



#### 2) Środowisko wirtualne i instalacja zależności

* Utworzenie środowiska wirtualnego
python -m venv .venv

* Aktywacja środowiska (Linux/macOS)/(Windows PowerShell):
source .venv/bin/activate / .\.venv\Scripts\Activate.ps1

* Instalacja wymaganych pakietów
```bash
pip install -r requirements.txt
```



#### 3) Generowanie dashboardu zarządczego

`python 05_executive_report.py`

Skrypt przetworzy pliki CSV, obliczy wskaźniki, wygeneruje gotowy plik executive_summary_report.html i automatycznie otworzy go w domyślnej przeglądarce.



<br>



## 9. Kierunki Dalszego Rozwoju
- **Integracja z Google BigQuery**: Bezpośrednie pobieranie danych ze strumienia zdarzeń GA4 bez konieczności ręcznego eksportu plików CSV.
- **Automatyczny alert wahań CPA**: Skrypt powiadamiający zespół (np. na Slacku), gdy koszt pozyskania transakcji (CPA) wzrośnie o ponad 30% tydzień do tygodnia.


<br>


## 10. Podsumowanie i Rekomendacje dla Zarządu

Wdrożenie wniosków z analizy pozwala na natychmiastowe oszczędności i wzrost rentowności:
- **Natychmiastowe cięcie kosztów**: Obcięcie budżetu nierentownej kampanii PowerBrand-Shopping o 50% oraz wyłączenie 'zerowych' kampanii (adbox_comparison, aku, DiamondTools discount) zatrzymuje stratę ponad 7 000 PLN kwartalnie.
- **Doinwestowanie Comparison Engine**: Ruch z porównywarki generuje 12-krotny zwrot (ROAS 12,31). Należy zabezpieczyć budżet i podnieść stawki na najlepiej konwertujące produkty, aby nie tracić wyświetleń przez wyczerpane saldo.
- **Naprawa checkoutu priorytetem przed zwiększaniem ruchu**: Sprowadzanie nowego ruchu przy porzucalności kasy na poziomie 76,5% to marnowanie budżetu. Wdrożenie płatności BLIK jednym kliknięciem oraz zakupów bez rejestracji podniesie zyski szybciej niż jakakolwiek nowa kampania reklamowa.
- **Skrócenie okna remarketingu**: Kampanie remarketingowe powinny skupić się na pierwszych 7 dniach od wizyty – po tym czasie szansa na domknięcie zakupu drastycznie spada.
