import unittest

import app as app_module


class _NullLogger:
    def log_request(self, record):
        pass


class ApiValidationTests(unittest.TestCase):
    def setUp(self):
        app_module.simulator.logger = _NullLogger()  # keep tests from touching logs/
        self.client = app_module.app.test_client()

    def test_valid_request(self):
        resp = self.client.post("/request", json={"location": "Delhi", "file_name": "index.html"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["X-Content-Type-Options"], "nosniff")

    def test_legacy_client_name_field_is_ignored(self):
        resp = self.client.post(
            "/request", json={"client_name": "x" * 500, "location": "Delhi", "file_name": "index.html"}
        )
        self.assertEqual(resp.status_code, 200)

    def test_responses_set_no_cookies(self):
        for resp in (
            self.client.get("/files"),
            self.client.get("/analytics"),
            self.client.post("/request", json={"location": "Delhi", "file_name": "index.html"}),
        ):
            self.assertNotIn("Set-Cookie", resp.headers)

    def test_missing_fields(self):
        self.assertEqual(self.client.post("/request", json={}).status_code, 400)

    def test_non_object_body_is_400_not_500(self):
        self.assertEqual(self.client.post("/request", json=["x"]).status_code, 400)

    def test_non_string_field_rejected(self):
        resp = self.client.post("/request", json={"location": 5, "file_name": "index.html"})
        self.assertEqual(resp.status_code, 400)

    def test_overlong_field_rejected(self):
        resp = self.client.post("/request", json={"location": "Delhi", "file_name": "a" * 500})
        self.assertEqual(resp.status_code, 400)

    def test_oversized_body_rejected(self):
        resp = self.client.post("/request", data="x" * 10000, content_type="application/json")
        self.assertEqual(resp.status_code, 413)


if __name__ == "__main__":
    unittest.main()
