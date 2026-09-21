"""
Aggregates processed requests into running statistics: hit ratio,
latency distribution, per-server load, and which file gets requested
the most.
"""

import json
import statistics
from collections import Counter


class Analytics:
    def __init__(self):
        self.total_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0  # includes stale hits, since both require a fresh fetch
        self.failed_requests = 0
        self.fastest_request = None
        self.slowest_request = None
        self._latencies = []
        self._requests_per_server = Counter()
        self._requests_per_file = Counter()

    def record(self, request_record):
        self.total_requests += 1

        if request_record.status != "SUCCESS":
            self.failed_requests += 1
            return

        if request_record.cache_status == "HIT":
            self.cache_hits += 1
        else:
            self.cache_misses += 1

        self._latencies.append(request_record.latency_ms)
        self._requests_per_server[request_record.server_name] += 1
        self._requests_per_file[request_record.file_name] += 1

        if self.fastest_request is None or request_record.latency_ms < self.fastest_request.latency_ms:
            self.fastest_request = request_record
        if self.slowest_request is None or request_record.latency_ms > self.slowest_request.latency_ms:
            self.slowest_request = request_record

    @property
    def latencies(self):
        return list(self._latencies)

    @property
    def hit_ratio(self):
        served = self.cache_hits + self.cache_misses
        return self.cache_hits / served if served else 0.0

    @property
    def miss_ratio(self):
        served = self.cache_hits + self.cache_misses
        return self.cache_misses / served if served else 0.0

    @property
    def average_latency_ms(self):
        return statistics.mean(self._latencies) if self._latencies else 0.0

    @property
    def median_latency_ms(self):
        return statistics.median(self._latencies) if self._latencies else 0.0

    def requests_per_server(self):
        return dict(self._requests_per_server)

    def most_requested_file(self):
        if not self._requests_per_file:
            return None
        return self._requests_per_file.most_common(1)[0]

    def summary(self):
        most_requested = self.most_requested_file()
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "failed_requests": self.failed_requests,
            "hit_ratio": round(self.hit_ratio, 4),
            "miss_ratio": round(self.miss_ratio, 4),
            "average_latency_ms": round(self.average_latency_ms, 2),
            "median_latency_ms": round(self.median_latency_ms, 2),
            "fastest_request_ms": round(self.fastest_request.latency_ms, 2) if self.fastest_request else None,
            "slowest_request_ms": round(self.slowest_request.latency_ms, 2) if self.slowest_request else None,
            "requests_per_server": self.requests_per_server(),
            "most_requested_file": most_requested[0] if most_requested else None,
            "most_requested_file_count": most_requested[1] if most_requested else None,
        }

    def report(self):
        s = self.summary()
        lines = [
            "MiniCDN Analytics Summary",
            "=" * 40,
            f"Total requests:       {s['total_requests']}",
            f"Cache hits:           {s['cache_hits']}",
            f"Cache misses:         {s['cache_misses']}",
            f"Failed requests:      {s['failed_requests']}",
            f"Hit ratio:            {s['hit_ratio']:.2%}",
            f"Miss ratio:           {s['miss_ratio']:.2%}",
            f"Average latency:      {s['average_latency_ms']} ms",
            f"Median latency:       {s['median_latency_ms']} ms",
            f"Fastest request:      {s['fastest_request_ms']} ms",
            f"Slowest request:      {s['slowest_request_ms']} ms",
            "",
            f"Most requested file:  {s['most_requested_file']} ({s['most_requested_file_count']} requests)",
            "",
            "Requests per server:",
        ]
        for server_name, count in s["requests_per_server"].items():
            lines.append(f"  {server_name:<12} {count}")
        return "\n".join(lines)

    def export_json(self, filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.summary(), f, indent=2)
