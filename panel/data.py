"""Merge Eurostat national accounts and BIS/FRED house prices on country and year."""

from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from .download import COUNTRIES

YEARS = range(1995, 2025)


def verify_snapshot(raw_dir: Path):
    manifest = json.loads((raw_dir / "download_manifest.json").read_text())
    for filename, source in manifest["sources"].items():
        if "sha256" not in source:
            continue
        actual = hashlib.sha256((raw_dir / filename).read_bytes()).hexdigest()
        if actual != source["sha256"]:
            raise ValueError(f"Panel source hash mismatch: {filename}")
    return manifest


def read_eurostat(path: Path, variable: str):
    payload = json.loads(path.read_text())
    dimensions = payload["id"]
    categories = {
        key: payload["dimension"][key]["category"]["index"] for key in dimensions
    }
    if set(categories["geo"]) != set(COUNTRIES):
        raise ValueError(f"Unexpected country selection in {path.name}")
    if any(
        len(categories[key]) != 1 for key in dimensions if key not in ("geo", "time")
    ):
        raise ValueError(f"Ambiguous non-country dimension in {path.name}")
    rows = []
    for country in COUNTRIES:
        for year in YEARS:
            if str(year) not in categories["time"]:
                continue
            choices = {"geo": country, "time": str(year)}
            indices = [
                categories[key][choices.get(key, next(iter(categories[key])))]
                for key in dimensions
            ]
            index = str(np.ravel_multi_index(indices, payload["size"]))
            value = payload["value"].get(index, np.nan)
            if pd.notna(value) and (not np.isfinite(value) or value <= 0):
                raise ValueError(f"Nonpositive/nonfinite {variable}: {country}, {year}")
            rows.append(
                dict(
                    country=country,
                    year=year,
                    **{
                        variable: value,
                        variable + "_status": payload.get("status", {}).get(index, ""),
                    },
                )
            )
    return pd.DataFrame(rows)


def annual_house_prices(path: Path):
    quarterly = pd.read_csv(path, parse_dates=["observation_date"])
    columns = [column for column in quarterly if column != "observation_date"]
    if len(columns) != 1:
        raise ValueError(f"Expected one BIS/FRED series in {path.name}")
    quarterly["year"] = quarterly.observation_date.dt.year
    quarterly = quarterly[quarterly.year.isin(YEARS)].copy()
    quarterly["quarter"] = quarterly.observation_date.dt.quarter
    if quarterly.duplicated(["year", "quarter"]).any():
        raise ValueError(f"Duplicate country-year quarter in {path.name}")
    quarterly["value"] = pd.to_numeric(quarterly[columns[0]], errors="coerce")
    observed = quarterly.value.dropna()
    if not np.isfinite(observed).all() or not observed.gt(0).all():
        raise ValueError(f"Invalid house-price index in {path.name}")
    annual = quarterly.groupby("year").value.agg(["mean", "count"]).reindex(YEARS)
    annual["house"] = annual["mean"].where(annual["count"].eq(4))
    return annual[["house", "count"]].rename(columns={"count": "house_quarters"})


def add_growth(data):
    """Use a complete calendar grid so missing years cannot be closed by differencing."""
    data = data.sort_values(["country", "year"]).copy()
    if data.duplicated(["country", "year"]).any():
        raise ValueError("Duplicate country-year observations")
    for country, group in data.groupby("country"):
        if group.year.tolist() != list(YEARS):
            raise ValueError(f"Incomplete calendar grid for {country}")
    for variable in ("manufacturing", "equipment", "ipp", "gdp", "house"):
        data["g_" + variable] = (
            np.log(data[variable]).groupby(data.country).diff() * 100
        )
    data["lag_house"] = data.groupby("country").g_house.shift(1)
    data["baseline_sample"] = (
        data[["g_manufacturing", "g_house", "g_gdp"]].notna().all(axis=1)
    )
    return data


def build_panel(raw_dir: Path):
    manifest = verify_snapshot(raw_dir)
    index = pd.MultiIndex.from_product([COUNTRIES, YEARS], names=["country", "year"])
    data = index.to_frame(index=False)
    data["country_name"] = data.country.map(COUNTRIES)
    for variable in ("manufacturing", "equipment", "ipp", "gdp"):
        source = read_eurostat(raw_dir / (variable + ".json"), variable)
        data = data.merge(
            source, on=["country", "year"], how="left", validate="one_to_one"
        )
    house_frames = []
    for country in COUNTRIES:
        filename = "house_" + country + ".csv"
        if "sha256" in manifest["sources"][filename]:
            annual = annual_house_prices(raw_dir / filename).reset_index()
        else:
            annual = pd.DataFrame(
                {"year": list(YEARS), "house": np.nan, "house_quarters": 0}
            )
        annual["country"] = country
        house_frames.append(annual)
    data = data.merge(
        pd.concat(house_frames),
        on=["country", "year"],
        how="left",
        validate="one_to_one",
    )
    data = add_growth(data)
    coverage = []
    for country, group in data.groupby("country", sort=True):
        sample = group[group.baseline_sample]
        usable_years = sample.year.tolist()
        coverage.append(
            dict(
                country=country,
                country_name=COUNTRIES[country],
                manufacturing_levels=int(group.manufacturing.notna().sum()),
                complete_house_years=int(group.house.notna().sum()),
                baseline_observations=len(sample),
                first_growth_year=min(usable_years) if usable_years else None,
                last_growth_year=max(usable_years) if usable_years else None,
                omitted_growth_years=",".join(
                    str(year) for year in range(1996, 2025) if year not in usable_years
                ),
                source_error=manifest["sources"]["house_" + country + ".csv"].get(
                    "error", ""
                ),
            )
        )
    return data, pd.DataFrame(coverage)
