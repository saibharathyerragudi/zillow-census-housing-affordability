# Data Notes

Raw data is intentionally excluded from Git and can be rebuilt with:

```bash
python scripts/build_dataset.py
```

Primary sources:

- Zillow Home Value Index metro CSV: `Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv`
- Census ACS median household income variable: `B19013_001E`

The pipeline attempts to fetch Census ACS data first. If the Census API redirects to `missing_key.html`, set:

```bash
export CENSUS_API_KEY="your_key"
```

If the Census API is unavailable in the local environment, the project creates a clearly labeled demo fallback income panel from the Zillow metro coverage so the Streamlit dashboard can still be reviewed across 50+ metros. Official analysis should be rebuilt with a Census API key.
