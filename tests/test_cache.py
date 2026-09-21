import unittest

from cache import LRUCache


class LRUCacheTests(unittest.TestCase):
    def test_put_and_get(self):
        cache = LRUCache(capacity_bytes=100)
        cache.put("a", "content-a", size_bytes=10)
        self.assertEqual(cache.get("a"), "content-a")

    def test_miss_returns_none(self):
        cache = LRUCache(capacity_bytes=100)
        self.assertIsNone(cache.get("missing"))

    def test_eviction_removes_least_recently_used(self):
        cache = LRUCache(capacity_bytes=20)
        cache.put("a", "A", size_bytes=10)
        cache.put("b", "B", size_bytes=10)
        cache.get("a")  # touch "a" so "b" becomes the least recently used
        cache.put("c", "C", size_bytes=10)  # forces one eviction

        self.assertIsNone(cache.get("b"))
        self.assertEqual(cache.get("a"), "A")
        self.assertEqual(cache.get("c"), "C")
        self.assertEqual(cache.eviction_count, 1)

    def test_item_larger_than_capacity_is_not_cached(self):
        cache = LRUCache(capacity_bytes=10)
        cache.put("huge", "data", size_bytes=50)
        self.assertIsNone(cache.get("huge"))
        self.assertEqual(len(cache), 0)

    def test_updating_existing_key_replaces_size(self):
        cache = LRUCache(capacity_bytes=20)
        cache.put("a", "A-v1", size_bytes=10)
        cache.put("a", "A-v2", size_bytes=15)
        self.assertEqual(cache.get("a"), "A-v2")
        self.assertEqual(cache.current_size_bytes, 15)

    def test_utilization(self):
        cache = LRUCache(capacity_bytes=100)
        cache.put("a", "A", size_bytes=25)
        self.assertAlmostEqual(cache.utilization, 0.25)

    def test_clear_resets_state(self):
        cache = LRUCache(capacity_bytes=100)
        cache.put("a", "A", size_bytes=25)
        cache.clear()
        self.assertEqual(len(cache), 0)
        self.assertEqual(cache.current_size_bytes, 0)


if __name__ == "__main__":
    unittest.main()
