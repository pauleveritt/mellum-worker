"""Command history."""


class History:
    """Most-recent-first, de-duplicated, bounded."""

    def __init__(self, capacity=10):
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self.capacity = capacity
        self._items = []

    def add(self, item):
        if item in self._items:
            self._items.remove(item)
        self._items.insert(0, item)
        del self._items[self.capacity:]

    def recent(self, n=None):
        return self._items[:n] if n is not None else list(self._items)
