"""
Central configuration for MiniCDN: server topology, city coordinates,
and simulation parameters. Everything here is a plain constant so the
rest of the codebase stays free of magic numbers, and paths are
resolved relative to this file so the project runs the same way
regardless of the working directory it's launched from.
"""

import os

from models import Coordinates

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "server.log")
DOCS_DIR = os.path.join(BASE_DIR, "docs")
CHART_DIR = os.path.join(DOCS_DIR, "charts")

# --- Origin ---
ORIGIN_BASE_LATENCY_MS = 180
ORIGIN_BANDWIDTH_MBPS = 1000

# --- Edge servers ---
# Coordinates are approximate city centers used only to rank edges by
# distance -- not surveyed values. Base latencies match the figures
# used throughout this project's design notes.
DELHI_COORDS = Coordinates(28.7041, 77.1025)
MUMBAI_COORDS = Coordinates(19.0760, 72.8777)
BANGALORE_COORDS = Coordinates(12.9716, 77.5946)

EDGE_SERVERS = {
    "Delhi": {
        "coordinates": DELHI_COORDS,
        "base_latency_ms": 25,
        "bandwidth_mbps": 500,
        "cache_capacity_bytes": 8 * 1024 * 1024,
    },
    "Mumbai": {
        "coordinates": MUMBAI_COORDS,
        "base_latency_ms": 55,
        "bandwidth_mbps": 400,
        "cache_capacity_bytes": 8 * 1024 * 1024,
    },
    "Bangalore": {
        "coordinates": BANGALORE_COORDS,
        "base_latency_ms": 80,
        "bandwidth_mbps": 350,
        "cache_capacity_bytes": 8 * 1024 * 1024,
    },
}

# --- Client-side cities ---
# Includes the edge cities themselves, since a client can be based in
# the same city as an edge server. "Punjab" is represented by
# Chandigarh, its de facto administrative center.
CLIENT_CITIES = {
    "Delhi": DELHI_COORDS,
    "Mumbai": MUMBAI_COORDS,
    "Bangalore": BANGALORE_COORDS,
    "Punjab": Coordinates(30.7333, 76.7794),
    "Jaipur": Coordinates(26.9124, 75.7873),
    "Lucknow": Coordinates(26.8467, 80.9462),
    "Kolkata": Coordinates(22.5726, 88.3639),
    "Hyderabad": Coordinates(17.3850, 78.4867),
    "Ahmedabad": Coordinates(23.0225, 72.5714),
}

SAMPLE_CLIENT_NAMES = [
    "Aarav", "Priya", "Rohan", "Ananya", "Vikram",
    "Neha", "Karan", "Simran", "Arjun", "Divya",
]

# --- Network simulation ---
NETWORK_JITTER_MS = 8
NETWORK_FAILURE_PROBABILITY = 0.02

# Chance that a random file on the origin gets a fresh version stamped
# on it while a batch simulation is running, so cache invalidation
# actually gets exercised instead of only being covered by unit tests.
ORIGIN_UPDATE_PROBABILITY = 0.01
