import os
import webbrowser
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

free_sources = [
    '(direct)',
    '(organic)',
    '(referral)',
    'Shopping Free Listings',
    '(ai-assistant)',
    '(not set)',
    'Not set (not set)'
]


def assign_campaign_and_source(row, col_source, col_campaign):
    """Isolates Comparison Engine from referral traffic and standardizes missing labels."""
    source_medium = str(row.get(col_source, '')).strip().lower()
    campaign = str(row.get(col_campaign, '')).strip()

    if any(k in source_medium for k in ['comparison_engine', 'ceneo']) or any(k in campaign.lower() for k in ['comparison_engine', 'ceneo']):
        return 'comparison_engine / referral'
    elif campaign in ['(not set)', '', 'nan']:
        return 'Not set (not set)'
    return campaign


# Time latency bucket assignment
def assign_time_bucket(day):
    if day == 0:
        return 'Day 0 (Immediate)'
    elif 1 <= day <= 3:
        return 'Days 1-3 (Short Consideration)'
    elif 4 <= day <= 7:
        return 'Days 4-7 (One Week)'
    else:
        return 'Over 7 Days'


# Files
last_touch = 'sales_performance.csv'
first_touch = 'first_touch_users.csv'
data = 'traffic_and_revenue.csv'
costs = 'campaign_costs.csv'
cohort_camp = 'cohort_analysis_campaigns.csv'
cohort_sour = 'cohort_analysis_sources.csv'

# Input datasets
df_lt = pd.read_csv(last_touch, encoding='utf-8-sig', on_bad_lines='skip', comment='#')
df_lt.columns = df_lt.columns.str.strip()
df_lt['Source_Campaign'] = df_lt.apply(
    lambda r: assign_campaign_and_source(r, 'Source_Medium', 'Campaign'), axis=1
)
lt_agg = df_lt.groupby('Source_Campaign', as_index=False).agg(Revenue_lt=('Purchase_Revenue', 'sum'))

df_ft = pd.read_csv(first_touch, encoding='utf-8-sig', on_bad_lines='skip', comment='#')
df_ft.columns = df_ft.columns.str.strip()
df_ft['Source_Campaign'] = df_ft.apply(
    lambda r: assign_campaign_and_source(r, 'Source_Medium', 'First_User_Campaign'), axis=1
)
ft_agg = df_ft.groupby('Source_Campaign', as_index=False).agg(Revenue_ft=('Purchase_Revenue', 'sum'))

df_attribution = pd.merge(ft_agg, lt_agg, on='Source_Campaign', how='outer').fillna(0.0)
df_attribution['ft_lt_%'] = np.where(
    df_attribution['Revenue_lt'] > 0,
    (np.minimum(df_attribution['Revenue_ft'], df_attribution['Revenue_lt']) /
     np.maximum(df_attribution['Revenue_ft'], df_attribution['Revenue_lt']) * 100).round(1),
    0.0
)

# Core metric calculations: Revenue, AOV, ROAS, CPA

df_traffic = pd.read_csv(data, encoding='utf-8-sig', on_bad_lines='skip', comment='#')
df_traffic.columns = df_traffic.columns.str.strip()

df_traffic['Source_Campaign'] = df_traffic.apply(
    lambda r: assign_campaign_and_source(r, 'Source_Medium', 'Campaign'), axis=1
)
df_traffic['Channel_Type'] = df_traffic['Source_Campaign'].apply(
    lambda x: 'organic / free' if x in free_sources else 'paid campaign'
)

# Type casting and data hygiene
df_traffic['Transactions'] = pd.to_numeric(df_traffic.get('Transactions', 0), errors='coerce').fillna(0).astype(int)
df_traffic['Revenue'] = pd.to_numeric(df_traffic.get('Purchase_Revenue', 0.0), errors='coerce').fillna(0.0).round(2)
df_traffic['Active_Users'] = pd.to_numeric(df_traffic.get('Active_Users', 0), errors='coerce').fillna(0).astype(int)

summary = (
    df_traffic.groupby(['Channel_Type', 'Source_Campaign'], as_index=False)
    .agg(
        Users=('Active_Users', 'sum'),
        Transactions=('Transactions', 'sum'),
        Revenue=('Revenue', 'sum'),
    )
)

df_k = pd.read_csv(costs, encoding='utf-8-sig', on_bad_lines='skip', comment='#')
df_k.columns = df_k.columns.str.strip()
df_k.rename(columns={'Campaign': 'Source_Campaign'}, inplace=True)
df_k['Cost'] = pd.to_numeric(df_k['Cost'], errors='coerce').fillna(0.0).round(2)
costs_table = df_k.groupby('Source_Campaign', as_index=False).agg(Cost=('Cost', 'sum'))

summary = pd.merge(summary, costs_table, on='Source_Campaign', how='left').fillna({'Cost': 0.0})

summary['ROAS'] = np.where(summary['Cost'] > 0, (summary['Revenue'] / summary['Cost']).round(2), 0.0)
summary['CPA'] = np.where(summary['Transactions'] > 0, (summary['Cost'] / summary['Transactions']).round(2), 0.0)
summary['AOV'] = np.where(summary['Transactions'] > 0, (summary['Revenue'] / summary['Transactions']).round(2), 0.0)
summary['CR_%'] = np.where(summary['Users'] > 0, ((summary['Transactions'] / summary['Users']) * 100).round(2), 0.0)


# Cohort processing
def load_cohorts(file_path):
    df = pd.read_csv(file_path, encoding='utf-8-sig', comment='#', dtype=str, on_bad_lines='skip')
    df.columns = df.columns.str.strip()
    if df.shape[1] >= 7:
        df = df.iloc[:, :7].copy()
        df.columns = ['Day_raw', 'Date', 'Source_Campaign', 'Row_Type', 'Users', 'Transactions_raw', 'Rate']
        df = df[df['Row_Type'].astype(str).str.strip() == 'date_range_0'].copy()
    else:
        df = df.iloc[:, :6].copy()
        df.columns = ['Day_raw', 'Date', 'Source_Campaign', 'Users', 'Transactions_raw', 'Rate']

    df = df[(~df['Source_Campaign'].astype(str).str.contains('RESERVED', case=False, na=False)) &
            (~df['Date'].astype(str).str.contains('RESERVED', case=False, na=False))].copy()

    df['Source_Campaign'] = df['Source_Campaign'].astype(str).str.strip().replace({'(not set)': 'Not set (not set)'})
    df['Day'] = pd.to_numeric(df['Day_raw'], errors='coerce').fillna(0).astype(int)
    df['Transactions'] = pd.to_numeric(df['Transactions_raw'], errors='coerce').fillna(0).astype(int)

    df = df.sort_values(by=['Source_Campaign', 'Date', 'Day']).reset_index(drop=True)
    df['New_Transactions'] = df.groupby(['Source_Campaign', 'Date'])['Transactions'].diff()
    df.loc[df['Day'] == 0, 'New_Transactions'] = df.loc[df['Day'] == 0, 'Transactions']
    df['New_Transactions'] = df['New_Transactions'].fillna(df['Transactions']).clip(lower=0)
    return df.groupby(['Source_Campaign', 'Day'], as_index=False)['New_Transactions'].sum()


k_campaigns = load_cohorts(cohort_camp)
k_sources = load_cohorts(cohort_sour)

mask_c = k_sources['Source_Campaign'].str.lower().isin(['comparison_engine', 'comparison_engine / referral', 'ceneo', 'ceneo.pl'])
k_ceneo = k_sources[mask_c].groupby('Day', as_index=False)['New_Transactions'].sum()
k_ceneo['Source_Campaign'] = 'comparison_engine / referral'

k_ref = k_campaigns[k_campaigns['Source_Campaign'] == '(referral)'].copy()
k_non_ref = k_campaigns[k_campaigns['Source_Campaign'] != '(referral)'].copy()

# Pre-aggregation before merge to prevent duplicate records
k_ref_agg = k_ref.groupby(['Source_Campaign', 'Day'], as_index=False)['New_Transactions'].sum()
k_ceneo_agg = k_ceneo.groupby('Day', as_index=False)['New_Transactions'].sum()

k_merged = pd.merge(k_ref_agg, k_ceneo_agg[['Day', 'New_Transactions']], on='Day', how='left', suffixes=('', '_c'))
k_merged['New_Transactions_c'] = k_merged['New_Transactions_c'].fillna(0)
k_merged['New_Transactions'] = (k_merged['New_Transactions'] - k_merged['New_Transactions_c']).clip(lower=0)
k_ref_clean = k_merged[['Source_Campaign', 'Day', 'New_Transactions']].copy()

k_final = pd.concat([
    k_non_ref[['Source_Campaign', 'Day', 'New_Transactions']],
    k_ref_clean,
    k_ceneo[['Source_Campaign', 'Day', 'New_Transactions']]
], ignore_index=True)

k_final['Channel_Type'] = k_final['Source_Campaign'].apply(
    lambda x: 'organic / free' if x in free_sources else 'paid campaign'
)
k_final['Time_Bucket'] = k_final['Day'].apply(assign_time_bucket)

time_buckets = [
    'Day 0 (Immediate)',
    'Days 1-3 (Short Consideration)',
    'Days 4-7 (One Week)',
    'Over 7 Days'
]

campaign_table = pd.pivot_table(
    k_final,
    values='New_Transactions',
    index=['Source_Campaign', 'Channel_Type'],
    columns='Time_Bucket',
    aggfunc='sum',
    fill_value=0
).reindex(columns=time_buckets, fill_value=0)

campaign_table['Total_Transactions'] = campaign_table.sum(axis=1)
campaign_table['% Purchases Day 0'] = np.where(
    campaign_table['Total_Transactions'] > 0,
    (campaign_table['Day 0 (Immediate)'] / campaign_table['Total_Transactions']) * 100,
    0.0
).round(1)

df_cohort_summary = campaign_table.reset_index()[['Source_Campaign', '% Purchases Day 0']].copy()
df_cohort_summary.rename(columns={'% Purchases Day 0': '% Transactions Day 0'}, inplace=True)
df_cohort_summary['% Deferred'] = (100.0 - df_cohort_summary['% Transactions Day 0']).round(1)

attribution_summary = summary.merge(df_attribution[['Source_Campaign', 'ft_lt_%']], on='Source_Campaign', how='left')
attribution_summary = attribution_summary.merge(df_cohort_summary, on='Source_Campaign', how='left')
attribution_summary = attribution_summary.fillna({'ft_lt_%': 0.0, '% Transactions Day 0': 0.0, '% Deferred': 0.0})


def assign_recommendation(row):
    if 'comparison_engine / referral' in str(row['Source_Campaign']).lower() or 'ceneo / referral' in str(row['Source_Campaign']).lower():
        return 'Top Performer'
    if row['Channel_Type'] == 'organic / free':
        return 'Maintain'
    if row['ROAS'] >= 5.0:
        return 'Scale'
    elif row['ROAS'] >= 2.0:
        return 'Maintain'
    else:
        return 'Audit / Optimize'


attribution_summary['Recommendation'] = attribution_summary.apply(assign_recommendation, axis=1)

# Sort prior to string formatting to maintain index integrity
attribution_summary = attribution_summary.sort_values(
    by=['Revenue', 'Transactions'], ascending=[False, False]
).reset_index(drop=True)

attribution_summary['Revenue_str'] = attribution_summary['Revenue'].apply(lambda x: f"{x:,.2f} PLN".replace(',', ' '))
attribution_summary['ROAS_str'] = np.where(
    attribution_summary['Channel_Type'] == 'organic / free',
    '-',
    attribution_summary['ROAS'].apply(lambda x: f"{x:.2f}")
)
attribution_summary['CPA_str'] = np.where(
    attribution_summary['Channel_Type'] == 'organic / free',
    '-',
    attribution_summary['CPA'].apply(lambda x: f"{x:,.2f} PLN".replace(',', ' ') if x > 0 else '-')
)
attribution_summary['AOV_str'] = attribution_summary['AOV'].apply(lambda x: f"{x:,.2f} PLN".replace(',', ' '))
attribution_summary['Users_str'] = attribution_summary['Users'].apply(lambda x: f"{x:,.0f}".replace(',', ' '))
attribution_summary['Transactions_str'] = attribution_summary['Transactions'].apply(
    lambda x: f"{x:,.0f}".replace(',', ' '))
attribution_summary['D0_str'] = attribution_summary['% Transactions Day 0'].apply(lambda x: f"{x:.1f}%")
attribution_summary['CR_str'] = attribution_summary['CR_%'].apply(lambda x: f"{x:.2f}%")
attribution_summary['Match_str'] = attribution_summary['ft_lt_%'].apply(lambda x: f"{x:.1f}%")

display_table = attribution_summary[[
    'Source_Campaign',
    'Users_str',
    'Transactions_str',
    'Revenue_str',
    'ROAS_str',
    'CPA_str',
    'AOV_str',
    'CR_str',
    'D0_str',
    'Match_str',
    'Recommendation'
]].copy()

# Final standardized column headers
display_table.columns = [
    'Source / Campaign',
    'Users',
    'Transactions',
    'Revenue',
    'ROAS',
    'CPA',
    'AOV',
    'CR%',
    '% Immediate Transactions',
    'First/Last Match',
    'Recommendation'
]

# Visualizations

# 1. ROAS vs CPA (Bubble Chart)
df_paid = summary[summary['Cost'] > 0].copy()


def get_label_position(row):
    if row['ROAS'] > 5:
        return 'bottom center'
    if row['CPA'] > 200:
        return 'top right'
    return 'top left'


df_paid['Text_Position'] = df_paid.apply(get_label_position, axis=1)
df_paid['Label'] = df_paid['Source_Campaign']
df_paid['Revenue_Formatted'] = df_paid['Revenue'].apply(lambda x: f"{x:,.2f}".replace(',', ' ') + " PLN")
df_paid['CPA_Formatted'] = df_paid['CPA'].apply(lambda x: f"{x:,.2f}".replace(',', ' ') + " PLN")

fig_bubble = px.scatter(
    df_paid,
    x='CPA',
    y='ROAS',
    size='Revenue',
    color='Source_Campaign',
    text='Label',
    size_max=45,
    title='<b>Paid Campaign Performance: ROAS vs CPA</b>',
    labels={
        'CPA': 'CPA - Cost per Acquisition (PLN)',
        'ROAS': 'ROAS - Return on Ad Spend',
        'Source_Campaign': 'Campaign',
    },
    template='plotly_dark',
)

fig_bubble.update_traces(
    mode='markers+text',
    textposition=df_paid['Text_Position'],
    textfont=dict(size=11, color='#CCCCCC', family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"),
    hoverlabel=dict(bgcolor='#222222', bordercolor='#444444', font=dict(color='white')),
    hovertemplate=(
        "<b>%{customdata[0]}</b><br>"
        "CPA: %{customdata[1]}<br>"
        "ROAS: %{y:.2f}<br>"
        "Revenue: %{customdata[2]}<extra></extra>"
    ),
    customdata=df_paid[['Source_Campaign', 'CPA_Formatted', 'Revenue_Formatted']].values
)

fig_bubble.update_layout(
    height=550,
    plot_bgcolor='#1e293b',
    paper_bgcolor='#1e293b',
    font=dict(
        family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        color='#f8fafc'
    ),
    xaxis=dict(showgrid=True, gridcolor='#334155', zeroline=False, tickformat='d'),
    yaxis=dict(showgrid=True, gridcolor='#334155', zeroline=False),
    margin=dict(l=50, r=80, t=60, b=50),
    showlegend=False,
)

# 2. Time-to-Conversion Distribution (Stacked Horizontal Bar Chart)
df_plot = campaign_table[campaign_table['Total_Transactions'] > 0].reset_index()
df_plot = df_plot.sort_values(by='Total_Transactions', ascending=True)

df_plot['Total_Transactions_Str'] = df_plot['Total_Transactions'].apply(lambda x: f"{x:,.0f}".replace(',', ' '))
df_plot['Source_N'] = (
        df_plot['Source_Campaign'] + ' (N=' + df_plot['Total_Transactions_Str'] + ')          '
)

df_plot = df_plot.melt(
    id_vars=['Source_N', 'Source_Campaign', 'Channel_Type', 'Total_Transactions', 'Total_Transactions_Str'],
    value_vars=time_buckets,
    var_name='Time_Bucket',
    value_name='Transaction_Count'
)
df_plot['Share_%'] = (df_plot['Transaction_Count'] / df_plot['Total_Transactions']) * 100
df_plot['Transaction_Count_Str'] = df_plot['Transaction_Count'].apply(lambda x: f"{x:,.0f}".replace(',', ' '))

fig_bar_cohort = px.bar(
    df_plot,
    x='Share_%',
    y='Source_N',
    color='Time_Bucket',
    orientation='h',
    title='<b>Time-to-Conversion Distribution per Source / Campaign</b>',
    labels={
        'Share_%': 'Share of Transactions (%)',
        'Source_N': 'Source / Campaign (Sample N)',
        'Time_Bucket': 'Time to Purchase'
    },
    color_discrete_sequence=['#38bdf8', '#fbbf24', '#34d399', '#f87171'],
    custom_data=['Source_Campaign', 'Channel_Type', 'Transaction_Count_Str', 'Total_Transactions_Str'],
    template='plotly_dark'
)

fig_bar_cohort.update_traces(
    hoverlabel=dict(
        bgcolor='#1e293b',
        bordercolor='#475569',
        font=dict(color='#ffffff')
    ),
    hovertemplate=(
            "<b>%{customdata[0]}</b> (%{customdata[1]})<br>" +
            "Interval: <b>%{fullData.name}</b><br>" +
            "Share: <b>%{x:.1f}%</b><br>" +
            "Transactions in interval: <b>%{customdata[2]}</b> of %{customdata[3]}<extra></extra>"
    )
)

fig_bar_cohort.update_layout(
    barmode='stack',
    plot_bgcolor='#1e293b',
    paper_bgcolor='#1e293b',
    font=dict(
        family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        color='#f8fafc'
    ),
    xaxis=dict(range=[0, 100], ticksuffix='%', showgrid=True, gridcolor='#334155'),
    yaxis=dict(title=''),
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=-0.22,
        xanchor='center',
        x=0.5,
        title=''
    ),
    hoverlabel=dict(bgcolor='#222222', bordercolor='#444444', font_size=12),
    height=600,
    margin=dict(l=20, r=40, t=60, b=80),
)

# 3. Funnel Events Data
df_events = pd.read_csv(
    'data/funnel_events.csv',
    encoding='utf-8-sig',
    on_bad_lines='skip',
    comment='#',
    sep=',',
)
df_events.columns = df_events.columns.str.strip()

df_events['Source_Campaign'] = df_events.apply(
    lambda r: assign_campaign_and_source(r, 'Source_Medium', 'Campaign'), axis=1
)
df_events['Event_Count'] = pd.to_numeric(df_events.get('Event_Count', 0), errors='coerce').fillna(0).astype(int)

event_mapping = {
    'session_start': '1. Session Start (Home/Landing)',
    'view_item': '2. Product View',
    'add_to_cart': '3. Add to Cart',
    'begin_checkout': '4. Begin Checkout',
    'purchase': '5. Purchase Completed'
}

selected_campaigns = [
    'PowerBrand – ElectroStore – Search Website',
    'comparison_engine / referral',
    'PowerBrand-Shopping',
    'PMax | DiamondTools'
]

df_filtered = df_events[
    (df_events['Source_Campaign'].isin(selected_campaigns)) &
    (df_events['Event_Name'].isin(event_mapping.keys()))
].copy()

df_filtered['Funnel_Step'] = df_filtered['Event_Name'].map(event_mapping)

df_agg = (
    df_filtered.groupby(['Source_Campaign', 'Funnel_Step'])
    .agg(Count=('Event_Count', 'sum'))
    .reset_index()
)

stage_order = list(event_mapping.values())
palette = ['#38bdf8', '#818cf8', '#fbbf24', '#f87171', '#34d399']

fig_funnel = go.Figure()

for i, campaign in enumerate(selected_campaigns):
    data_k = df_agg[df_agg['Source_Campaign'] == campaign].set_index('Funnel_Step')
    values = [int(data_k.loc[step, 'Count']) if step in data_k.index else 0 for step in stage_order]
    text_labels = [f"{v:,.0f}".replace(',', ' ') for v in values]

    fig_funnel.add_trace(
        go.Funnel(
            name=campaign,
            y=stage_order,
            x=values,
            text=text_labels,
            textinfo="text",
            textposition="auto",
            insidetextfont=dict(size=13, color="white", family="Arial Black"),
            outsidetextfont=dict(size=13, color="white", family="Arial Black"),
            hoverlabel=dict(bgcolor='#1e293b', bordercolor='#475569', font=dict(color='white', family="Arial")),
            customdata=text_labels,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Event Count: %{customdata}<br>"
                "Conversion from Initial: %{percentInitial:.1%}<br>"
                "Step-to-Step Conversion: %{percentPrevious:.1%}"
                "<extra></extra>"
            ),
            marker=dict(color=palette, line=dict(width=0)),
            connector=dict(visible=False),
            visible=(i == 0)
        )
    )

# Dropdown menu to switch funnel views
buttons = []
for i, campaign in enumerate(selected_campaigns):
    visibility = [False] * len(selected_campaigns)
    visibility[i] = True
    buttons.append(dict(
        label=campaign[:28] + '...' if len(campaign) > 28 else campaign,
        method="update",
        args=[
            {"visible": visibility},
            {"title.text": f"<b>Purchase Funnel:</b> {campaign}"}
        ]
    ))

fig_funnel.update_layout(
    updatemenus=[dict(
        type="dropdown",
        direction="down",
        active=0,
        buttons=buttons,
        x=1,
        y=1.12,
        xanchor='center',
        yanchor='top',
        bgcolor='#0f172a',
        bordercolor='#334155',
        font=dict(color='white', size=11)
    )],
    title=dict(
        text=f"<b>Purchase Funnel:</b> {selected_campaigns[0]}",
        font=dict(color="white", size=16),
        x=0.03,
        xanchor='left'
    ),
    yaxis=dict(
        visible=True,
        showline=False,
        showgrid=False,
        ticks="",
        tickfont=dict(size=13, color="white", family="Arial")
    ),
    plot_bgcolor='#1e293b',
    paper_bgcolor='#1e293b',
    font=dict(color="#f8fafc", size=12),
    height=560,
    margin=dict(l=220, r=80, t=90, b=40)
)

bubble_chart_html = fig_bubble.to_html(full_html=False, include_plotlyjs=False)
cohort_chart_html = fig_bar_cohort.to_html(full_html=False, include_plotlyjs=False)
funnel_chart_html = fig_funnel.to_html(full_html=False, include_plotlyjs=False)

# HTML Insights Section (czcionki zmniejszone o 2px w ramkach)
insights_section = """
    <!-- CARD 1: ANALYTICAL FINDINGS -->
    <div class="card" style="margin-top: 28px;">
        <div style="margin-bottom: 20px;">
            <h3 style="margin: 0 0 6px 0; color: #f8fafc; font-size: 1.5rem;">
                Key Analytical Findings
            </h3>
            <!-- INSIGHTS INTRO -->
            <div style="margin-top: 16px; margin-bottom: 28px; max-width: 950px;">
            <p style="color: #94a3b8; font-size: 13px; line-height: 1.6; margin: 0;">
                A notable <strong style="color: #f8fafc;">88.5% of transactions</strong> conclude on Day 0 (the initial visit), confirming an impulse-driven purchase behavior. The primary systemic bottleneck across paid campaigns occurs at checkout initiation: steep attrition results in only <strong style="color: #f8fafc;">23.5%</strong> of checkout sessions converting into completed orders. Consequently, overall end-to-end funnel conversion (CR) ranges between <strong style="color: #f8fafc;">0.4% and 2.5%</strong>.
            </p>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px;">

            <!-- FINDING 1 -->
            <div style="background: rgba(56, 189, 248, 0.04); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 12px; padding: 20px; font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;">
                <div style="margin-bottom: 12px;">
                    <span style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; font-size: 9px; margin-bottom: 10px; font-weight: 700; padding: 3px 8px; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.04em; border: 1px solid rgba(56, 189, 248, 0.25);">
                        Comparison Engine, Search, PMax | DiamondTools
                    </span>
                </div>
                <h4 style="color: #f8fafc; margin: 0 0 14px 0; font-size: 13px; font-weight: 700; letter-spacing: -0.01em; margin-bottom: 16px;">
                    Core Revenue Drivers & Closing Efficiency
                </h4>

                <div style="background: rgba(15, 23, 42, 0.65); border: 1px solid #334155; border-radius: 8px; padding: 14px; margin-bottom: 10px;">
                    <div style="color: #f8fafc; font-size: 13px; font-weight: 700; margin-bottom: 6px;">
                        Comparison Engine / Referral
                    </div>
                    <p style="color: #94a3b8; font-size: 12px; line-height: 1.55; margin: 0;">
                        Primary profitability driver (105 711.99 PLN revenue, ROAS 12.31, AOV 1 215.08 PLN). Full attribution parity (100% Match) with strong conversion efficiency (CR 2.27%). Blends fast checkout completion (72.7% Day 0) with a price comparison role (24 deferred transactions).
                    </p>
                </div>

                <div style="background: rgba(15, 23, 42, 0.65); border: 1px solid #334155; border-radius: 8px; padding: 14px; margin-bottom: 10px;">
                    <div style="color: #f8fafc; font-size: 13px; font-weight: 700; margin-bottom: 6px;">
                        PowerBrand – ElectroStore – Search Website
                    </div>
                    <p style="color: #94a3b8; font-size: 12px; line-height: 1.55; margin: 0;">
                        Second largest revenue contributor (43 398.90 PLN, ROAS 3.63). Direct conversion characteristics (73.5% Day 0, Match 90.7%). Requires on-site CRO to compress high acquisition costs (CPA 265.86 PLN) and lift conversion rates (CR 1.04%).
                    </p>
                </div>

                <div style="background: rgba(15, 23, 42, 0.65); border: 1px solid #334155; border-radius: 8px; padding: 14px;">
                    <div style="color: #f8fafc; font-size: 13px; font-weight: 700; margin-bottom: 6px;">
                        PMax | DiamondTools
                    </div>
                    <p style="color: #94a3b8; font-size: 12px; line-height: 1.55; margin: 0;">
                        High-converting, stable channel (ROAS 3.65, CR 2.98%, low CPA 100.51 PLN). Primed for budget scaling provided average order value (AOV) is systematically raised via cross-selling.
                    </p>
                </div>
            </div>

            <!-- FINDING 2 -->
            <div style="background: rgba(56, 189, 248, 0.04); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 12px; padding: 20px; font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;">
                <div style="margin-bottom: 12px;">
                    <span style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; font-size: 9px; margin-bottom: 10px; font-weight: 700; padding: 3px 8px; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.04em; border: 1px solid rgba(56, 189, 248, 0.25);">
                        PowerBrand-Shopping, Micro-Campaigns
                    </span>
                </div>
                <h4 style="color: #f8fafc; margin: 0 0 14px 0; font-size: 13px; font-weight: 700; letter-spacing: -0.01em; margin-bottom: 16px;">
                    Unprofitable Spend & Traffic Inefficiencies
                </h4>

                <div style="background: rgba(15, 23, 42, 0.65); border: 1px solid #334155; border-radius: 8px; padding: 14px; margin-bottom: 10px;">
                    <div style="color: #f8fafc; font-size: 13px; font-weight: 700; margin-bottom: 6px;">
                        PowerBrand-Shopping
                    </div>
                    <p style="color: #94a3b8; font-size: 12px; line-height: 1.55; margin: 0;">
                        Highest aggregate ad spend (12 921.38 PLN) yielding critical underperformance (ROAS = 1.08, CPA = 208.41 PLN) with a poor 0.45% CR. While capturing 13 783 users (>50% of aggregate traffic), only 0.4% convert end-to-end.
                    </p>
                </div>

                <div style="background: rgba(15, 23, 42, 0.65); border: 1px solid #334155; border-radius: 8px; padding: 14px;">
                    <div style="color: #f8fafc; font-size: 13px; font-weight: 700; margin-bottom: 6px;">
                        Micro-Campaigns (adbox_comparison, DiamondTools discount, aku, cross-network)
                    </div>
                    <p style="color: #94a3b8; font-size: 12px; line-height: 1.55; margin: 0;">
                        Negligible transaction volume, negative ROI, and steep acquisition costs for cross-network (CPA 296.00 PLN), generating net capital drag.
                    </p>
                </div>
            </div>

            <!-- FINDING 3 -->
            <div style="background: rgba(56, 189, 248, 0.04); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 12px; padding: 20px; font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;">
                <div style="margin-bottom: 12px;">
                    <span style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; font-size: 9px; font-weight: 700; padding: 3px 8px; border-radius: 4px; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.04em; border: 1px solid rgba(56, 189, 248, 0.25);">
                        Organic & Consideration Window
                    </span>
                </div>
                <h4 style="color: #f8fafc; margin: 0 0 14px 0; font-size: 13px; font-weight: 700; letter-spacing: -0.01em; margin-bottom: 16px;">
                    Assisted Conversions & Consideration Cycle
                </h4>

                <div style="background: rgba(15, 23, 42, 0.65); border: 1px solid #334155; border-radius: 8px; padding: 14px; margin-bottom: 10px;">
                    <div style="color: #f8fafc; font-size: 13px; font-weight: 700; margin-bottom: 6px;">
                        Organic Search (SEO)
                    </div>
                    <p style="color: #94a3b8; font-size: 12px; line-height: 1.55; margin: 0;">
                        Closes 4 505.83 PLN more under Last-Touch than it initiates at First-Touch, cost-effectively finalizing customer journeys originally sparked by paid campaigns.
                    </p>
                </div>

                <div style="background: rgba(15, 23, 42, 0.65); border: 1px solid #334155; border-radius: 8px; padding: 14px;">
                    <div style="color: #f8fafc; font-size: 13px; font-weight: 700; margin-bottom: 6px;">
                        1-7 Day Consideration Window
                    </div>
                    <p style="color: #94a3b8; font-size: 12px; line-height: 1.55; margin: 0;">
                        Between 20% and 27% of users from primary channels take up to a week to finalize checkout. Absence of active retargeting exposes comparing prospects to competitor churn.
                    </p>
                </div>
            </div>

            <!-- FINDING 4 -->
            <div style="background: rgba(56, 189, 248, 0.04); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 12px; padding: 20px; font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;">
                <div style="margin-bottom: 12px;">
                    <span style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; font-size: 9px; font-weight: 700; padding: 3px 8px; margin-bottom: 10px; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.04em; border: 1px solid rgba(56, 189, 248, 0.25);">
                        Unpaid Channels & Tracking Gaps
                    </span>
                </div>
                <h4 style="color: #f8fafc; margin: 0 0 14px 0; font-size: 13px; font-weight: 700; letter-spacing: -0.01em; margin-bottom: 16px;">
                    High-Value Baskets & Attribution Leaks
                </h4>

                <div style="background: rgba(15, 23, 42, 0.65); border: 1px solid #334155; border-radius: 8px; padding: 14px; margin-bottom: 10px;">
                    <div style="color: #f8fafc; font-size: 13px; font-weight: 700; margin-bottom: 6px;">
                        Direct & Referral
                    </div>
                    <p style="color: #94a3b8; font-size: 12px; line-height: 1.55; margin: 0;">
                        High brand trust and premium basket size (AOV 800.00-1 000.00 PLN, CR up to 5.13%), indicating established B2B and repeat customer segments.
                    </p>
                </div>

                <div style="background: rgba(15, 23, 42, 0.65); border: 1px solid #334155; border-radius: 8px; padding: 14px; margin-bottom: 10px;">
                    <div style="color: #f8fafc; font-size: 13px; font-weight: 700; margin-bottom: 6px;">
                        AI Assistant Traffic
                    </div>
                    <p style="color: #94a3b8; font-size: 12px; line-height: 1.55; margin: 0;">
                        Highest conversion rate (5.41%) and record ARPU (54.91 PLN/user). Despite early-stage scale (37 users), this represents a high-intent conversion vector for ongoing tracking.
                    </p>
                </div>

                <div style="background: rgba(15, 23, 42, 0.65); border: 1px solid #334155; border-radius: 8px; padding: 14px;">
                    <div style="color: #f8fafc; font-size: 13px; font-weight: 700; margin-bottom: 6px;">
                        Tracking Leaks & Data Noise
                    </div>
                    <p style="color: #94a3b8; font-size: 12px; line-height: 1.55; margin: 0;">
                        The '(not set)' segment accounts for ~4% of revenue with an 81.8% CR, requiring UTM audits to restore clean attribution. Shopping Free Listings metrics reflect micro-sample distortion (2 transactions).
                    </p>
                </div>
            </div>
        </div>
    </div>

    <!-- CARD 2: STRATEGIC RECOMMENDATIONS -->
    <div class="card" style="margin-top: 24px;">
        <div style="margin-bottom: 20px;">
            <h3 style="margin: 0 0 6px 0; color: #f8fafc; font-size: 1.5rem;">
                Strategic Recommendations
            </h3>
            <div style="margin-top: 16px; margin-bottom: 28px; max-width: 950px;">
                <p style="margin: 0; font-size: 14px; color: #94a3b8;">
                    Tactical initiatives covering paid media reallocation, on-site conversion optimization, CRM lifecycle workflows, and organic visibility.
                </p>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px;">

            <!-- RECOMMENDATION 1 -->
            <div style="background: rgba(56, 189, 248, 0.04); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 10px; padding: 18px;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
                    <span style="font-size: 10px; font-weight: 700; color: #38bdf8; letter-spacing: 0.05em; text-transform: uppercase;">1. Paid Media Budget Allocation</span>
                </div>
                <h4 style="color: #f8fafc; margin: 0 0 16px 0; font-size: 13px;">Scale Capital Efficiency & Eliminate Waste</h4>

                <p style="color: #cbd5e1; font-size: 12px; line-height: 1.55; margin: 0 0 14px 0;">
- <b>Fund Comparison Engine Liquidity:</b> Maintain active pre-paid balances and lift CPC caps on high-margin catalog items to prevent delivery interruptions.

                </p>

                <p style="color: #cbd5e1; font-size: 12px; line-height: 1.55; margin: 0 0 14px 0;">
- <b>Curb Inefficient Spend:</b> Cut PowerBrand-Shopping ad spend by at least 50% and pause zero-conversion micro-campaigns (adbox_comparison, DiamondTools discount, aku). Reallocate budget toward Comparison Engine and PMax DiamondTools.

                </p>

                <p style="color: #cbd5e1; font-size: 12px; line-height: 1.55; margin: 0;">
- <b>PMax DiamondTools Strategy:</b> Scale budget incrementally while introducing catalog bundling and cross-sell modules on product pages to raise AOV.

                </p>
            </div>

            <!-- RECOMMENDATION 2 -->
            <div style="background: rgba(56, 189, 248, 0.04); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 10px; padding: 18px;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
                    <span style="font-size: 10px; font-weight: 700; color: #38bdf8; letter-spacing: 0.05em; text-transform: uppercase;">2. Store Experience & Checkout CRO</span>
                </div>
               <h4 style="color: #f8fafc; margin: 0 0 16px 0; font-size: 13px;">Eliminate Conversion Bottlenecks</h4>

                <p style="color: #cbd5e1; font-size: 12px; line-height: 1.55; margin: 0 0 14px 0;">
- <b>Frictionless Checkout:</b> Remove mandatory account registration, enable one-click wallets (BLIK, Apple Pay, Google Pay), and display real-time dispatch countdowns to lift checkout completion toward 50%.

                </p>

                <p style="color: #cbd5e1; font-size: 12px; line-height: 1.55; margin: 0;">
- <b>Homepage Layout & A/B Testing:</b> Downsize hero banners, implement a top-deal product carousel, and integrate structured technical specification tables and FAQ sections on product detail pages.

                </p>
            </div>

            <!-- RECOMMENDATION 3 -->
            <div style="background: rgba(56, 189, 248, 0.04); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 10px; padding: 18px;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
                    <span style="font-size: 10px; font-weight: 700; color: #38bdf8; letter-spacing: 0.05em; text-transform: uppercase;">3. Retargeting & Cart Recovery</span>
                </div>
                <h4 style="color: #f8fafc; margin: 0 0 16px 0; font-size: 13px;">Capture Extended Decision Windows</h4>

                <p style="color: #cbd5e1; font-size: 12px; line-height: 1.55; margin: 0 0 14px 0;">
- <b>Automated Cart Recovery:</b> Trigger automated email/push notifications for abandoned checkouts alongside time-sensitive incentives (e.g., 60-minute vouchers) to secure immediate purchase completion.

                </p>

                <p style="color: #cbd5e1; font-size: 12px; line-height: 1.55; margin: 0 0 14px 0;">
- <b>Direct Customer Retention:</b> Implement tiered B2B pricing models, targeted newsletters, and 'Reorder Now' triggers for returning customers.

                </p>

                <p style="color: #cbd5e1; font-size: 12px; line-height: 1.55; margin: 0;">
- <b>Dynamic Remarketing (7-Day Window):</b> Limit retargeting windows to 7 days to eliminate ad spend waste beyond active purchase consideration.

                </p>
            </div>

            <!-- RECOMMENDATION 4 -->
            <div style="background: rgba(56, 189, 248, 0.04); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 10px; padding: 18px;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
                    <span style="font-size: 10px; font-weight: 700; color: #38bdf8; letter-spacing: 0.05em; text-transform: uppercase;">4. SEO, AI Readiness & Data Quality</span>
                </div>
                <h4 style="color: #f8fafc; margin: 0 0 16px 0; font-size: 13px;">Zero-Cost Visibility & Tracking Accuracy</h4>

                <p style="color: #cbd5e1; font-size: 12px; line-height: 1.55; margin: 0 0 14px 0;">
- <b>SEO & Schema.org Rich Snippets:</b> Strengthen organic visibility for PowerBrand and DiamondTools brand keywords and implement Schema markup for search engine and generative AI discovery.

                </p>

                <p style="color: #cbd5e1; font-size: 12px; line-height: 1.55; margin: 0 0 14px 0;">
- <b>Referral Growth:</b> Secure backlink placements across official manufacturer directories ('Where to Buy / Authorized Dealers') and industry networks.

                </p>

                <p style="color: #cbd5e1; font-size: 12px; line-height: 1.55; margin: 0;">
- <b>Resolve '(not set)' Traffic:</b> Perform complete UTM tag auditing across active campaigns to eliminate attribution gaps.

                </p>
            </div>

        </div>
    </div>
"""


# HTML Report Generation

def style_recommendations(val):
    if 'Top Performer' in val:
        return f'<span style="background: rgba(52, 211, 153, 0.2); color: #34d399; padding: 4px 8px; border-radius: 4px; font-weight: 700;">{val}</span>'
    elif 'Scale' in val:
        return f'<span style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; padding: 4px 8px; border-radius: 4px; font-weight: 700;">{val}</span>'
    elif 'Maintain' in val:
        return f'<span style="background: rgba(148, 163, 184, 0.2); color: #94a3b8; padding: 4px 8px; border-radius: 4px;">{val}</span>'
    else:
        return f'<span style="background: rgba(239, 68, 68, 0.2); color: #ef4444; padding: 4px 8px; border-radius: 4px;">{val}</span>'


table_html_ready = display_table.copy()
table_html_ready['Recommendation'] = table_html_ready['Recommendation'].apply(style_recommendations)
table_html = table_html_ready.to_html(index=False, escape=False, classes='tabela-executive')

final_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Executive Summary - Campaign Performance & Attribution Analysis</title>
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <style>
        body {{
            background-color: #0f172a;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: #f8fafc;
            padding: 40px 20px;
            margin: 0;
        }}
        .container {{
            max-width: 1240px;
            margin: 0 auto;
        }}
        .card {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 28px;
        }}
        .tabela-executive {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            text-align: left;
        }}
        .tabela-executive th {{
            background-color: #0b1120;
            color: #94a3b8;
            padding: 14px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 2px solid #334155;
            font-size: 11px;
        }}
        .tabela-executive td {{
            padding: 12px 14px;
            border-bottom: 1px solid #334155;
            color: #e2e8f0;
            white-space: nowrap;
        }}
        .tabela-executive tr:hover {{
            background-color: #334155;
        }}
        .tabela-executive tr:first-child {{
            background-color: rgba(52, 211, 153, 0.08);
            font-weight: bold;
        }}
    </style>
</head>
<body>
<div class="container">

    <!-- REPORT HEADER -->
    <div style="margin-bottom: 28px;">
        <h1 style="font-size: 26px; font-weight: 700; color: #f8fafc; margin: 0 0 8px 0; letter-spacing: -0.02em;">
            E-Commerce Campaign Performance & Conversion Models Report (08.05-05.08.2026)
        </h1>
        <p style="font-size: 15px; color: #94a3b8; margin: 0; line-height: 1.5;">
            First vs Last Touch attribution modeling, time-to-conversion cohort analysis, and profitability evaluation across 14 traffic sources
        </p>
    </div>

    <!-- 1. KPI SUMMARY CARDS -->
    <div style="margin-bottom: 16px;">
        <h3 style="font-size: 1.15rem; font-weight: 700; color: #f8fafc; margin: 0;">
           Top Performing Channel: COMPARISON ENGINE
        </h3>
    </div>

    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-bottom: 32px;">

      <div style="background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 20px;">
        <div style="font-size: 11px; font-weight: 700; color: #94a3b8; letter-spacing: 0.05em; text-transform: uppercase;">Revenue</div>
        <div style="font-size: 24px; font-weight: 700; color: #f8fafc; margin-top: 6px;">105 711.99 PLN</div>
        <div style="font-size: 12px; color: #34d399; margin-top: 6px; font-weight: 500;">31.5% store share • 87 transactions</div>
      </div>

      <div style="background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 20px;">
        <div style="font-size: 11px; font-weight: 700; color: #94a3b8; letter-spacing: 0.05em; text-transform: uppercase;">ROAS</div>
        <div style="font-size: 24px; font-weight: 700; color: #34d399; margin-top: 6px;">ROAS 12.31</div>
        <div style="font-size: 12px; color: #94a3b8; margin-top: 6px;">Profit leader • Lowest CPA (98.72 PLN)</div>
      </div>

      <div style="background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 20px;">
        <div style="font-size: 11px; font-weight: 700; color: #94a3b8; letter-spacing: 0.05em; text-transform: uppercase;">Average Order Value (AOV)</div>
        <div style="font-size: 24px; font-weight: 700; color: #34d399; margin-top: 6px;">1 215.08 PLN</div>
        <div style="font-size: 12px; color: #94a3b8; margin-top: 6px;">33.10 PLN ARPU • CR 2.27%</div>
      </div>

      <div style="background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 20px;">
        <div style="font-size: 11px; font-weight: 700; color: #94a3b8; letter-spacing: 0.05em; text-transform: uppercase;">Purchase Latency & Path</div>
        <div style="font-size: 24px; font-weight: 700; color: #f8fafc; margin-top: 6px;">100% First=Last</div>
        <div style="font-size: 12px; color: #94a3b8; margin-top: 6px;">72.7% Day 0 • 27.3% Days 1-7</div>
      </div>

    </div>

    <!-- 2. EXECUTIVE SUMMARY TABLE -->
    <div class="card" style="overflow-x: auto;">
        <h3 style="margin: 0 0 16px 0; color: #f8fafc; font-size: 1.2rem;">Campaign Performance & Attribution Overview</h3>
        {table_html}
    </div>

    <!-- 3. CHART 1: ROAS VS CPA -->
    <div class="card">
        {bubble_chart_html}
    </div>

    <!-- 4. CHART 2: TIME-TO-CONVERSION COHORTS -->
    <div class="card">
        {cohort_chart_html}
    </div>

    <!-- 5. CHART 3: PURCHASE FUNNEL -->
    <div class="card">
        {funnel_chart_html}
    </div>

    <!-- 6. INSIGHTS & RECOMMENDATIONS -->
    {insights_section}

</div>
</body>
</html>
"""

# Save and launch in browser
report_path = "executive_summary_report.html"
with open(report_path, "w", encoding="utf-8") as f:
    f.write(final_html)

print(f"\nHTML Report generated: {os.path.abspath(report_path)}")
webbrowser.open('file://' + os.path.realpath(report_path))