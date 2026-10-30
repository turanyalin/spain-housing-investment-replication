"""The 13 specifications and the calendar-aware Newey-West covariance."""

import numpy as np
from scipy import stats


def calendar_hac_meat(scores, years, lag=1):
    """Apply Bartlett weights to score pairs at actual calendar-year distances.

    For example, dropping 2020 does not make 2019 and 2021 one lag apart.
    Years must be unique and increasing; the original gaps are preserved.
    """
    scores = np.asarray(scores, dtype=float)
    years = np.asarray(years)
    if scores.ndim != 2 or years.ndim != 1 or len(years) != len(scores):
        raise ValueError("Scores must have one row per calendar year")
    if not np.isfinite(scores).all() or not np.isfinite(years).all():
        raise ValueError("Scores and years must be finite")
    if not np.equal(years, years.astype(int)).all() or (np.diff(years) <= 0).any():
        raise ValueError("Calendar years must be distinct, increasing integers")
    if not isinstance(lag, int) or lag < 0:
        raise ValueError("HAC lag must be a nonnegative integer")
    meat = scores.T @ scores
    for distance in range(1, lag + 1):
        cross = np.zeros((scores.shape[1], scores.shape[1]))
        for i in range(len(years)):
            for j in range(i):
                if years[i] - years[j] == distance:
                    cross += np.outer(scores[i], scores[j])
        meat += (1 - distance / (lag + 1)) * (cross + cross.T)
    return meat


def ols_hac(data, outcome, names, lag=1):
    """Fit one OLS specification with calendar-aware Bartlett HAC inference."""
    z = data[["year", outcome] + names].dropna()
    x = np.column_stack([np.ones(len(z)), z[names].to_numpy(float)])
    y = z[outcome].to_numpy(float)
    n, k = x.shape
    if np.linalg.matrix_rank(x) != k or n <= k:
        raise ValueError("Regression design must have full rank and n > k")
    b = np.linalg.lstsq(x, y, rcond=None)[0]
    u = y - x @ b
    inv = np.linalg.inv(x.T @ x)
    xu = x * u[:, None]
    years = z.year.to_numpy(int)
    cov = n / (n - k) * inv @ calendar_hac_meat(xu, years, lag) @ inv
    se = np.sqrt(np.diag(cov))
    t = b / se
    p = 2 * stats.t.sf(np.abs(t), n - k)
    q = stats.t.ppf(0.975, n - k)
    r2 = 1 - u @ u / np.sum((y - y.mean()) ** 2)
    return dict(
        covariance=cov.tolist(),
        n=n,
        df=n - k,
        r2=float(r2),
        adj_r2=float(1 - (1 - r2) * (n - 1) / (n - k)),
        year_start=int(z.year.min()),
        year_end=int(z.year.max()),
        years=z.year.tolist(),
        outcome=outcome,
        hac_lags=lag,
        dw=float(np.sum(np.diff(u) ** 2) / (u @ u)),
        coefficients={
            name: dict(
                beta=float(bb),
                se=float(ss),
                p=float(pp),
                lo=float(bb - q * ss),
                hi=float(bb + q * ss),
            )
            for name, bb, ss, pp in zip(["constant"] + names, b, se, p)
        },
        residuals=u.tolist(),
        fitted=(x @ b).tolist(),
    )


def estimate_models(data, status_flags):
    """Fit the published specifications and collect sensitivity summaries."""
    sample = data[data.year >= 1996]
    specs = {
        "M1": (sample, "g_manufacturing", ["g_house"], 1),
        "M2": (sample, "g_manufacturing", ["g_house", "g_gdp"], 1),
        "M3": (sample, "g_manufacturing", ["g_house", "g_gdp", "covid"], 1),
        "M4": (
            sample,
            "g_manufacturing",
            ["g_house", "g_gdp", "covid", "lag_house"],
            1,
        ),
        "R1_equipment": (sample, "g_equipment", ["g_house", "g_gdp", "covid"], 1),
        "R2_ipp": (sample, "g_ipp", ["g_house", "g_gdp", "covid"], 1),
        "R3_pre2008": (
            sample[sample.year <= 2007],
            "g_manufacturing",
            ["g_house", "g_gdp"],
            1,
        ),
        "R4_exclude_covid": (
            sample[~sample.year.isin([2020, 2021])],
            "g_manufacturing",
            ["g_house", "g_gdp"],
            1,
        ),
        "R5_hac2": (sample, "g_manufacturing", ["g_house", "g_gdp", "covid"], 2),
        "R6_AR1": (
            sample,
            "g_manufacturing",
            ["g_house", "g_gdp", "covid", "lag_manufacturing"],
            1,
        ),
        "R7_to2023": (
            sample[sample.year <= 2023],
            "g_manufacturing",
            ["g_house", "g_gdp", "covid"],
            1,
        ),
        "R8_pre2008_omit2000": (
            sample[(sample.year <= 2007) & (sample.year != 2000)],
            "g_manufacturing",
            ["g_house", "g_gdp"],
            1,
        ),
        "R9_boom_only": (
            sample[(sample.year >= 2001) & (sample.year <= 2007)],
            "g_manufacturing",
            ["g_house", "g_gdp"],
            1,
        ),
    }
    results = {key: ols_hac(*args) for key, args in specs.items()}
    # Leave-one-year-out sensitivity of M3, retain chronological gaps in HAC.
    loo = {
        int(y): ols_hac(
            sample[sample.year != y],
            "g_manufacturing",
            ["g_house", "g_gdp", "covid"],
            1,
        )["coefficients"]["g_house"]["beta"]
        for y in sample.year
        if y != 2020
    }
    # Omitting the sole COVID year makes the dummy constant; refit without it.
    loo[2020] = ols_hac(
        sample[sample.year != 2020], "g_manufacturing", ["g_house", "g_gdp"], 1
    )["coefficients"]["g_house"]["beta"]
    summaries = {
        c: dict(
            mean=float(sample[c].mean()),
            sd=float(sample[c].std()),
            minimum=float(sample[c].min()),
            maximum=float(sample[c].max()),
            n=int(sample[c].notna().sum()),
        )
        for c in ["g_manufacturing", "g_house", "g_gdp", "g_equipment", "g_ipp"]
    }
    phases = {}
    for name, lo, hi in [
        ("early", 2001, 2003),
        ("late", 2004, 2007),
        ("bust", 2008, 2013),
        ("recovery", 2014, 2019),
        ("recent", 2020, 2024),
    ]:
        phases[name] = {
            "years": f"{lo}-{hi}",
            **{
                c: float(data.loc[lo:hi, c].mean())
                for c in ["g_manufacturing", "g_house", "g_gdp"]
            },
        }
    status = {
        k: {str(y): f for y, f in v.items() if f} for k, v in status_flags.items()
    }
    bundle = dict(
        models=results,
        summary=summaries,
        phases=phases,
        status=status,
        loo=loo,
        correlation=float(sample.g_house.corr(sample.g_manufacturing)),
        growth_2000_2007={
            c: float(100 * (data.loc[2007, c] / data.loc[2000, c] - 1))
            for c in ["manufacturing", "house", "gdp", "equipment", "ipp"]
        },
    )
    return bundle
