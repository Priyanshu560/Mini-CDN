"""
Distance-based routing: picks whichever edge server is geographically
closest to the client making the request.
"""

import config
from utils import haversine_distance_km


class InvalidLocationError(Exception):
    def __init__(self, location_name):
        super().__init__(f"Unknown client location: '{location_name}'")
        self.location_name = location_name


class Router:
    def __init__(self, edge_servers):
        self.edge_servers = edge_servers  # dict[str, EdgeServer]

    def select_edge_server(self, location_name):
        client_coords = self._resolve(location_name)

        nearest_name = min(
            self.edge_servers,
            key=lambda name: haversine_distance_km(client_coords, self.edge_servers[name].coordinates),
        )
        return self.edge_servers[nearest_name]

    def distances_from(self, location_name):
        """Returns {edge_name: distance_km}, useful for debugging and demos."""
        client_coords = self._resolve(location_name)
        return {
            name: round(haversine_distance_km(client_coords, edge.coordinates), 1)
            for name, edge in self.edge_servers.items()
        }

    @staticmethod
    def _resolve(location_name):
        if location_name not in config.CLIENT_CITIES:
            raise InvalidLocationError(location_name)
        return config.CLIENT_CITIES[location_name]
