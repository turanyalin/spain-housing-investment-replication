# Code sample: from archived observations to manuscript outputs

Start with [`replication/analyze.py`](../replication/analyze.py). Its main function shows the entire analysis workflow:

```python
data, source_flags = build_dataset(ROOT)
results = estimate_models(data, source_flags)
write_results(data, results, ROOT)
make_figures(data, results["models"], ROOT)
```

The numerical work is separated from file ingestion and presentation:

| Module | Responsibility |
| --- | --- |
| [`data.py`](../replication/data.py) | Select Eurostat JSON-stat series, validate quarterly coverage and positive annual levels, merge sources by year, and construct growth rates and lags. |
| [`models.py`](../replication/models.py) | Define the 13 specifications, estimate models, preserve calendar gaps in HAC inference, and collect sensitivity summaries. |
| [`reporting.py`](../replication/reporting.py) | Export tidy CSV and complete JSON results; render the empirical LaTeX table snippets from those results. |
| [`figures.py`](../replication/figures.py) | Generate PNG and vector PDF figures from the annual dataset and model estimates. |
| [`verify_analysis.py`](../replication/verify_analysis.py) | Independently check results with statsmodels and calculate the time-series diagnostics. |
| [`render_tables.py`](../replication/render_tables.py) | Read the result and diagnostic JSON files and write the four empirical table snippets included by `main.tex`. |

`data.py` rejects ambiguous source selections, incomplete or duplicated house-price quarters, and missing or nonpositive annual levels. It retains Eurostat status flags alongside the observations. The raw responses remain unchanged.

`calendar_hac_meat` is the specialized numerical component. Pairing observations by their actual year distance ensures that removing 2020 does not turn 2019 and 2021 into adjacent years. The independent check pads missing years with zero scores before calling statsmodels. Unit tests cover this gap, multiple bandwidths, consecutive-year equivalence, and invalid calendar ordering.

The paper includes the generated tables for descriptive statistics, main regressions, sensitivity estimates, and ADF diagnostics. Source definitions and published microeconomic estimates are maintained separately. Numerical prose still requires editorial review after any change to the data or model specifications.

Run the complete pipeline with `python reproduce.py`; run the focused checks with `python -m unittest discover -s tests -v`. The code sample uses the archived Spain analysis. A country-by-year panel would require a new data-coverage assessment, model specification, and inference design.
