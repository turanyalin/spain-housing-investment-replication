# Reproduction notes

## Environment

Use Python 3.12 and the versions in `replication/requirements.txt`. A virtual environment keeps the reproduction separate from other projects. The original recorded Python version is 3.12.14. TeX is optional for the numerical analysis and is needed only for building the paper PDF.

## Validation sequence

`python reproduce.py` checks raw-file and active analysis-code hashes before running the pipeline. It retains the supplied JSON outputs in memory, rebuilds the analysis, runs the independent statsmodels audit, and compares every value in the regenerated model-results and diagnostics JSON files with the references. It also generates four empirical table snippets and checks that the tables and both vector figures are nonempty.

The reference comparison uses absolute tolerance `1e-8` and relative tolerance `1e-9`. The independent audit uses the checks described in the [analysis README](../replication/README.md). Figures are regenerated without requiring byte identity because metadata and rendering can vary.

To return to the published references after editing outputs, use a fresh clone or restore the intended files from your chosen Git commit. Replacing reference outputs with arbitrary new results defeats the comparison.

## Manuscript build

Run the analysis before compiling if you want fresh figures. `make paper` reproduces the numerical analysis and compiles the manuscript; `make reproduce` runs the numerical pipeline; `make test` checks calendar gaps and ingestion; `make clean` removes temporary TeX files with `latexmk -c`.

Tables 2, 3, 4, and 6 load their generated contents from `tables/`. Source definitions, literature estimates, and numerical prose remain in `main.tex`. Changing a specification therefore still requires reviewing the manuscript text. See the [pipeline walkthrough](code_walkthrough.md) for the code sample and module responsibilities.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| `ModuleNotFoundError` | Activate the virtual environment and run `python -m pip install -r requirements.txt` from the root. |
| No matching package version | Confirm Python 3.12, a supported platform, and an index with the pinned releases. Do not silently substitute versions for an exact reproduction. |
| Hash mismatch | Compare the affected file with the published commit or use a fresh clone. Raw inputs and the versioned active scripts should match the selected commit. |
| Numerical mismatch | Retain the error, Python and package versions, platform, and repository commit when opening an issue. |
| Missing `latexmk` or TeX package | Install a TeX distribution with the packages requested by `main.tex`, or use Overleaf. |
| Different results from live data | Series may have been revised. Use the archived files for exact reproduction and treat fresh observations as a separate update. |

## Changes from the source archive

The analysis is refactored into ingestion, estimation, reporting, and figure modules. Four empirical manuscript tables are now generated from the saved results. The original scripts remain available in Git history; their hashes are recorded separately from the active module hashes in `replication/source_manifest.json`. Raw responses, model definitions, bibliography, and numerical reference results are preserved. The manuscript prose has been edited for clarity, and Appendix A focuses on calendar-gap HAC inference.
