# Reproduction notes

## Environment

Use Python 3.12 and the versions in `replication/requirements.txt`. A virtual environment keeps the reproduction separate from other projects. The original recorded Python version is 3.12.14. TeX is optional for the numerical analysis and is needed only for building the paper PDF.

## Validation sequence

`python reproduce.py` checks raw-file and original analysis-code hashes before running either script. It retains the supplied JSON outputs in memory, rebuilds the analysis, runs the independent statsmodels audit, and compares every value in the regenerated model-results and diagnostics JSON files with the references. It also checks that both vector figures are nonempty.

The reference comparison uses absolute tolerance `1e-8` and relative tolerance `1e-9`. The independent audit uses the checks described in the [analysis README](../replication/README.md). Figures are regenerated without requiring byte identity because metadata and rendering can vary.

To return to the published references after editing outputs, use a fresh clone or restore the intended files from your chosen Git commit. Replacing reference outputs with arbitrary new results defeats the comparison.

## Manuscript build

Run the analysis before compiling if you want fresh figures. `make paper` compiles the manuscript; `make reproduce` runs the numerical reproduction; `make clean` removes temporary TeX files with `latexmk -c`.

Tables and reported numerical prose in `main.tex` are editable LaTeX and are not generated from `results.json`. Changing a specification does not automatically produce a revised manuscript.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| `ModuleNotFoundError` | Activate the virtual environment and run `python -m pip install -r requirements.txt` from the root. |
| No matching package version | Confirm Python 3.12, a supported platform, and an index with the pinned releases. Do not silently substitute versions for an exact reproduction. |
| Hash mismatch | Compare the affected file with the published commit or use a fresh clone. Raw inputs and original analysis scripts should remain unchanged. |
| Numerical mismatch | Retain the error, Python and package versions, platform, and repository commit when opening an issue. |
| Missing `latexmk` or TeX package | Install a TeX distribution with the packages requested by `main.tex`, or use Overleaf. |
| Different results from live data | Series may have been revised. Use the archived files for exact reproduction and treat fresh observations as a separate update. |

## Changes from the source archive

The original analysis scripts, raw responses, manuscript, bibliography, and reference numerical outputs are preserved. Packaging adds the reproduction runner, setup entry point, documentation, citation metadata, software license, and build commands. Original file hashes remain in `replication/source_manifest.json`.
