"""Read the archived Eurostat and BIS/FRED observations into one annual dataset."""

from pathlib import Path
import json
import numpy as np
import pandas as pd

FIRST_YEAR = 1995
LAST_YEAR = 2024


def read_eurostat(path: Path, **selection: str) -> tuple[pd.Series, dict]:
    """Select one annual series from a Eurostat JSON-stat response.

    Dimensions with several categories must be selected explicitly. Missing
    observations remain missing until the dataset validation rejects them.
    """
    response = json.loads(path.read_text())
    dimensions = response["id"]
    categories = {
        key: response["dimension"][key]["category"]["index"] for key in dimensions
    }
    for key in selection:
        if key not in dimensions:
            raise ValueError(f"{path.name}: unknown dimension {key}")
    values, flags = {}, {}
    for year in categories["time"]:
        indices = []
        for key in dimensions:
            choice = year if key == "time" else selection.get(key)
            if choice is None:
                if len(categories[key]) != 1:
                    raise ValueError(f"{path.name}: select a category for {key}")
                choice = next(iter(categories[key]))
            if choice not in categories[key]:
                raise ValueError(f"{path.name}: unknown {key} category {choice}")
            indices.append(categories[key][choice])
        index = str(np.ravel_multi_index(indices, response["size"]))
        values[int(year)] = response["value"].get(index, np.nan)
        flags[int(year)] = response.get("status", {}).get(index, "")
    return pd.Series(values, dtype=float).sort_index(), flags


def read_house_prices(path: Path, years: range) -> pd.Series:
    """Average exactly four distinct, observed quarters for each sample year."""
    quarterly = pd.read_csv(path, parse_dates=["observation_date"])
    quarterly["year"] = quarterly.observation_date.dt.year
    quarterly = quarterly[quarterly.year.isin(years)].copy()
    quarterly["quarter"] = quarterly.observation_date.dt.quarter
    if quarterly.duplicated(["year", "quarter"]).any():
        raise ValueError("House-price data contain duplicate calendar quarters")
    quarterly["QESR628BIS"] = pd.to_numeric(quarterly["QESR628BIS"], errors="raise")
    if not np.isfinite(quarterly["QESR628BIS"]).all():
        raise ValueError("House-price data contain missing or nonfinite values")
    annual = quarterly.groupby("year")["QESR628BIS"].agg(["mean", "count"])
    if not annual.reindex(years)["count"].eq(4).all():
        raise ValueError("Each sample year must have four house-price quarters")
    return annual["mean"]


def build_dataset(source_dir: Path) -> tuple[pd.DataFrame, dict]:
    """Merge annual source series, validate levels, then construct growth and lags."""
    years = range(FIRST_YEAR, LAST_YEAR + 1)
    data = pd.DataFrame(index=years)
    flags = {}
    for name, asset in [
        ("manufacturing", "N11G"),
        ("equipment", "N11MG"),
        ("ipp", "N117G"),
    ]:
        data[name], flags[name] = read_eurostat(
            source_dir / "manufacturing_raw.json", unit="CLV20_MEUR", asset10=asset
        )
    data["gdp"], flags["gdp"] = read_eurostat(
        source_dir / "gdp_raw.json", unit="CLV20_MEUR"
    )
    data["dwelling"], flags["dwelling"] = read_eurostat(
        source_dir / "investment_raw.json", unit="CLV20_MEUR", asset10="N111G"
    )
    data["house"] = read_house_prices(source_dir / "house_raw.csv", years)
    if not np.isfinite(data.to_numpy()).all() or not data.gt(0).all().all():
        raise ValueError("All selected annual levels must be observed and positive")
    for name in data.columns.tolist():
        data["g_" + name] = 100 * np.log(data[name]).diff()
    data["lag_house"] = data.g_house.shift(1)
    data["lag_manufacturing"] = data.g_manufacturing.shift(1)
    data["covid"] = (data.index == 2020).astype(int)
    data["year"] = data.index
    return data, flags
