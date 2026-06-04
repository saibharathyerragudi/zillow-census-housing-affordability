from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Rectangle

from housing_affordability.config import FIGURES_DIR, PROCESSED_DIR


BG = "#f4f6f8"
PANEL = "#ffffff"
KPI = "#303236"
LINE = "#d8dee8"
TEXT = "#1f2937"
MUTED = "#667085"
ACCENT = "#22c7c4"
WARNING = "#cc5362"
YELLOW = "#d8bd3b"


def fmt_index(value: float) -> str:
    return f"{value:.1f}x"


def fmt_pct(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.1f}%"


def panel(fig, x: float, y: float, w: float, h: float) -> None:
    fig.patches.append(
        Rectangle((x, y), w, h, transform=fig.transFigure, facecolor=PANEL, edgecolor=LINE, linewidth=1.1)
    )


def style_axis(ax) -> None:
    ax.set_facecolor(PANEL)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.grid(color="#dfe4eb", alpha=0.75)
    for spine in ax.spines.values():
        spine.set_color(LINE)


def draw_metric(fig, x: float, y: float, w: float, h: float, label: str, value: str, detail: str, tone: str) -> None:
    fig.patches.append(
        Rectangle((x, y), w, h, transform=fig.transFigure, facecolor=KPI, edgecolor="#26282c", linewidth=1.0)
    )
    fig.patches.append(
        Rectangle((x, y + h - 0.006), w, 0.006, transform=fig.transFigure, facecolor=tone, edgecolor=tone)
    )
    fig.text(x + 0.018, y + h - 0.032, label.upper(), color="#c4c8d0", fontsize=8, weight="bold")
    fig.text(x + 0.018, y + 0.043, value, color="#ffffff", fontsize=25, weight="bold")
    fig.text(x + 0.018, y + 0.018, detail, color="#d2d6de", fontsize=8, weight="bold")


def main() -> None:
    affordability = pd.read_csv(PROCESSED_DIR / "metro_year_affordability.csv")
    summary = pd.read_csv(PROCESSED_DIR / "metro_affordability_summary.csv")
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    selected = ["Austin, TX", "Miami, FL", "Phoenix, AZ", "Seattle, WA", "Dallas, TX", "Tampa, FL"]
    subset = affordability[affordability["metro"].isin(selected)]
    latest_year = int(affordability["year"].max())
    first_year = int(affordability["year"].min())
    latest = affordability[affordability["year"] == latest_year]
    top_burden = latest.sort_values("price_to_income_index", ascending=False).head(10)
    top_change = summary.sort_values("index_change_pct", ascending=False).iloc[0]
    worst = top_burden.iloc[0]

    fig = plt.figure(figsize=(16, 9), facecolor=BG)
    fig.text(0.045, 0.918, "ZILLOW + CENSUS HOUSING AFFORDABILITY INDEX", color=ACCENT, fontsize=10, weight="bold")
    fig.text(0.045, 0.878, "Housing affordability by metro", color=TEXT, fontsize=25, weight="bold")
    fig.text(
        0.045,
        0.842,
        "Price-to-income index, market rankings, and income vs. home value movement across U.S. metros.",
        color=MUTED,
        fontsize=11,
    )
    fig.patches.append(Rectangle((0.755, 0.865), 0.07, 0.035, transform=fig.transFigure, facecolor=PANEL, edgecolor=LINE, linewidth=1.0))
    fig.patches.append(Rectangle((0.835, 0.865), 0.08, 0.035, transform=fig.transFigure, facecolor=PANEL, edgecolor=LINE, linewidth=1.0))
    fig.patches.append(Rectangle((0.925, 0.865), 0.065, 0.035, transform=fig.transFigure, facecolor=PANEL, edgecolor=LINE, linewidth=1.0))
    fig.text(0.768, 0.877, f"{first_year}-{latest_year}", color=MUTED, fontsize=8, weight="bold")
    fig.text(0.848, 0.877, f"{affordability['metro'].nunique():,} metros", color=MUTED, fontsize=8, weight="bold")
    fig.text(0.942, 0.877, "Index", color=MUTED, fontsize=8, weight="bold")

    draw_metric(fig, 0.045, 0.705, 0.205, 0.105, "Metros analyzed", f"{affordability['metro'].nunique():,}", f"{first_year}-{latest_year} annual panel", ACCENT)
    draw_metric(fig, 0.275, 0.705, 0.205, 0.105, "Median latest index", fmt_index(latest["price_to_income_index"].median()), "Latest metro median", YELLOW)
    draw_metric(fig, 0.505, 0.705, 0.205, 0.105, "Highest burden", fmt_index(worst["price_to_income_index"]), str(worst["metro"]), WARNING)
    draw_metric(fig, 0.735, 0.705, 0.22, 0.105, "Fastest worsening", fmt_pct(top_change["index_change_pct"]), str(top_change["metro"]), WARNING)

    ax_trend = fig.add_axes([0.045, 0.34, 0.58, 0.295])
    style_axis(ax_trend)
    for metro, group in subset.groupby("metro"):
        ax_trend.plot(group["year"], group["price_to_income_index"], marker="o", linewidth=2.2, label=metro)
    ax_trend.axhspan(4.5, 6.0, color=YELLOW, alpha=0.12)
    ax_trend.axhspan(6.0, max(7, subset["price_to_income_index"].max() + 0.4), color=WARNING, alpha=0.10)
    ax_trend.set_title("Price-to-Income Trend", loc="left", color=TEXT, fontsize=13, weight="bold", pad=12)
    ax_trend.set_ylabel("Home value / median income", color=MUTED, fontsize=9)
    ax_trend.legend(loc="upper left", ncols=3, frameon=False, fontsize=7, labelcolor=MUTED)

    ax_rank = fig.add_axes([0.675, 0.34, 0.28, 0.295])
    style_axis(ax_rank)
    rank = top_burden.sort_values("price_to_income_index")
    colors = [WARNING if value >= 6 else KPI for value in rank["price_to_income_index"]]
    ax_rank.barh(rank["metro"], rank["price_to_income_index"], color=colors)
    ax_rank.set_title("Latest Metro Ranking", loc="left", color=TEXT, fontsize=13, weight="bold", pad=12)
    ax_rank.set_xlabel("Price-to-income index", color=MUTED, fontsize=9)

    panel(fig, 0.045, 0.095, 0.28, 0.165)
    fig.text(0.065, 0.222, "Metro spotlight", color=MUTED, fontsize=8, weight="bold")
    fig.text(0.065, 0.188, "Austin, TX", color=TEXT, fontsize=18, weight="bold")
    austin = summary[summary["metro"] == "Austin, TX"]
    if not austin.empty:
        fig.text(0.065, 0.155, f"Burden change: {fmt_pct(austin.iloc[0]['index_change_pct'])}", color=WARNING, fontsize=11, weight="bold")
    fig.text(0.065, 0.128, "Data quality", color=MUTED, fontsize=8, weight="bold")
    fig.text(0.065, 0.106, f"{first_year}-{latest_year} annual data | {affordability['metro'].nunique():,} metros | source labeled", color=MUTED, fontsize=8)

    ax_scatter = fig.add_axes([0.38, 0.095, 0.575, 0.165])
    style_axis(ax_scatter)
    scatter = latest.merge(summary[["metro", "index_change_pct"]], on="metro", how="left")
    ax_scatter.scatter(
        scatter["median_household_income"],
        scatter["zhvi"],
        s=scatter["price_to_income_index"] * 16,
        c=scatter["index_change_pct"],
        cmap="coolwarm",
        alpha=0.7,
        edgecolor="#ffffff",
        linewidth=0.45,
    )
    ax_scatter.set_title("Income vs. Home Value Pressure", loc="left", color=TEXT, fontsize=13, weight="bold", pad=10)
    ax_scatter.set_xlabel("Median household income", color=MUTED, fontsize=9)
    ax_scatter.set_ylabel("Zillow Home Value Index", color=MUTED, fontsize=9)

    for out_name in ["housing_affordability_preview.png", "streamlit_dashboard.png"]:
        fig.savefig(FIGURES_DIR / out_name, dpi=180, bbox_inches="tight", facecolor=BG)
    print(FIGURES_DIR / "streamlit_dashboard.png")


if __name__ == "__main__":
    main()
