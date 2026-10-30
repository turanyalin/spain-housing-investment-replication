"""Rebuild the archived analysis and check its numerical reference outputs."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import os

ROOT = Path(__file__).resolve().parent
REPLICATION = ROOT / "replication"


def compare(actual: object, expected: object, location: str) -> None:
    """Compare numerical results, allowing insignificant floating-point drift."""
    if isinstance(expected, bool) or expected is None or isinstance(expected, str):
        if type(actual) is not type(expected) or actual != expected:
            raise ValueError(
                f"Reference mismatch at {location}: {actual!r} != {expected!r}"
            )
    elif isinstance(expected, (int, float)):
        if isinstance(actual, bool) or not isinstance(actual, (int, float)):
            raise ValueError(f"Expected a number at {location}, got {actual!r}")
        if not math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-8):
            raise ValueError(
                f"Numerical mismatch at {location}: {actual!r} != {expected!r}"
            )
    elif isinstance(expected, dict):
        if not isinstance(actual, dict) or actual.keys() != expected.keys():
            raise ValueError(f"Result fields changed at {location}")
        for key, value in expected.items():
            compare(actual[key], value, f"{location}.{key}")
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise ValueError(f"Result length changed at {location}")
        for i, value in enumerate(expected):
            compare(actual[i], value, f"{location}[{i}]")
    else:
        raise TypeError(f"Unsupported reference value at {location}")


def main() -> None:
    manifest = json.loads((REPLICATION / "source_manifest.json").read_text())
    for section in ("sha256", "analysis_code_sha256"):
        for filename, expected_hash in manifest[section].items():
            actual_hash = hashlib.sha256(
                (REPLICATION / filename).read_bytes()
            ).hexdigest()
            if actual_hash != expected_hash:
                raise ValueError(
                    f"Archived file SHA-256 mismatch: replication/{filename}"
                )
    print("Archived data and analysis-code hashes verified.", flush=True)

    panel_manifest = json.loads((ROOT / "panel/source_manifest.json").read_text())
    raw_manifest = ROOT / "panel/raw/download_manifest.json"
    if (
        hashlib.sha256(raw_manifest.read_bytes()).hexdigest()
        != panel_manifest["raw_manifest_sha256"]
    ):
        raise ValueError("Panel download-manifest hash mismatch")
    for filename, expected_hash in panel_manifest["code_sha256"].items():
        actual_hash = hashlib.sha256((ROOT / filename).read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            raise ValueError(f"Panel code hash mismatch: {filename}")
    panel_reference = json.loads((ROOT / "panel/output/panel_results.json").read_text())

    output_names = ("results.json", "submission_statistical_checks.json")
    references = {
        name: json.loads((REPLICATION / name).read_text()) for name in output_names
    }
    if len(references["results.json"]["models"]) != 13:
        raise ValueError("The archived reference must contain all 13 models.")

    (ROOT / "figures").mkdir(exist_ok=True)
    for script in ("analyze.py", "verify_analysis.py", "render_tables.py"):
        print(f"\nRunning {script} with {sys.executable}", flush=True)
        subprocess.run(
            [sys.executable, str(REPLICATION / script)], cwd=REPLICATION, check=True
        )

    for filename, expected in references.items():
        actual = json.loads((REPLICATION / filename).read_text())
        compare(actual, expected, filename)
    for filename in ("figure1.pdf", "figure2.pdf"):
        path = ROOT / "figures" / filename
        if not path.is_file() or not path.stat().st_size:
            raise ValueError(f"Missing or empty figure: {path}")
    for filename in (
        "descriptive_table.tex",
        "main_models_table.tex",
        "sensitivity_table.tex",
        "diagnostics_table.tex",
    ):
        path = ROOT / "tables" / filename
        if not path.is_file() or not path.stat().st_size:
            raise ValueError(f"Missing or empty generated table: {path}")

    environment = os.environ.copy()
    environment["OPENBLAS_NUM_THREADS"] = "1"
    environment["OMP_NUM_THREADS"] = "1"
    for module in ("panel.run", "panel.verify"):
        subprocess.run(
            [sys.executable, "-m", module], cwd=ROOT, env=environment, check=True
        )
    actual_panel = json.loads((ROOT / "panel/output/panel_results.json").read_text())
    compare(actual_panel, panel_reference, "panel_results.json")
    for filename in (
        "main_table.tex",
        "sensitivity_table.tex",
        "summary_table.tex",
        "coverage_table.tex",
        "estimates.tex",
        "coverage.pdf",
        "coefficients.pdf",
    ):
        path = ROOT / "panel/output" / filename
        if not path.is_file() or not path.stat().st_size:
            raise ValueError(f"Missing or empty panel output: {path}")
    print(
        "\nReplication passed: 12 EU panel models, 13 Spain models, independent "
        "statistical checks, and archived numerical outputs verified.",
        flush=True,
    )


if __name__ == "__main__":
    try:
        main()
    except (ValueError, TypeError, OSError, subprocess.CalledProcessError) as error:
        print(f"Replication failed: {error}", file=sys.stderr)
        sys.exit(1)
