<div align="right">
  <strong>English</strong> | <a href="./README.pl.md">Polski</a>
</div>

# Multichannel Campaign Performance & Attribution Modeling in E-Commerce

An end-to-end analytics engine evaluating paid and organic marketing performance for an e-commerce platform (hardware & power tools sector) over the period **08.05–05.08.2026**. The project was built to address a critical business dilemma: **how to stop ad-spend waste caused by misleading Last-Click attribution and identify where potential customers actually drop off along the purchase journey**.

The project combines raw GA4 event-log preprocessing, media efficiency calculations (ROAS, CPA, AOV), purchase latency cohort modeling, and an automated Python script generating an interactive executive HTML dashboard.

> **Data Notice:**  
> This analysis is grounded in real transaction records and behavioral logs extracted from an operational e-commerce store. All sensitive commercial metrics and monetary totals were anonymized and standardized (feature-scaled), fully preserving authentic behavioral patterns, conversion dynamics, and cross-channel relationships.


<br>


<img width="1897" height="1096" alt="image" src="https://github.com/user-attachments/assets/693745a7-b68a-4e3e-9ef1-ee87858c14b8" />



<br>


## 1. Business Problem

In e-commerce operations, allocating ad spend strictly according to standard Last-Touch GA4 reports causes three costly strategic mistakes:
1. **Misjudging top-of-funnel & prospecting campaigns:** Channels introducing new buyers are prematurely paused because they do not "close" transactions directly, while Direct and Organic Search claim zero-marginal-cost credit for journeys initiated by paid ads.
2. **Hidden budget bleeding:** High-volume traffic sources appear healthy on reach metrics, but once ad costs are integrated, they reveal unsustainable unit economics (prohibitive CPA, low average order values).
3. **Misaligned remarketing windows:** Without empirical time-to-conversion cohort tracking, marketing teams guess whether remarketing budgets should run for 3 days, 7 days, or a month.

**Project Objective:** Deliver data-driven clarity on which campaigns to scale, which micro-budgets to cut immediately, why shoppers abandon checkout, and how purchase decisions unfold over time.


<br>


## 2. Data Workflow

```text
Raw GA4 Event Logs & Ad Spend CSVs
       ↓
Data Cleaning, Label Standardization & Ceneo Channel Isolation
       ↓
Attribution Modeling (First-Touch vs Last-Touch Delta)
       ↓
Cost Integration & Unit Economics (ROAS, CPA, AOV, ARPU)
       ↓
Cohort Purchase Latency Decomposition (Day 0 vs D1-3 vs D4-7 vs >D7)
       ↓
5-Stage E-Commerce Funnel Diagnostics (Checkout Drop-off Analysis)
       ↓
Performance Segmentation Matrix & Tactical Recommendations
       ↓
Stand-Alone Dark-Mode HTML Executive Dashboard Generation (Plotly.js)
```


<br>


## 3. Data & Dataset Preparation

The pipeline ingests and synchronizes 6 source datasets exported from GA4 and advertising platforms (Google Ads, Ceneo):
- `sales_performance.csv` – Transaction counts and revenue under the Last-Touch model.
- `first_touch_users.csv` – User acquisition touchpoints (First-User Campaign / Source-Medium).
- `traffic_and_revenue.csv` – Aggregated active users, transactions, and gross revenue per source.
- `campaign_costs.csv` – Direct media ad spend across paid campaigns.
- `funnel_events.csv` – Core e-commerce events: `session_start`, `view_item`, `add_to_cart`, `begin_checkout`, `purchase`.
- `cohort_analysis_campaigns.csv` & `cohort_analysis_sources.csv` – Daily cohort tracking matrices recording purchase intervals.


<br>


### 1) Data Preprocessing & Cleansing
- **Ceneo Isolation:** In standard GA4 setups, comparison shopping engine traffic from Ceneo defaults to generic `(referral)`. Because Ceneo operates as a paid Cost-Per-Click (CPC) channel, it was algorithmically separated into `ceneo / referral` to prevent distorting unpaid organic referral metrics.
- **Null & Missing Data Hygiene:** Missing entries, tracking blanks, and untagged parameters were unified into `'Not set (not set)'`.
- **GA4 System Artifact Removal:** Stripped internal summary rows (`RESERVED`) and duplicated records across multiple date ranges (`date_range_0` validation).


<br>



### 2) Feature Engineering & Formulas
- **Attribution Delta:** Direct variance between initial reach value and closing value:

<br>


$$
\Delta \text{Revenue} = \text{Revenue}_{\text{First-Touch}} - \text{Revenue}_{\text{Last-Touch}}
$$

  
<br>


- **Model Match Rate (Match %):** Quantifies source autonomy in concluding conversions on-domain:
  
  
<br>



  $$\text{Match}_{\%} = \frac{\min(\text{Revenue}_{\text{FT}}, \text{Revenue}_{\text{LT}})}{\max(\text{Revenue}_{\text{FT}}, \text{Revenue}_{\text{LT}})} \times 100$$
  
  
<br>



- **Media Profitability Ratios (ROAS & CPA):**
  
  
<br>



  $$\text{ROAS} = \frac{\text{Revenue}}{\text{Cost}}, \quad \text{CPA} = \frac{\text{Cost}}{\text{Transactions}}$$
  
  
<br>



- **Incremental Cohort Latency Extraction:** Converted cumulative GA4 cohort values into true non-cumulative daily conversions via series differencing (`diff()`), mapped into 4 analytical windows: **Day 0 (Same-Day)**, **Days 1–3**, **Days 4–7**, and **Over 7 Days**.


<br>


### 3) Feature Space & Channel Classification
- **Organic & Unpaid Channels:** `(direct)`, `(organic)`, `(referral)`, `Shopping Free Listings`, `(ai-assistant)`, `Not set (not set)`.
- **Paid Media Campaigns:** `comparison_engine / referral`, `PowerBrand – ElectroStore – Search Website`, `PowerBrand-Shopping`, `PMax | DiamondTools`, `(cross-network)`, `adbox_comparison`, `DiamondTools discount`, `aku`.


<br>


### 4) Performance Matrix Segmentation
- **Core / High-Value:** Premium basket size ($\text{AOV} \ge 500\text{ PLN}$) and above-median return per user ($\text{ARPU} \ge \text{median}$).
- **Strong Conversion:** Resilient, high conversion baseline ($\text{CR} \ge 2.0\%$).
- **Low AOV:** Fast-moving catalog accessories requiring bundle optimization.
- **Needs Audit:** Campaigns with active spend but 0 attributed transactions.


<br>


## 4. Evaluation & Channel Performance Benchmark

Consolidated performance evaluation matrix across all audited traffic channels:

| Source / Campaign | Users | Trans. | Revenue (PLN) | ROAS | CPA (PLN) | CR % | Recommendation |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **comparison_engine / referral** | 3,831 | 87 | 105,711.99 | **12.31** | **98.72** | 2.27% | **Scale Budget (Top Performer)** |
| **PowerBrand – ElectroStore – Search Website** | 4,338 | 45 | 43,398.90 | **3.63** | **265.86** | 1.04% | **Maintain + On-Site** |
| **(direct)** | 1,234 | 39 | 38,064.50 | — | — | 3.16% | **Maintain (Loyal Core)** |
| **(organic)** | 2,630 | 26 | 23,214.10 | — | — | 0.99% | **Maintain (Paid Closer)** |
| **PowerBrand-Shopping** | 13,783 | 62 | 12,921.38 | **1.08** | **208.41** | 0.45% | **Cut Budget by 50%** |
| **PMax \| DiamondTools** | 470 | 14 | 5,152.00 | **3.65** | **100.51** | 2.98% | **Scale + Cross-Selling** |
| **Not set (not set)** | 135 | 11 | 9,845.20 | — | — | 8.15% | **UTM Tagging Audit** |
| **(ai-assistant)** | 37 | 2 | 2,031.80 | — | — | 5.41% | **Emerging Channel (Track)** |
| **Shopping Free Listings** | 22 | 2 | 484.00 | — | — | 8.89% | **Feed Optimization** |
| **(cross-network)** | 312 | 1 | 296.00 | **0.52** | **296.00** | 0.32% | **Pause / Restructure** |
| **Zero-conversion paid (3 campaigns)\*** | 20 | 0 | 0.00 | **0.00** | — | 0.00% | **Decommission Spend** |

*\*Includes: `adbox_comparison`, `DiamondTools discount`, `aku`.*


<br>


### Key Business Takeaways
1. **Comparison Engine is the Primary Profit Engine:** Generates 105.7k PLN (31.5% store share), the highest basket size (AOV 1,215 PLN), and an unmatched **ROAS of 12.31**. Comparison-shopper intent is immediate: 72.7% convert on Day 0, while the remaining 27.3% return within 7 days.
2. **Critical Ad Inefficiency in `PowerBrand-Shopping`:** Consumed over 50% of aggregate traffic (13.7k users) and the largest media budget (12.9k PLN), barely clearing break-even (**ROAS 1.08**). A CPA of 208 PLN against an AOV of 208 PLN produces net operating losses once COGS and fulfillment are accounted for.
3. **Synergy Between Paid Search & SEO:** `PowerBrand Search` introduces considerable new-prospect volume (generating 4.4k PLN more in First-Touch than Last-Touch). Conversely, Organic Search closes **4.5k PLN more in Last-Touch**, confirming that users initially acquired via paid ads later finalize orders via organic search at zero marginal cost.
4. **AI-Assistant Traffic Represents High Intent:** The `(ai-assistant)` referral vector recorded only 37 visits but yielded 2 large orders totaling 2,031 PLN (**CR = 5.41%**, **AOV > 1,000 PLN**), highlighting an emerging channel worth monitoring.


<br>


### Reallocation Simulation
- Slashing ad spend on `PowerBrand-Shopping` by 50% unlocks **~6,460 PLN**.
- Reallocating 70% toward Comparison Engine (raising CPC caps on top-margin inventory) and 30% to PMax DiamondTools boosts composite ad-spend **ROAS from 4.12 to over 6.50** without sacrificing sales volume.


<br>


## 5. Visual Analytics & BI Charts

### 1) Paid Media Efficiency: ROAS vs CPA
Bubble chart mapping Cost Per Acquisition against Return on Ad Spend. Bubble size represents attributed revenue.


<br>


<img width="1542" height="727" alt="image" src="https://github.com/user-attachments/assets/0bb39ad2-22eb-48e5-822c-86696cdb2425" />


- **Takeaway:** Top-left campaigns (Comparison Engine) deliver high returns at minimal acquisition costs. Bottom-right campaigns (`PowerBrand-Shopping`, `cross-network`) generate capital drag and require immediate budget caps.


### 2) Purchase Latency: Time-to-Conversion Cohort Decomposition
Horizontal stacked distribution tracking days elapsed from user acquisition to order placement.


<br>


<img width="1531" height="792" alt="image" src="https://github.com/user-attachments/assets/84d2b75f-4b39-425a-8246-35d977caf723" />


- **Takeaway:** **88.5% of store-wide transactions close on Day 0**. Users requiring consideration finalize checkout within a 1–7 day window (20–27% of volume in Comparison Engine and Search). Retargeting campaigns running past 7 days produce diminishing returns.


### 3) 5-Stage Purchase Funnel (Drop-off Diagnostics)
E-commerce conversion funnel with campaign-level dropdown filtering.


<br>


<img width="1540" height="745" alt="image" src="https://github.com/user-attachments/assets/6083bebf-1c5d-4f20-843a-42107be8b797" />


- **Core Conversion Bottleneck:** A steep drop-off occurs between `begin_checkout` and `purchase`: **76.5% of users abandon checkout** (only 23.5% complete payment). High intent is lost at the final step, indicating friction around payment gateways, forced account registration, or shipping clarity.


<br>


## 6. Tech Stack

- **Core Language & Processing:** Python 3.10+, Pandas, NumPy
- **Interactive Data Visualization:** Plotly Express, Plotly Graph Objects
- **Dashboard Reporting:** Autonomous HTML5 / CSS3 dark-mode template with responsive Flexbox/Grid and embedded Plotly.js—runs locally in any browser with zero web server dependencies.


<br>


## 7. Repository Structure

```text
ecommerce-analytics/
├── data/
│   ├── sales_performance.csv             # Last-Touch transaction logs
│   ├── first_touch_users.csv             # First-Touch acquisition sources
│   ├── traffic_and_revenue.csv           # Aggregate traffic & revenue metrics
│   ├── campaign_costs.csv                # Paid media advertising expenditures
│   ├── funnel_events.csv                 # E-commerce step event data
│   ├── cohort_analysis_campaigns.csv     # Daily cohort records by campaign
│   └── cohort_analysis_sources.csv       # Daily cohort records by source
├── 01_first_vs_last_touch.py             # Script 1: First vs Last Touch modeling
├── 02_user_performance.py                # Script 2: Efficiency matrix (CR / AOV / ARPU)
├── 03_traffic_vs_revenue_analysis.py     # Script 3: Leaky funnel & ROAS analytics
├── 04_cohort_analysis.py                 # Script 4: Time-to-conversion cohort analysis
├── 05_final_insights_and_recommendations.py # Script 5: Consolidated HTML dashboard generator
├── requirements.txt                      # Python dependencies
├── README.md
└── README.pl.md
```


<br>



## 8. Getting Started


<br>


1. Clone the repository
```bash
git clone [https://github.com/laura-szczerbowska/ecommerce-analytics.git](https://github.com/laura-szczerbowska/ecommerce-analytics.git)
cd ecommerce-analytics
```


<br>



2. Set up virtual environment & install dependencies
```bash
# Create virtual environment
python -m venv .venv
```


<br>


- Activate on Linux/macOS: source .venv/bin/activate
- Activate on Windows (PowerShell): .\.venv\Scripts\Activate.ps1

Install requirements: 
```bash
pip install -r requirements.txt
```

<br>


3. Generate the Executive Dashboard
```bash
python 05_executive_report.py
```

The script parses all CSV records, calculates attribution and cohort matrices, outputs executive_summary_report.html, and automatically launches it in your default web browser.


<br>


## 9. Future Roadmap
* **Algorithmic Multi-Touch Attribution**: Upgrade heuristic models to probabilistic Markov Chains or cooperative Shapley value attribution.
* **Direct Cloud Integration**: Automate data ingestion via Google BigQuery and the GA4 event stream, deprecating manual CSV exports.
* **Real-Time CPA Anomaly Alerts**: Implement automated Slack/email notifications triggered when channel acquisition costs spike by >30% week-over-week.


<br>


10. Summary & Executive Recommendations

    
Executing these data-driven initiatives delivers immediate cost containment and bottom-line impact:
* **Instant Cost Reduction**: Slashing spend on Milwaukee-Ogrod by 50% and freezing zero-conversion micro-campaigns (adbox_ceneo, aku, Distar rabat) preserves over 7,000 PLN in quarterly ad spend.
* **Maximize Ceneo Liquidity**: Ceneo operates as a 12x ROAS engine. Ensure zero budget downtime and lift CPC bids on top-margin catalog items.
* **Checkout Friction Removal Over Traffic Acquisition**: Pouring traffic into a funnel with 76.5% checkout abandonment is economically inefficient. Introducing express 1-click wallets (BLIK, Apple Pay, Google Pay) and guest checkout will lift revenue faster than scaling media spend.
* **Cap Retargeting Windows to 7 Days**: Restrict dynamic remarketing to a tight 7-day window—prospects not converting within a week exhibit near-zero conversion probability.
