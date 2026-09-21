"""
Per-server network characteristics: base latency, link bandwidth,
jitter, and a small chance of simulated failure. Both the origin and
every edge server hold one of these to describe how their own link
behaves.
"""

import random

import config


class NetworkFailureError(Exception):
    def __init__(self, server_name):
        super().__init__(f"Simulated network failure while reaching '{server_name}'")
        self.server_name = server_name


class Network:
    BYTES_PER_MS_PER_MBPS = 125  # 1 Mbps == 125 bytes/millisecond

    def __init__(self, base_latency_ms, bandwidth_mbps,
                 jitter_range_ms=None, failure_probability=None):
        self.base_latency_ms = base_latency_ms
        self.bandwidth_mbps = bandwidth_mbps
        self.jitter_range_ms = (
            config.NETWORK_JITTER_MS if jitter_range_ms is None else jitter_range_ms
        )
        self.failure_probability = (
            config.NETWORK_FAILURE_PROBABILITY if failure_probability is None else failure_probability
        )

    def transfer_time_ms(self, size_bytes):
        bytes_per_ms = self.bandwidth_mbps * self.BYTES_PER_MS_PER_MBPS
        return size_bytes / bytes_per_ms

    def round_trip_ms(self, size_bytes):
        """Base latency plus transfer time for one hop over this link."""
        return self.base_latency_ms + self.transfer_time_ms(size_bytes)

    def jitter(self):
        return random.uniform(-self.jitter_range_ms, self.jitter_range_ms)

    def has_failed(self):
        return random.random() < self.failure_probability
