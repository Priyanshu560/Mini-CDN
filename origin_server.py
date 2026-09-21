"""
The origin server: the single source of truth for every file the CDN
serves. Edge servers only ever hold copies, and compare version
numbers against the origin to decide whether their copy is stale.
"""

import json
import os
from datetime import datetime

import config
from models import FileObject
from network import Network


class OriginFileNotFoundError(Exception):
    def __init__(self, file_name):
        super().__init__(f"File not found on origin: '{file_name}'")
        self.file_name = file_name


class OriginServer:
    def __init__(self, data_dir, manifest_path=None):
        self.data_dir = data_dir
        self.manifest_path = manifest_path or os.path.join(data_dir, "manifest.json")
        self.network = Network(config.ORIGIN_BASE_LATENCY_MS, config.ORIGIN_BANDWIDTH_MBPS)
        self._files = {}
        self._load_catalog()

    def _load_catalog(self):
        with open(self.manifest_path, encoding="utf-8") as manifest_file:
            manifest = json.load(manifest_file)

        for entry in manifest["files"]:
            size_bytes = entry.get("simulated_size_bytes")
            content = ""

            if size_bytes is None:
                # Real, on-disk file: read its content and use its actual size.
                file_path = os.path.join(self.data_dir, entry["name"])
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                size_bytes = os.path.getsize(file_path)

            self._files[entry["name"]] = FileObject(
                name=entry["name"],
                content_type=entry["content_type"],
                size_bytes=size_bytes,
                version=1,
                last_modified=datetime.now(),
                content=content,
            )

    def get_file(self, file_name):
        if file_name not in self._files:
            raise OriginFileNotFoundError(file_name)
        return self._files[file_name]

    def list_files(self):
        return list(self._files.keys())

    def update_file(self, file_name):
        """Simulate an origin-side content change: bump version and timestamp."""
        file_object = self.get_file(file_name)
        file_object.version += 1
        file_object.last_modified = datetime.now()
        return file_object
