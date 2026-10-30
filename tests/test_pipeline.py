"""Regression checks for calendar gaps and source-observation validation."""

import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from statsmodels.stats.sandwich_covariance import S_hac_simple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "replication"))
from data import build_dataset, read_eurostat, read_house_prices
from models import calendar_hac_meat


class CalendarGapTests(unittest.TestCase):
    def setUp(self):
        self.scores = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])

    def test_missing_year_does_not_create_adjacent_pair(self):
        actual = calendar_hac_meat(self.scores, [1999, 2001, 2002], lag=1)
        np.testing.assert_array_equal(actual, [[50.0, 63.0], [63.0, 80.0]])
        compressed = S_hac_simple(self.scores, nlags=1)
        self.assertFalse(np.allclose(actual, compressed))

    def test_zero_padded_statsmodels_matches_for_multiple_lags(self):
        padded = np.insert(self.scores, 1, [0.0, 0.0], axis=0)
        for lag in (0, 1, 2):
            with self.subTest(lag=lag):
                actual = calendar_hac_meat(self.scores, [1999, 2001, 2002], lag)
                np.testing.assert_allclose(actual, S_hac_simple(padded, nlags=lag))

    def test_consecutive_years_match_standard_hac(self):
        np.testing.assert_allclose(
            calendar_hac_meat(self.scores, [2000, 2001, 2002], 1),
            S_hac_simple(self.scores, nlags=1),
        )

    def test_unsorted_or_duplicate_years_are_rejected(self):
        for years in ([2000, 2000, 2002], [2002, 2000, 2001]):
            with self.subTest(years=years), self.assertRaises(ValueError):
                calendar_hac_meat(self.scores, years)


class IngestionTests(unittest.TestCase):
    def test_archived_dataset_has_expected_coverage_and_lags(self):
        data, flags = build_dataset(ROOT / "replication")
        self.assertEqual(data.year.tolist(), list(range(1995, 2025)))
        self.assertEqual(data.g_house.notna().sum(), 29)
        self.assertEqual(data.lag_house.notna().sum(), 28)
        self.assertEqual(data.covid.sum(), 1)
        self.assertIn("manufacturing", flags)

    def test_ambiguous_eurostat_selection_is_rejected(self):
        with self.assertRaises(ValueError):
            read_eurostat(ROOT / "replication/manufacturing_raw.json")

    def test_incomplete_or_duplicated_quarters_are_rejected(self):
        observed = pd.DataFrame(
            {
                "observation_date": [
                    "2000-01-01",
                    "2000-04-01",
                    "2000-07-01",
                    "2000-10-01",
                ],
                "QESR628BIS": [100.0, 101.0, 102.0, 103.0],
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "quarters.csv"
            for invalid in (
                observed.iloc[:3],
                pd.concat([observed, observed.iloc[:1]]),
            ):
                invalid.to_csv(path, index=False)
                with self.assertRaises(ValueError):
                    read_house_prices(path, range(2000, 2001))


if __name__ == "__main__":
    unittest.main()
