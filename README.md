# Spain housing and manufacturing investment

Replication code and archived public data for **House Prices, Bank Credit, and Manufacturing Investment in Spain**, by Turan Celik (29 October 2026).

This repository reconstructs the annual dataset, four main OLS regressions, nine sensitivity specifications, statistical diagnostics, and two figures used in the manuscript. It includes the LaTeX manuscript and bibliography. The analysis runs from archived data without downloading new observations or requiring an API key.

## Quick start

Use **Python 3.12**. Run these commands from the repository root:

```bash
git clone https://github.com/turanyalin/spain-housing-investment-replication.git
cd spain-housing-investment-replication
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python reproduce.py
```

On Windows, create the environment with `py -3.12 -m venv .venv` and activate it with `.venv\Scripts\Activate.ps1` in PowerShell. You can also download and extract the repository ZIP instead of using Git.

The reproduction command checks the archived input and analysis-code SHA-256 hashes, regenerates the analysis and figures, independently checks all 13 regressions with statsmodels, and compares numerical results and diagnostics with the supplied reference outputs. A successful run ends with `Replication passed: 13 models, independent statistical audit, and archived numerical outputs verified.`

Installing Python packages requires internet access. The analysis itself uses local files only. Keep the supplied `replication/results.json` and `replication/submission_statistical_checks.json` for the first run; these are the numerical references checked by the runner. Generated files are overwritten when you rerun the analysis.

## What is reproduced

The sample contains annual levels for Spain in **1995–2024** and log growth rates for **1996–2024**. The largest regression sample has 29 observations; models with lags or restricted time windows use fewer.

| Output | Location |
| --- | --- |
| Annual levels, growth rates, controls, and lags | [`replication/analysis_data.csv`](replication/analysis_data.csv) |
| All model results, covariance matrices, fitted values, and residuals | [`replication/results.json`](replication/results.json) |
| Coefficients, HAC standard errors, confidence intervals, and p-values | [`replication/regression_results.csv`](replication/regression_results.csv) |
| Descriptive statistics | [`replication/summary_statistics.csv`](replication/summary_statistics.csv) |
| Independent regression checks and time-series diagnostics | [`replication/submission_statistical_checks.json`](replication/submission_statistical_checks.json) |
| PNG figures | `replication/figure1.png`, `replication/figure2.png` |
| Vector figures used in the manuscript | `figures/figure1.pdf`, `figures/figure2.pdf` |

The code also reports growth by historical phase, leave-one-year-out estimates, and the Frisch–Waugh–Lovell coefficient check. See the [analysis guide](replication/README.md) for model definitions and the [data guide](replication/DATA.md) for sources, units, transformations, and reuse information.

## Build the paper

Install a TeX distribution with `latexmk`, pdfLaTeX, and BibTeX, then run:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

This creates `main.pdf`. Alternatively run `pdflatex main`, `bibtex main`, `pdflatex main`, and `pdflatex main`, in that order. On Overleaf, upload the repository ZIP and select `main.tex` as the main document. The supplied `main.bbl` is a prebuilt bibliography; `references.bib` is the editable source.

Python regenerates the figure files, datasets, regression results, and diagnostics. LaTeX tables contain the archived estimates as editable text; they are **not automatically rewritten** by Python. If you change the data or specifications, update the manuscript tables and discussion before rebuilding the paper.

## Repository guide

| Path | Purpose |
| --- | --- |
| [`reproduce.py`](reproduce.py) | Reproduce and validate the analysis in one command |
| [`requirements.txt`](requirements.txt) | Entry point to the pinned Python environment |
| [`replication/`](replication/README.md) | Original code, archived inputs, and reference outputs |
| [`figures/`](figures/README.md) | Vector figure files |
| [`docs/`](docs/README.md) | Checks, troubleshooting, and manuscript notes |
| [`main.tex`](main.tex) | Editable manuscript |
| [`references.bib`](references.bib) | Bibliography |
| [`Makefile`](Makefile) | Optional convenience commands |

## Interpretation and scope

These aggregate regressions describe associations. They do not identify a causal effect of house prices or directly reproduce the restricted bank- or firm-level microdata analyses discussed in the paper. The full-sample conditional house-price coefficient is imprecise, and the small sample makes inference sensitive to specification and time window. Some source observations are flagged as provisional. No interpolation or synthetic observations are used.

Reproducing the archived snapshot can reproduce the supplied estimates. Downloading the same source URLs later may produce different estimates because statistical agencies revise their data.

## Reuse and citation

The Python code, repository documentation, and build configuration are provided under the [MIT License](LICENSE). The manuscript, bibliography, and third-party data are excluded from that software license; the underlying data remain subject to their providers' terms. Preserve the attribution in [`replication/DATA.md`](replication/DATA.md) and [`replication/source_manifest.json`](replication/source_manifest.json).

If you use this work, cite the author, manuscript title, year, and repository commit. GitHub citation metadata is supplied in [`CITATION.cff`](CITATION.cff). Include the exact model, data snapshot, environment, and command when reporting a reproduction problem.
