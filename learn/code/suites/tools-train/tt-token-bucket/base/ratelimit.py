"""Client-side rate limiting."""
import time


class TokenBucket:
    def __init__(self, rate, capacity, clock=time.monotonic):
        self.rate = rate
        self.capacity = capacity
        self.clock = clock

    def try_acquire(self, tokens=1):
        raise NotImplementedError
