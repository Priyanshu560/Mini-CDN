import unittest

from edge_server import EdgeServer
from models import Coordinates, FileObject
from network import Network
from origin_server import OriginFileNotFoundError


class _StubOrigin:
    """A minimal stand-in for OriginServer so edge tests don't touch disk."""

    def __init__(self):
        self.network = Network(base_latency_ms=100, bandwidth_mbps=1000,
                                jitter_range_ms=0, failure_probability=0)
        self._files = {
            "style.css": FileObject("style.css", "text/css", size_bytes=500, version=1,
                                     last_modified=None, content="body{}"),
        }

    def get_file(self, file_name):
        if file_name not in self._files:
            raise OriginFileNotFoundError(file_name)
        return self._files[file_name]

    def bump_version(self, file_name):
        self._files[file_name].version += 1


class EdgeServerTests(unittest.TestCase):
    def setUp(self):
        self.origin = _StubOrigin()
        self.edge = EdgeServer(
            name="TestEdge",
            coordinates=Coordinates(0, 0),
            base_latency_ms=10,
            bandwidth_mbps=1000,
            cache_capacity_bytes=10_000,
            origin=self.origin,
        )
        self.edge.network.jitter_range_ms = 0
        self.edge.network.failure_probability = 0

    def test_first_request_is_a_miss(self):
        response = self.edge.handle_request("style.css")
        self.assertEqual(response.cache_status, "MISS")

    def test_second_request_is_a_hit(self):
        self.edge.handle_request("style.css")
        response = self.edge.handle_request("style.css")
        self.assertEqual(response.cache_status, "HIT")

    def test_hit_is_faster_than_miss(self):
        miss_response = self.edge.handle_request("style.css")
        hit_response = self.edge.handle_request("style.css")
        self.assertLess(hit_response.latency_ms, miss_response.latency_ms)

    def test_stale_cache_is_detected_after_origin_update(self):
        self.edge.handle_request("style.css")
        self.origin.bump_version("style.css")
        response = self.edge.handle_request("style.css")
        self.assertEqual(response.cache_status, "STALE")

    def test_missing_file_raises(self):
        with self.assertRaises(OriginFileNotFoundError):
            self.edge.handle_request("does-not-exist.txt")

    def test_requests_served_counter_increments(self):
        self.edge.handle_request("style.css")
        self.edge.handle_request("style.css")
        self.assertEqual(self.edge.requests_served, 2)


if __name__ == "__main__":
    unittest.main()
