from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Generic, TypeVar


T = TypeVar("T")


@dataclass
class _CacheEntry(Generic[T]):
    value: T
    expires_at: float


class TTLCache(Generic[T]):
    def __init__(self, ttl_seconds: int) -> None:
        self._ttl_seconds = ttl_seconds
        self._entries: dict[str, _CacheEntry[T]] = {}

    def get(self, key: str) -> T | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        if entry.expires_at <= monotonic():
            self._entries.pop(key, None)
            return None
        return entry.value

    def set(self, key: str, value: T) -> None:
        self._entries[key] = _CacheEntry(
            value=value,
            expires_at=monotonic() + self._ttl_seconds,
        )

    def invalidate(self, key: str) -> None:
        self._entries.pop(key, None)
