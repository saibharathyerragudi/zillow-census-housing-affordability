from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from housing_affordability.config import FIGURES_DIR, PROCESSED_DIR, RAW_DIR, SQL_DIR, TOP_METRO_COUNT
from housing_affordability.ingest import (
    build_demo_income_from_zillow,
    download_zillow_zhvi,
    fetch_census_income,
    load_sample_income,
    load_zillow_annual,
)
from housing_affordability.metrics import build_affordability_table, build_metro_summary, estimate_trends, write_sqlite


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    SQL_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    zillow_path = download_zillow_zhvi(RAW_DIR / "zillow_metro_zhvi.csv")
    zhvi = load_zillow_annual(zillow_path, top_n=TOP_METRO_COUNT)

    try:
        income = fetch_census_income()
        income_status = "Census ACS API"
    except Exception as exc:
        print(f"Census API unavailable, using demo fallback income panel: {exc}")
        income = build_demo_income_from_zillow(zhvi)
        income_status = "Demo fallback income estimate"

    affordability = build_affordability_table(zhvi, income)
    if affordability.empty:
        income = load_sample_income()
        income_status = "Seeded fallback income sample"
        affordability = build_affordability_table(zhvi, income)

    summary = build_metro_summary(affordability)
    trends = estimate_trends(affordability)
    summary = summary.merge(trends, on="metro", how="left")

    affordability.to_csv(PROCESSED_DIR / "metro_year_affordability.csv", index=False)
    summary.to_csv(PROCESSED_DIR / "metro_affordability_summary.csv", index=False)
    summary.head(25).to_csv(PROCESSED_DIR / "top_worsening_affordability.csv", index=False)
    write_sqlite(
        SQL_DIR / "housing_affordability.sqlite",
        {
            "metro_year_affordability": affordability,
            "metro_affordability_summary": summary,
            "top_worsening_affordability": summary.head(25),
        },
    )

    print(f"Rows: {len(affordability):,}")
    print(f"Metros: {affordability['metro'].nunique():,}")
    print(f"Income source: {income_status}")
    print(f"Wrote processed data to {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
