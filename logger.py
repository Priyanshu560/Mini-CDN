"""
Structured request logging. Every processed request produces one
line in logs/server.log, in a key=value format that's easy to grep
or feed into a log parser later.
"""

import logging
import os


def _build_logger(log_file):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logger = logging.getLogger("mini_cdn")
    logger.setLevel(logging.INFO)

    if not logger.handlers:  # avoid duplicate handlers if this runs more than once per process
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter("%(asctime)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


class RequestLogger:
    def __init__(self, log_file):
        self._logger = _build_logger(log_file)

    def log_request(self, record):
        self._logger.info(
            "client=%s location=%s file=%s server=%s cache=%s latency=%.2fms status=%s",
            record.client_name,
            record.location,
            record.file_name,
            record.server_name,
            record.cache_status,
            record.latency_ms,
            record.status,
        )
