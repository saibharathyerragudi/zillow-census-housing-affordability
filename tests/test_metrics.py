import unittest

from housing_affordability.ingest import normalize_metro_name
from housing_affordability.metrics import classify_affordability


class MetricsTests(unittest.TestCase):
    def test_normalize_metro_name_removes_area_suffix(self):
        self.assertEqual(
            normalize_metro_name("Austin-Round Rock-Georgetown, TX Metro Area"),
            "austin round rock georgetown tx",
        )

    def test_classify_affordability_thresholds(self):
        self.assertEqual(classify_affordability(2.8), "Affordable")
        self.assertEqual(classify_affordability(4.2), "Stretched")
        self.assertEqual(classify_affordability(6.2), "Severely stretched")
        self.assertEqual(classify_affordability(8.1), "Extremely unaffordable")


if __name__ == "__main__":
    unittest.main()
