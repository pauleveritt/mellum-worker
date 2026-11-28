"""Client-side rate limiting."""
import time


class TokenBucket:
    def __init__(self, rate, capacity, clock=time.monotonic):
        self.rate = rate
        self.capacity = capacity
        self.clock = clock
        self._tokens = float(capacity)
        self._last = clock()

    def _refill(self):
        now = self.clock()
        self._tokens = min(self.capacity, self._tokens + (now - self._last) * self.rate)
        self._last = now

    def try_acquire(self, tokens=1):
        self._refill()
        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False
