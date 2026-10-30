"""Two-way fixed-effects OLS with country-and-year clustered covariance."""

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.formula.api as smf
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups


def fit_panel(
    data, outcome="g_manufacturing", controls=("g_gdp",), clustering="two_way"
):
    terms = ["g_house", *controls]
    sample = (
        data.dropna(subset=[outcome, *terms]).sort_values(["country", "year"]).copy()
    )
    counts = sample.groupby("country").size()
    sample = sample[sample.country.isin(counts[counts > 1].index)].copy()
    if sample.duplicated(["country", "year"]).any():
        raise ValueError("Panel regression requires unique country-year cells")
    formula = outcome + " ~ " + " + ".join(terms) + " + C(country) + C(year)"
    fit = smf.ols(formula, data=sample).fit()
    n, k = fit.model.exog.shape
    if np.linalg.matrix_rank(fit.model.exog) != k:
        raise ValueError("Fixed-effects design is not full column rank")
    country_codes, countries = pd.factorize(sample.country, sort=True)
    year_codes, years = pd.factorize(sample.year, sort=True)
    g_country, g_year = len(countries), len(years)
    if min(g_country, g_year) < 2:
        raise ValueError("At least two country and year clusters are required")
    both, country_cov, year_cov = cov_cluster_2groups(
        fit, country_codes, year_codes, use_correction=True
    )
    covariance = both if clustering == "two_way" else country_cov
    df_inference = (
        min(g_country, g_year) - 1 if clustering == "two_way" else g_country - 1
    )
    indices = [fit.model.exog_names.index(term) for term in terms]
    focal_cov = covariance[np.ix_(indices, indices)]
    if (np.diag(focal_cov) <= 0).any():
        raise ValueError(
            "Nonpositive variance for a reported slope; inspect cluster covariance"
        )
    standard_errors = np.sqrt(np.diag(focal_cov))
    critical = stats.t.ppf(0.975, df_inference)
    coefficients = {}
    for term, se in zip(terms, standard_errors):
        beta = float(fit.params[term])
        coefficients[term] = dict(
            beta=beta,
            se=float(se),
            p=float(2 * stats.t.sf(abs(beta / se), df_inference)),
            lo=float(beta - critical * se),
            hi=float(beta + critical * se),
        )
    null = smf.ols(outcome + " ~ C(country) + C(year)", data=sample).fit()
    return dict(
        n=int(n),
        k=int(k),
        outcome=outcome,
        controls=list(controls),
        formula=formula,
        countries=countries.tolist(),
        years=[int(year) for year in years],
        observations=sample[["country", "year"]].to_dict("records"),
        country_clusters=g_country,
        year_clusters=g_year,
        inference_df=int(df_inference),
        clustering=clustering,
        correction="G/(G-1) * (N-1)/(N-K) per cluster component",
        coefficients=coefficients,
        covariance=focal_cov.tolist(),
        r2_overall=float(fit.rsquared),
        r2_within=float(1 - fit.ssr / null.ssr),
        country_fe=True,
        year_fe=True,
    )


def estimate_panel(data):
    baseline = data[data.baseline_sample].copy()
    recent = baseline[baseline.year.between(2010, 2024)]
    complete = recent.groupby("country").size()
    balanced = recent[recent.country.isin(complete[complete.eq(15)].index)]
    specs = {
        "P1_house": (baseline, "g_manufacturing", (), "two_way"),
        "P2_gdp": (baseline, "g_manufacturing", ("g_gdp",), "two_way"),
        "P3_lag": (baseline, "g_manufacturing", ("g_gdp", "lag_house"), "two_way"),
        "S_equipment": (data, "g_equipment", ("g_gdp",), "two_way"),
        "S_ipp": (data, "g_ipp", ("g_gdp",), "two_way"),
        "S_no_spain": (
            baseline[baseline.country.ne("ES")],
            "g_manufacturing",
            ("g_gdp",),
            "two_way",
        ),
        "S_pre2008": (
            baseline[baseline.year.le(2007)],
            "g_manufacturing",
            ("g_gdp",),
            "two_way",
        ),
        "S_post2008": (
            baseline[baseline.year.ge(2008)],
            "g_manufacturing",
            ("g_gdp",),
            "two_way",
        ),
        "S_exclude_covid": (
            baseline[~baseline.year.isin([2020, 2021])],
            "g_manufacturing",
            ("g_gdp",),
            "two_way",
        ),
        "S_to2023": (
            baseline[baseline.year.le(2023)],
            "g_manufacturing",
            ("g_gdp",),
            "two_way",
        ),
        "S_balanced": (balanced, "g_manufacturing", ("g_gdp",), "two_way"),
        "S_country_cluster": (baseline, "g_manufacturing", ("g_gdp",), "country"),
    }
    results = {name: fit_panel(*arguments) for name, arguments in specs.items()}
    leave_one_out = {}
    for country in sorted(baseline.country.unique()):
        result = fit_panel(baseline[baseline.country.ne(country)])
        leave_one_out[country] = result["coefficients"]["g_house"]["beta"]
    summary = {
        variable: dict(
            n=int(baseline[variable].count()),
            mean=float(baseline[variable].mean()),
            sd=float(baseline[variable].std()),
            minimum=float(baseline[variable].min()),
            maximum=float(baseline[variable].max()),
        )
        for variable in ("g_manufacturing", "g_house", "g_gdp")
    }
    return dict(
        models=results,
        leave_one_country_out=leave_one_out,
        summary=summary,
        design="Unweighted EU27-cohort country-year panel; country and year fixed effects",
    )
