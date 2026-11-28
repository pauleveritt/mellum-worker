"""A thin API client over an injected transport."""
from ratelimit import TokenBucket


class RateLimited(Exception):
    """The client's limiter refused the request."""


class ApiClient:
    def __init__(self, transport, limiter: TokenBucket | None = None):
        self.transport = transport
        self.limiter = limiter

    def get(self, path):
        return self.transport(path)
