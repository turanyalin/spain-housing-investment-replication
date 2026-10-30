# Code sample: source data to manuscript outputs

The main EU workflow is [`panel/run.py`](../panel/run.py):

```python
data, coverage = build_panel(ROOT / "raw")
results = estimate_panel(data)
write_outputs(data, coverage, results, ROOT / "output")
make_figures(data, coverage, results, ROOT / "output")
```

Each step has one responsibility:

| Module | Responsibility |
| --- | --- |
| [`panel/download.py`](../panel/download.py) | Retrieve the Eurostat and BIS/FRED snapshot explicitly and record URLs and hashes. |
| [`panel/data.py`](../panel/data.py) | Decode source dimensions, validate quarters, merge country/year keys, preserve missing calendar years, and construct growth and lags. |
| [`panel/models.py`](../panel/models.py) | Estimate country/year fixed effects with statsmodels and country-and-year clustered inference; define all sensitivity samples. |
| [`panel/reporting.py`](../panel/reporting.py) | Export tidy results, generate LaTeX tables and numerical macros, and draw coverage and coefficient figures. |
| [`panel/verify.py`](../panel/verify.py) | Independently verify unbalanced within slopes and clustered covariance. |

The panel has 656 baseline observations from all 27 countries. Complete calendars prevent accidentally calculating a two-year change as a one-year growth rate. Country grouping prevents lags from leaking between countries. House-price annual means require all four quarters.

The main estimator uses explicit fixed-effect indicators and a library covariance routine. Alternating projections and score aggregation are kept in the independent verification module rather than dominating the main code sample.

The original Spain pipeline remains in [`replication/analyze.py`](../replication/analyze.py), with separate ingestion, models, reporting, and figure modules. Its specialized `calendar_hac_meat` preserves actual year distances when a national time-series sample omits years.

`python reproduce.py` rebuilds both analyses and their manuscript outputs. The empirical tables and panel baseline text values are generated; source descriptions, literature estimates, and other numerical prose still require editorial review after changes to the analysis.
