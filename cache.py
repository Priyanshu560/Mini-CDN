"""
A byte-budgeted least-recently-used cache built on top of
OrderedDict. get() and put() are O(1), and eviction always removes
whichever entry was touched longest ago -- no separate linked list or
timestamp bookkeeping needed, OrderedDict already tracks that order.
"""

from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity_bytes):
        self.capacity_bytes = capacity_bytes
        self.current_size_bytes = 0
        self.eviction_count = 0
        self._store = OrderedDict()

    def __contains__(self, key):
        return key in self._store

    def __len__(self):
        return len(self._store)

    def get(self, key):
        if key not in self._store:
            return None
        self._store.move_to_end(key)
        return self._store[key][0]

    def put(self, key, value, size_bytes):
        if size_bytes > self.capacity_bytes:
            return  # will never fit, not worth storing

        if key in self._store:
            self.current_size_bytes -= self._store[key][1]
            del self._store[key]

        while self.current_size_bytes + size_bytes > self.capacity_bytes:
            self._evict_oldest()

        self._store[key] = (value, size_bytes)
        self.current_size_bytes += size_bytes

    def clear(self):
        self._store.clear()
        self.current_size_bytes = 0

    def _evict_oldest(self):
        _, (_, evicted_size) = self._store.popitem(last=False)
        self.current_size_bytes -= evicted_size
        self.eviction_count += 1

    @property
    def utilization(self):
        return self.current_size_bytes / self.capacity_bytes if self.capacity_bytes else 0.0
