<div align="right">
  <strong>English</strong> | <a href="./README.pl.md">Polski</a>
</div>

# Multichannel Campaign Performance & Attribution Modeling in E-Commerce


An analytical module evaluating the performance of paid campaigns and organic traffic sources in an e-commerce store between **08.05 and 05.08.2026**. It addresses a critical business challenge: demonstrating how to allocate ad spend more effectively without relying solely on the Last-Touch model, while pinpointing exactly where users drop off along the purchase journey.

The project combines raw GA4 log preprocessing, profitability metrics calculation (ROAS, CPA, AOV), purchase latency cohort analysis, and a standalone script generating an interactive executive HTML dashboard. Dedicated scripts (01-04) execute focused analyses with bespoke visualisations and findings, which are subsequently consolidated in script 05 to deliver a cohesive executive summary report.

> **Data Notice:**  
> This analysis is grounded in real transaction records and behavioral logs extracted from an operational e-commerce store. All sensitive commercial metrics and monetary totals were anonymized and standardized (feature-scaled), fully preserving authentic behavioral patterns, conversion dynamics, and cross-channel relationships.



<br>


<br>



## Executive Dashboard Preview

A quick walkthrough of the interactive executive dashboard, covering filters, the conversion funnel, cohort analysis, and strategic business recommendations.



<br>









https://github.com/user-attachments/assets/0bba1208-afd2-4955-9d4d-816013570960

















<br>


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
Data Cleaning, Label Standardization & Comparison Engine Channel Isolation
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


### Analytical Modules & Script Scope

1. **First vs Last Touch Attribution (`01_first_vs_last_touch.py`):**
   * Demonstrates the assisting role of Paid Search campaigns (PowerBrand) and the closing role of organic SEO traffic (+4.5k PLN under the Last-Touch model).
2. **Traffic Quality Matrix (`02_user_performance.py`):**
   * Segments sources into 4 performance tiers based on CR (2.0%) and AOV (500 PLN) thresholds. Identifies AI Assistant traffic as the highest-converting channel (CR = 5.41%).
3. **Cost Efficiency & Funnel Diagnostics (`03_traffic_vs_revenue_analysis.py`):**
   * Computes unit economics: Cost Per Acquisition (CPA) and Return on Ad Spend (ROAS). Pinpoints the primary checkout bottleneck (a 76.5% drop-off between checkout initiation and purchase).
4. **Purchase Latency Cohort Analysis (`04_cohort_analysis.py`):**
   * Evaluates the time-to-conversion window - ~75–88% of purchases conclude on Day 0, with customer consideration fully closing within 7 days.
5. **Executive Dashboard (`05_final_insights_and_recommendations.py`):**
   * Consolidates all metrics into an interactive HTML dashboard featuring KPI summary cards, an actionable recommendation matrix, and cohesive Plotly visualizations.


<br>



## 3. Data & Dataset Preparation

The pipeline ingests and synchronizes 6 source datasets exported from GA4 and advertising platforms (Google Ads, Comparison Engine):
- `sales_performance.csv` – Transaction counts and revenue under the Last-Touch model.
- `first_touch_users.csv` – User acquisition touchpoints (First-User Campaign / Source-Medium).
- `traffic_and_revenue.csv` – Aggregated active users, transactions, and gross revenue per source.
- `campaign_costs.csv` – Direct media ad spend across paid campaigns.
- `funnel_events.csv` – Core e-commerce events: `session_start`, `view_item`, `add_to_cart`, `begin_checkout`, `purchase`.
- `cohort_analysis_campaigns.csv` & `cohort_analysis_sources.csv` – Daily cohort tracking matrices recording purchase intervals.


<br>


### 1) Data Preprocessing & Cleansing
- **Comparison Engine Isolation:** In standard GA4 setups, comparison shopping engine traffic from Comparison Engine defaults to generic `(referral)`. Because Comparison Engine operates as a paid Cost-Per-Click (CPC) channel, it was algorithmically separated into `comparison_engine / referral` to prevent distorting unpaid organic referral metrics.
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



$$
\text{Match Rate} = \frac{\min(\text{Revenue}_{\text{FT}}, \text{Revenue}_{\text{LT}})}{\max(\text{Revenue}_{\text{FT}}, \text{Revenue}_{\text{LT}})} \times 100\%
$$
  
  
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


<br>


<div style="overflow-x: auto; white-space: nowrap;">

| Source / Campaign | Users | Trans. | Revenue (PLN) | ROAS | CPA (PLN) | AOV (PLN) | CR % | % Immediate (D0) | First/Last Match | Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **comparison_engine / referral** | 3 841 | 87 | 105&nbsp;711.99 | 12.31 | 98.72 | 1&nbsp;215.08 | 2.27% | 72.7% | 100.0% | **Protect & Fund** |
| **PowerBrand – ElectroStore – Search Website** | 4 343 | 45 | 43&nbsp;398.90 | 3.63 | 265.86 | 964.42 | 1.04% | 73.5% | 90.7% | **Maintain & Optimize** |
| **(direct)** | 824 | 26 | 15&nbsp;644.72 | - | - | 601.72 | 3.16% | 84.6% | 98.1% | **Leverage & Retain** |
| **(organic)** | 1 619 | 16 | 13&nbsp;940.86 | - | - | 871.30 | 0.99% | 76.9% | 67.7% | **Leverage & Retain** |
| **PowerBrand-Shopping** | 13 783 | 62 | 13&nbsp;928.87 | 1.08 | 208.41 | 224.66 | 0.45% | 80.0% | 89.5% | **Audit & Restructure** |
| **PMax \| DiamondTools** | 638 | 19 | 6&nbsp;963.90 | 3.65 | 100.51 | 366.52 | 2.98% | 81.0% | 94.5% | **Maintain & Optimize** |
| **(referral)** | 510 | 5 | 4&nbsp;137.48 | - | - | 827.50 | 0.98% | 0.0% | 87.3% | **Leverage & Retain** |
| **(ai-assistant)** | 39 | 2 | 2&nbsp;031.56 | - | - | 1&nbsp;015.78 | 5.13% | 50.0% | 100.0% | **Leverage & Retain** |
| **Not set (not set)** | 123 | 6 | 1&nbsp;607.22 | - | - | 267.87 | 4.88% | 81.8% | 52.6% | **Leverage & Retain** |
| **Shopping Free Listings** | 59 | 2 | 767.13 | - | - | 383.56 | 3.39% | 50.0% | 79.0% | **Leverage & Retain** |
| **(cross-network)** | 204 | 2 | 671.80 | 1.13 | 296.25 | 335.90 | 0.98% | 100.0% | 47.5% | **Audit & Restructure** |
| **Zero-conversion paid (3 campaigns)\*** | 36 | 0 | 0.00 | 0.00 | - | 0.00 | 0.00% | 0.0% | 0.0% | **Pause / Cut Spend** |

*\*Includes: `adbox_comparison`, `DiamondTools discount`, `aku`.*

</div>




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


<img width="1512" height="712" alt="image" src="https://github.com/user-attachments/assets/60478b30-e445-490d-a9eb-1ad0ea03e178" />



<br>


<br>


- **Takeaway:** Top-left campaigns (Comparison Engine) deliver high returns at minimal acquisition costs. Bottom-right campaigns (`PowerBrand-Shopping`, `cross-network`) generate capital drag and require immediate budget caps.


<br>


<br>


### 2) Purchase Latency: Time-to-Conversion Cohort Decomposition
Horizontal stacked distribution tracking days elapsed from user acquisition to order placement.


<br>

<br>


<img width="1542" height="847" alt="image" src="https://github.com/user-attachments/assets/b582754e-e67c-4f81-974a-7508079a1db4" />



<br>


<br>

- **Takeaway:** **~75%** of store-wide transactions close on Day 0**. Users requiring consideration finalize checkout within a 1–7 day window (20–27% of volume in Comparison Engine and Search). Retargeting campaigns running past 7 days produce diminishing returns.


<br>


### 3) 5-Stage Purchase Funnel (Drop-off Diagnostics)
E-commerce conversion funnel with campaign-level dropdown filtering.


<br>


<img width="1521" height="717" alt="image" src="https://github.com/user-attachments/assets/8c548772-73df-45c7-88eb-13ca32ad735f" />



<br>


<br>


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
│   ├── sales_performance.csv              # Last-Touch transactions and revenue
│   ├── first_touch_users.csv              # First-Touch user acquisition sources
│   ├── traffic_and_revenue.csv            # Traffic and revenue per campaign
│   ├── campaign_costs.csv                 # Advertising spend for paid campaigns
│   ├── funnel_events.csv                  # Purchase journey events (funnel stages)
│   └── cohort_analysis_campaigns.csv      # GA4 cohort logs (retention & purchases over time)
├── 01_first_vs_last_touch.py              # Script 1: Attribution model comparison (First vs Last Touch)
├── 02_user_performance.py                 # Script 2: Source segmentation matrix (CR vs AOV vs ARPU)
├── 03_traffic_vs_revenue_analysis.py      # Script 3: Traffic scale, ROAS, CPA, and conversion funnel analysis
├── 04_cohort_analysis.py                  # Script 4: Purchase latency cohort analysis (time-to-conversion)
├── 05_final_insights_and_recommendations.py # Script 5: Metric consolidation & HTML executive dashboard generator
├── executive_summary_report.html          # Standalone, interactive executive dashboard
├── requirements.txt                       # Required Python dependencies
├── README.md                              # English documentation
└── README.pl.md                           # Polish documentation
```


<br>



## 8. Getting Started


<br>


1) Clone the repository
```bash
git clone [https://github.com/laura-szczerbowska/ecommerce-analytics.git]
cd ecommerce-analytics
```


<br>



2) Set up virtual environment & install dependencies
```bash
# Create virtual environment
python -m venv .venv
```


<br>

- Activate on Linux/macOS:
```bash
 source .venv/bin/activate
```

- Activate on Windows (PowerShell):
```bash
.\.venv\Scripts\Activate.ps1
```

Install requirements: 
```bash
pip install -r requirements.txt
```

<br>


3) Generate the Executive Dashboard

```bash
python 05_executive_report.py
```

The script parses all CSV records, calculates attribution and cohort matrices, outputs executive_summary_report.html, and automatically launches it in your default web browser.


<br>


## 9. Future Roadmap
- **Direct Cloud Integration**: Automate data ingestion via Google BigQuery and the GA4 event stream, deprecating manual CSV exports.
- **Real-Time CPA Anomaly Alerts**: Implement automated Slack/email notifications triggered when channel acquisition costs spike by >30% week-over-week.


<br>


## 10. Summary & Executive Recommendations

Executing these data-driven initiatives delivers immediate cost containment and bottom-line impact:
- **Instant Cost Reduction**: Slashing spend on PowerBrand-Shopping by 50% and freezing zero-conversion micro-campaigns (adbox_comparison, aku, DiamondTools discount) preserves over 7,000 PLN in quarterly ad spend.
- **Maximize Comparison Engine Liquidity**: Comparison Engine operates as a 12x ROAS engine. Ensure zero budget downtime and lift CPC bids on top-margin catalog items.
- **Checkout Friction Removal Over Traffic Acquisition**: Pouring traffic into a funnel with 76.5% checkout abandonment is economically inefficient. Introducing express 1-click wallets (BLIK, Apple Pay, Google Pay) and guest checkout will lift revenue faster than scaling media spend.
- **Cap Retargeting Windows to 7 Days**: Restrict dynamic remarketing to a tight 7-day window—prospects not converting within a week exhibit near-zero conversion probability.
