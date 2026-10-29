# Analysis and statistical verification

This folder preserves the analysis and independent verification scripts from the LaTeX replication package. Both use paths relative to their own files, so they can be called from the repository root.

## Run the complete replication

Install the dependencies using the [root instructions](../README.md), then run `python reproduce.py` from the repository root. To run the original scripts separately:

```bash
python replication/analyze.py
python replication/verify_analysis.py
```

The second script must run after the first. Running them separately performs their internal assertions and statistical audit but omits the wrapper's input-hash and archived-output comparisons.

## Model definitions

All models include an intercept. Growth is `100 × (log(level_t) − log(level_t−1))`. `g_house` is real house-price growth, `g_gdp` is real GDP growth, and `covid` equals one in 2020 and zero otherwise. Unless specified below, the sample is 1996–2024 and the outcome is manufacturing investment growth.

| Model | Regressors besides the intercept | Variation | HAC lags |
| --- | --- | --- | --- |
| M1 | `g_house` | Main model | 1 |
| M2 | `g_house`, `g_gdp` | Main model | 1 |
| M3 | `g_house`, `g_gdp`, `covid` | Baseline conditional model | 1 |
| M4 | `g_house`, `g_gdp`, `covid`, `lag_house` | Lagged house-price growth; 1997–2024 | 1 |
| R1_equipment | `g_house`, `g_gdp`, `covid` | Equipment investment growth outcome | 1 |
| R2_ipp | `g_house`, `g_gdp`, `covid` | Intellectual property investment growth outcome | 1 |
| R3_pre2008 | `g_house`, `g_gdp` | 1996–2007 | 1 |
| R4_exclude_covid | `g_house`, `g_gdp` | Omit 2020 and 2021 | 1 |
| R5_hac2 | `g_house`, `g_gdp`, `covid` | Baseline with two HAC lags | 2 |
| R6_AR1 | `g_house`, `g_gdp`, `covid`, `lag_manufacturing` | Lagged outcome growth; 1997–2024 | 1 |
| R7_to2023 | `g_house`, `g_gdp`, `covid` | End sample in 2023 | 1 |
| R8_pre2008_omit2000 | `g_house`, `g_gdp` | 1996–2007 excluding 2000 | 1 |
| R9_boom_only | `g_house`, `g_gdp` | 2001–2007 | 1 |

HAC standard errors use Bartlett weights and finite-sample correction `n/(n−k)`, where `k` includes the intercept. P-values and 95% confidence intervals use Student's t distribution with `n−k` degrees of freedom. Excluded years retain their **calendar gaps** in the covariance matrix; observations on either side of a missing year are not treated as adjacent years.

## What each script does

`analyze.py` selects the Eurostat series, averages the four quarterly BIS/FRED house-price observations for each year, calculates growth rates and lags, and estimates all 13 models. It checks complete positive observations, full-rank designs, and the Frisch–Waugh–Lovell identity. It also calculates descriptive statistics, phase averages, and leave-one-year-out sensitivity, and writes CSV, JSON, PNG, and PDF outputs.

`verify_analysis.py` independently fits OLS with statsmodels and compares coefficients, HAC standard errors, full covariance matrices, and R-squared values. Missing calendar years receive zero score contributions in its HAC estimate. It also reports baseline residual Ljung–Box diagnostics, maximum leverage for the 2020 dummy, and fixed-lag Augmented Dickey–Fuller diagnostics for manufacturing investment, house-price, and GDP growth.

The numerical checks are assertions; run Python normally without `-O` or `PYTHONOPTIMIZE`. Coefficient, standard-error, and covariance differences must be below `1e-8`; R-squared differences must be below `1e-10`. The root wrapper compares regenerated JSON values with absolute tolerance `1e-8` and relative tolerance `1e-9`.

## Data and outputs

See [`DATA.md`](DATA.md) for sources and transformations. [`source_manifest.json`](source_manifest.json) records the retrieval date, exact URLs, original code and data hashes, and recorded versions. [`requirements.txt`](requirements.txt) pins the Python packages.

The supplied CSV and JSON files are reference outputs and are overwritten by the scripts. PNG figures are written here; vector PDFs are written to [`../figures/`](../figures/README.md). The extra dwelling series is retained for completeness and is not used in the reported regressions.
