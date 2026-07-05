# services/rate_limiter.py
# In-memory rate limiter for production (Vercel functions ephemeral,
# but acceptable for MVP — use Redis for multi-instance prod).

import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple
from threading import Lock


class RateLimiter:
    """Sliding window rate limiter (in-memory).

    Usage:
        limiter = RateLimiter.get("auth", max_requests=5, window_seconds=60)
        if limiter.is_allowed(ip):
            ...
    """

    _instances: Dict[str, "RateLimiter"] = {}
    _lock = Lock()

    def __init__(self, name: str, max_requests: int, window_seconds: int):
        self.name = name
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._mu = Lock()

    @classmethod
    def get(cls, name: str, max_requests: int, window_seconds: int) -> "RateLimiter":
        """Singleton getter."""
        with cls._lock:
            if name not in cls._instances:
                cls._instances[name] = cls(name, max_requests, window_seconds)
            return cls._instances[name]

    def is_allowed(self, key: str) -> Tuple[bool, int]:
        """Returns (allowed, remaining).

        remaining = how many more requests allowed in current window.
        """
        now = time.time()
        with self._mu:
            bucket = self._hits[key]
            # Sliding window: evict old hits
            cutoff = now - self.window_seconds
            while bucket and bucket[0] < cutoff:
                bucket.popleft()

            if len(bucket) >= self.max_requests:
                return False, 0

            bucket.append(now)
            return True, max(0, self.max_requests - len(bucket))

    def reset(self, key: str | None = None) -> None:
        """Reset limit for a key (or all keys)."""
        with self._mu:
            if key:
                self._hits.pop(key, None)
            else:
                self._hits.clear()


# Pre-configured rate limiters
AUTH_LOGIN = RateLimiter.get("auth_login", max_requests=5, window_seconds=60)
AUTH_REGISTER = RateLimiter.get("auth_register", max_requests=3, window_seconds=3600)
ATTEMPT_SUBMIT = RateLimiter.get("attempt_submit", max_requests=120, window_seconds=60)
