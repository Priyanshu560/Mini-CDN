import os
import shutil
import tempfile
import unittest
from datetime import datetime

from origin_server import OriginFileNotFoundError, OriginServer


class OriginServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self._write("index.html", "<html></html>")
        self._write(
            "manifest.json",
            '{"files": ['
            '{"name": "index.html", "content_type": "text/html"}, '
            '{"name": "video.mp4", "content_type": "video/mp4", "simulated_size_bytes": 1000}'
            ']}',
        )
        self.origin = OriginServer(self.tmp_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _write(self, name, content):
        with open(os.path.join(self.tmp_dir, name), "w", encoding="utf-8") as f:
            f.write(content)

    def test_lists_files_from_manifest(self):
        self.assertEqual(set(self.origin.list_files()), {"index.html", "video.mp4"})

    def test_reads_real_content_for_text_files(self):
        file_object = self.origin.get_file("index.html")
        self.assertEqual(file_object.content, "<html></html>")
        self.assertGreater(file_object.size_bytes, 0)

    def test_uses_simulated_size_for_binary_files(self):
        file_object = self.origin.get_file("video.mp4")
        self.assertEqual(file_object.size_bytes, 1000)
        self.assertEqual(file_object.content, "")

    def test_missing_file_raises(self):
        with self.assertRaises(OriginFileNotFoundError):
            self.origin.get_file("missing.txt")

    def test_update_file_bumps_version_and_timestamp(self):
        before = self.origin.get_file("index.html")
        original_version = before.version

        updated = self.origin.update_file("index.html")

        self.assertEqual(updated.version, original_version + 1)
        self.assertIsInstance(updated.last_modified, datetime)


if __name__ == "__main__":
    unittest.main()
