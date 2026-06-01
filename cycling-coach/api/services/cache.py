"""In-memory cache with TTL expiry."""

import time
from typing import Any


class InMemoryCache:
    """Simple in-memory cache with per-entry TTL.

    Protects expensive Strava API calls and bike profile loads from being
    repeated on every request.
    """

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Any | None:
        """Return the cached value for *key*, or None if missing/expired."""
        if key not in self._store:
            return None
        value, expires_at = self._store[key]
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: int = 60) -> None:
        """Store *value* under *key* with a TTL of *ttl_seconds*."""
        self._store[key] = (value, time.time() + ttl_seconds)

    def delete(self, key: str) -> None:
        """Remove *key* from the cache if present."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Evict all entries."""
        self._store.clear()


# Global singleton used by all routers
cache = InMemoryCache()
