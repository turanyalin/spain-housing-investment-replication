# EU housing and manufacturing investment

Replication code and archived public data for **House Prices and Manufacturing Investment in the European Union: Panel Evidence and the Spanish Credit Channel**, by Turan Celik (30 October 2026).

The main empirical analysis is an EU27 country-by-year panel with **656 baseline observations over 1996–2024**, country and year fixed effects, and country-and-year clustered standard errors. Spain remains the institutional case study and microdata synthesis. The original 29-observation Spain analysis is preserved alongside the panel.

The [code walkthrough](docs/code_walkthrough.md) shows the ingestion, estimation, table, and figure workflow. All numerical analysis uses the archived public-source responses; no API key or live download is needed after installing Python dependencies.

## Reproduce everything

Use **Python 3.12** and run from the repository root:

```bash
git clone https://github.com/turanyalin/spain-housing-investment-replication.git
cd spain-housing-investment-replication
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python reproduce.py
python -m unittest discover -s tests -v
```

On Windows, create the environment with `py -3.12 -m venv .venv` and activate `.venv\Scripts\Activate.ps1` in PowerShell. A repository ZIP also works in place of Git.

`reproduce.py` validates archived input and code hashes, regenerates the 12 EU panel specifications and the 13 Spain specifications, runs independent statistical checks, compares numerical results to the supplied references, and generates manuscript tables and figures. Its success message lists both analyses. Installing packages requires internet access; the analysis itself reads local files. Generated output files are overwritten on each run.

## Main results and coverage

The EU baseline has 27 countries, 29 distinct regression years, and 656 observations: **22.6 times** the original Spain sample. It is an unbalanced panel of the current EU27 cohort followed historically, including pre-accession years. Each house-price annual mean requires four observed quarters, and growth and lags preserve missing calendar years. See the [coverage CSV](panel/output/country_coverage.csv) for country-specific starts, ends, and omitted years.

The house-price coefficient is approximately **0.010** after controlling for real GDP growth, with two-way clustered SE **0.173** and 95% CI **[-0.347, 0.366]**. The larger panel changes the empirical conclusion: the conditional total-manufacturing estimate is near zero. Country exclusions, time windows, and a balanced 2010–2024 sample are reported rather than selecting a preferred significant specification.

Fixed effects absorb persistent country differences and common annual shocks. They do not establish causal identification. Observations within countries and years are dependent; the numerical increase in observations is not an equivalent increase in independent observations.

## Output guide

| Location | Contents |
| --- | --- |
| [`panel/raw/`](panel/README.md) | Four Eurostat JSON responses, 27 BIS/FRED quarterly CSV files, and their URL/hash manifest |
| [`panel/output/panel_data.csv`](panel/output/panel_data.csv) | Complete country-year calendar, levels, growth, lags, source flags, and baseline eligibility |
| [`panel/output/panel_results.json`](panel/output/panel_results.json) | All 12 panel fits, exact model samples, slopes, focal covariance matrices, summaries, and country influence |
| [`panel/output/panel_regressions.csv`](panel/output/panel_regressions.csv) | Tidy coefficients, standard errors, intervals, p-values, and cluster counts |
| [`panel/output/verification.json`](panel/output/verification.json) | Independent fixed-effects and covariance checks for each panel model |
| [`panel/output/`](panel/README.md) | Generated panel LaTeX tables, numerical-text macros, and vector figures |
| [`replication/`](replication/README.md) | Preserved Spain data, specifications, calendar-gap HAC, and outputs |
| [`tables/`](tables/README.md), [`figures/`](figures/README.md) | Generated Spain benchmark tables and figures |
| [`tests/`](tests/test_panel.py) | Calendar-gap, ingestion, panel-merge, within-transformation, and cluster-covariance checks |

## Build the paper

Install a TeX distribution with pdfLaTeX, BibTeX, and `latexmk`:

```bash
python reproduce.py
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

This creates `main.pdf`. `make paper` combines these steps; `make test` runs the tests. The committed generated snippets also allow direct LaTeX compilation without Python. For Overleaf, upload a repository ZIP and select `main.tex`.

The main manuscript loads the generated panel tables, coverage table, numerical macros, and figures. The Spain benchmark table and historical figure are also generated. Literature estimates, source descriptions, and much of the numerical discussion remain manuscript text, so any change to data or specifications requires editorial review.

## Refreshing sources

Exact reproduction uses the archived snapshot. To fetch a new vintage without overwriting it:

```bash
python -m panel.download --output-dir /path/to/new-snapshot
```

`--refresh` explicitly replaces an existing snapshot. Downloading fresh observations may change coverage and estimates; update the source manifest, references, manuscript, and tests as a deliberate new release. Do not change input hashes merely to suppress a reproduction error. See the [panel guide](panel/README.md) for filters and inference conventions.

## Reuse and citation

The Python code, documentation, and build configuration use the [MIT License](LICENSE). Third-party data, the manuscript, bibliography, and data-derived files retain their respective rights. Preserve attribution to Eurostat, national sources, the BIS Residential Property Price database, and FRED; see the exact archived URLs and provider terms linked in the [panel guide](panel/README.md).

Use [`CITATION.cff`](CITATION.cff) and cite the repository commit used. The repository URL is retained for continuity with the original Spain release.
