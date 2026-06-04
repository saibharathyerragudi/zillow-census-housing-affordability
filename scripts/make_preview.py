from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Rectangle

from housing_affordability.config import FIGURES_DIR, PROCESSED_DIR


BG = "#0b0c0f"
PANEL = "#151517"
LINE = "#2a2b31"
TEXT = "#f7f7f8"
MUTED = "#9a9aa3"
ACCENT = "#25d6d2"
WARNING = "#d94b5f"
YELLOW = "#f0d24a"


def fmt_index(value: float) -> str:
    return f"{value:.1f}x"


def fmt_pct(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.1f}%"


def style_axis(ax) -> None:
    ax.set_facecolor(PANEL)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.grid(color="#ffffff", alpha=0.08)
    for spine in ax.spines.values():
        spine.set_color(LINE)


def draw_metric(fig, x: float, y: float, w: float, h: float, label: str, value: str, detail: str, tone: str) -> None:
    fig.patches.append(
        Rectangle((x, y), w, h, transform=fig.transFigure, facecolor=PANEL, edgecolor=LINE, linewidth=1.2)
    )
    fig.patches.append(
        Rectangle((x, y + h - 0.006), w, 0.006, transform=fig.transFigure, facecolor=tone, edgecolor=tone)
    )
    fig.text(x + 0.018, y + h - 0.032, label.upper(), color=MUTED, fontsize=8, weight="bold")
    fig.text(x + 0.018, y + 0.042, value, color=TEXT, fontsize=25, weight="bold")
    fig.text(x + 0.018, y + 0.018, detail, color=MUTED, fontsize=8, weight="bold")


def main() -> None:
    data_path = PROCESSED_DIR / "metro_year_affordability.csv"
    summary_path = PROCESSED_DIR / "metro_affordability_summary.csv"
    affordability = pd.read_csv(data_path)
    summary = pd.read_csv(summary_path)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    selected = ["Austin, TX", "Miami, FL", "Phoenix, AZ", "Seattle, WA", "Dallas, TX", "Tampa, FL"]
    subset = affordability[affordability["metro"].isin(selected)]
    latest_year = int(affordability["year"].max())
    first_year = int(affordability["year"].min())
    latest = affordability[affordability["year"] == latest_year]
    top_burden = latest.sort_values("price_to_income_index", ascending=False).head(12)
    top_change = summary.sort_values("index_change_pct", ascending=False).head(8)
    worst = top_burden.iloc[0]
    fastest = top_change.iloc[0]

    fig = plt.figure(figsize=(16, 9), facecolor=BG)
    fig.text(0.035, 0.935, "ZILLOW + CENSUS HOUSING AFFORDABILITY INDEX", color=ACCENT, fontsize=10, weight="bold")
    fig.text(0.035, 0.885, "Metro affordability pressure, ranked and explained.", color=TEXT, fontsize=30, weight="bold")
    fig.text(
        0.035,
        0.845,
        "Price-to-income index across U.S. metros with trend movement, burden ranking, and market segmentation.",
        color=MUTED,
        fontsize=11,
    )

    draw_metric(fig, 0.035, 0.705, 0.21, 0.105, "Metros analyzed", f"{affordability['metro'].nunique():,}", f"{first_year}-{latest_year} annual panel", ACCENT)
    draw_metric(fig, 0.265, 0.705, 0.21, 0.105, "Median latest index", fmt_index(latest["price_to_income_index"].median()), "Latest metro median", YELLOW)
    draw_metric(fig, 0.495, 0.705, 0.21, 0.105, "Highest burden", fmt_index(worst["price_to_income_index"]), str(worst["metro"]), WARNING)
    draw_metric(fig, 0.725, 0.705, 0.24, 0.105, "Fastest worsening", fmt_pct(fastest["index_change_pct"]), str(fastest["metro"]), WARNING)

    ax_trend = fig.add_axes([0.035, 0.36, 0.58, 0.285])
    style_axis(ax_trend)
    for metro, group in subset.groupby("metro"):
        ax_trend.plot(group["year"], group["price_to_income_index"], marker="o", linewidth=2.4, label=metro)
    ax_trend.axhspan(4.5, 6.0, color=YELLOW, alpha=0.08)
    ax_trend.axhspan(6.0, max(7, subset["price_to_income_index"].max() + 0.4), color=WARNING, alpha=0.08)
    ax_trend.set_title("Trend Comparison", loc="left", color=TEXT, fontsize=13, weight="bold", pad=12)
    ax_trend.set_ylabel("Home value / median income", color=MUTED, fontsize=9)
    ax_trend.legend(loc="upper left", ncols=3, frameon=False, fontsize=7, labelcolor=MUTED)

    ax_rank = fig.add_axes([0.66, 0.36, 0.305, 0.285])
    style_axis(ax_rank)
    rank = top_burden.sort_values("price_to_income_index")
    colors = [WARNING if value >= 5.5 else YELLOW if value >= 4.5 else ACCENT for value in rank["price_to_income_index"]]
    ax_rank.barh(rank["metro"], rank["price_to_income_index"], color=colors)
    ax_rank.set_title("Latest Burden Ranking", loc="left", color=TEXT, fontsize=13, weight="bold", pad=12)
    ax_rank.set_xlabel("Price-to-income index", color=MUTED, fontsize=9)

    ax_change = fig.add_axes([0.035, 0.075, 0.45, 0.225])
    style_axis(ax_change)
    change = top_change.sort_values("index_change_pct")
    ax_change.barh(change["metro"], change["index_change_pct"], color=WARNING)
    ax_change.set_title("Largest Burden Increase", loc="left", color=TEXT, fontsize=13, weight="bold", pad=12)
    ax_change.set_xlabel("2018-2024 change (%)", color=MUTED, fontsize=9)

    ax_scatter = fig.add_axes([0.535, 0.075, 0.43, 0.225])
    style_axis(ax_scatter)
    scatter = latest.merge(summary[["metro", "index_change_pct"]], on="metro", how="left")
    ax_scatter.scatter(
        scatter["median_household_income"],
        scatter["zhvi"],
        s=scatter["price_to_income_index"] * 18,
        c=scatter["index_change_pct"],
        cmap="coolwarm",
        alpha=0.86,
        edgecolor="#ffffff",
        linewidth=0.35,
    )
    ax_scatter.set_title("Income vs. Home Value Pressure", loc="left", color=TEXT, fontsize=13, weight="bold", pad=12)
    ax_scatter.set_xlabel("Median household income", color=MUTED, fontsize=9)
    ax_scatter.set_ylabel("Zillow Home Value Index", color=MUTED, fontsize=9)

    for out_name in ["housing_affordability_preview.png", "streamlit_dashboard.png"]:
        fig.savefig(FIGURES_DIR / out_name, dpi=180, bbox_inches="tight", facecolor=BG)
    print(FIGURES_DIR / "streamlit_dashboard.png")


if __name__ == "__main__":
    main()
