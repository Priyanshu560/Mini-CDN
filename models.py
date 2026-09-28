"""
Shared data containers.

These are plain dataclasses with no behavior of their own, kept in one
place so every other module can import from here without risking
circular imports between the server, router, and analytics layers.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Coordinates:
    latitude: float
    longitude: float


@dataclass
class FileObject:
    """A single file as tracked by the origin server."""
    name: str
    content_type: str
    size_bytes: int
    version: int
    last_modified: datetime
    content: str = ""  # real text content for small files; "" for simulated binaries


@dataclass
class Client:
    location: str


@dataclass
class EdgeResponse:
    """What an edge server hands back after resolving a single request."""
    file_object: FileObject
    cache_status: str  # "HIT", "STALE", or "MISS"
    latency_ms: float


@dataclass
class Request:
    """A fully resolved request, ready to be logged and analyzed."""
    request_id: int
    timestamp: datetime
    location: str
    file_name: str
    server_name: str
    cache_status: str  # "HIT", "STALE", "MISS", or "-" if the request never reached a server
    latency_ms: float
    status: str  # "SUCCESS", "INVALID_LOCATION", "FILE_NOT_FOUND", or "NETWORK_FAILURE"
