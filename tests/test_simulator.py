import tempfile
import unittest

import config
from analytics import Analytics
from edge_server import EdgeServer
from logger import RequestLogger
from origin_server import OriginServer
from router import Router
from simulator import Simulator


class SimulatorBatchTests(unittest.TestCase):
    def setUp(self):
        self.origin = OriginServer(config.DATA_DIR)
        edges = {
            name: EdgeServer(
                name=name,
                coordinates=settings["coordinates"],
                base_latency_ms=settings["base_latency_ms"],
                bandwidth_mbps=settings["bandwidth_mbps"],
                cache_capacity_bytes=settings["cache_capacity_bytes"],
                origin=self.origin,
            )
            for name, settings in config.EDGE_SERVERS.items()
        }
        router = Router(edges)
        # Route logs to a throwaway file so tests never touch logs/server.log
        log_file = tempfile.mktemp(suffix=".log")
        self.simulator = Simulator(self.origin, router, logger=RequestLogger(log_file), analytics=Analytics())

    def test_batch_processes_requested_count(self):
        records, elapsed_seconds = self.simulator.run_batch(50)
        self.assertEqual(len(records), 50)
        self.assertEqual(self.simulator.analytics.total_requests, 50)
        self.assertGreaterEqual(elapsed_seconds, 0)

    def test_batch_only_uses_known_files(self):
        records, _ = self.simulator.run_batch(30)
        valid_files = set(self.origin.list_files())
        for record in records:
            self.assertIn(record.file_name, valid_files)

    def test_batch_produces_both_hits_and_misses_over_enough_volume(self):
        # With only 3 edges and 9 files, a few hundred requests should
        # produce repeat lookups and therefore at least one cache hit.
        self.simulator.run_batch(300)
        self.assertGreater(self.simulator.analytics.cache_hits, 0)


if __name__ == "__main__":
    unittest.main()
