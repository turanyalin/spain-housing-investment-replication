# Reproduction and manuscript notes

Use Python 3.12 with the pinned packages in `replication/requirements.txt` (included by the root requirements file). The recorded Python version is 3.12.14. TeX is needed only to compile the paper.

## Complete workflow

`python reproduce.py` validates the archived Spain inputs and active code, the panel code, and the panel download manifest. It runs the Spain pipeline and its independent HAC audit, runs the EU panel and its independent fixed-effects/cluster checks, compares regenerated numerical results with frozen references, and requires nonempty generated tables and figures. Raw panel responses are separately checked against their archived SHA-256 hashes.

`make test` runs the ingestion, calendar, fixed-effects, and covariance regression checks. `make paper` reproduces the analyses and compiles `main.tex`. `make clean` removes temporary TeX files.

Numerical reference comparison allows absolute tolerance `1e-8` and relative tolerance `1e-9`; independent panel covariance checks allow `1e-8` absolute and `1e-7` relative tolerance. Figures are not required to be byte-identical because PDF metadata can differ. Use a clean clone to recover the intended frozen references after exploratory edits.

## Manuscript assets

The main paper loads panel tables, text macros, coverage, and coefficient figures from `panel/output/`. It also loads the generated Spain benchmark table and historical figure. Other Spain sensitivity and diagnostic outputs remain available in `replication/` and `tables/`. Captions, source descriptions, the microeconomic literature table, and much of the numerical prose remain in `main.tex`.

The EU baseline uses 656 observations and changes the main empirical finding to a near-zero conditional house-price coefficient. The Spain case and original 13 specifications are retained. The repository URL remains unchanged so existing replication links keep working.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| `ModuleNotFoundError` | Activate the environment and install `python -m pip install -r requirements.txt`. |
| Hash mismatch | Compare the input or code with the intended Git commit. Do not edit hashes simply to suppress a mismatch. |
| Numerical mismatch | Keep the error, package versions, platform, and Git commit when reporting the issue. |
| Missing table or figure | Run the complete reproduction before compiling, or recover the committed generated assets. |
| Missing TeX package | Install the packages requested by `main.tex`, or compile in Overleaf. |
| Different estimates from new downloads | Data revisions create a new vintage. Preserve it separately and update references and manuscript deliberately. |

See the [code walkthrough](code_walkthrough.md) and [panel guide](../panel/README.md) for implementation details.
