"""Generate manuscript table rows after estimation and statistical verification."""

import json
from pathlib import Path
from reporting import write_tables

ROOT = Path(__file__).resolve().parent


def main():
    results = json.loads((ROOT / "results.json").read_text())
    diagnostics = json.loads((ROOT / "submission_statistical_checks.json").read_text())
    paths = write_tables(results, diagnostics, ROOT.parent / "tables")
    print(f"Generated {len(paths)} empirical manuscript tables.")


if __name__ == "__main__":
    main()
