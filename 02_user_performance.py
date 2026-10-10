import pandas as pd
import plotly.express as px

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

free_sources = [
    '(direct)',
    '(organic)',
    '(referral)',
    'Shopping Free Listings',
    '(ai-assistant)',
    'Not set (not set)'
]

# Load data file
df = pd.read_csv(
    'data/first_touch_users.csv',
    encoding='utf-8-sig',
    on_bad_lines='skip',
    comment='#',
)
df.columns = df.columns.str.strip()


# Isolate comparison_engine traffic
# Extract 'comparison_engine / referral' as a standalone channel, then adjust generic referral values accordingly
def assign_campaign_and_source(row, col_source='Source_Medium', col_campaign='First_User_Campaign'):
    source_medium = str(row.get(col_source, '')).strip().lower()
    campaign = str(row.get(col_campaign, '')).strip()

    if any(k in source_medium for k in ['comparison_engine']) or any(k in campaign.lower() for k in ['comparison_engine']):
        return 'comparison_engine / referral'

    # Default fallbacks
    elif campaign in ['(not set)', '', 'nan']:
        return 'Not set (not set)'

    return campaign


df['Source_Campaign'] = df.apply(
    lambda r: assign_campaign_and_source(r, 'Source_Medium', 'First_User_Campaign'), axis=1
)

# Categorize into paid vs organic/free traffic
df['Channel_Type'] = df['Source_Campaign'].apply(
    lambda x: 'organic / free' if x in free_sources else 'paid campaign'
)

# Data cleaning and type casting
df['Transactions'] = (
    pd.to_numeric(df.get('Transactions', 0), errors='coerce').fillna(0).astype(int)
)
df['Revenue'] = (
    pd.to_numeric(df.get('Purchase_Revenue', 0.0), errors='coerce')
    .fillna(0.0)
    .round(2)
)
df['Total_Users'] = (
    pd.to_numeric(df.get('Total_Users', 0), errors='coerce')
    .fillna(0)
    .astype(int)
)

# Campaign-level aggregation
report = (
    df.groupby(['Channel_Type', 'Source_Campaign'], as_index=False)
    .agg(
        Users=('Total_Users', 'sum'),
        Transactions=('Transactions', 'sum'),
        Revenue=('Revenue', 'sum'),
    )
)

# Metric calculations
# Average Order Value (AOV)
report['AOV'] = (
    report['Revenue'] / report['Transactions']
).fillna(0).round(2)

# Conversion Rate (CR)
report['CR_%'] = (
    (report['Transactions'] / report['Users']) * 100
).fillna(0).round(2)

# Revenue per User (ARPU)
report['Revenue_per_User'] = (
    report['Revenue'] / report['Users']
).fillna(0).round(2)

# Performance-based campaign segmentation
median_arpu = (
    report[report['Revenue'] > 0]['Revenue_per_User'].median() or 5.0
)


def categorize_campaign(row):
    if row['Transactions'] == 0:
        return 'Needs Audit'
    elif row['Revenue_per_User'] >= median_arpu and row['AOV'] >= 500:
        return 'Core / High-Value'
    elif row['CR_%'] >= 2.0:
        return 'Strong Conversion (Stable)'
    else:
        return 'Low AOV'


report['Performance_Segment'] = report.apply(categorize_campaign, axis=1)

# Sort results
report = report.sort_values(by=['Revenue', 'Users'], ascending=[False, False]).reset_index(drop=True)

print(report)

# Scatter plot visualization
fig_scatter = px.scatter(
    report,
    x='CR_%',
    y='AOV',
    size='Revenue_per_User',
    color='Performance_Segment',
    hover_name='Source_Campaign',
    text='Source_Campaign',
    size_max=40,
    template='plotly_dark',
    title='<b>Campaign Performance Matrix: Conversion vs AOV vs Revenue/User</b>',
    labels={
        'CR_%': 'Conversion Rate (%)',
        'AOV': 'Average Order Value (AOV in PLN)',
        'Revenue_per_User': 'Revenue per User (PLN)',
        'Performance_Segment': 'Segment',
    },
    color_discrete_map={
        'Core / High-Value': '#00CC96',
        'Strong Conversion (Stable)': '#636EFA',
        'Low AOV': '#FFA15A',
        'Needs Audit': '#EF553B',
    },
)

# Label positioning above markers
fig_scatter.update_traces(
    textposition='top center',
    textfont=dict(size=10),
    cliponaxis=False,  # Prevents text clipping at axis boundaries
    hovertemplate='<b>%{hovertext}</b><br>'
    + 'Conversion Rate: <b>%{x:.2f}%</b><br>'
    + 'Average Order Value (AOV): <b>%{y:,.2f} PLN</b><br>'
    + 'Revenue per User: <b>%{marker.size:,.2f} PLN</b><extra></extra>',
)

# Horizontal AOV benchmark line with right-aligned annotation
fig_scatter.add_hline(
    y=500,
    line_dash='dot',
    line_color='rgba(255, 255, 255, 0.35)',
    annotation_text='AOV Threshold (500 PLN)',
    annotation_position='top right',
)

# Vertical CR benchmark line with top-left annotation (avoids overlap)
fig_scatter.add_vline(
    x=2.0,
    line_dash='dot',
    line_color='rgba(255, 255, 255, 0.35)',
    annotation_text='CR Threshold (2.0%)',
    annotation_position='top left',
)

# Axis padding and margins
fig_scatter.update_layout(
    plot_bgcolor='#121212',
    paper_bgcolor='#121212',
    font_color='white',
    height=650,
    margin=dict(t=90, l=60, r=90, b=60),
    xaxis=dict(
        range=[-0.5, 9],  # Allocates space for Shopping Free Listings
        showgrid=True,
        gridcolor='rgba(255, 255, 255, 0.1)',
        zeroline=False,
    ),
    yaxis=dict(
        range=[-80, 1350],  # Padding top and bottom for zero-value bubbles
        showgrid=True,
        gridcolor='rgba(255, 255, 255, 0.1)',
        zeroline=False,
    ),
)

fig_scatter.show()

# RECOMMENDATIONS

""" Key Observations:

1. comparison_engine / referral - Undisputed Leader: 105.7k PLN in revenue, highest Average Order Value (AOV) of 1,215.08 PLN, and unit return of 33.10 PLN/user across 87 transactions.

Takeaway: Maintain full product feed integration and preserve price competitiveness. This channel consistently attracts high-intent buyers seeking premium inventory; maximizing budget and resource allocation here is strongly recommended.

2. PowerBrand – ElectroStore – Search Website Campaign and Direct Traffic: Both represent primary profit drivers with above-median basket values (AOV 590-976 PLN) and revenue per user >12 PLN, establishing a reliable base of high-value and returning customers.
Recommendations: Sustain and gradually scale paid spend for PowerBrand – ElectroStore – Search Website (it systematically acquires buyers for higher-margin inventory). Concurrently, roll out targeted retention initiatives for Direct traffic (dedicated B2B volume pricing, tiered loyalty discounts, automated reordering triggers) to maximize customer lifetime value (LTV).

The (ai-assistant) source recorded the second-highest conversion rate (5.41%) and an exceptional unit revenue of 54.91 PLN/user. While aggregate volume remains low (37 users), this represents an emerging, high-intent touchpoint that warrants ongoing tracking.

3. Shopping Free Listings (Highest Conversion Rate = 8.89%) and PMax | DiamondTools (CR = 3.57%): Both channels exhibit lower average order values (242-368 PLN). They effectively capture purchase-ready shoppers focused on budget-friendly items and accessories.
PMax | DiamondTools Recommendation: Implement product bundling and cross-selling widgets on lower-priced product detail pages to lift AOV. Strong conversion stability (3.57%) justifies controlled budget scaling.
Shopping Free Listings Recommendation: Capitalize on the leading conversion rate (8.89%) through merchant feed optimization. Enhance product titles and metadata with technical, high-intent keywords, and selectively prioritize top-selling, high-margin, or seasonal products to drive basket value.

4. PowerBrand-Shopping (Budget Allocation Anomaly): This campaign absorbed over 50% of aggregate store traffic (13,099 users) while yielding only 12.47k PLN in revenue. This inefficiency is reflected in a sub-optimal conversion rate (CR = 0.44%) and negligible return per user (0.95 PLN).
Takeaway: The campaign requires an immediate operational audit - including negative keyword scrubbing, search query cleanup, and validation of product-listing relevance.

5. aku, DiamondTools discount, and adbox_comparison (Immediate Audit Required): These campaigns totaled 20 users with 0 PLN in attributed revenue.
Recommended Action: Pause or fully restructure these campaigns, reallocating unspent capital toward established high-converting acquisition channels.
"""
