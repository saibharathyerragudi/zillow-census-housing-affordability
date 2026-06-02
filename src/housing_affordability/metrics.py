from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm


def build_affordability_table(zhvi: pd.DataFrame, income: pd.DataFrame) -> pd.DataFrame:
    merged = zhvi.merge(
        income[["metro_key", "year", "median_household_income", "income_source"]],
        on=["metro_key", "year"],
        how="inner",
    )
    merged["price_to_income_index"] = merged["zhvi"] / merged["median_household_income"]
    merged["zhvi_yoy_pct"] = merged.groupby("metro")["zhvi"].pct_change() * 100
    merged["income_yoy_pct"] = merged.groupby("metro")["median_household_income"].pct_change() * 100
    merged["affordability_burden_yoy_pct"] = merged.groupby("metro")["price_to_income_index"].pct_change() * 100
    cols = [
        "RegionID",
        "SizeRank",
        "metro",
        "StateName",
        "year",
        "zhvi",
        "median_household_income",
        "price_to_income_index",
        "zhvi_yoy_pct",
        "income_yoy_pct",
        "affordability_burden_yoy_pct",
        "income_source",
    ]
    return merged[cols].sort_values(["SizeRank", "year"]).reset_index(drop=True)


def build_metro_summary(affordability: pd.DataFrame) -> pd.DataFrame:
    first_year = affordability["year"].min()
    last_year = affordability["year"].max()
    first = affordability[affordability["year"] == first_year][["metro", "price_to_income_index", "zhvi", "median_household_income"]]
    last = affordability[affordability["year"] == last_year][["metro", "price_to_income_index", "zhvi", "median_household_income", "StateName"]]
    summary = first.merge(last, on="metro", suffixes=(f"_{first_year}", f"_{last_year}"))
    summary["index_change"] = summary[f"price_to_income_index_{last_year}"] - summary[f"price_to_income_index_{first_year}"]
    summary["index_change_pct"] = summary["index_change"] / summary[f"price_to_income_index_{first_year}"] * 100
    return summary.sort_values("index_change_pct", ascending=False).reset_index(drop=True)


def estimate_trends(affordability: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for metro, group in affordability.groupby("metro"):
        if group["year"].nunique() < 3:
            continue
        x = sm.add_constant(group["year"] - group["year"].min())
        y = group["price_to_income_index"]
        model = sm.OLS(y, x, missing="drop").fit()
        rows.append(
            {
                "metro": metro,
                "annual_index_slope": float(model.params.iloc[1]),
                "trend_r2": float(model.rsquared),
                "trend_pvalue": float(model.pvalues.iloc[1]),
            }
        )
    return pd.DataFrame(rows).sort_values("annual_index_slope", ascending=False)


def write_sqlite(path: Path, tables: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        for name, frame in tables.items():
            frame.to_sql(name, conn, if_exists="replace", index=False)


def classify_affordability(index: float) -> str:
    if pd.isna(index):
        return "Unknown"
    if index < 3:
        return "Affordable"
    if index < 5:
        return "Stretched"
    if index < 7:
        return "Severely stretched"
    return "Extremely unaffordable"

