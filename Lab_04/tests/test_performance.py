"""Порівняння часу: recursive vs iterative пошук, fib з lru_cache vs без кешу."""

from __future__ import annotations

from timeit import timeit

from algorithms import (
    binary_search_iterative,
    binary_search_recursive,
    fib,
    fib_iter,
    fib_naive,
)


def test_search_recursive_vs_iterative() -> None:
    seq = tuple(range(0, 200_000, 2))
    targets = list(range(0, 200_000, 97))
    rec = timeit(lambda: [binary_search_recursive(seq, t) for t in targets], number=3)
    it = timeit(lambda: [binary_search_iterative(seq, t) for t in targets], number=3)
    print(f"\nrecursive: {rec:.4f}s  iterative: {it:.4f}s  ratio: x{rec / it:.2f}")
    assert [binary_search_recursive(seq, t) for t in targets] == [
        binary_search_iterative(seq, t) for t in targets
    ]


def test_fib_memoization_speedup() -> None:
    naive = timeit(lambda: fib_naive(22), number=1)

    def cached_run() -> int:
        fib.cache_clear()
        return fib(22)

    cached = timeit(cached_run, number=1)
    iterative = timeit(lambda: fib_iter(22), number=1)
    print(f"\nfib(22) naive={naive:.5f}s lru_cache={cached:.6f}s iter={iterative:.6f}s")
    assert cached < naive
