import unittest
from datetime import datetime

from analytics import Analytics
from models import Request


def _record(server_name, cache_status, latency_ms, status="SUCCESS", file_name="index.html"):
    return Request(
        request_id=1,
        timestamp=datetime.now(),
        location="Delhi",
        file_name=file_name,
        server_name=server_name,
        cache_status=cache_status,
        latency_ms=latency_ms,
        status=status,
    )


class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.analytics = Analytics()

    def test_hit_and_miss_counts(self):
        self.analytics.record(_record("Delhi", "HIT", 30))
        self.analytics.record(_record("Delhi", "MISS", 200))

        self.assertEqual(self.analytics.cache_hits, 1)
        self.assertEqual(self.analytics.cache_misses, 1)
        self.assertAlmostEqual(self.analytics.hit_ratio, 0.5)

    def test_failed_requests_do_not_count_toward_hit_ratio(self):
        self.analytics.record(_record("-", "-", 0, status="INVALID_LOCATION"))
        self.analytics.record(_record("Delhi", "HIT", 30))

        self.assertEqual(self.analytics.failed_requests, 1)
        self.assertEqual(self.analytics.hit_ratio, 1.0)

    def test_fastest_and_slowest_request_tracked(self):
        self.analytics.record(_record("Delhi", "HIT", 30))
        self.analytics.record(_record("Mumbai", "MISS", 200))
        self.analytics.record(_record("Delhi", "HIT", 15))

        self.assertEqual(self.analytics.fastest_request.latency_ms, 15)
        self.assertEqual(self.analytics.slowest_request.latency_ms, 200)

    def test_most_requested_file(self):
        self.analytics.record(_record("Delhi", "HIT", 30, file_name="style.css"))
        self.analytics.record(_record("Delhi", "HIT", 30, file_name="style.css"))
        self.analytics.record(_record("Delhi", "HIT", 30, file_name="index.html"))

        file_name, count = self.analytics.most_requested_file()
        self.assertEqual(file_name, "style.css")
        self.assertEqual(count, 2)

    def test_summary_has_no_crash_when_empty(self):
        summary = self.analytics.summary()
        self.assertEqual(summary["total_requests"], 0)
        self.assertEqual(summary["hit_ratio"], 0.0)
        self.assertIsNone(summary["most_requested_file"])


if __name__ == "__main__":
    unittest.main()
