from __future__ import annotations

import io
import os
import re
from pathlib import Path

import pandas as pd
import requests

from housing_affordability.config import ANALYSIS_YEARS, RAW_DIR, ZILLOW_ZHVI_URL
from housing_affordability.sample_income import SAMPLE_INCOME_ROWS


def ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)


def normalize_metro_name(value: str) -> str:
    text = str(value).lower()
    text = re.sub(r"\b(metro area|micro area|metropolitan statistical area|micropolitan statistical area)\b", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def download_zillow_zhvi(path: Path | None = None) -> Path:
    ensure_dirs()
    out = path or RAW_DIR / "zillow_metro_zhvi.csv"
    if out.exists():
        return out

    response = requests.get(ZILLOW_ZHVI_URL, timeout=60)
    response.raise_for_status()
    out.write_bytes(response.content)
    return out


def load_zillow_annual(path: Path, years: list[int] | None = None, top_n: int = 75) -> pd.DataFrame:
    years = years or ANALYSIS_YEARS
    wide = pd.read_csv(path)
    wide = wide.sort_values("SizeRank").head(top_n).copy()
    id_cols = ["RegionID", "SizeRank", "RegionName", "RegionType", "StateName"]
    date_cols = [c for c in wide.columns if re.match(r"^\d{4}-\d{2}-\d{2}$", c)]
    long = wide[id_cols + date_cols].melt(id_vars=id_cols, var_name="date", value_name="zhvi")
    long["date"] = pd.to_datetime(long["date"])
    long["year"] = long["date"].dt.year
    annual = (
        long[long["year"].isin(years)]
        .groupby(id_cols + ["year"], as_index=False)["zhvi"]
        .mean()
    )
    annual["metro"] = annual["RegionName"]
    annual["metro_key"] = annual["metro"].map(normalize_metro_name)
    return annual


def fetch_census_income_year(year: int, survey: str = "acs1") -> pd.DataFrame:
    url = f"https://api.census.gov/data/{year}/acs/{survey}"
    params = {
        "get": "NAME,B19013_001E",
        "for": "metropolitan statistical area/micropolitan statistical area:*",
    }
    api_key = os.getenv("CENSUS_API_KEY")
    if api_key:
        params["key"] = api_key
    response = requests.get(url, params=params, timeout=45)
    response.raise_for_status()
    payload = response.json()
    frame = pd.DataFrame(payload[1:], columns=payload[0])
    frame["year"] = year
    frame["median_household_income"] = pd.to_numeric(frame["B19013_001E"], errors="coerce")
    frame["metro"] = frame["NAME"].str.replace(r"\s+(Metro|Micro) Area$", "", regex=True)
    frame["metro_key"] = frame["metro"].map(normalize_metro_name)
    frame["income_source"] = f"Census ACS {survey.upper()}"
    return frame[["metro", "metro_key", "year", "median_household_income", "income_source"]]


def fetch_census_income(years: list[int] | None = None) -> pd.DataFrame:
    rows = []
    for year in years or ANALYSIS_YEARS:
        surveys = ["acs1"] if year != 2020 else ["acs1", "acs5"]
        last_error = None
        for survey in surveys:
            try:
                rows.append(fetch_census_income_year(year, survey=survey))
                break
            except Exception as exc:  # API availability differs by year.
                last_error = exc
        if last_error and len(rows) == 0:
            raise last_error
    if not rows:
        raise RuntimeError("No Census income rows returned.")
    return pd.concat(rows, ignore_index=True)


def load_sample_income() -> pd.DataFrame:
    frame = pd.DataFrame(SAMPLE_INCOME_ROWS)
    frame["metro_key"] = frame["metro"].map(normalize_metro_name)
    frame["income_source"] = "Seeded fallback income sample"
    return frame


def build_demo_income_from_zillow(zhvi: pd.DataFrame) -> pd.DataFrame:
    """Create a 75-metro demo income panel when Census API access is unavailable.

    This is intentionally labeled as a demo fallback. It keeps the Streamlit app
    reviewable without a Census API key, but official analysis should be rebuilt
    with CENSUS_API_KEY set.
    """
    metros = zhvi[["metro", "metro_key", "SizeRank", "year", "zhvi"]].copy()
    metro_base = (
        metros[metros["year"] == metros["year"].min()]
        .sort_values("SizeRank")
        .assign(
            base_index=lambda d: 3.2 + (d["SizeRank"].clip(0, 75) / 75) * 2.8,
            base_income=lambda d: (d["zhvi"] / d["base_index"]).clip(52000, 145000),
        )[["metro", "metro_key", "base_income"]]
    )
    out = metros.merge(metro_base, on=["metro", "metro_key"], how="left")
    out["years_elapsed"] = out["year"] - out["year"].min()
    out["median_household_income"] = out["base_income"] * (1.045 ** out["years_elapsed"])
    out["income_source"] = "Demo fallback income estimate - replace with Census ACS API"
    return out[["metro", "metro_key", "year", "median_household_income", "income_source"]]
