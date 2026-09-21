"""
Small stateless helpers used across the codebase.
"""

import math


def haversine_distance_km(coord_a, coord_b):
    """Great-circle distance between two lat/long points, in kilometers."""
    earth_radius_km = 6371.0

    lat1, lon1 = math.radians(coord_a.latitude), math.radians(coord_a.longitude)
    lat2, lon2 = math.radians(coord_b.latitude), math.radians(coord_b.longitude)
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius_km * c


def format_bytes(size_bytes):
    """Human-readable byte size, e.g. 1536 -> '1.5 KB'."""
    size = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{int(size)} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"
