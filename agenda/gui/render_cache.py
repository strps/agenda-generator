"""Qt-free preview helpers: config hash, bounded LRU image cache, debounce, stale-result gate."""

import hashlib
import time
from collections import OrderedDict
from collections.abc import Callable, Hashable
from typing import Any

from agenda.config import Config


def config_hash(cfg: Config) -> str:
    """Stable digest of the validated config; any field change changes it."""
    return hashlib.sha1(cfg.model_dump_json().encode()).hexdigest()


def cache_key(cfg_hash: str, page: int, zoom: Hashable) -> tuple[str, int, Hashable]:
    """Cache key: (config hash, 0-based plan index, zoom key)."""
    return (cfg_hash, page, zoom)


class LruCache:
    """Least-recently-used cache holding at most ``maxsize`` entries."""

    def __init__(self, maxsize: int = 64) -> None:
        if maxsize < 1:
            raise ValueError("maxsize must be >= 1")
        self.maxsize = maxsize
        self._data: OrderedDict[Hashable, Any] = OrderedDict()

    def get(self, key: Hashable) -> Any | None:
        if key not in self._data:
            return None
        self._data.move_to_end(key)
        return self._data[key]

    def put(self, key: Hashable, value: Any) -> None:
        self._data[key] = value
        self._data.move_to_end(key)
        while len(self._data) > self.maxsize:
            self._data.popitem(last=False)

    def __contains__(self, key: Hashable) -> bool:
        return key in self._data

    def __len__(self) -> int:
        return len(self._data)

    def clear(self) -> None:
        self._data.clear()


class Debounce:
    """Holds the latest pushed value until ``delay`` seconds pass with no newer push."""

    def __init__(self, delay: float = 0.3, clock: Callable[[], float] = time.monotonic) -> None:
        self.delay = delay
        self._clock = clock
        self._value: Any = None
        self._at = 0.0
        self.pending = False

    def push(self, value: Any = None) -> None:
        self._value, self._at, self.pending = value, self._clock(), True

    def take(self) -> tuple[bool, Any]:
        """(True, value) once the delay has elapsed since the last push, else (False, None)."""
        if self.pending and self._clock() - self._at >= self.delay:
            return self.flush()
        return False, None

    def flush(self) -> tuple[bool, Any]:
        """Like ``take`` but ignores the delay."""
        if not self.pending:
            return False, None
        self.pending = False
        return True, self._value


class LatestGate:
    """Request ids: only the result of the most recently issued request is accepted."""

    def __init__(self) -> None:
        self._latest = 0

    def issue(self) -> int:
        self._latest += 1
        return self._latest

    def is_current(self, request_id: int) -> bool:
        return request_id == self._latest
