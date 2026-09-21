"""
An edge server: a caching reverse proxy in front of the origin. Each
edge keeps its own LRU cache and its own network profile, and decides
independently whether its cached copy of a file is still fresh by
comparing version numbers with the origin.
"""

from dataclasses import replace

from cache import LRUCache
from models import EdgeResponse
from network import Network, NetworkFailureError


class EdgeServer:
    def __init__(self, name, coordinates, base_latency_ms, bandwidth_mbps,
                 cache_capacity_bytes, origin):
        self.name = name
        self.coordinates = coordinates
        self.origin = origin
        self.cache = LRUCache(cache_capacity_bytes)
        self.network = Network(base_latency_ms, bandwidth_mbps)
        self.requests_served = 0

    def handle_request(self, file_name):
        """
        Resolves a single file request against this edge's cache,
        falling back to the origin on a miss or a stale copy.

        Raises NetworkFailureError if this edge's link is simulated as
        down, or OriginFileNotFoundError if the file doesn't exist
        anywhere in the system.
        """
        self.requests_served += 1

        if self.network.has_failed():
            raise NetworkFailureError(self.name)

        origin_file = self.origin.get_file(file_name)  # raises OriginFileNotFoundError
        cached_file = self.cache.get(file_name)

        if cached_file is not None and cached_file.version == origin_file.version:
            latency_ms = self._deliver_latency(cached_file.size_bytes)
            return EdgeResponse(file_object=cached_file, cache_status="HIT", latency_ms=latency_ms)

        cache_status = "STALE" if cached_file is not None else "MISS"
        # Cache a snapshot, not the live origin object -- otherwise a
        # later version bump on the origin would silently "update" every
        # edge's cached copy too, since they'd be the same object.
        cached_copy = replace(origin_file)
        self.cache.put(file_name, cached_copy, cached_copy.size_bytes)
        latency_ms = self._fetch_and_deliver_latency(cached_copy.size_bytes)
        return EdgeResponse(file_object=cached_copy, cache_status=cache_status, latency_ms=latency_ms)

    def _deliver_latency(self, size_bytes):
        """Latency for serving a fresh cache hit straight to the client."""
        latency = self.network.round_trip_ms(size_bytes) + self.network.jitter()
        return max(latency, 1.0)

    def _fetch_and_deliver_latency(self, size_bytes):
        """Latency for pulling from the origin first, then serving the client."""
        latency = (
            self.origin.network.round_trip_ms(size_bytes)
            + self.network.round_trip_ms(size_bytes)
            + self.network.jitter()
        )
        return max(latency, 1.0)
