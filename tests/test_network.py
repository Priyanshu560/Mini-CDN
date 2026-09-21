import unittest

from network import Network


class NetworkTests(unittest.TestCase):
    def test_transfer_time_scales_with_size(self):
        net = Network(base_latency_ms=10, bandwidth_mbps=100, jitter_range_ms=0, failure_probability=0)
        small = net.transfer_time_ms(1_250)
        large = net.transfer_time_ms(12_500)
        self.assertAlmostEqual(large, small * 10, places=5)

    def test_round_trip_includes_base_latency(self):
        net = Network(base_latency_ms=50, bandwidth_mbps=100, jitter_range_ms=0, failure_probability=0)
        self.assertGreaterEqual(net.round_trip_ms(0), 50)

    def test_jitter_stays_within_range(self):
        net = Network(base_latency_ms=0, bandwidth_mbps=100, jitter_range_ms=5, failure_probability=0)
        for _ in range(200):
            self.assertTrue(-5 <= net.jitter() <= 5)

    def test_zero_failure_probability_never_fails(self):
        net = Network(base_latency_ms=0, bandwidth_mbps=100, failure_probability=0.0)
        self.assertFalse(any(net.has_failed() for _ in range(200)))

    def test_certain_failure_probability_always_fails(self):
        net = Network(base_latency_ms=0, bandwidth_mbps=100, failure_probability=1.0)
        self.assertTrue(all(net.has_failed() for _ in range(200)))


if __name__ == "__main__":
    unittest.main()
