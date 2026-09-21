"""
Drives request generation: either a single request supplied by a
caller, or a batch of randomly generated ones processed in simulated
arrival order via a priority queue.
"""

import heapq
import random
import time
from datetime import datetime

import config
from analytics import Analytics
from logger import RequestLogger
from models import Client, Request
from network import NetworkFailureError
from origin_server import OriginFileNotFoundError
from router import InvalidLocationError


class Simulator:
    def __init__(self, origin, router, logger=None, analytics=None):
        self.origin = origin
        self.router = router
        self.logger = logger or RequestLogger(config.LOG_FILE)
        self.analytics = analytics or Analytics()
        self._next_request_id = 1

    def process_request(self, client, file_name):
        request_id = self._next_request_id
        self._next_request_id += 1
        timestamp = datetime.now()

        server_name, cache_status, latency_ms, status = "-", "-", 0.0, "SUCCESS"

        try:
            edge = self.router.select_edge_server(client.location)
            server_name = edge.name
            response = edge.handle_request(file_name)
            cache_status = response.cache_status
            latency_ms = response.latency_ms
        except InvalidLocationError:
            status = "INVALID_LOCATION"
        except OriginFileNotFoundError:
            status = "FILE_NOT_FOUND"
        except NetworkFailureError:
            status = "NETWORK_FAILURE"

        record = Request(
            request_id=request_id,
            timestamp=timestamp,
            client_name=client.name,
            location=client.location,
            file_name=file_name,
            server_name=server_name,
            cache_status=cache_status,
            latency_ms=latency_ms,
            status=status,
        )

        self.logger.log_request(record)
        self.analytics.record(record)
        return record

    def run_batch(self, num_requests, origin_update_probability=config.ORIGIN_UPDATE_PROBABILITY):
        """
        Generates `num_requests` random client requests, schedules them
        on a priority queue ordered by simulated arrival time, and
        processes them in that order -- similar to how an event-driven
        server handles arrivals rather than a plain for loop.

        Returns (records, elapsed_seconds), where elapsed_seconds is the
        real wall-clock time this call took to run, as distinct from the
        simulated network latency reported inside each record.
        """
        event_queue = []
        simulated_clock = 0.0

        for sequence in range(num_requests):
            simulated_clock += random.uniform(0.01, 0.4)
            client = Client(
                name=random.choice(config.SAMPLE_CLIENT_NAMES),
                location=random.choice(list(config.CLIENT_CITIES.keys())),
            )
            file_name = random.choice(self.origin.list_files())
            # `sequence` breaks ties between equal clock values so heapq
            # never needs to compare two Client objects directly.
            heapq.heappush(event_queue, (simulated_clock, sequence, client, file_name))

        started_at = time.perf_counter()
        records = []
        while event_queue:
            _, _, client, file_name = heapq.heappop(event_queue)

            if random.random() < origin_update_probability:
                self.origin.update_file(file_name)

            records.append(self.process_request(client, file_name))
        elapsed_seconds = time.perf_counter() - started_at

        return records, elapsed_seconds
