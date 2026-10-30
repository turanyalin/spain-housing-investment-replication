# EU country-by-year panel

The frozen baseline contains **656 observations, 27 countries, and 29 years**. The target is the current EU27 membership cohort, followed retrospectively over annual levels from 1995 through 2024. The primary growth sample is 1996–2024. Historical EU accession is not a treatment variable.

## Source snapshot

[`raw/download_manifest.json`](raw/download_manifest.json) contains the exact URLs, UTC retrieval times, response sizes, and SHA-256 hashes for 31 sources:

- Eurostat `nama_10_a64_p5`: annual, `unit=CLV20_MEUR`, `nace_r2=C`, `na_item=P51G`, separately selecting `asset10=N11G`, `N11MG`, and `N117G` for all 27 countries.
- Eurostat `nama_10_gdp`: annual, `unit=CLV20_MEUR`, `na_item=B1GQ`, with the same cohort and window.
- BIS real residential property price indices, retrieved as the FRED series `Q<ISO2>R628BIS`. Eurostat Greece `EL` maps to BIS/FRED `GR`.

The [BIS selected indicators](https://data.bis.org/topics/RPP) are designed to improve cross-country comparability, but national coverage and compilation still differ. Provider rights remain applicable: [BIS permitted use](https://data.bis.org/help/legal), [Eurostat data policy](https://ec.europa.eu/eurostat/about-us/policies/copyright), and source notices on the FRED series pages.

## Ingestion and sample construction

`data.py` validates the source hashes, decodes Eurostat JSON-stat dimensions, and merges sources one-to-one on country and year. It retains a complete 27 × 30 calendar grid before computing changes. Annual house prices require four distinct observed quarters; partial years remain missing. A missing level also makes the adjacent growth change missing, and lagged growth never crosses a country boundary or closes a missing year.

`output/panel_data.csv` retains levels, growth rates, lags, quarter counts, Eurostat flags, and baseline eligibility. `output/country_coverage.csv` records usable growth counts, first and last years, omitted years, and download errors. All 31 sources succeeded for this snapshot. The baseline has 656 complete manufacturing/house/GDP growth observations; alternative outcomes can have different coverage.

## Models and inference

`models.py` uses statsmodels OLS with explicit `C(country)` and `C(year)` indicators. Model P1 includes house-price growth, P2 adds GDP growth, and P3 adds lagged house-price growth. P1 and P2 use the same complete-case sample. No pandemic dummy is included because year effects already span it. Country singletons are removed after any sample restriction.

The primary covariance uses [`cov_cluster_2groups`](https://www.statsmodels.org/devel/generated/statsmodels.stats.sandwich_covariance.cov_cluster_2groups.html) with `use_correction=True`: country covariance plus year covariance minus country-year intersection covariance. Each component uses `G/(G−1) × (N−1)/(N−K)`, with K counting the complete estimated dummy-variable design. Inference uses Student's t with `min(country clusters, year clusters)−1` reference degrees of freedom; the country-only comparison uses country clusters minus one. These are approximate finite-cluster inference conventions.

The nine sensitivities change the outcome to equipment or intellectual property, omit Spain, use pre-2008 or post-2008 periods, omit 2020–2021, end in 2023, use a balanced 2010–2024 sample, or cluster by country only. The balanced sample has 375 observations in 25 countries. A separate leave-one-country-out exercise covers all 27 possible omissions. Sensitivity p-values are unadjusted for multiplicity.

## Run and inspect

```bash
python -m panel.run
python -m panel.verify
```

Run these from the repository root after installing `requirements.txt`. `run.py` coordinates ingestion, estimation, JSON/CSV exports, four LaTeX tables, numerical-text macros, and two vector figures. `verify.py` checks all 12 models using:

1. Iterative alternating country/year projections, independently reproducing the dummy-variable slope estimates in the unbalanced panel.
2. Direct aggregation of country, year, and intersection score totals, reproducing the reported covariance matrices independently of the covariance API.

The root `python reproduce.py` additionally checks frozen numerical references and the original Spain analysis. Unit tests run with `python -m unittest discover -s tests -v`.

## Repository structure

| File | Responsibility |
| --- | --- |
| `download.py` | Explicit source acquisition; no downloads occur during normal reproduction |
| `data.py` | Source validation, calendar-safe ingestion, merge, growth, and coverage |
| `models.py` | Fixed-effects specifications and clustered inference |
| `reporting.py` | Tidy results, manuscript table snippets, text macros, and figures |
| `run.py` | Short pipeline entry point |
| `verify.py` | Independent slope and covariance checks |
| `source_manifest.json` | Code hashes, archived download-manifest hash, settings, and software versions |
| `output/` | Frozen numerical reference outputs and regenerated manuscript assets |
