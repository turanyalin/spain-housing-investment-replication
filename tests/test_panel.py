"""Panel merge, calendar, fixed-effects, and cluster-inference regression checks."""

import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups
from panel.data import build_panel, add_growth, annual_house_prices
from panel.verify import within_transform, manual_cluster_covariance

ROOT = Path(__file__).resolve().parents[1]


class PanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.coverage = build_panel(ROOT / "panel/raw")
        cls.sample = cls.data[cls.data.baseline_sample].copy()
        cls.fit = smf.ols(
            "g_manufacturing ~ g_house + g_gdp + C(country) + C(year)", data=cls.sample
        ).fit()

    def test_frozen_snapshot_coverage(self):
        self.assertEqual(len(self.sample), 656)
        self.assertEqual(self.sample.country.nunique(), 27)
        self.assertEqual(self.sample.year.nunique(), 29)
        self.assertFalse(self.sample.duplicated(["country", "year"]).any())
        self.assertTrue(self.sample.house_quarters.eq(4).all())

    def test_missing_level_does_not_bridge_a_year(self):
        data = self.data.copy()
        data.loc[data.country.eq("ES") & data.year.eq(2000), "manufacturing"] = np.nan
        changed = add_growth(data).set_index(["country", "year"])
        self.assertTrue(np.isnan(changed.loc[("ES", 2000), "g_manufacturing"]))
        self.assertTrue(np.isnan(changed.loc[("ES", 2001), "g_manufacturing"]))
        self.assertTrue(np.isfinite(changed.loc[("ES", 2002), "g_manufacturing"]))

    def test_lags_stay_within_country(self):
        data = self.data.set_index(["country", "year"])
        for country in ("AT", "BE", "ES"):
            self.assertTrue(np.isnan(data.loc[(country, 1996), "lag_house"]))
            self.assertAlmostEqual(
                data.loc[(country, 1997), "lag_house"],
                data.loc[(country, 1996), "g_house"],
            )

    def test_unbalanced_within_slopes_match_full_dummy_fit(self):
        transformed = within_transform(
            self.sample[["g_manufacturing", "g_house", "g_gdp"]],
            self.sample.country,
            self.sample.year,
        )
        actual = np.linalg.lstsq(transformed[:, 1:], transformed[:, 0], rcond=None)[0]
        np.testing.assert_allclose(
            actual, self.fit.params[["g_house", "g_gdp"]], rtol=1e-9, atol=1e-9
        )

    def test_independent_country_year_covariance_matches_library(self):
        country = pd.factorize(self.sample.country, sort=True)[0]
        year = pd.factorize(self.sample.year, sort=True)[0]
        expected = cov_cluster_2groups(self.fit, country, year, use_correction=True)[0]
        actual = manual_cluster_covariance(
            self.fit, self.sample.country, self.sample.year
        )
        np.testing.assert_allclose(actual, expected, rtol=1e-7, atol=1e-8)

    def test_partial_house_year_is_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "partial.csv"
            pd.DataFrame(
                {
                    "observation_date": ["2000-01-01", "2000-04-01", "2000-07-01"],
                    "QXXR628BIS": [100.0, 101.0, 102.0],
                }
            ).to_csv(path, index=False)
            annual = annual_house_prices(path)
            self.assertEqual(annual.loc[2000, "house_quarters"], 3)
            self.assertTrue(np.isnan(annual.loc[2000, "house"]))


if __name__ == "__main__":
    unittest.main()
