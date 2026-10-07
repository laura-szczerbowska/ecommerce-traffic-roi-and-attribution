import pandas as pd
import plotly.express as px

pd.set_option('display.max_columns', None)  # display all columns
pd.set_option('display.width', 1000)

free_sources = [
    '(direct)',
    '(organic)',
    '(referral)',
    'Shopping Free Listings',
    '(ai-assistant)',
    'Not set (not set)'
]


def assign_campaign_and_source(row, col_source, col_campaign):
    """
    Extracts comparison_engine as a separate row and excludes it from the main referral channel.
    It functions as a paid channel, whereas standard referral is unpaid, so this separation is critical.
    """
    source_medium = str(row.get(col_source, '')).strip().lower()
    campaign = str(row.get(col_campaign, '')).strip()

    if any(k in source_medium for k in ['comparison_engine', 'ceneo']) or any(k in campaign.lower() for k in ['comparison_engine', 'ceneo']):
        return 'comparison_engine / referral'

    elif campaign in ['(not set)', '', 'nan']:
        return 'Not set (not set)'

    return campaign


# Loading last-touch data file
df1 = pd.read_csv(
    'data/sales_performance.csv',
    encoding='utf-8-sig',
    on_bad_lines='skip',
    comment='#',
    sep=',',
)
df1.columns = df1.columns.str.strip()

# Date parsing
df1['Date'] = pd.to_datetime(
    df1['Date'].astype(str).str.replace(r'\.0$', '', regex=True),
    format='%Y%m%d',
    errors='coerce',
)

# Source mapping and channel classification
df1['Source_Campaign'] = df1.apply(
    lambda r: assign_campaign_and_source(r, 'Source_Medium', 'Campaign'),
    axis=1
)
df1['Channel_Type'] = df1['Source_Campaign'].apply(
    lambda x: 'organic / free' if x in free_sources else 'paid campaign'
)

# Last-Touch Aggregation
lt_df = (
    df1.groupby(['Channel_Type', 'Source_Campaign'], as_index=False)
    .agg(
        Revenue_Last_Touch=('Purchase_Revenue', 'sum'),
        Transactions_Last_Touch=('Transactions', 'sum'),
    )
)
lt_df['Revenue_Last_Touch'] = lt_df['Revenue_Last_Touch'].round(2)
lt_df = lt_df.sort_values(by='Revenue_Last_Touch', ascending=False).reset_index(drop=True)


# Loading first-touch data file
df2 = pd.read_csv(
    'data/first_touch_users.csv',
    encoding='utf-8-sig',
    on_bad_lines='skip',
    comment='#',
    sep=',',
)
df2.columns = df2.columns.str.strip()

# First visit date parsing
df2['First_Visit_Date'] = pd.to_datetime(
    df2['First_Visit_Date'].astype(str).str.replace(r'\.0$', '', regex=True),
    format='%Y%m%d',
    errors='coerce',
)

# Source mapping and channel classification
df2['Source_Campaign'] = df2.apply(
    lambda r: assign_campaign_and_source(r, 'Source_Medium', 'First_User_Campaign'),
    axis=1
)
df2['Channel_Type'] = df2['Source_Campaign'].apply(
    lambda x: 'organic / free' if x in free_sources else 'paid campaign'
)

# First-Touch Aggregation
ft_df = (
    df2.groupby(['Channel_Type', 'Source_Campaign'], as_index=False)
    .agg(
        Revenue_First_Touch=('Purchase_Revenue', 'sum'),
        Transactions_First_Touch=('Transactions', 'sum'),
    )
)
ft_df['Revenue_First_Touch'] = ft_df['Revenue_First_Touch'].round(2)
ft_df = ft_df.sort_values(by='Revenue_First_Touch', ascending=False).reset_index(drop=True)


# Merging datasets
comparison = pd.merge(
    ft_df,
    lt_df,
    on=['Channel_Type', 'Source_Campaign'],
    how='outer',
).fillna({
    'Revenue_First_Touch': 0.0,
    'Transactions_First_Touch': 0,
    'Revenue_Last_Touch': 0.0,
    'Transactions_Last_Touch': 0
})

comparison['Difference'] = (
    (comparison['Revenue_First_Touch'] - comparison['Revenue_Last_Touch']).round(2)
)

print("Comparison")
print(comparison.sort_values(by='Difference', ascending=False))


# VISUALIZATION

# Reshaping DataFrame for visualization
df_plot = comparison.melt(
    id_vars=['Source_Campaign'],
    value_vars=['Revenue_First_Touch', 'Revenue_Last_Touch'],
    var_name='Attribution_Model',
    value_name='Revenue',
)

df_plot['Attribution_Model'] = df_plot['Attribution_Model'].replace(
    {
        'Revenue_First_Touch': 'First-Touch',
        'Revenue_Last_Touch': 'Last-Touch',
    }
)

# Calculating model totals and percentage share for tooltips
model_totals = df_plot.groupby('Attribution_Model')['Revenue'].transform('sum')
df_plot['Share_%'] = (
    (df_plot['Revenue'] / model_totals) * 100
).fillna(0).round(2)

# Preparing space-separated currency values for tooltips (e.g. 105 711.99 PLN)
df_plot['Revenue_Formatted'] = df_plot['Revenue'].apply(
    lambda x: f"{x:,.2f}".replace(',', ' ') + " PLN"
)

# Building bar chart with percentage share passed to custom_data
fig = px.bar(
    df_plot,
    x='Attribution_Model',
    y='Revenue',
    color='Source_Campaign',
    custom_data=['Share_%', 'Revenue_Formatted'],
    title='Total Revenue Comparison per Attribution Model',
    labels={
        'Attribution_Model': '',
        'Revenue': 'Revenue (PLN)',
        'Source_Campaign': 'Source / Campaign',
    },
    template='plotly_dark',
    color_discrete_sequence=px.colors.qualitative.Alphabet,
)

# Formatting hover labels with space thousands separator
fig.update_traces(
    hovertemplate='<b>%{fullData.name}</b><br>'
    + 'Model: %{x}<br>'
    + 'Revenue: %{customdata[1]}<br>'
    + 'Share in model: <b>%{customdata[0]}%</b>'
    + '<extra></extra>'
)


y_max = int(df_plot.groupby('Attribution_Model')['Revenue'].sum().max() * 1.1)
y_ticks = list(range(0, y_max + 25000, 25000))
y_ticktext = [f"{val:,.0f}".replace(',', ' ') for val in y_ticks]

fig.update_layout(
    plot_bgcolor='#121212',
    paper_bgcolor='#121212',
    font=dict(
        family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
        color='#f1f5f9',
        size=12
    ),
    title=dict(
        text='<b>Total Revenue Comparison per Attribution Model</b>',
        font=dict(
            family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
            size=22,
            color='#ffffff'
        ),
        x=0.04,
        y=0.92,
        xanchor='left',
        yanchor='top'
    ),
    bargap=0.45,
    yaxis=dict(
        showgrid=True,
        gridcolor='rgba(255, 255, 255, 0.08)',
        tickmode='array',
        tickvals=y_ticks,
        ticktext=y_ticktext,
        title=dict(text='Revenue (PLN)', font=dict(size=13, color='#94a3b8'))
    ),
    xaxis=dict(
        tickfont=dict(size=13, color='#e2e8f0', weight=600)
    ),
    legend=dict(
        orientation='v',
        yanchor='top',
        y=0.92,
        xanchor='left',
        x=1.02,
        font=dict(size=11, color='#cbd5e1'),
        title=dict(text='Source / Campaign', font=dict(size=12, color='#94a3b8'))
    ),
    margin=dict(l=60, r=40, t=110, b=50),
)

fig.show()


# FINDINGS from attribution analysis (First-Touch vs Last-Touch)

""" Key Observations:

Cohort exploration (file 04_cohort_analysis) in GA4 indicates that approximately 88.5% of users complete a purchase immediately following First-Touch interaction. The observed transaction volumes fully corroborate this pattern.
Although total top-line revenue appeared identical in high-level explorations, detailed analysis uncovers granular discrepancies between 'Revenue_First_Touch' and 'Revenue_Last_Touch', as detailed in the summary table below.

The vast majority of campaigns and traffic sources (78%) convert on the user's initial visit. This validates strong touchpoint effectiveness and precise audience-product targeting.

1. High Efficiency of comparison_engine / referral: This source generates the highest aggregate revenue (105 711.99 PLN), showing 100% parity between First-Touch and Last-Touch models. Traffic from comparison shopping engines delivers instant conversions without requiring multi-stage lead nurturing.

2. Core Acquisition Driver - PowerBrand – ElectroStore – Search Website: This campaign ranks as the second-largest revenue driver, generating 4 470.93 PLN more in the First-Touch model compared to Last-Touch (49 vs 45 transactions). It serves a dual role: successfully driving new prospect acquisition while closing 91% of initiated purchases autonomously, with the residual volume assisting later touchpoints finalized via other channels (e.g., Organic Search).
3. Organic Search (organic) closes 4 505.83 PLN more revenue under Last-Touch (16 transactions) than First-Touch (11 transactions). This demonstrates its critical role in capturing and finalizing assisted conversions originated by upstream paid campaigns at zero marginal acquisition cost.

Recommendations:
1. Maintain or increase budget allocation for the PowerBrand Search campaign. Scaling back this spend will reduce top-of-funnel acquisition, directly suppressing downstream conversion volume across organic and direct channels.

2. Maximize clarity, visual appeal, and technical depth across product detail pages (comprehensive specifications, user guides, FAQ sections, and technical blog posts). Users acquired via upper-funnel reach campaigns must have all purchase hesitations resolved on-site to avoid off-platform research (which increases churn risk to competitors). The complete decision cycle must conclude on-domain.
3. Strengthen organic SEO positioning around high-intent branded keywords and specific product/category lines (e.g., PowerBrand tools, DiamondTools), alongside proactive re-engagement workflows (automated email recovery / abandoned cart funnels). Organic search captures 4 505.83 PLN more in closing value than it initiates, making organic optimization essential for converting paid-traffic prospects cost-effectively.
4. Audit zero-revenue campaigns across both attribution models (adbox_comparison, DiamondTools discount, aku). If these campaigns incur non-zero Cost Per Click (CPC) without yielding assisted or direct conversions, pause spend and reallocate capital toward proven top-converting channels."""