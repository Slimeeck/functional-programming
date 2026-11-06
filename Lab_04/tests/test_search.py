from __future__ import annotations

import random

import pytest

from algorithms import (
    binary_search_cached,
    binary_search_iterative,
    binary_search_recursive,
    binary_search_tramp,
    binary_search_with_depth,
    find_first,
    linear_search_recursive,
    lower_bound_recursive,
    trampoline,
)

SEQ = (2, 5, 8, 12, 16, 23, 38, 56, 72, 91)


@pytest.mark.parametrize("index, value", list(enumerate(SEQ)))
def test_found_every_element(index: int, value: int) -> None:
    assert binary_search_recursive(SEQ, value) == index
    assert binary_search_iterative(SEQ, value) == index


@pytest.mark.parametrize("missing", [-5, 0, 3, 13, 57, 92, 1000])
def test_missing_values(missing: int) -> None:
    assert binary_search_recursive(SEQ, missing) == -1
    assert binary_search_iterative(SEQ, missing) == -1


def test_edge_cases_empty_and_single() -> None:
    assert binary_search_recursive((), 1) == -1
    assert binary_search_iterative((), 1) == -1
    assert binary_search_recursive((7,), 7) == 0
    assert binary_search_recursive((7,), 8) == -1


def test_first_and_last_and_strings() -> None:
    assert binary_search_recursive(SEQ, SEQ[0]) == 0
    assert binary_search_recursive(SEQ, SEQ[-1]) == len(SEQ) - 1
    words = ("ant", "bee", "cat", "dog")
    assert binary_search_recursive(words, "cat") == 2
    assert binary_search_recursive(words, "cow") == -1


def test_input_is_not_mutated() -> None:
    data = [1, 3, 5, 7]
    snapshot = list(data)
    binary_search_recursive(data, 5)
    assert data == snapshot


def test_duplicates_lower_bound() -> None:
    seq = (1, 2, 2, 2, 3)
    assert find_first(seq, 2) == 1
    assert find_first(seq, 4) == -1
    assert lower_bound_recursive(seq, 0) == 0
    assert lower_bound_recursive(seq, 99) == len(seq)


def test_recursive_matches_iterative_random() -> None:
    rng = random.Random(0)
    seq = tuple(sorted(rng.sample(range(10_000), 500)))
    for target in rng.sample(range(10_000), 300):
        expected = seq.index(target) if target in seq else -1
        assert binary_search_recursive(seq, target) == expected
        assert binary_search_iterative(seq, target) == expected


def test_depth_is_logarithmic() -> None:
    seq = tuple(range(1_000_000))
    _, depth = binary_search_with_depth(seq, -1)
    assert depth <= 21  # ceil(log2(1e6)) + 1


def test_linear_recursion_hits_limit_but_binary_does_not() -> None:
    seq = tuple(range(5000))
    with pytest.raises(RecursionError):
        linear_search_recursive(seq, 4999)
    assert binary_search_recursive(seq, 4999) == 4999


def test_trampoline_search() -> None:
    seq = tuple(range(0, 100, 5))
    assert trampoline(binary_search_tramp(seq, 35, 0, len(seq) - 1)) == 7
    assert trampoline(binary_search_tramp(seq, 36, 0, len(seq) - 1)) == -1


def test_cache_info_and_clear() -> None:
    binary_search_cached.cache_clear()
    binary_search_cached(SEQ, 23)
    binary_search_cached(SEQ, 23)
    binary_search_cached(SEQ, 24)
    info = binary_search_cached.cache_info()
    assert (info.hits, info.misses, info.currsize) == (1, 2, 2)
    binary_search_cached.cache_clear()
    assert binary_search_cached.cache_info().currsize == 0
