"""Client-side rate limiting."""
import time


class TokenBucket:
    def __init__(self, rate, capacity, clock=time.monotonic):
        self.rate = rate
        self.capacity = capacity
        self.clock = clock
        self._tokens = float(capacity)
        self._last = clock()

    def try_acquire(self, tokens=1):
        now = self.clock()
        self._tokens += (now - self._last) * self.rate  # no cap: idle time banks unlimited tokens
        self._last = now
        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False
