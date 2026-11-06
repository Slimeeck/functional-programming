"""Порівняння часу: рекурсивний vs ітеративний бінарний пошук, fib з кешем і без.

python benchmark.py  -> друкує таблицю та зберігає benchmark_results.json
"""

from __future__ import annotations

import json
import random
from bisect import bisect_left
from pathlib import Path
from timeit import timeit

from algorithms import (
    binary_search_cached,
    binary_search_iterative,
    binary_search_recursive,
    fib,
    fib_iter,
    fib_naive,
    linear_search_recursive,
)


def measure_search(size: int, queries: int = 2000) -> dict[str, float]:
    rng = random.Random(42)
    seq = tuple(range(0, size * 2, 2))  # відсортована незмінна послідовність
    targets = [rng.randrange(0, size * 2) for _ in range(queries)]

    def run(fn: object) -> float:
        return timeit(lambda: [fn(seq, t) for t in targets], number=1)  # type: ignore[operator]

    binary_search_cached.cache_clear()
    result = {
        "recursive": run(binary_search_recursive),
        "iterative": run(binary_search_iterative),
        "cached_cold": run(binary_search_cached),
        "cached_warm": run(binary_search_cached),
        "bisect_stdlib": run(lambda s, t: bisect_left(s, t)),
    }
    if size <= 500:  # лінійна рекурсія має глибину O(n)
        result["linear_recursive"] = run(linear_search_recursive)
    return result


def cached_fib(n: int) -> int:
    fib.cache_clear()
    return fib(n)


def measure_fib(n: int) -> dict[str, float]:
    fib.cache_clear()
    return {
        "fib_naive": timeit(lambda: fib_naive(n), number=1),
        "fib_lru_cache": timeit(lambda: cached_fib(n), number=1),
        "fib_iter": timeit(lambda: fib_iter(n), number=1),
    }


def main() -> None:
    results: dict[str, dict[str, float]] = {}
    header = ("size", "recursive", "iterative", "cached warm", "bisect")
    print("{:>9} | {:>10} | {:>10} | {:>11} | {}".format(*header))
    for size in (100, 10_000, 1_000_000):
        r = measure_search(size)
        results[f"search_{size}"] = r
        print(
            f"{size:>9} | {r['recursive']:>10.5f} | {r['iterative']:>10.5f} |"
            f" {r['cached_warm']:>11.5f} | {r['bisect_stdlib']:.5f}"
        )
    print("(час у секундах на 2000 пошуків)")

    fr = measure_fib(25)
    results["fib_25"] = fr
    print(
        f"fib(25): naive={fr['fib_naive']:.5f}s  "
        f"lru_cache={fr['fib_lru_cache']:.6f}s  iter={fr['fib_iter']:.6f}s"
    )
    Path(__file__).with_name("benchmark_results.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
