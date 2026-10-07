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
    'Not set (not set)',
    '(not set)'
]

df = pd.read_csv(
    'data/traffic_and_revenue.csv',
    encoding='utf-8-sig',
    on_bad_lines='skip',
    comment='#',
    sep=',',
)
df.columns = df.columns.str.strip()


# Isolate Comparison Engine as a standalone row from general referral
def assign_campaign_and_source(row, col_source='Source_Medium', col_campaign='Campaign'):
    source_medium = str(row.get(col_source, '')).strip().lower()
    campaign = str(row.get(col_campaign, '')).strip()

    if any(k in source_medium for k in ['comparison_engine', 'ceneo']) or any(k in campaign.lower() for k in ['comparison_engine', 'ceneo']):
        return 'comparison_engine / referral'

    elif campaign in ['(not set)', '', 'nan']:
        return 'Not set (not set)'

    return campaign


df['Source_Campaign'] = df.apply(
    lambda r: assign_campaign_and_source(r, 'Source_Medium', 'Campaign'), axis=1
)

# Paid vs organic/free traffic classification
df['Channel_Type'] = df['Source_Campaign'].apply(
    lambda x: 'organic / free' if x in free_sources else 'paid campaign'
)

# Data cleaning and type casting
df['Transactions'] = pd.to_numeric(df.get('Transactions', 0), errors='coerce').fillna(0).astype(int)
df['Revenue'] = pd.to_numeric(df.get('Purchase_Revenue', 0.0), errors='coerce').fillna(0.0).round(2)
df['Active_Users'] = pd.to_numeric(df.get('Active_Users', 0), errors='coerce').fillna(0).astype(int)

funnel = (
    df.groupby(['Channel_Type', 'Source_Campaign'])
    .agg(
        Users=('Active_Users', 'sum'),
        Transactions=('Transactions', 'sum'),
        Revenue=('Revenue', 'sum'),
    )
    .reset_index()
)

funnel['Conversion_Rate_%'] = np.where(
    funnel['Users'] > 0,
    ((funnel['Transactions'] / funnel['Users']) * 100).round(2),
    np.nan
)

funnel = funnel.sort_values(by='Revenue', ascending=False).reset_index(drop=True)

# Merge funnel metrics with campaign costs
df_costs = pd.read_csv('data/campaign_costs.csv', encoding='utf-8-sig', on_bad_lines='skip', comment='#')
df_costs.columns = df_costs.columns.str.strip()
df_costs.rename(columns={'Campaign': 'Source_Campaign'}, inplace=True)
df_costs['Cost'] = pd.to_numeric(df_costs['Cost'], errors='coerce').fillna(0.0).round(2)

costs_summary = df_costs.groupby('Source_Campaign').agg(Cost=('Cost', 'sum')).reset_index()

summary = pd.merge(funnel, costs_summary, on='Source_Campaign', how='left').fillna(0)

# ROAS and CPA calculations

# Return on Ad Spend (ROAS)
summary['ROAS'] = np.where(
    summary['Cost'] > 0,
    (summary['Revenue'] / summary['Cost']).round(2),
    0.00
)

# Cost Per Acquisition (CPA) - spend per completed transaction
summary['CPA'] = np.where(
    summary['Transactions'] > 0,
    (summary['Cost'] / summary['Transactions']).round(2),
    0.00
)

print(summary)

# print(summary['Conversion_Rate_%'].mean())


# VISUALIZATIONS

# BUBBLE CHART: ROAS vs CPA for paid campaigns

df_paid = summary[summary['Cost'] > 0].copy()


def get_bubble_text_position(row):
    if row['ROAS'] > 5:
        return 'bottom center'
    if row['CPA'] > 200:
        return 'top right'
    return 'top left'


df_paid['Text_Position'] = df_paid.apply(get_bubble_text_position, axis=1)
df_paid['Label'] = df_paid['Source_Campaign']

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
    textfont=dict(size=11, color='#CCCCCC', family='Arial'),
    hoverlabel=dict(bgcolor='#222222', bordercolor='#444444', font=dict(color='white')),
    hovertemplate=(
        "<b>%{customdata[0]}</b><br>"
        "CPA (Cost per Acquisition): %{x:.2f} PLN<br>"
        "ROAS: %{y:.2f}<br>"
        "Revenue: %{customdata[1]:.2f} PLN"
        "<extra></extra>"
    ),
    customdata=df_paid[['Source_Campaign', 'Revenue']].values
)

fig_bubble.update_layout(
    height=600,
    plot_bgcolor='#111111',
    paper_bgcolor='#111111',
    font=dict(color='white'),
    xaxis=dict(showgrid=True, gridcolor='#262626', zeroline=False),
    yaxis=dict(showgrid=True, gridcolor='#262626', zeroline=False),
    margin=dict(l=60, r=120, t=80, b=50),
    showlegend=False,
)

fig_bubble.show()


# SCATTER PLOT: Traffic Scale vs Conversion Rate

def assign_label_and_position(row):
    name = row['Source_Campaign']
    users = row['Users']
    cr = row['Conversion_Rate_%']

    # Suppress labels for low-traffic points with negligible conversion
    if users < 500 and cr < 0.5:
        return '', 'top right'

    # Custom label alignment to prevent overlap and axis clipping
    if 'PowerBrand-Shopping' in name or 'PowerBrand-Ogród' in name or 'PowerBrand-Ogrod' in name:
        return name, 'middle left'
    if '(ai-assistant)' in name:
        return name, 'top right'
    if 'Not set' in name or 'Brak nazwy' in name:
        return name, 'bottom right'
    if 'Shopping Free' in name:
        return name, 'top right'
    if 'PMax' in name:
        return name, 'bottom right'
    if '(direct)' in name:
        return name, 'top right'
    if '(organic)' in name:
        return name, 'top right'
    if 'cross-network' in name or 'cross' in name:
        return name, 'top right'
    if 'referral' in name and 'comparison_engine' not in name:
        return name, 'bottom right'
    if 'comparison_engine' in name:
        return name, 'top center'
    if 'Search Website' in name:
        return name, 'top right'

    return name, 'top right'


labels_and_positions = summary.apply(assign_label_and_position, axis=1)
summary['Label_CR'] = [lp[0] for lp in labels_and_positions]
summary['Position_CR'] = [lp[1] for lp in labels_and_positions]

max_x = summary['Users'].max()

fig_scatter = px.scatter(
    summary,
    x='Users',
    y='Conversion_Rate_%',
    size='Revenue',
    color='Channel_Type',
    text='Label_CR',
    size_max=40,
    title='<b>Traffic Scale vs Efficiency: Active Users vs Conversion Rate (CR)</b>',
    labels={
        'Users': 'Active Users',
        'Conversion_Rate_%': 'Conversion Rate (%)',
        'Channel_Type': 'Traffic Type',
    },
    template='plotly_dark',
)

for trace in fig_scatter.data:
    df_subset = summary[summary['Channel_Type'] == trace.name]
    trace.mode = 'markers+text'
    trace.textposition = df_subset['Position_CR'].tolist()
    trace.textfont = dict(size=11, color='#CCCCCC', family='Arial')
    trace.hoverlabel = dict(bgcolor='#222222', bordercolor='#444444', font=dict(color='white'))
    trace.customdata = df_subset[['Source_Campaign', 'Revenue', 'CPA', 'ROAS']].values
    trace.hovertemplate = (
        "<b>%{customdata[0]}</b><br>"
        "Active Users: %{x}<br>"
        "Conversion Rate (%): %{y:.2f}%<br>"
        "Revenue: %{customdata[1]:.2f} PLN"
        "<extra></extra>"
    )

fig_scatter.update_layout(
    height=650,
    plot_bgcolor='#111111',
    paper_bgcolor='#111111',
    font=dict(color='white'),
    xaxis=dict(
        showgrid=True,
        gridcolor='#262626',
        zeroline=False,
        tick0=0,
        dtick=1000,
        tickformat="d",
        range=[0, max_x * 1.18]
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor='#262626',
        zeroline=False,
        range=[-0.3, summary['Conversion_Rate_%'].max() * 1.15]
    ),
    margin=dict(l=60, r=140, t=90, b=50),
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
)

fig_scatter.show()

# FUNNEL CHART: Conversion Funnel by Event

# Load dedicated event-level data for the conversion funnel
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

# Define 5 key funnel stages
event_mapping = {
    'session_start': '1. Session Start (Home/Landing)',
    'view_item': '2. Product View',
    'add_to_cart': '3. Add to Cart',
    'begin_checkout': '4. Begin Checkout',
    'purchase': '5. Purchase Completed'
}

# Select top-performing and high-volume campaigns
selected_campaigns = [
    'PowerBrand – ElectroStore – Search Website',
    'comparison_engine / referral',
    'PowerBrand-Shopping',
    'PMax | DiamondTools'
]

# Filter data for selected campaigns and mapped funnel events
df_filtered = df_events[
    (df_events['Source_Campaign'].isin(selected_campaigns)) &
    (df_events['Event_Name'].isin(event_mapping.keys()))
].copy()

# Map standardized stage names and aggregate event volumes
df_filtered['Funnel_Step'] = df_filtered['Event_Name'].map(event_mapping)

df_agg = (
    df_filtered.groupby(['Source_Campaign', 'Funnel_Step'])
    .agg(Count=('Event_Count', 'sum'))
    .reset_index()
)

stage_order = list(event_mapping.values())

# Funnel visualization
palette = ['#4C8BF5', '#76D275', '#F5A623', '#FF6B6B', '#8E44AD']

fig = go.Figure()

for i, campaign in enumerate(selected_campaigns):
    data_k = df_agg[df_agg['Source_Campaign'] == campaign].set_index('Funnel_Step')

    values = [int(data_k.loc[step, 'Count']) if step in data_k.index else 0 for step in stage_order]

    fig.add_trace(
        go.Funnel(
            name=campaign,
            y=stage_order,
            x=values,
            textinfo="value",
            texttemplate="%{value: }",
            textposition="auto",
            insidetextfont=dict(size=14, color="white", family="Arial Black"),
            outsidetextfont=dict(size=14, color="white", family="Arial Black"),
            hoverlabel=dict(bgcolor='#222222', bordercolor='#444444', font=dict(color='white', family="Arial")),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Event Count: %{x: }<br>"
                "Conversion from Initial: %{percentInitial:.1%}<br>"
                "Step-to-Step Conversion: %{percentPrevious:.1%}"
                "<extra></extra>"
            ),
            marker=dict(
                color=palette,
                line=dict(width=0)
            ),
            connector=dict(visible=False),
            visible=(i == 0)
        )
    )

# Dropdown menu to switch between the 4 campaigns
buttons = []
for i, campaign in enumerate(selected_campaigns):
    visibility = [False] * len(selected_campaigns)
    visibility[i] = True
    buttons.append(dict(
        label=campaign,
        method="update",
        args=[
            {"visible": visibility},
            {"title.text": f"<b>Purchase Funnel:</b> {campaign}"}
        ]
    ))

fig.update_layout(
    updatemenus=[dict(
        active=0,
        buttons=buttons,
        x=1.0,
        y=1.18,
        xanchor='right',
        yanchor='top',
        bgcolor='#222222',
        bordercolor='#444444',
        font=dict(color='white', size=12)
    )],
    title=dict(
        text=f"<b>Purchase Funnel:</b> {selected_campaigns[0]}",
        font=dict(color="white", size=18),
        x=0.05,
        xanchor='left'
    ),
    yaxis=dict(
        visible=True,
        showline=False,
        showgrid=False,
        ticks="",
        tickfont=dict(size=14, color="white", family="Arial")
    ),
    plot_bgcolor='#111111',
    paper_bgcolor='#111111',
    font=dict(color="white", size=13),
    height=600,
    margin=dict(l=240, r=100, t=90, b=40)
)

fig.show()


# FINDINGS AND RECOMMENDATIONS

""" Key Observations:

During the analyzed period (08.05-05.08.2026), the store maintained an average conversion rate of 1.88%. 
Organic Search and Direct traffic demonstrated superior audience intent and strong conversion performance (0.99% and 3.16% respectively), 
delivering reliable revenue and reflecting a solid baseline of returning customers without incremental ad spend.

1. Paid Campaign Performance (ROAS & CPA)


Paid acquisition channels display stark operational divergence:
- Comparison Engine (comparison_engine / referral) - Core Profit Engine:

  This channel generated the highest aggregate revenue (105,711.99 PLN) with an exceptional ROAS of 12.31 and a 2.27% conversion rate. 
  Cost Per Acquisition (CPA) stood at 98.72 PLN.

- Campaigns Requiring Optimization:

  PowerBrand-Shopping: Incurred the largest ad expenditure (12,921.38 PLN) while producing sub-optimal returns (ROAS = 1.08, CPA = 208.41 PLN) 
  and a low conversion rate of 0.45%. Despite driving massive volume (13,783 users), only 0.4% converted end-to-end.

  PowerBrand – ElectroStore – Search Website: Produced substantial gross revenue (43,398.90 PLN), but at an elevated acquisition cost (CPA = 265.86 PLN) 
  and moderate efficiency (ROAS = 3.63).

  PMax | DiamondTools: Demonstrated strong conversion efficiency (2.98%) alongside a solid ROAS of 3.65 (CPA = 100.51 PLN).

  Underperforming Ad Spend: Sources including DiamondTools discount, adbox_comparison, aku, and (cross-network) incurred ad costs while producing negligible 
  or zero conversions, resulting in net capital drag.

2. Purchase Funnel Diagnostics (Chart 3)
Funnel stage analysis highlights checkout drop-off as the primary conversion bottleneck:

- While product engagement and cart additions are robust, a sharp attrition cliff emerges between checkout initiation and order completion: 

  only 23.5% of users who initiate checkout ultimately finalize their purchase.
- End-to-end funnel conversion (from initial session start to purchase) ranges between 0.4% and 2.5% across segments, showing consistent step drop-offs.

- Early drop-off between 'Session Start' and 'Product View' accounts for an immediate loss of over 35% of inbound traffic.

  Potential root causes: intrusive pop-ups/promotional banners, cluttered navigation menus, cognitive overload on landing, or misaligned information hierarchy.


RECOMMENDATIONS

1. Checkout Funnel Optimization:

   Streamline the checkout flow: introduce express checkout methods (BLIK, Apple Pay, Google Pay), enable frictionless guest checkout, 
   add urgency/shipping countdown triggers ('Order within 1.5h for same-day dispatch'), and simplify form validation. 
   Target lifting checkout completion to at least 40-50%.

2. Ad Spend Reallocation:
   Significantly curb ad spend or overhaul audience targeting for PowerBrand-Shopping (currently operating near break-even).
   Scale capital toward proven high-efficiency channels (comparison_engine / referral and PMax | DiamondTools).
   Decommission zero-conversion micro-campaigns (adbox_comparison, DiamondTools discount, aku).
   Implement automated cart recovery flows (email and push notifications) to recapture abandoned checkout sessions.

3. Landing Page UX & A/B Testing:
   Simplify the home and category landing layouts. Consolidate oversized promotional banners that crowd the initial viewport. 
   Implement a clean product carousel for promotional items ('Hity Cenowe') instead of fragmented standalone blocks, 
   and position static company info in the footer to preserve above-the-fold focus.
"""