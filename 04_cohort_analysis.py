import numpy as np
import pandas as pd
import plotly.express as px

# Set display options for wide table visualization in terminal
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

# Define unpaid/organic traffic sources for channel classification
free_sources = [
    '(direct)',
    '(organic)',
    '(referral)',
    'Shopping Free Listings',
    '(ai-assistant)',
    '(not set)',
    'Not set (not set)',
    'Brak nazwy (not set)'
]

def assign_time_bucket(day):
    """Categorize conversion latency into standardized consideration buckets."""
    if day == 0:
        return 'Day 0 (Immediate)'
    elif 1 <= day <= 3:
        return 'Days 1-3 (Short Consideration)'
    elif 4 <= day <= 7:
        return 'Days 4-7 (One Week)'
    else:
        return 'Over 7 Days'

def load_and_preprocess_cohort_data(file_path):
    """Load GA4 cohort export, clean reserved rows, and calculate incremental daily transactions."""
    df = pd.read_csv(file_path, encoding='utf-8-sig', comment='#', dtype=str, on_bad_lines='skip')
    df.columns = df.columns.str.strip()

    # Standardize column schema depending on whether Row_Type is present
    if df.shape[1] >= 7:
        df = df.iloc[:, :7]
        df.columns = [
            'Day_raw', 'Date', 'Source_Campaign', 'Row_Type',
            'Users', 'Transactions_raw', 'Rate'
        ]
        # Keep only the active date range rows and exclude aggregated totals
        df = df[df['Row_Type'].astype(str).str.strip() == 'date_range_0'].copy()
    else:
        df = df.iloc[:, :6]
        df.columns = [
            'Day_raw', 'Date', 'Source_Campaign',
            'Users', 'Transactions_raw', 'Rate'
        ]

    # Drop GA4 system-generated summary and reserved rows
    df = df[
        (~df['Source_Campaign'].astype(str).str.contains('RESERVED', case=False, na=False)) &
        (~df['Date'].astype(str).str.contains('RESERVED', case=False, na=False))
    ].copy()

    # Normalize missing source labels and cast data types
    df['Source_Campaign'] = df['Source_Campaign'].astype(str).str.strip().replace({
        '(not set)': 'Not set (not set)'
    })
    df['Day'] = pd.to_numeric(df['Day_raw'], errors='coerce').fillna(0).astype(int)
    df['Transactions'] = pd.to_numeric(df['Transactions_raw'], errors='coerce').fillna(0).astype(int)

    # Sort sequentially to calculate incremental new transactions per cohort day
    df = df.sort_values(by=['Source_Campaign', 'Date', 'Day']).reset_index(drop=True)
    df['New_Transactions'] = df.groupby(['Source_Campaign', 'Date'])['Transactions'].diff()
    df.loc[df['Day'] == 0, 'New_Transactions'] = df.loc[df['Day'] == 0, 'Transactions']
    df['New_Transactions'] = df['New_Transactions'].fillna(df['Transactions']).clip(lower=0)

    # Aggregate incremental transactions by source/campaign and latency day
    return df.groupby(['Source_Campaign', 'Day'], as_index=False)['New_Transactions'].sum()

# Load cleaned campaign cohort dataset
df_final = load_and_preprocess_cohort_data('data/cohort_analysis_campaigns.csv')

# Assign channel classifications and time-to-conversion buckets
df_final['Channel_Type'] = df_final['Source_Campaign'].apply(
    lambda x: 'organic / free' if x in free_sources else 'paid campaign'
)
df_final['Time_Bucket'] = df_final['Day'].apply(assign_time_bucket)

# Define column ordering for the pivot table
time_buckets_ordered = [
    'Day 0 (Immediate)',
    'Days 1-3 (Short Consideration)',
    'Days 4-7 (One Week)',
    'Over 7 Days'
]

# Pivot table: aggregate conversion volumes across latency intervals
campaign_table = pd.pivot_table(
    df_final,
    values='New_Transactions',
    index=['Source_Campaign', 'Channel_Type'],
    columns='Time_Bucket',
    aggfunc='sum',
    fill_value=0
).reindex(columns=time_buckets_ordered, fill_value=0)

# Compute total conversions and immediate purchase share
campaign_table['Total_Transactions'] = campaign_table.sum(axis=1)

campaign_table['% Purchases Day 0'] = np.where(
    campaign_table['Total_Transactions'] > 0,
    (campaign_table['Day 0 (Immediate)'] / campaign_table['Total_Transactions']) * 100,
    np.nan
).round(1)

# Sort campaigns by aggregate volume descending
campaign_table = campaign_table.sort_values(by='Total_Transactions', ascending=False)

# Calculate overall contribution share to store-wide sales
total_store_transactions = campaign_table['Total_Transactions'].sum()
campaign_table['Store_Sales_Share_%'] = np.where(
    total_store_transactions > 0,
    (campaign_table['Total_Transactions'] / total_store_transactions) * 100,
    0
).round(2)

print(campaign_table)



# VISUALIZATION (Plotly Stacked Horizontal Bar Chart)

# Filter active converting campaigns and sort ascending for horizontal bar display
df_plot = campaign_table[campaign_table['Total_Transactions'] > 0].reset_index()
df_plot = df_plot.sort_values(by='Total_Transactions', ascending=True)

# Generate Y-axis label displaying sample size N
df_plot['Source_N'] = (
    df_plot['Source_Campaign'] + ' (N=' + df_plot['Total_Transactions'].astype(int).astype(str) + ')'
)

# Reshape data into long format for Plotly Express
df_long = df_plot.melt(
    id_vars=['Source_N', 'Source_Campaign', 'Channel_Type', 'Total_Transactions'],
    value_vars=time_buckets_ordered,
    var_name='Time_Bucket',
    value_name='Transaction_Count'
)

# Calculate percentage share within each individual channel
df_long['Share_%'] = (df_long['Transaction_Count'] / df_long['Total_Transactions']) * 100

# Build horizontal stacked bar chart
fig = px.bar(
    df_long,
    x='Share_%',
    y='Source_N',
    color='Time_Bucket',
    orientation='h',
    title='<b>Time-to-Conversion Distribution per Source / Campaign</b>',
    labels={
        'Share_%': 'Share of Transactions (%)',
        'Source_N': 'Source / Campaign',
        'Time_Bucket': 'Time to Purchase'
    },
    color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'],
    custom_data=['Source_Campaign', 'Channel_Type', 'Transaction_Count', 'Total_Transactions']
)

# Configure custom hover tooltip
fig.update_traces(
    hovertemplate=(
        "<b>%{customdata[0]}</b> (%{customdata[1]})<br>" +
        "Interval: <b>%{fullData.name}</b><br>" +
        "Share: <b>%{x:.1f}%</b><br>" +
        "Transactions in bucket: <b>%{customdata[2]:.0f}</b> of %{customdata[3]:.0f}<extra></extra>"
    )
)

# Layout styling and legend positioning
fig.update_layout(
    barmode='stack',
    xaxis=dict(range=[0, 100], ticksuffix='%', showgrid=True, gridcolor='rgba(200,200,200,0.3)'),
    yaxis=dict(title=''),
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=-0.25,
        xanchor='center',
        x=0.5,
        title=''
    ),
    hoverlabel=dict(bgcolor="white", font_size=12),
    height=600,
    margin=dict(l=20, r=40, t=60, b=80),
    template='plotly_white'
)

fig.show()


# FINDINGS AND RECOMMENDATIONS

""" Key Observations and Strategic Recommendations:

1. Dominance of Same-Day Conversions (Day 0):

91.7% of active traffic sources (11 out of 12) secure at least 50% of their total conversions on Day 0.
Paid campaigns register at least 72.7% immediate purchases (averaging 75-80%).

This confirms an audience characterized by high intent and immediate purchase readiness.

General Recommendations:
- Remove all unnecessary friction in the purchase path: implement frictionless guest checkout, one-click digital wallets (BLIK, Apple Pay, Google Pay) to minimize time-to-order.

- Introduce urgency and shipping triggers (FOMO): display dynamic delivery countdowns and dispatch guarantees on product detail pages (e.g., 'Order within 1h 30m for same-day dispatch').

- Short-fuse cart promotions: test limited-time checkout discount codes (e.g., 60-minute countdown voucher) to incentivize immediate checkout completion.


2. Primary Revenue Drivers (Comparison Engine, PowerBrand – ElectroStore – Search Website, PowerBrand-Shopping):
comparison_engine / referral - primary sales engine: accounts for 31.54% of store-wide transactions, with 72.7% converting on Day 0. It also generates the largest nominal volume of deferred purchases (24 conversions after Day 0, including 9 taking over 7 days). It serves a dual function: driving rapid direct sales while simultaneously acting as a price-comparison benchmark for extended consideration journeys.

PowerBrand-Shopping: 21.51% store share, 80.0% closed on Day 0.
PowerBrand - Search: 17.56% store share, 73.5% closed on Day 0.

Together, these three channels generate over 70% of total transactions with strong baseline conversion efficiency.

Recommendations:
- Maintain full budget liquidity (zero Lost IS Budget) in Google Ads for PowerBrand - Search and sustain CPC account funding on Comparison Engine to prevent impression caps on top-performing inventory.

- Implement deferred conversion remarketing: deploy dynamic remarketing campaigns targeting visitors with a 1-7 day window to protect leads from shifting to competitors during price evaluation. Analysis confirms customer consideration rarely extends past 7 days.

- Cart abandonment automation: deploy automated email/push notifications within the first 24 hours following cart abandonment.


3. Niche Paid Channels ((cross-network), adbox_comparison):
These sources exhibit 100% Day 0 conversions, but contribute marginally to aggregate sales volume (3 total transactions, ~1% share). They demonstrate closing capability but remain limited by reach.

Recommendations:
- Gradually expand daily budgets or broaden catalog coverage for these campaigns, focusing on high-margin items and seasonal toolkits with distinct price advantages.


4. Organic and Free Traffic Sources:
Core unpaid channels convert immediately:
(direct): 84.6%, (organic): 76.9%, (not set): 81.8%.
This indicates strong brand loyalty and effective organic ranking on transactional queries.

Emerging sources (Shopping Free Listings and (ai-assistant)) reflect longer consideration paths (50% Day 0, 50% Days 1-3 across low sample sizes).
Standard (referral) recorded 0% on Day 0 (both transactions delayed, representing 0.72% store share).

Recommendations:
- Standardize technical product specification tables so prospective buyers have immediate access to complete product data.

- Integrate Schema.org structured data (e-commerce product rich snippets) to facilitate indexation by search engines and generative AI agents.

- For referral growth, verify listings on manufacturer 'Where to Buy' / 'Authorized Dealer' pages with active outbound links.


5. Zero-Conversion Campaigns ('DiamondTools discount', 'aku'):
Both campaigns produced 0 transactions over the tracked period.
Recommendation: Verify tracking links, pause non-performing ad groups, and reallocate budget toward proven channels.

6. Address '(not set)' Traffic (~4% of total sales):
Given that this segment converts at 81.8%, audit GA4 tracking tags and campaign URL parameters (UTMs) to eliminate tracking leakage and restore complete attribution.
"""