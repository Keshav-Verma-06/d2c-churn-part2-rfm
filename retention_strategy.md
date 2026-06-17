# Retention Strategy by Segment

**Snapshot date:** 2025-09-30  
**Universe:** 2,400 customers | **Observed churn (60d):** 47.0% overall  
**Segmentation:** RFM (180-day window) + support tickets (90d) + web/campaign engagement

Thresholds were set from data quantiles (e.g., recency 75th = 129 days, monetary 80th = ₹1,899, discount 75th = 34%).

---

## Champions

- **Count:** 132 (5.5% of base)
- **Key behavior:** Avg recency **10 days**, frequency **3.5** orders/180d, monetary **₹3,001**, sessions **8.1**/30d. Churn **5%** (vs 47% overall).
- **Recommended action:** VIP early-access to new launches and referral incentives — **no blanket discount**. Reinforce habit with category cross-sell based on `preferred_category`.
- **Expected business value:** Highest LTV preservation; low discount spend; strong word-of-mouth potential.

---

## Loyal Customers

- **Count:** 1,429 (59.5%)
- **Key behavior:** Avg recency **58 days**, frequency **1.9**, monetary **₹1,371**, tickets **0.24**/90d. Churn **36%** — meaningful but not crisis-level.
- **Recommended action:** Personalized replenishment reminders and loyalty-tier enrollment for the **57%** without `loyalty_tier`. Use content/education, not deep discounts.
- **Expected business value:** Stable margin; incremental uplift from reducing “silent drift” before they become At-Risk.

---

## At-Risk

- **Count:** 311 (13.0%)
- **Key behavior:** Avg recency **114 days** (>75th percentile) with prior frequency **≥2**, monetary **₹1,030**, sessions **1.7**/30d. Churn **71%**.
- **Recommended action:** Win-back sequence: “We miss you” email + free shipping on next order (not 30%+ off). Pair with browse-abandonment push if `sessions_30d` ≤ 2.
- **Expected business value:** High ROI — proven buyers who are disengaging; cheaper than acquiring new paid traffic.

---

## Discount-Sensitive

- **Count:** 189 (7.9%)
- **Key behavior:** Avg discount **≥34%** (75th percentile) with monetary **₹355** (bottom 30%). Recency **72 days**. Churn **58%**.
- **Recommended action:** Small, time-bound offer tied to bundle (e.g., 15% on 2+ SKUs) instead of site-wide coupons. Cap margin erosion with minimum basket.
- **Expected business value:** Converts price-driven shoppers without training Champions/Loyal to wait for discounts.

---

## Dormant

- **Count:** 302 (12.6%)
- **Key behavior:** No orders in 180d (frequency **0**) or recency **≥196 days** (90th percentile). Monetary **₹0**. Churn **91%**.
- **Recommended action:** Low-cost reactivation test only (email/SMS). Avoid high-cost outbound or large discounts unless `manual_priority_bucket == high` and recent web signal exists.
- **Expected business value:** Low recovery probability; spend should be minimal and measured against holdout.

---

## High-Value Unhappy

- **Count:** 37 (1.5%)
- **Key behavior:** Monetary top **30%** (≥₹1,471) with **≥2** support tickets in 90d. Avg recency **26 days**, frequency **3.6**. Churn **5%** in labels but **high complaint risk**.
- **Recommended action:** Proactive support outreach (manager callback) + goodwill credit or replacement **before** a discount campaign. Do not blast promotional email until tickets resolved.
- **Expected business value:** Protects high spenders and NPS; prevents public reviews and chargebacks.

---

# Campaign Budget Prioritization

**Assumption:** Limited budget covers **500 customers** for one retention wave.

| Priority | Segment | Customers to target (from 500) | Justification |
|:--:|---|---|---|
| **1** | **At-Risk** | ~280 | **71%** churn with prior purchase history; win-back + free shipping has better expected recovery than discounting Dormant. Median monetary ~₹1,030 justifies moderate offer cost. |
| **2** | **High-Value Unhappy** | ~37 (all) | Small cohort but **₹2,666** avg spend and active complaints — fixing experience retains margin better than acquisition. |
| **3** | **Loyal Customers** (high monetary, rising recency) | ~120 | Subset with recency 60–129 days and monetary > median — prevent slide into At-Risk at **36%** churn with low-cost nudges. |
| **4** | **Discount-Sensitive** | ~50 | Test controlled bundle offer; monitor margin. Only after At-Risk and service recovery. |
| **5** | **Champions** | ~13 | Recognition-only touch; not a budget priority for save offers. |

**Deprioritize:**

- **Dormant (302):** **91%** churn and **₹0** recent monetary — budget better spent on **At-Risk** with proven frequency ≥2.
- **Broad discounts to Loyal/Champions:** Risks margin and trains full base to wait for promotions; data shows Champions churn only **5%** without discounts.

**Allocation summary (500 slots):** At-Risk 280 → High-Value Unhappy 37 → Loyal (at-risk recency band) 120 → Discount-Sensitive 50 → Champions 13.

---

*Metrics from `rfm_segmentation.ipynb` / `segments.csv` (pre-snapshot orders only, `_DUP` rows removed).*
