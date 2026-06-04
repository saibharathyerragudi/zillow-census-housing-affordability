from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "metro_year_affordability.csv"
SUMMARY_PATH = ROOT / "data" / "processed" / "metro_affordability_summary.csv"

ACCENT = "#25d6d2"
WARNING = "#d94b5f"
YELLOW = "#f0d24a"
TEXT = "#f7f7f8"
MUTED = "#9a9aa3"
PANEL = "#151517"


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
        --bg: #0b0c0f;
        --panel: #151517;
        --panel-soft: #1d1d20;
        --line: rgba(255,255,255,0.1);
        --text: #f7f7f8;
        --muted: #9a9aa3;
        --accent: #25d6d2;
        --warning: #d94b5f;
      }
      .stApp {
        background:
          radial-gradient(circle at 18% 5%, rgba(37,214,210,0.18), transparent 28%),
          radial-gradient(circle at 88% 12%, rgba(217,75,95,0.13), transparent 28%),
          linear-gradient(180deg, #0b0c0f 0%, #07080a 100%);
        color: var(--text);
      }
      [data-testid="stSidebar"] {
        background: rgba(12,12,14,0.92);
        border-right: 1px solid var(--line);
      }
      [data-testid="stSidebar"] * {
        color: var(--text);
      }
      .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1500px;
      }
      .hero {
        border: 1px solid var(--line);
        background:
          linear-gradient(135deg, rgba(37,214,210,0.13), transparent 38%),
          linear-gradient(90deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
        border-radius: 8px;
        padding: 28px 30px;
        margin-bottom: 18px;
      }
      .eyebrow, .section-label {
        color: var(--accent);
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.15em;
        text-transform: uppercase;
      }
      .hero h1 {
        color: var(--text);
        font-size: clamp(2.2rem, 5vw, 4.7rem);
        line-height: 0.95;
        margin: 10px 0 12px;
        letter-spacing: -0.04em;
      }
      .hero p {
        color: var(--muted);
        font-size: 1.05rem;
        max-width: 940px;
      }
      .metric-card {
        min-height: 142px;
        border: 1px solid rgba(255,255,255,0.12);
        border-top: 3px solid var(--tone);
        background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.025));
        border-radius: 8px;
        padding: 18px 18px 16px;
        box-shadow: 0 18px 44px rgba(0,0,0,0.22);
      }
      .metric-card span {
        display: block;
        color: var(--muted);
        font-size: 0.73rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 12px;
      }
      .metric-card strong {
        display: block;
        color: var(--text);
        font-size: clamp(1.75rem, 4vw, 2.6rem);
        line-height: 1;
        margin-bottom: 12px;
      }
      .metric-card small {
        color: rgba(247,247,248,0.66);
        font-size: 0.88rem;
        font-weight: 650;
      }
      .section-label {
        margin: 18px 0 10px;
      }
      .insight-card {
        border: 1px solid var(--line);
        background: rgba(21,21,23,0.82);
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

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Zillow + Census Housing Affordability Index</div>
      <h1>Metro affordability pressure, ranked and explained.</h1>
      <p>Interactive housing analytics dashboard tracking price-to-income movement across U.S. metros, with trend slopes, burden change, and market-level risk bands.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

income_source = affordability["income_source"].iloc[0]
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
    color_discrete_sequence=px.colors.qualitative.Set2,
)
trend.update_traces(line_width=3, marker_size=7)
trend.add_hrect(y0=4.5, y1=6, fillcolor=YELLOW, opacity=0.08, line_width=0)
trend.add_hrect(y0=6, y1=max(7, filtered["price_to_income_index"].max() + 0.3), fillcolor=WARNING, opacity=0.09, line_width=0)
trend.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(255,255,255,0.02)",
    height=430,
    margin=dict(l=20, r=20, t=28, b=20),
    legend_title_text="",
    font_color=TEXT,
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
        color="price_to_income_index",
        color_continuous_scale=[[0, ACCENT], [0.6, YELLOW], [1, WARNING]],
        labels={"price_to_income_index": "Price-to-income index", "metro": ""},
    )
    fig_rank.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.02)",
        height=520,
        margin=dict(l=10, r=18, t=16, b=20),
        coloraxis_showscale=False,
        font_color=TEXT,
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
            line=dict(color=ACCENT, width=4),
            marker=dict(size=8),
            yaxis="y1",
        )
    )
    spotlight.add_trace(
        go.Scatter(
            x=focus_history["year"],
            y=focus_history["median_household_income"],
            mode="lines+markers",
            name="Income",
            line=dict(color=YELLOW, width=3),
            marker=dict(size=7),
            yaxis="y2",
        )
    )
    spotlight.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.02)",
        height=324,
        margin=dict(l=18, r=18, t=18, b=20),
        legend=dict(orientation="h", y=1.08),
        yaxis=dict(title="Home value", tickprefix="$", gridcolor="rgba(255,255,255,0.08)"),
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
        color_continuous_scale=[[0, ACCENT], [0.55, YELLOW], [1, WARNING]],
        labels={
            "median_household_income": "Median household income",
            "zhvi": "Zillow Home Value Index",
            "index_change_pct": "2018-2024 change %",
        },
    )
    scatter.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.02)",
        height=430,
        margin=dict(l=18, r=18, t=16, b=20),
        font_color=TEXT,
    )
    st.plotly_chart(scatter, use_container_width=True)

with s2:
    band_fig = px.bar(
        seg_summary,
        x="metros",
        y="affordability_band",
        orientation="h",
        color="median_index",
        color_continuous_scale=[[0, ACCENT], [0.6, YELLOW], [1, WARNING]],
        labels={"metros": "Metro count", "affordability_band": "", "median_index": "Median index"},
    )
    band_fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.02)",
        height=430,
        margin=dict(l=10, r=18, t=16, b=20),
        coloraxis_showscale=False,
        font_color=TEXT,
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
