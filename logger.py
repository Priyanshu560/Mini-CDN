"""
Structured request logging. Every processed request produces one
line in logs/server.log, in a key=value format that's easy to grep
or feed into a log parser later.

User-supplied values are sanitized so they can't forge extra lines.
"""

import logging
import os
import re
from logging.handlers import RotatingFileHandler

import config

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
_MAX_LOGGED_LENGTH = 128


def sanitize_for_log(value):
    """Replace control characters (incl. newlines) and cap the length."""
    return _CONTROL_CHARS.sub(" ", str(value))[:_MAX_LOGGED_LENGTH]


def _build_logger(log_file):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logger = logging.getLogger("mini_cdn")
    logger.setLevel(logging.INFO)

    if not logger.handlers:  # avoid duplicate handlers if this runs more than once per process
        handler = RotatingFileHandler(
            log_file,
            maxBytes=config.LOG_MAX_BYTES,
            backupCount=config.LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        formatter = logging.Formatter("%(asctime)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


class RequestLogger:
    def __init__(self, log_file):
        self._logger = _build_logger(log_file)

    def log_request(self, record):
        self._logger.info(
            "location=%s file=%s server=%s cache=%s latency=%.2fms status=%s",
            sanitize_for_log(record.location),
            sanitize_for_log(record.file_name),
            sanitize_for_log(record.server_name),
            record.cache_status,
            record.latency_ms,
            record.status,
        )
