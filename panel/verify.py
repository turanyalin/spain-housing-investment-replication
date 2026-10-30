"""Independently check fixed-effects slopes and two-way clustered covariance."""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parent


def within_transform(values, country, year, tolerance=1e-12):
    """Alternating projections are required for an unbalanced two-way panel."""
    transformed = np.asarray(values, dtype=float).copy()
    codes = [pd.factorize(group, sort=True)[0] for group in (country, year)]
    for _ in range(10000):
        previous = transformed.copy()
        for groups in codes:
            count = np.bincount(groups)
            sums = np.zeros((len(count), transformed.shape[1]))
            np.add.at(sums, groups, transformed)
            transformed -= sums[groups] / count[groups, None]
        if np.max(np.abs(transformed - previous)) < tolerance:
            return transformed
    raise ValueError("Unbalanced within projection did not converge")


def manual_cluster_covariance(fit, country, year, clustering="two_way"):
    """Aggregate scores independently of statsmodels' cluster covariance routine."""
    x = fit.model.exog
    scores = x * fit.resid.to_numpy()[:, None]
    n, k = x.shape
    bread = np.linalg.inv(x.T @ x)
    country_codes = pd.factorize(country, sort=True)[0]
    year_codes = pd.factorize(year, sort=True)[0]
    _, intersections = np.unique(
        np.column_stack([country_codes, year_codes]), axis=0, return_inverse=True
    )
    components = []
    for groups in (country_codes, year_codes, intersections):
        g = int(groups.max() + 1)
        totals = np.zeros((g, k))
        np.add.at(totals, groups, scores)
        components.append(
            g / (g - 1) * (n - 1) / (n - k) * (bread @ totals.T @ totals @ bread)
        )
    return (
        components[0]
        if clustering == "country"
        else components[0] + components[1] - components[2]
    )


def main():
    data = pd.read_csv(ROOT / "output/panel_data.csv")
    results = json.loads((ROOT / "output/panel_results.json").read_text())
    checks = {}
    for name, result in results["models"].items():
        keys = pd.DataFrame(result["observations"])
        sample = keys.merge(data, on=["country", "year"], validate="one_to_one")
        fit = smf.ols(result["formula"], data=sample).fit()
        terms = list(result["coefficients"])
        observed = np.array([result["coefficients"][term]["beta"] for term in terms])
        transformed = within_transform(
            sample[[result["outcome"], *terms]].to_numpy(), sample.country, sample.year
        )
        within_beta = np.linalg.lstsq(
            transformed[:, 1:], transformed[:, 0], rcond=None
        )[0]
        np.testing.assert_allclose(within_beta, observed, rtol=1e-8, atol=1e-8)
        covariance = manual_cluster_covariance(
            fit, sample.country, sample.year, result["clustering"]
        )
        indices = [fit.model.exog_names.index(term) for term in terms]
        np.testing.assert_allclose(
            covariance[np.ix_(indices, indices)],
            result["covariance"],
            rtol=1e-7,
            atol=1e-8,
        )
        checks[name] = dict(
            n=len(sample), within_slopes_verified=True, cluster_covariance_verified=True
        )
    (ROOT / "output/verification.json").write_text(json.dumps(checks, indent=2) + "\n")
    print(
        f"Verified {len(checks)} panel models: alternating-projection slopes and independently aggregated cluster covariance."
    )


if __name__ == "__main__":
    main()
