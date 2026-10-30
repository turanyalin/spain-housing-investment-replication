"""Download a dated EU27 snapshot. Normal reproduction reads these archives only."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import argparse
import hashlib
import json
import time

ROOT = Path(__file__).resolve().parent
COUNTRIES = {
    "AT": "Austria",
    "BE": "Belgium",
    "BG": "Bulgaria",
    "HR": "Croatia",
    "CY": "Cyprus",
    "CZ": "Czechia",
    "DK": "Denmark",
    "EE": "Estonia",
    "FI": "Finland",
    "FR": "France",
    "DE": "Germany",
    "EL": "Greece",
    "HU": "Hungary",
    "IE": "Ireland",
    "IT": "Italy",
    "LV": "Latvia",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "MT": "Malta",
    "NL": "Netherlands",
    "PL": "Poland",
    "PT": "Portugal",
    "RO": "Romania",
    "SK": "Slovakia",
    "SI": "Slovenia",
    "ES": "Spain",
    "SE": "Sweden",
}


def source_urls():
    """Use the current EU27 membership cohort throughout 1995–2024."""
    base = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
    common = [
        ("freq", "A"),
        ("unit", "CLV20_MEUR"),
        ("sinceTimePeriod", "1995"),
        ("untilTimePeriod", "2024"),
    ]
    geographies = [("geo", code) for code in COUNTRIES]
    urls = {}
    for name, asset in [
        ("manufacturing", "N11G"),
        ("equipment", "N11MG"),
        ("ipp", "N117G"),
    ]:
        query = (
            common
            + [("nace_r2", "C"), ("na_item", "P51G"), ("asset10", asset)]
            + geographies
        )
        urls[name + ".json"] = base + "nama_10_a64_p5?" + urlencode(query)
    urls["gdp.json"] = (
        base + "nama_10_gdp?" + urlencode(common + [("na_item", "B1GQ")] + geographies)
    )
    for code in COUNTRIES:
        bis_code = "GR" if code == "EL" else code
        urls["house_" + code + ".csv"] = (
            "https://fred.stlouisfed.org/graph/fredgraph.csv?id=Q"
            + bis_code
            + "R628BIS"
        )
    return urls


def fetch_one(filename, url, destination):
    started = datetime.now(timezone.utc).isoformat()
    for attempt in range(3):
        try:
            request = Request(
                url, headers={"User-Agent": "EU-housing-investment-replication/1.0"}
            )
            with urlopen(request, timeout=45) as response:
                data = response.read()
                status = response.status
            if filename.endswith(".json"):
                payload = json.loads(data)
                if "value" not in payload or "dimension" not in payload:
                    raise ValueError("Expected a Eurostat JSON-stat response")
                found = set(payload["dimension"]["geo"]["category"]["index"])
                if found != set(COUNTRIES):
                    raise ValueError(f"Eurostat returned unexpected countries: {found}")
            elif not data.startswith(b"observation_date,"):
                raise ValueError("Expected a FRED CSV response")
            (destination / filename).write_bytes(data)
            return filename, dict(
                url=url,
                retrieved_utc=started,
                http_status=status,
                size_bytes=len(data),
                sha256=hashlib.sha256(data).hexdigest(),
            )
        except Exception as error:
            if attempt == 2:
                return filename, dict(url=url, retrieved_utc=started, error=str(error))
            time.sleep(attempt + 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "raw")
    parser.add_argument(
        "--refresh", action="store_true", help="Explicitly replace an existing snapshot"
    )
    args = parser.parse_args()
    destination = args.output_dir.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    manifest_path = destination / "download_manifest.json"
    if manifest_path.exists() and not args.refresh:
        raise SystemExit(
            "Snapshot already exists. Choose another directory or explicitly use --refresh."
        )
    entries = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [
            pool.submit(fetch_one, name, url, destination)
            for name, url in source_urls().items()
        ]
        for future in as_completed(futures):
            name, result = future.result()
            entries[name] = result
            print(name, "OK" if "sha256" in result else "UNAVAILABLE", flush=True)
    manifest = dict(
        countries=COUNTRIES,
        level_window=[1995, 2024],
        sources={name: entries[name] for name in sorted(entries)},
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    failed = [name for name, entry in entries.items() if "error" in entry]
    print(
        "Downloaded",
        len(entries) - len(failed),
        "of",
        len(entries),
        "sources; unavailable:",
        failed,
    )
    if any(name.endswith(".json") for name in failed):
        raise SystemExit(
            "A core Eurostat source failed; inspect the manifest before proceeding."
        )


if __name__ == "__main__":
    main()
