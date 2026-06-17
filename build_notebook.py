"""Generate rfm_segmentation.ipynb from notebook cell definitions."""
import json
from pathlib import Path

ROOT = Path(__file__).parent

def md(text: str):
    return {"cell_type": "markdown", "metadata": {}, "source": [text]}

def code(text: str):
    return {"cell_type": "code", "metadata": {}, "source": [text], "outputs": [], "execution_count": None}

cells = [
    md("# Part 2 — RFM Segmentation & Retention Strategy\n\n**Snapshot:** 2025-09-30 | **Features:** pre-snapshot orders/tickets only"),
    md("## Phase 1 — Load & filter (leakage guardrails)"),
    code("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

SNAPSHOT = pd.Timestamp('2025-09-30')
WINDOW_180_START = pd.Timestamp('2025-04-03')
WINDOW_90_START = pd.Timestamp('2025-07-02')
RECENCY_NO_ORDER = 999
ROOT = Path('.')

customers = pd.read_csv(ROOT / 'customers.csv')
orders = pd.read_csv(ROOT / 'orders.csv', parse_dates=['order_date'])
tickets = pd.read_csv(ROOT / 'support_tickets.csv', parse_dates=['ticket_date'])
web = pd.read_csv(ROOT / 'web_events_snapshot.csv')
intervention = pd.read_csv(ROOT / 'intervention_history.csv')
labels = pd.read_csv(ROOT / 'churn_labels.csv')

orders_pre = orders[orders['order_date'] <= SNAPSHOT].copy()
tickets_pre = tickets[tickets['ticket_date'] <= SNAPSHOT].copy()
orders_pre = orders_pre[~orders_pre['order_id'].str.endswith('_DUP', na=False)]
orders_pre = orders_pre.drop_duplicates(subset=['order_id'], keep='first')

assert (orders_pre['order_date'] > SNAPSHOT).sum() == 0
print('orders_pre rows:', len(orders_pre), '| max date:', orders_pre['order_date'].max())

base = customers.merge(web[['customer_id','sessions_30d','campaign_clicks_30d','last_visit_days_ago']], on='customer_id', how='left')
base = base.merge(intervention[['customer_id','last_campaign_received']], on='customer_id', how='left')
base = base.merge(labels[['customer_id','churn_next_60d']], on='customer_id', how='left')
for c in ['sessions_30d','campaign_clicks_30d']:
    base[c] = base[c].fillna(0)
print('base shape:', base.shape)
assert len(base) == 2400"""),
    md("## Phase 2 — RFM features (180-day window)\n\nWindow **2025-04-03 → 2025-09-30** aligns with capstone modeling snapshot and seasonal purchase cycles."),
    code("""win = orders_pre[orders_pre['order_date'] >= WINDOW_180_START]
cust_ids = customers['customer_id']

last_order = orders_pre.groupby('customer_id')['order_date'].max().reindex(cust_ids)
recency = (SNAPSHOT - last_order).dt.days.fillna(RECENCY_NO_ORDER).astype(int)
frequency = win.groupby('customer_id').size().reindex(cust_ids, fill_value=0).astype(int)
monetary = win.groupby('customer_id')['gross_amount'].sum().reindex(cust_ids, fill_value=0.0)
return_rate_180d = win.groupby('customer_id')['returned'].mean().reindex(cust_ids, fill_value=0.0)
avg_discount_pct_180d = win.groupby('customer_id')['discount_pct'].mean().reindex(cust_ids, fill_value=0.0)

df = base.copy()
df['recency'] = recency.values
df['frequency'] = frequency.values
df['monetary'] = monetary.values
df['return_rate_180d'] = return_rate_180d.values
df['avg_discount_pct_180d'] = avg_discount_pct_180d.values
df[['recency','frequency','monetary']].describe()"""),
    md("## Phase 3 — Non-RFM signals"),
    code("""tickets_90 = tickets_pre[tickets_pre['ticket_date'] >= WINDOW_90_START]
df['ticket_count_90d'] = tickets_90.groupby('customer_id').size().reindex(cust_ids, fill_value=0).astype(int).values
df['campaign_engaged'] = np.where(df['last_campaign_received'].fillna('none') == 'none', 'No Campaign', 'Engaged')

cols = ['recency','frequency','monetary','ticket_count_90d','sessions_30d','campaign_clicks_30d']
print(df[cols].corr().round(2))"""),
    md("## Phase 4 — Segments (quantile-based rules)"),
    code("""active = df[df['frequency'] > 0]
TH = {
    'recency_75': df['recency'].quantile(0.75),
    'recency_90': df['recency'].quantile(0.90),
    'freq_50': active['frequency'].quantile(0.50),
    'freq_75': active['frequency'].quantile(0.75),
    'monetary_80': df['monetary'].quantile(0.80),
    'monetary_70': df['monetary'].quantile(0.70),
    'monetary_30': df['monetary'].quantile(0.30),
    'monetary_50': df['monetary'].quantile(0.50),
    'discount_75': df['avg_discount_pct_180d'].quantile(0.75),
    'sessions_25': df['sessions_30d'].quantile(0.25),
    'recency_champion_max': int(df[df['frequency'] > 0]['recency'].quantile(0.25)),
}
print('Thresholds:', TH)

def assign_segment_v2(row, t):
    r, f, m = int(row['recency']), int(row['frequency']), float(row['monetary'])
    tickets, disc, sessions = int(row['ticket_count_90d']), float(row['avg_discount_pct_180d']), int(row['sessions_30d'])
    if f == 0 or r >= t['recency_90']:
        return 'Dormant'
    if m >= t['monetary_70'] and tickets >= 2:
        return 'High-Value Unhappy'
    if r <= t['recency_champion_max'] and f >= t['freq_75'] and m >= t['monetary_80']:
        return 'Champions'
    if disc >= t['discount_75'] and m <= t['monetary_30']:
        return 'Discount-Sensitive'
    if r > t['recency_75'] and f >= 2:
        return 'At-Risk'
    if f >= max(2, t['freq_50']) and tickets <= 1 and r <= t['recency_75']:
        return 'Loyal Customers'
    if sessions <= t['sessions_25'] and r > t['recency_champion_max']:
        return 'At-Risk'
    return 'Loyal Customers'

df['segment_name'] = df.apply(lambda r: assign_segment_v2(r, TH), axis=1)
print(df['segment_name'].value_counts())
print('\\nChurn by segment:')
print(df.groupby('segment_name')['churn_next_60d'].mean().sort_values(ascending=False))"""),
    md("## Phase 5 — Export `segments.csv` & charts"),
    code("""out = df[['customer_id','segment_name','recency','frequency','monetary','ticket_count_90d','sessions_30d','campaign_clicks_30d']]
out.to_csv('segments.csv', index=False)
print('segments.csv rows:', len(out))

CHARTS = Path('charts')
CHARTS.mkdir(exist_ok=True)
seg_churn = df.groupby('segment_name')['churn_next_60d'].mean().reset_index()

fig, ax = plt.subplots(figsize=(10,5))
sns.barplot(data=seg_churn, x='segment_name', y='churn_next_60d', hue='segment_name', legend=False, ax=ax)
ax.set_title('Churn rate by segment')
plt.xticks(rotation=25, ha='right')
plt.tight_layout()
plt.savefig(CHARTS / 'churn_by_segment.png', dpi=120)
plt.show()

fig, ax = plt.subplots(figsize=(10,5))
sns.boxplot(data=df, x='segment_name', y='monetary', hue='segment_name', legend=False, ax=ax)
ax.set_yscale('symlog')
ax.set_title('Monetary by segment')
plt.xticks(rotation=25, ha='right')
plt.tight_layout()
plt.savefig(CHARTS / 'monetary_by_segment.png', dpi=120)
plt.show()

plot_df = df[df['recency'] < RECENCY_NO_ORDER].sample(min(1500, len(df)), random_state=42)
fig, ax = plt.subplots(figsize=(9,6))
sns.scatterplot(data=plot_df, x='recency', y='frequency', hue='segment_name', alpha=0.6, ax=ax)
plt.tight_layout()
plt.savefig(CHARTS / 'recency_frequency_scatter.png', dpi=120)
plt.show()"""),
    md("## Phase 8 — Validation checklist"),
    code("""seg = pd.read_csv('segments.csv')
checks = {
    'rows_2400': len(seg) == 2400,
    'required_cols': set(['customer_id','segment_name','recency','frequency','monetary','ticket_count_90d','sessions_30d','campaign_clicks_30d']).issubset(seg.columns),
    'segments_5plus': seg['segment_name'].nunique() >= 5,
    'no_post_snapshot_orders': (orders_pre['order_date'] > SNAPSHOT).sum() == 0,
}
for k, v in checks.items():
    print(f"[{'x' if v else ' '}] {k}: {v}")
print('\\nSegment counts:\\n', seg['segment_name'].value_counts())"""),
]

nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11.0"},
    },
    "cells": cells,
}

out_path = ROOT / "rfm_segmentation.ipynb"
out_path.write_text(json.dumps(nb, indent=1), encoding="utf-8")
print("Wrote", out_path)
