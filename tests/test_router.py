import unittest

from models import Coordinates
from router import InvalidLocationError, Router


class _StubEdge:
    def __init__(self, name, coordinates):
        self.name = name
        self.coordinates = coordinates


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.edges = {
            "Delhi": _StubEdge("Delhi", Coordinates(28.7041, 77.1025)),
            "Mumbai": _StubEdge("Mumbai", Coordinates(19.0760, 72.8777)),
            "Bangalore": _StubEdge("Bangalore", Coordinates(12.9716, 77.5946)),
        }
        self.router = Router(self.edges)

    def test_selects_closest_edge_for_known_city(self):
        # Chandigarh (used for "Punjab") is much closer to Delhi than to
        # Mumbai or Bangalore.
        selected = self.router.select_edge_server("Punjab")
        self.assertEqual(selected.name, "Delhi")

    def test_client_in_edge_city_routes_to_itself(self):
        selected = self.router.select_edge_server("Mumbai")
        self.assertEqual(selected.name, "Mumbai")

    def test_unknown_location_raises(self):
        with self.assertRaises(InvalidLocationError):
            self.router.select_edge_server("Atlantis")

    def test_distances_from_returns_all_edges(self):
        distances = self.router.distances_from("Kolkata")
        self.assertEqual(set(distances.keys()), {"Delhi", "Mumbai", "Bangalore"})
        self.assertTrue(all(value >= 0 for value in distances.values()))


if __name__ == "__main__":
    unittest.main()
