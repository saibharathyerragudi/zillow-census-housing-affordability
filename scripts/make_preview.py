from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import matplotlib.pyplot as plt
import pandas as pd

from housing_affordability.config import FIGURES_DIR, PROCESSED_DIR


def main() -> None:
    data_path = PROCESSED_DIR / "metro_year_affordability.csv"
    summary_path = PROCESSED_DIR / "metro_affordability_summary.csv"
    affordability = pd.read_csv(data_path)
    summary = pd.read_csv(summary_path)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    selected = ["Austin, TX", "Miami, FL", "Phoenix, AZ", "Seattle, WA", "Dallas, TX"]
    subset = affordability[affordability["metro"].isin(selected)]
    top = summary.sort_values("index_change_pct", ascending=False).head(10)

    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    fig.patch.set_facecolor("#f8fafc")
    for metro, group in subset.groupby("metro"):
        axes[0].plot(group["year"], group["price_to_income_index"], marker="o", label=metro)
    axes[0].set_title("Price-to-Income Index Trend", fontsize=13, weight="bold")
    axes[0].set_xlabel("Year")
    axes[0].set_ylabel("Home value / median income")
    axes[0].legend(frameon=False, fontsize=9)
    axes[0].grid(alpha=0.25)

    top.sort_values("index_change_pct").plot(
        kind="barh",
        x="metro",
        y="index_change_pct",
        ax=axes[1],
        color="#dc2626",
        legend=False,
    )
    axes[1].set_title("Largest Affordability Burden Increase", fontsize=13, weight="bold")
    axes[1].set_xlabel("Index change, 2018-2024 (%)")
    axes[1].set_ylabel("")
    axes[1].grid(axis="x", alpha=0.25)
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
    income_source = affordability["income_source"].iloc[0]
    fig.suptitle("Housing Affordability Index Preview", fontsize=18, weight="bold", color="#0f172a")
    fig.text(
        0.5,
        0.01,
        f"Income source in this build: {income_source}. Set CENSUS_API_KEY for official Census ACS ingestion.",
        ha="center",
        fontsize=9,
        color="#64748b",
    )
    fig.tight_layout(rect=[0, 0.04, 1, 0.95])
    out = FIGURES_DIR / "housing_affordability_preview.png"
    fig.savefig(out, dpi=180, bbox_inches="tight")
    print(out)


if __name__ == "__main__":
    main()
