from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "metro_year_affordability.csv"
SUMMARY_PATH = ROOT / "data" / "processed" / "metro_affordability_summary.csv"


st.set_page_config(page_title="Housing Affordability Index", layout="wide")


@st.cache_data
def load_data():
    affordability = pd.read_csv(DATA_PATH)
    summary = pd.read_csv(SUMMARY_PATH)
    return affordability, summary


st.title("Zillow & Census Housing Affordability Index")
st.caption("Metro-level price-to-income analysis using Zillow ZHVI and Census ACS median household income.")

if not DATA_PATH.exists():
    st.warning("Processed data not found. Run `python scripts/build_dataset.py` first.")
    st.stop()

affordability, summary = load_data()
income_source = affordability["income_source"].iloc[0]
if "Demo fallback" in income_source:
    st.info(
        "This local build is using a demo fallback income panel because Census API access was unavailable. "
        "Set CENSUS_API_KEY and rerun `python scripts/build_dataset.py` for official Census ACS income."
    )
else:
    st.success(f"Income source: {income_source}")
metros = sorted(affordability["metro"].unique())
default_metros = [m for m in ["Austin, TX", "Miami, FL", "Phoenix, AZ", "Seattle, WA", "Dallas, TX"] if m in metros]
selected = st.sidebar.multiselect("Metros", metros, default=default_metros or metros[:5])
years = sorted(affordability["year"].unique())
year_range = st.sidebar.slider("Year range", min_value=min(years), max_value=max(years), value=(min(years), max(years)))

filtered = affordability[
    affordability["metro"].isin(selected)
    & affordability["year"].between(year_range[0], year_range[1])
]

latest_year = affordability["year"].max()
latest = affordability[affordability["year"] == latest_year]
summary_latest = summary.copy()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Metros analyzed", f"{affordability['metro'].nunique():,}")
col2.metric("Years", f"{affordability['year'].min()}-{affordability['year'].max()}")
col3.metric("Median latest index", f"{latest['price_to_income_index'].median():.1f}x")
col4.metric("Worst latest index", f"{latest['price_to_income_index'].max():.1f}x")

st.subheader("Price-to-Income Index Trend")
fig = px.line(
    filtered,
    x="year",
    y="price_to_income_index",
    color="metro",
    markers=True,
    labels={"price_to_income_index": "Home value / median household income", "year": "Year"},
)
st.plotly_chart(fig, width="stretch")

left, right = st.columns([1, 1])
with left:
    st.subheader("Latest Metro Ranking")
    rank = latest.sort_values("price_to_income_index", ascending=False).head(20)
    fig_rank = px.bar(
        rank.sort_values("price_to_income_index"),
        x="price_to_income_index",
        y="metro",
        orientation="h",
        labels={"price_to_income_index": "Price-to-income index", "metro": ""},
    )
    st.plotly_chart(fig_rank, width="stretch")

with right:
    st.subheader("Largest Burden Increase")
    top = summary_latest.sort_values("index_change_pct", ascending=False).head(20)
    fig_top = px.bar(
        top.sort_values("index_change_pct"),
        x="index_change_pct",
        y="metro",
        orientation="h",
        labels={"index_change_pct": "2018-2024 change (%)", "metro": ""},
    )
    st.plotly_chart(fig_top, width="stretch")

st.subheader("Metro Detail Table")
display = affordability[affordability["metro"].isin(selected)].copy()
display["zhvi"] = display["zhvi"].round(0)
display["median_household_income"] = display["median_household_income"].round(0)
display["price_to_income_index"] = display["price_to_income_index"].round(2)
st.dataframe(display, width="stretch")
