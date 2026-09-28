import logging
import os
import tempfile
import unittest
from datetime import datetime

from logger import RequestLogger, sanitize_for_log
from models import Request


def _record(file_name="index.html", location="Delhi"):
    return Request(
        request_id=1, timestamp=datetime.now(),
        location=location, file_name=file_name, server_name="Delhi",
        cache_status="HIT", latency_ms=12.5, status="SUCCESS",
    )


class LoggerTests(unittest.TestCase):
    def _reset_logger(self):
        # The "mini_cdn" logger is process-wide; drop any handler another
        # test module attached so this test writes to its own temp file.
        logger = logging.getLogger("mini_cdn")
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)

    def setUp(self):
        self._reset_logger()
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "logs", "server.log")

    def tearDown(self):
        self._reset_logger()
        self.tmp.cleanup()

    def _read(self):
        with open(self.path, encoding="utf-8") as f:
            return f.read()

    def test_log_line_has_expected_fields_and_no_client_field(self):
        RequestLogger(self.path).log_request(_record())
        line = self._read()
        self.assertIn("location=Delhi file=index.html server=Delhi", line)
        self.assertNotIn("client=", line)

    def test_newlines_cannot_forge_log_lines(self):
        RequestLogger(self.path).log_request(_record(file_name="a\nFAKE ENTRY status=SUCCESS"))
        self.assertEqual(len(self._read().strip().splitlines()), 1)

    def test_sanitize_caps_length(self):
        self.assertLessEqual(len(sanitize_for_log("x" * 1000)), 128)


if __name__ == "__main__":
    unittest.main()
