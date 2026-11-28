"""Command history."""


class History:
    def __init__(self, capacity=10):
        self.capacity = capacity
        self._items = []

    def add(self, item):
        self._items.append(item)

    def recent(self):
        return self._items
