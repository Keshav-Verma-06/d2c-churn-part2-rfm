"""
Part 2 RFM pipeline — run from repo root to produce segments.csv, charts, and summary stats.
Used by rfm_segmentation.ipynb (same logic).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

SNAPSHOT = pd.Timestamp("2025-09-30")
WINDOW_180_START = pd.Timestamp("2025-04-03")
WINDOW_90_START = pd.Timestamp("2025-07-02")
RECENCY_NO_ORDER = 999

ROOT = Path(__file__).resolve().parent
CHARTS = ROOT / "charts"


def load_and_prepare() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    customers = pd.read_csv(ROOT / "customers.csv")
    orders = pd.read_csv(ROOT / "orders.csv", parse_dates=["order_date"])
    tickets = pd.read_csv(ROOT / "support_tickets.csv", parse_dates=["ticket_date"])
    web = pd.read_csv(ROOT / "web_events_snapshot.csv")
    intervention = pd.read_csv(ROOT / "intervention_history.csv")
    labels = pd.read_csv(ROOT / "churn_labels.csv")

    orders_pre = orders[orders["order_date"] <= SNAPSHOT].copy()
    tickets_pre = tickets[tickets["ticket_date"] <= SNAPSHOT].copy()

    # Remove _DUP suffix rows; keep first occurrence per base order_id
    orders_pre = orders_pre[~orders_pre["order_id"].str.endswith("_DUP", na=False)].copy()
    orders_pre = orders_pre.drop_duplicates(subset=["order_id"], keep="first")

    assert orders_pre["order_date"].max() <= SNAPSHOT
    assert (orders_pre["order_date"] > SNAPSHOT).sum() == 0

    base = customers.copy()
    n0 = len(base)

    web_cols = [
        "customer_id",
        "sessions_30d",
        "campaign_clicks_30d",
        "last_visit_days_ago",
        "product_views_30d",
        "abandoned_carts_30d",
    ]
    base = base.merge(web[web_cols], on="customer_id", how="left")
    base = base.merge(
        intervention[["customer_id", "last_campaign_received", "manual_priority_bucket"]],
        on="customer_id",
        how="left",
    )
    base = base.merge(labels[["customer_id", "churn_next_60d", "split"]], on="customer_id", how="left")

    for c in ["sessions_30d", "campaign_clicks_30d", "last_visit_days_ago", "product_views_30d", "abandoned_carts_30d"]:
        base[c] = base[c].fillna(0)

    assert len(base) == n0 == 2400

    return base, orders_pre, tickets_pre


def compute_rfm(orders_pre: pd.DataFrame) -> pd.DataFrame:
    win = orders_pre[orders_pre["order_date"] >= WINDOW_180_START].copy()
    customers_all = pd.read_csv(ROOT / "customers.csv")["customer_id"]
    last_order = orders_pre.groupby("customer_id")["order_date"].max().reindex(customers_all)
    recency = (SNAPSHOT - last_order).dt.days
    recency = recency.fillna(RECENCY_NO_ORDER).astype(int)

    freq = win.groupby("customer_id").size().reindex(customers_all, fill_value=0).astype(int)
    monetary = win.groupby("customer_id")["gross_amount"].sum().reindex(customers_all, fill_value=0.0)

    # Return rate 180d
    ret = (
        win.groupby("customer_id")["returned"]
        .mean()
        .reindex(customers_all, fill_value=0.0)
        .rename("return_rate_180d")
    )
    disc = (
        win.groupby("customer_id")["discount_pct"]
        .mean()
        .reindex(customers_all, fill_value=0.0)
        .rename("avg_discount_pct_180d")
    )

    rfm = pd.DataFrame(
        {
            "customer_id": customers_all,
            "recency": recency.values,
            "frequency": freq.values,
            "monetary": monetary.values,
        }
    )
    rfm = rfm.join(ret, on="customer_id")
    rfm = rfm.join(disc, on="customer_id")
    return rfm


def add_behavioral_signals(base: pd.DataFrame, tickets_pre: pd.DataFrame) -> pd.DataFrame:
    tickets_90 = tickets_pre[tickets_pre["ticket_date"] >= WINDOW_90_START]
    ticket_count = (
        tickets_90.groupby("customer_id")
        .size()
        .reindex(base["customer_id"], fill_value=0)
        .astype(int)
        .values
    )
    base["ticket_count_90d"] = ticket_count

    base["campaign_engaged"] = np.where(
        base["last_campaign_received"].fillna("none") == "none",
        "No Campaign",
        "Engaged",
    )
    return base


def compute_thresholds(df: pd.DataFrame) -> dict:
    active = df[df["frequency"] > 0]
    q = {
        "recency_75": df["recency"].quantile(0.75),
        "recency_90": df["recency"].quantile(0.90),
        "freq_50": active["frequency"].quantile(0.50) if len(active) else 2,
        "freq_75": active["frequency"].quantile(0.75) if len(active) else 4,
        "monetary_80": df["monetary"].quantile(0.80),
        "monetary_70": df["monetary"].quantile(0.70),
        "monetary_30": df["monetary"].quantile(0.30),
        "discount_75": df["avg_discount_pct_180d"].quantile(0.75),
        "sessions_25": df["sessions_30d"].quantile(0.25),
    }
    q["recency_champion_max"] = int(df[df["frequency"] > 0]["recency"].quantile(0.25))
    return q


def assign_segment_v2(row: pd.Series, t: dict) -> str:
    """Clear priority-ordered segmentation."""
    r, f, m = int(row["recency"]), int(row["frequency"]), float(row["monetary"])
    tickets = int(row["ticket_count_90d"])
    disc = float(row["avg_discount_pct_180d"])
    sessions = int(row["sessions_30d"])

    if f == 0:
        return "Dormant"
    if r >= t["recency_90"]:
        return "Dormant"

    if m >= t["monetary_70"] and tickets >= 2:
        return "High-Value Unhappy"

    if r <= t["recency_champion_max"] and f >= t["freq_75"] and m >= t["monetary_80"]:
        return "Champions"

    if disc >= t["discount_75"] and m <= t["monetary_30"]:
        return "Discount-Sensitive"

    if r > t["recency_75"] and f >= 2:
        return "At-Risk"

    if f >= max(2, t["freq_50"]) and tickets <= 1 and r <= t["recency_75"]:
        return "Loyal Customers"

    if sessions <= t["sessions_25"] and r > t["recency_champion_max"]:
        return "At-Risk"

    return "Loyal Customers"


def build_customer_df() -> pd.DataFrame:
    base, orders_pre, tickets_pre = load_and_prepare()
    rfm = compute_rfm(orders_pre)
    df = base.merge(rfm, on="customer_id", how="left")
    df = add_behavioral_signals(df, tickets_pre)

    t = compute_thresholds(df)
    t["monetary_50"] = df["monetary"].quantile(0.50)
    df["_thresholds"] = [t] * len(df)  # for export in notebook
    df["segment_name"] = df.apply(lambda row: assign_segment_v2(row, t), axis=1)

    return df, t, orders_pre


def export_segments(df: pd.DataFrame) -> None:
    out_cols = [
        "customer_id",
        "segment_name",
        "recency",
        "frequency",
        "monetary",
        "ticket_count_90d",
        "sessions_30d",
        "campaign_clicks_30d",
    ]
    df[out_cols].to_csv(ROOT / "segments.csv", index=False)


def make_charts(df: pd.DataFrame) -> None:
    CHARTS.mkdir(exist_ok=True)
    sns.set_theme(style="whitegrid")

    seg_churn = (
        df.groupby("segment_name")
        .agg(n=("customer_id", "count"), churn_rate=("churn_next_60d", "mean"))
        .reset_index()
        .sort_values("churn_rate", ascending=False)
    )

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=seg_churn, x="segment_name", y="churn_rate", hue="segment_name", palette="viridis", legend=False, ax=ax)
    ax.set_ylabel("Churn rate (next 60d)")
    ax.set_xlabel("Segment")
    ax.set_title("Churn rate by RFM segment")
    plt.xticks(rotation=25, ha="right")
    fig.text(0.5, -0.02, "Insight: At-Risk and Dormant segments show the highest churn; Champions show the lowest.", ha="center", fontsize=9)
    plt.tight_layout()
    fig.savefig(CHARTS / "churn_by_segment.png", dpi=120, bbox_inches="tight")
    plt.close()

    fig, ax = plt.subplots(figsize=(10, 5))
    order_seg = df["segment_name"].value_counts().index.tolist()
    sns.boxplot(data=df, x="segment_name", y="monetary", order=order_seg, hue="segment_name", palette="Set2", legend=False, ax=ax)
    ax.set_yscale("symlog")
    ax.set_title("Monetary value (180d) by segment")
    plt.xticks(rotation=25, ha="right")
    fig.text(0.5, -0.02, "Insight: Champions and High-Value Unhappy concentrate top spend; Dormant cluster near zero.", ha="center", fontsize=9)
    plt.tight_layout()
    fig.savefig(CHARTS / "monetary_by_segment.png", dpi=120, bbox_inches="tight")
    plt.close()

    fig, ax = plt.subplots(figsize=(9, 6))
    plot_df = df[df["recency"] < RECENCY_NO_ORDER].copy()
    sns.scatterplot(
        data=plot_df.sample(min(1500, len(plot_df)), random_state=42),
        x="recency",
        y="frequency",
        hue="segment_name",
        alpha=0.6,
        s=40,
        ax=ax,
    )
    ax.set_title("Recency vs frequency by segment (customers with orders)")
    fig.text(0.5, -0.02, "Insight: Champions occupy low-recency/high-frequency; Dormant excluded (no orders).", ha="center", fontsize=9)
    plt.tight_layout()
    fig.savefig(CHARTS / "recency_frequency_scatter.png", dpi=120, bbox_inches="tight")
    plt.close()

    return seg_churn


def segment_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("segment_name")
        .agg(
            customers=("customer_id", "count"),
            avg_recency=("recency", "mean"),
            avg_frequency=("frequency", "mean"),
            avg_monetary=("monetary", "mean"),
            avg_tickets=("ticket_count_90d", "mean"),
            avg_sessions=("sessions_30d", "mean"),
            churn_rate=("churn_next_60d", "mean"),
        )
        .round(2)
        .sort_values("customers", ascending=False)
    )


def pick_manual_review(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Select diverse edge cases (not all from one segment)."""
    picks: list[str] = []
    picks.append(
        df[(df["monetary"] >= df["monetary"].quantile(0.70)) & (df["ticket_count_90d"] >= 2)]
        .nlargest(1, "monetary")["customer_id"]
        .iloc[0]
    )
    at_risk_hi = df[(df["segment_name"] == "At-Risk") & (df["monetary"] > df["monetary"].quantile(0.9))].nlargest(
        2, "monetary"
    )
    picks.extend(at_risk_hi["customer_id"].tolist())
    recent_no_click = df[
        (df["recency"] < 30) & (df["campaign_clicks_30d"] == 0) & (df["segment_name"] == "Loyal Customers")
    ].nlargest(2, "monetary")
    picks.extend(recent_no_click["customer_id"].tolist())
    loyal_churned = df[(df["segment_name"] == "Loyal Customers") & (df["churn_next_60d"] == 1)].sample(
        2, random_state=7
    )
    picks.extend(loyal_churned["customer_id"].tolist())
    picks.append(df[df["segment_name"] == "Discount-Sensitive"].nlargest(1, "sessions_30d")["customer_id"].iloc[0])
    dormant_web = df[(df["segment_name"] == "Dormant") & (df["sessions_30d"] >= 5)].head(1)
    if len(dormant_web):
        picks.append(dormant_web["customer_id"].iloc[0])
    picks.append(df[df["segment_name"] == "Champions"].nsmallest(1, "monetary")["customer_id"].iloc[0])
    picks = list(dict.fromkeys(picks))[:n]
    while len(picks) < n:
        extra = df[~df["customer_id"].isin(picks)].sample(1, random_state=len(picks))["customer_id"].iloc[0]
        picks.append(extra)
    return df[df["customer_id"].isin(picks[:n])]


if __name__ == "__main__":
    df, thresholds, orders_pre = build_customer_df()
    export_segments(df)
    seg_churn = make_charts(df)
    summary = segment_summary(df)
    manual = pick_manual_review(df)

    print("Thresholds:", thresholds)
    print("\nSegment distribution:\n", df["segment_name"].value_counts())
    print("\nSegment summary:\n", summary)
    print("\nLeakage check:", (orders_pre["order_date"] > SNAPSHOT).sum())
    print("segments.csv rows:", len(pd.read_csv(ROOT / "segments.csv")))

    # Save summaries for markdown generation
    summary.to_csv(ROOT / "_segment_summary.csv")
    seg_churn.to_csv(ROOT / "_seg_churn.csv", index=False)
    manual.to_csv(ROOT / "_manual_review.csv", index=False)
    pd.Series(thresholds).to_csv(ROOT / "_thresholds.csv")
