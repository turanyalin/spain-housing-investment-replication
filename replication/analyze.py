"""Reconstruct the archived Spain analysis and generate its numerical outputs."""

from pathlib import Path
from data import build_dataset
from models import estimate_models
from figures import make_figures
from reporting import write_results

ROOT = Path(__file__).resolve().parent


def main():
    data, source_flags = build_dataset(ROOT)
    results = estimate_models(data, source_flags)
    write_results(data, results, ROOT)
    make_figures(data, results["models"], ROOT)
    print(f"Generated dataset, {len(results['models'])} models, and two figures.")


if __name__ == "__main__":
    main()
