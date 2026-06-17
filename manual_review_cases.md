# Manual Review Cases — Ambiguous Segmentation & Retention Decisions

Ten customers where RFM rules, engagement, or churn label conflict. Metrics are as of snapshot **2025-09-30**.

| customer_id | segment | R | F | M (₹) | tickets_90d | sessions_30d | campaign_clicks | churn_label |
|---|---|---:|---:|---:|---:|---:|---:|---|
| CUST00654 | High-Value Unhappy | 8 | 4 | 4,672 | 2 | 8 | 0 | 0 |
| CUST00675 | At-Risk | 130 | 2 | 4,218 | 0 | 8 | 1 | 0 |
| CUST02350 | At-Risk | 132 | 3 | 3,620 | 0 | 1 | 1 | 0 |
| CUST00463 | Loyal Customers | 29 | 4 | 5,049 | 0 | 0 | 0 | 0 |
| CUST01683 | Loyal Customers | 26 | 4 | 4,532 | 0 | 7 | 0 | 0 |
| CUST00790 | Loyal Customers | 78 | 1 | 459 | 1 | 9 | 1 | 1 |
| CUST02118 | Loyal Customers | 93 | 1 | 1,688 | 0 | 5 | 0 | 1 |
| CUST00413 | Discount-Sensitive | 26 | 1 | 221 | 1 | 16 | 0 | 0 |
| CUST00051 | Dormant | 210 | 0 | 0 | 0 | 6 | 2 | 1 |
| CUST00418 | Champions | 5 | 2 | 1,920 | 1 | 8 | 2 | 0 |

---

### CUST00654 — High spend + complaints, zero campaign clicks

**Why ambiguous:** Monetary **₹4,672** and recency **8 days** look like a Champion, but **2 tickets** in 90d and **50%** return rate signal dissatisfaction. **0** campaign clicks despite `welcome_offer`.

**Action:** Priority support resolution + quality check on last order. Hold promotional discount until sentiment improves. Re-classify to Champions only after 60 days ticket-free.

---

### CUST00675 — At-Risk label vs high value and engagement

**Why ambiguous:** Segment **At-Risk** (recency **130d**) but monetary **₹4,218**, frequency **2**, and **8** sessions — looks engaged on site but not purchasing.

**Action:** Cart/browse recovery email with free shipping (not 30% off). Investigate category stock-outs or price comparison; not a dormant case.

---

### CUST02350 — High monetary At-Risk with minimal digital touch

**Why ambiguous:** **₹3,620** spend and **3** orders, but only **1** session and recency **132 days**.

**Action:** Win-back call/email referencing last purchased category. Low digital activity suggests email/offline channel preference.

---

### CUST00463 — Loyal segment, champion-level spend, zero web activity

**Why ambiguous:** **₹5,049** and **4** orders with recency **29 days** fits Champions, but rule assigned **Loyal** (frequency below 75th for champions). **0** sessions — offline or marketplace buyer?

**Action:** Treat as high-value Loyal: replenishment SMS if phone on file; do not rely on app-only campaigns.

---

### CUST01683 — Recent high spender, no campaign engagement

**Why ambiguous:** Recency **26 days**, **₹4,532**, **4** orders, yet **0** campaign clicks and `last_campaign_received = none`.

**Action:** Test non-discount trigger (new SKU sample). Avoid assuming discount need; may be organic loyalist.

---

### CUST00790 — Loyal segment but churned in label window

**Why ambiguous:** Classified **Loyal** but `churn_next_60d = 1` with recency **78 days**, low monetary **₹459**, **1** ticket.

**Action:** Move to At-Risk treatment queue: win-back + support follow-up on ticket. Segment rule should be overridden in CRM.

---

### CUST02118 — Medium recency, churned, moderate spend

**Why ambiguous:** **Loyal** by ticket/frequency rules but **93-day** recency and churn label **1**; monetary **₹1,688** supports save effort.

**Action:** Personalized win-back (category: from order history). Priority over generic Loyal cohort.

---

### CUST00413 — Discount-Sensitive with heavy browsing

**Why ambiguous:** Low monetary **₹221** and high discount sensitivity, but **16** sessions — engaged browser, not buyer.

**Action:** Small bundle incentive on viewed category; monitor margin. Not eligible for Champion/VIP perks.

---

### CUST00051 — Dormant with web activity

**Why ambiguous:** **Dormant** (no 180d orders, recency **210**) yet **6** sessions and **2** campaign clicks — interested but not converting.

**Why ambiguous:** Churn label **1** confirms no post-snapshot purchase.

**Action:** Low-cost email test only; if no purchase in 30 days, suppress from paid campaigns to save budget.

---

### CUST00418 — Borderline Champion (low monetary for segment)

**Why ambiguous:** Assigned **Champions** (recency **5**, good engagement) but monetary **₹1,920** is near the segment minimum vs avg **₹3,001**.

**Action:** Nurture with loyalty enrollment and second-order cross-sell; defer VIP perks until monetary crosses **₹1,899** (80th percentile) consistently.

---

*Selected via ambiguity scoring in `rfm_segmentation.ipynb` (high-M + tickets, At-Risk + high-M, Loyal + churn=1, Dormant + sessions, etc.).*
