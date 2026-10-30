# Generated empirical tables

These files are written by `python replication/render_tables.py` after `analyze.py` and `verify_analysis.py`, or by the complete `python reproduce.py` command.

| File | Manuscript table | Numerical source |
| --- | --- | --- |
| `descriptive_table.tex` | Table 2: descriptive statistics | `results.json`, `summary` |
| `main_models_table.tex` | Table 3: four main regressions | `results.json`, `models` |
| `sensitivity_table.tex` | Table 4: nine sensitivity estimates | `results.json`, `models` |
| `diagnostics_table.tex` | Table 6: ADF diagnostics | `submission_statistical_checks.json` |

`main.tex` includes these snippets inside its table layouts. Edit the analysis or reporting code, then regenerate; do not edit generated tables by hand. Table 1 describes the sources, and Table 5 attributes published microeconomic estimates, so their contents remain in the manuscript. Numerical prose is also maintained in the manuscript.
