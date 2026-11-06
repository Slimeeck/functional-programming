from __future__ import annotations

import random

from algorithms import (
    hybrid_sort,
    insertion_sort,
    median_of_three,
    quicksort,
    quicksort_3way,
)


def test_quicksort_basic() -> None:
    assert quicksort([]) == []
    assert quicksort([1]) == [1]
    assert quicksort([3, 2, 1]) == [1, 2, 3]
    assert quicksort([2, 2, 1, 3, 2]) == [1, 2, 2, 2, 3]


def test_quicksort_random_against_sorted() -> None:
    rng = random.Random(7)
    xs = [rng.randint(-1000, 1000) for _ in range(1000)]
    assert quicksort(xs) == sorted(xs)
    assert quicksort_3way(xs) == sorted(xs)
    assert hybrid_sort(xs) == sorted(xs)


def test_many_duplicates_3way() -> None:
    xs = [5] * 500 + [1] * 300 + [9] * 200
    assert quicksort_3way(xs) == sorted(xs)


def test_quicksort_does_not_mutate() -> None:
    xs = [3, 1, 2]
    quicksort(xs)
    quicksort_3way(xs)
    assert xs == [3, 1, 2]


def test_insertion_and_median() -> None:
    assert insertion_sort([4, 1, 3, 1]) == [1, 1, 3, 4]
    assert median_of_three(1, 2, 3) == 2
    assert median_of_three(3, 1, 2) == 2
    assert median_of_three(2, 3, 1) == 2
