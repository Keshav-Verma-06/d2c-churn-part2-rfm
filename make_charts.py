"""Generate chart PNGs using the project .venv (avoids broken Anaconda matplotlib)."""
import os

# Jupyter sets MPLBACKEND=matplotlib_inline; must override before import
os.environ["MPLBACKEND"] = "Agg"

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parent
CHARTS = ROOT / "charts"
RECENCY_NO_ORDER = 999


def main() -> None:
    seg = pd.read_csv(ROOT / "segments.csv")
    labels = pd.read_csv(ROOT / "churn_labels.csv")[["customer_id", "churn_next_60d"]]
    df = seg.merge(labels, on="customer_id", how="left")

    CHARTS.mkdir(exist_ok=True)
    sns.set_theme(style="whitegrid")

    seg_churn = df.groupby("segment_name")["churn_next_60d"].mean().reset_index()
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(
        data=seg_churn,
        x="segment_name",
        y="churn_next_60d",
        hue="segment_name",
        palette="viridis",
        legend=False,
        ax=ax,
    )
    ax.set_ylabel("Churn rate (next 60d)")
    ax.set_title("Churn rate by RFM segment")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    fig.savefig(CHARTS / "churn_by_segment.png", dpi=120, bbox_inches="tight")
    plt.close()

    fig, ax = plt.subplots(figsize=(10, 5))
    order_seg = df["segment_name"].value_counts().index.tolist()
    sns.boxplot(
        data=df,
        x="segment_name",
        y="monetary",
        order=order_seg,
        hue="segment_name",
        palette="Set2",
        legend=False,
        ax=ax,
    )
    ax.set_yscale("symlog")
    ax.set_title("Monetary value (180d) by segment")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    fig.savefig(CHARTS / "monetary_by_segment.png", dpi=120, bbox_inches="tight")
    plt.close()

    plot_df = df[df["recency"] < RECENCY_NO_ORDER].copy()
    if len(plot_df) > 1500:
        plot_df = plot_df.sample(1500, random_state=42)
    fig, ax = plt.subplots(figsize=(9, 6))
    sns.scatterplot(
        data=plot_df,
        x="recency",
        y="frequency",
        hue="segment_name",
        alpha=0.6,
        s=40,
        ax=ax,
    )
    ax.set_title("Recency vs frequency by segment")
    plt.tight_layout()
    fig.savefig(CHARTS / "recency_frequency_scatter.png", dpi=120, bbox_inches="tight")
    plt.close()

    print("Saved charts to", CHARTS)


if __name__ == "__main__":
    main()
