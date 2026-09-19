import unittest
from datetime import date
from tempfile import TemporaryDirectory

from app.catalog import OBSERVATIONS, SERIES, filter_observations, get_series
from app.store import Store


class CatalogTests(unittest.TestCase):
    def test_each_series_has_ordered_observations(self):
        for series in SERIES:
            self.assertIn(series.id, OBSERVATIONS)
            self.assertGreater(len(OBSERVATIONS[series.id]), 1)
            dates = [point[0] for point in OBSERVATIONS[series.id]]
            self.assertEqual(dates, sorted(dates))

    def test_observation_date_filter(self):
        points = filter_observations("IN-REPO-RATE", date(2026, 1, 1), date(2026, 2, 1))
        self.assertEqual([point["date"] for point in points], ["2026-01-01", "2026-02-01"])

    def test_unknown_series_returns_none(self):
        self.assertIsNone(get_series("NOT-A-SERIES"))

    def test_store_seeds_and_returns_latest_vintage(self):
        with TemporaryDirectory() as temporary_directory:
            store = Store(f"{temporary_directory}/test.db")
            store.initialize()
            series = store.get_series("IN-CPI-HEADLINE")
            self.assertEqual(series["observation_count"], 8)
            self.assertTrue(series["is_demo_data"])
            observations = store.observations("IN-CPI-HEADLINE")
            self.assertEqual(observations[-1]["date"], "2026-05-01")
            self.assertIn("vintage_date", observations[-1])


if __name__ == "__main__":
    unittest.main()
