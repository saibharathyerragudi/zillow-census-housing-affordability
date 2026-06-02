# Methodology

## Metric

The core metric is:

```text
price_to_income_index = Zillow metro ZHVI / Census median household income
```

An index of `6.5x` means the typical home value is 6.5 times the annual median household income for that metro and year.

## Interpretation

When the index rises, the housing burden increases and affordability worsens. For example, moving from `6.5x` to `11.0x` is a burden increase of:

```text
(11.0 - 6.5) / 6.5 = 69.2%
```

That should be described as a roughly 69% increase in price-to-income burden, not a 69% decline from 6.5x to 11x.

## Data Sources

- Zillow Research: metro-level ZHVI monthly time series
- U.S. Census ACS: median household income using variable `B19013_001E`

## Trend Model

For each metro, the project estimates a simple Statsmodels OLS trend:

```text
price_to_income_index ~ year
```

The slope shows the average annual change in affordability burden.

