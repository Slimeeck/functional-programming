from __future__ import annotations

import pytest

from algorithms import fact_tail, fact_tramp, fib, fib_iter, fib_naive, trampoline


def test_fib_small() -> None:
    expected = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    assert [fib(i) for i in range(10)] == expected
    assert [fib_naive(i) for i in range(10)] == expected


def test_fib_iter_matches() -> None:
    for n in range(50):
        assert fib(n) == fib_iter(n)


def test_cache_clear_and_info() -> None:
    fib.cache_clear()
    assert fib.cache_info().currsize == 0
    fib(30)
    info = fib.cache_info()
    assert info.misses == 31 and info.currsize == 31
    fib(30)
    assert fib.cache_info().hits == info.hits + 1


def test_negative_input() -> None:
    for fn in (fib, fib_iter, fib_naive):
        with pytest.raises(ValueError):
            fn(-1)


def test_tail_recursion_no_tco_and_trampoline() -> None:
    assert fact_tail(5) == 120
    with pytest.raises(RecursionError):
        fact_tail(10_000)
    assert trampoline(fact_tramp(5)) == 120
    assert trampoline(fact_tramp(10_000)) > 0  # без RecursionError
