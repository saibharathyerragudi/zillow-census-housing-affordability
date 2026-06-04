from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "metro_year_affordability.csv"
SUMMARY_PATH = ROOT / "data" / "processed" / "metro_affordability_summary.csv"

ACCENT = "#22c7c4"
WARNING = "#cc5362"
YELLOW = "#d8bd3b"
TEXT = "#1f2937"
MUTED = "#667085"
PANEL = "#ffffff"
GRID = "#e5e7eb"
CHARCOAL = "#303236"


st.set_page_config(page_title="Housing Affordability Index", layout="wide")


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    affordability = pd.read_csv(DATA_PATH)
    summary = pd.read_csv(SUMMARY_PATH)
    return affordability, summary


def money(value: float) -> str:
    if pd.isna(value):
        return "n/a"
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    return f"${value / 1_000:.0f}K"


def number(value: float, suffix: str = "") -> str:
    if pd.isna(value):
        return "n/a"
    return f"{value:,.1f}{suffix}"


def delta_text(value: float) -> str:
    if pd.isna(value):
        return "n/a"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.1f}%"


def band(index: float) -> str:
    if index >= 6:
        return "Severely stretched"
    if index >= 4.5:
        return "Stretched"
    if index >= 3.5:
        return "Watchlist"
    return "Relatively affordable"


def metric_card(label: str, value: str, detail: str, tone: str = ACCENT) -> None:
    st.markdown(
        f"""
        <div class="metric-card" style="--tone:{tone}">
          <span>{label}</span>
          <strong>{value}</strong>
          <small>{detail}</small>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_label(text: str) -> None:
    st.markdown(f'<div class="section-label">{text}</div>', unsafe_allow_html=True)


st.markdown(
    """
    <style>
      :root {
        --bg: #f4f6f8;
        --panel: #ffffff;
        --panel-soft: #f8fafc;
        --line: #d8dee8;
        --text: #1f2937;
        --muted: #667085;
        --accent: #22c7c4;
        --warning: #d85b6a;
      }
      .stApp {
        background: var(--bg);
        color: var(--text);
      }
      [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid var(--line);
      }
      [data-testid="stSidebar"] * {
        color: var(--text);
      }
      .block-container {
        padding-top: 2.25rem;
        padding-bottom: 4rem;
        max-width: 1380px;
      }
      .report-header {
        display: flex;
        justify-content: space-between;
        gap: 28px;
        align-items: flex-start;
        border: 1px solid var(--line);
        background: #ffffff;
        border-radius: 10px;
        padding: 22px 26px;
        margin-bottom: 22px;
        box-shadow: 0 12px 30px rgba(16,24,40,0.06);
      }
      .report-meta {
        display: flex;
        justify-content: flex-end;
        flex-wrap: wrap;
        gap: 8px;
        min-width: 260px;
      }
      .report-meta span {
        border: 1px solid var(--line);
        background: var(--panel-soft);
        border-radius: 999px;
        padding: 7px 10px;
        color: var(--muted);
        font-size: 0.78rem;
        font-weight: 750;
      }
      .eyebrow, .section-label {
        color: var(--accent);
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.15em;
        text-transform: uppercase;
      }
      .report-header h1 {
        color: var(--text);
        font-size: clamp(1.85rem, 3vw, 2.8rem);
        line-height: 1.02;
        margin: 8px 0 10px;
        letter-spacing: -0.03em;
      }
      .report-header p {
        color: var(--muted);
        font-size: 0.98rem;
        max-width: 760px;
      }
      .metric-card {
        min-height: 118px;
        border: 1px solid #2f3237;
        border-top: 3px solid var(--tone);
        background: #303236;
        border-radius: 8px;
        padding: 17px 18px 15px;
        box-shadow: 0 14px 26px rgba(16,24,40,0.08);
      }
      .metric-card span {
        display: block;
        color: #c4c8d0;
        font-size: 0.73rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 12px;
      }
      .metric-card strong {
        display: block;
        color: #ffffff;
        font-size: clamp(1.65rem, 3vw, 2.3rem);
        line-height: 1;
        margin-bottom: 12px;
      }
      .metric-card small {
        color: #d2d6de;
        font-size: 0.88rem;
        font-weight: 650;
      }
      .section-label {
        margin: 30px 0 12px;
      }
      .insight-card {
        border: 1px solid var(--line);
        background: #ffffff;
        border-radius: 8px;
        padding: 20px;
        min-height: 100%;
      }
      .insight-card h3 {
        color: var(--text);
        margin: 0 0 8px;
      }
      .insight-card p {
        color: var(--muted);
        margin: 0;
      }
      .stDataFrame {
        border: 1px solid var(--line);
        border-radius: 8px;
        overflow: hidden;
        background: #ffffff;
      }
      @media (max-width: 900px) {
        .report-header {
          display: block;
        }
        .report-meta {
          justify-content: flex-start;
          min-width: 0;
          margin-top: 14px;
        }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

if not DATA_PATH.exists():
    st.warning("Processed data not found. Run `python scripts/build_dataset.py` first.")
    st.stop()

affordability, summary = load_data()
metros = sorted(affordability["metro"].unique())
years = sorted(affordability["year"].unique())
latest_year = max(years)
first_year = min(years)
latest = affordability[affordability["year"] == latest_year].copy()
summary_latest = summary.copy()

default_metros = [
    metro
    for metro in ["Austin, TX", "Miami, FL", "Phoenix, AZ", "Seattle, WA", "Dallas, TX", "Tampa, FL"]
    if metro in metros
]

with st.sidebar:
    st.markdown("### Dashboard Controls")
    selected = st.multiselect("Compare metros", metros, default=default_metros or metros[:6])
    year_range = st.slider("Year range", min_value=first_year, max_value=latest_year, value=(first_year, latest_year))
    focus_metro = st.selectbox("Metro spotlight", selected or metros, index=0)
    top_n = st.slider("Ranking size", min_value=8, max_value=25, value=15, step=1)

if not selected:
    selected = [focus_metro]

filtered = affordability[
    affordability["metro"].isin(selected)
    & affordability["year"].between(year_range[0], year_range[1])
].copy()
focus_history = affordability[affordability["metro"] == focus_metro].sort_values("year")
focus_latest = focus_history[focus_history["year"] == latest_year].iloc[0]
focus_summary = summary_latest[summary_latest["metro"] == focus_metro].iloc[0]

income_source = affordability["income_source"].iloc[0]
st.markdown(
    f"""
    <div class="report-header">
      <div>
        <div class="eyebrow">Zillow + Census Housing Affordability Index</div>
        <h1>Housing affordability by metro</h1>
        <p>Price-to-income index, market rankings, and income vs. home value movement across U.S. metros.</p>
      </div>
      <div class="report-meta">
        <span>{first_year}-{latest_year}</span>
        <span>{affordability['metro'].nunique():,} metros</span>
        <span>{income_source.split(' - ')[0]}</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if "Demo fallback" in income_source:
    st.info(
        "Local build uses a demo fallback income panel because Census API access was unavailable. "
        "Set CENSUS_API_KEY and rerun the build script for official Census ACS income."
    )

worst_latest = latest.sort_values("price_to_income_index", ascending=False).iloc[0]
fastest_worse = summary_latest.sort_values("index_change_pct", ascending=False).iloc[0]
median_latest = latest["price_to_income_index"].median()
median_change = summary_latest["index_change_pct"].median()

k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_card("Metros analyzed", f"{affordability['metro'].nunique():,}", f"{first_year}-{latest_year} annual panel")
with k2:
    metric_card("Median latest index", number(median_latest, "x"), f"{delta_text(median_change)} median burden change", YELLOW)
with k3:
    metric_card("Highest burden", number(worst_latest["price_to_income_index"], "x"), str(worst_latest["metro"]), WARNING)
with k4:
    metric_card("Fastest worsening", delta_text(fastest_worse["index_change_pct"]), str(fastest_worse["metro"]), WARNING)

section_label("Trend Comparison")
trend = px.line(
    filtered,
    x="year",
    y="price_to_income_index",
    color="metro",
    markers=True,
    labels={"price_to_income_index": "Home value / median household income", "year": ""},
    color_discrete_sequence=["#2c7fb8", "#22a06b", "#7c5fb8", "#f08a24", "#cc5362", "#8f6d5d"],
)
trend.update_traces(line_width=2.8, marker_size=6)
trend.add_hrect(y0=4.5, y1=6, fillcolor=YELLOW, opacity=0.08, line_width=0)
trend.add_hrect(y0=6, y1=max(7, filtered["price_to_income_index"].max() + 0.3), fillcolor=WARNING, opacity=0.09, line_width=0)
trend.update_layout(
    template="plotly_white",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#ffffff",
    height=390,
    margin=dict(l=28, r=28, t=34, b=26),
    legend_title_text="",
    font_color=TEXT,
    xaxis=dict(gridcolor=GRID),
    yaxis=dict(gridcolor=GRID),
)
st.plotly_chart(trend, use_container_width=True)

left, right = st.columns([1.05, 0.95])
with left:
    section_label("Latest Burden Ranking")
    rank = latest.sort_values("price_to_income_index", ascending=False).head(top_n).sort_values("price_to_income_index")
    fig_rank = px.bar(
        rank,
        x="price_to_income_index",
        y="metro",
        orientation="h",
        labels={"price_to_income_index": "Price-to-income index", "metro": ""},
    )
    rank_colors = [WARNING if value >= 6 else CHARCOAL for value in rank["price_to_income_index"]]
    fig_rank.update_traces(marker_color=rank_colors)
    fig_rank.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        height=460,
        margin=dict(l=18, r=24, t=22, b=28),
        coloraxis_showscale=False,
        font_color=TEXT,
        xaxis=dict(gridcolor=GRID),
        yaxis=dict(gridcolor=GRID),
    )
    st.plotly_chart(fig_rank, use_container_width=True)

with right:
    section_label("Metro Spotlight")
    c1, c2 = st.columns(2)
    with c1:
        metric_card("Latest index", number(focus_latest["price_to_income_index"], "x"), band(focus_latest["price_to_income_index"]))
    with c2:
        metric_card("2018-2024 change", delta_text(focus_summary["index_change_pct"]), "Price-to-income movement", WARNING if focus_summary["index_change_pct"] > 0 else ACCENT)

    spotlight = go.Figure()
    spotlight.add_trace(
        go.Scatter(
            x=focus_history["year"],
            y=focus_history["zhvi"],
            mode="lines+markers",
            name="ZHVI",
        line=dict(color="#2c7fb8", width=3.2),
        marker=dict(size=7),
            yaxis="y1",
        )
    )
    spotlight.add_trace(
        go.Scatter(
            x=focus_history["year"],
            y=focus_history["median_household_income"],
            mode="lines+markers",
            name="Income",
        line=dict(color="#22a06b", width=2.8),
        marker=dict(size=6),
            yaxis="y2",
        )
    )
    spotlight.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        height=286,
        margin=dict(l=24, r=24, t=24, b=28),
        legend=dict(orientation="h", y=1.08),
        yaxis=dict(title="Home value", tickprefix="$", gridcolor=GRID),
        yaxis2=dict(title="Income", overlaying="y", side="right", tickprefix="$", showgrid=False),
        font_color=TEXT,
    )
    st.plotly_chart(spotlight, use_container_width=True)

section_label("Market Segmentation")
segmented = latest.copy()
segmented["affordability_band"] = segmented["price_to_income_index"].apply(band)
seg_summary = segmented.groupby("affordability_band", as_index=False).agg(
    metros=("metro", "count"),
    median_index=("price_to_income_index", "median"),
)
scatter_data = latest.merge(summary_latest[["metro", "index_change_pct"]], on="metro", how="left")

s1, s2 = st.columns([0.58, 0.42])
with s1:
    scatter = px.scatter(
        scatter_data,
        x="median_household_income",
        y="zhvi",
        size="price_to_income_index",
        color="index_change_pct",
        hover_name="metro",
        color_continuous_scale=[[0, "#8ab6f9"], [0.55, "#d9dce3"], [1, WARNING]],
        labels={
            "median_household_income": "Median household income",
            "zhvi": "Zillow Home Value Index",
            "index_change_pct": "2018-2024 change %",
        },
    )
    scatter.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        height=370,
        margin=dict(l=28, r=28, t=24, b=30),
        font_color=TEXT,
        xaxis=dict(gridcolor=GRID),
        yaxis=dict(gridcolor=GRID),
    )
    st.plotly_chart(scatter, use_container_width=True)

with s2:
    band_fig = px.bar(
        seg_summary,
        x="metros",
        y="affordability_band",
        orientation="h",
        labels={"metros": "Metro count", "affordability_band": "", "median_index": "Median index"},
    )
    band_colors = [WARNING if value >= 5.5 else "#3f434a" for value in seg_summary["median_index"]]
    band_fig.update_traces(marker_color=band_colors)
    band_fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        height=370,
        margin=dict(l=18, r=24, t=24, b=30),
        coloraxis_showscale=False,
        font_color=TEXT,
        xaxis=dict(gridcolor=GRID),
        yaxis=dict(gridcolor=GRID),
    )
    st.plotly_chart(band_fig, use_container_width=True)

section_label("Metro Detail Table")
display = affordability[affordability["metro"].isin(selected)].copy()
display["zhvi"] = display["zhvi"].map(money)
display["median_household_income"] = display["median_household_income"].map(money)
display["price_to_income_index"] = display["price_to_income_index"].map(lambda value: f"{value:.2f}x")
display["zhvi_yoy_pct"] = display["zhvi_yoy_pct"].map(lambda value: "" if pd.isna(value) else delta_text(value))
display["income_yoy_pct"] = display["income_yoy_pct"].map(lambda value: "" if pd.isna(value) else delta_text(value))
display = display[
    ["metro", "StateName", "year", "zhvi", "median_household_income", "price_to_income_index", "zhvi_yoy_pct", "income_yoy_pct"]
].rename(
    columns={
        "metro": "Metro",
        "StateName": "State",
        "year": "Year",
        "zhvi": "ZHVI",
        "median_household_income": "Median income",
        "price_to_income_index": "Index",
        "zhvi_yoy_pct": "Home value YoY",
        "income_yoy_pct": "Income YoY",
    }
)
st.dataframe(display, use_container_width=True, hide_index=True)
