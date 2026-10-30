"""Reproduce the EU panel, empirical tables and figures from the archived snapshot."""

from pathlib import Path
from .data import build_panel
from .models import estimate_panel
from .reporting import write_outputs, make_figures

ROOT = Path(__file__).resolve().parent


def main():
    data, coverage = build_panel(ROOT / "raw")
    results = estimate_panel(data)
    write_outputs(data, coverage, results, ROOT / "output")
    make_figures(data, coverage, results, ROOT / "output")
    baseline = results["models"]["P2_gdp"]
    print(
        f"Panel reproduced: {baseline['n']} observations, {baseline['country_clusters']} countries, "
        f"{len(results['models'])} models, four tables and two figures.",
        flush=True,
    )


if __name__ == "__main__":
    main()
