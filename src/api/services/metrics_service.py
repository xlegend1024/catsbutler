from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter


@dataclass
class TimedResult:
    value: object
    elapsed_ms: float


def measure(callable_fn):
    started = perf_counter()
    value = callable_fn()
    elapsed_ms = (perf_counter() - started) * 1000
    return TimedResult(value=value, elapsed_ms=elapsed_ms)
