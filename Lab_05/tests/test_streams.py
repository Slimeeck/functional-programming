from __future__ import annotations

import operator
from itertools import accumulate, count, islice, starmap

import pytest

from streams import (
    chunked,
    counting,
    drop,
    fib_stream,
    geometric,
    geometric_accumulate,
    geometric_count,
    geometric_sum_formula,
    moving_average,
    multiples_window_pipeline,
    naturals,
    primes,
    progression_report,
    ratios,
    running_product,
    running_sum,
    skip_below,
    sliding_window,
    take,
    tee_safe,
    up_to_threshold,
    while_above,
)


# ===================== Геометрична прогресія (варіант 4) ===================
def test_geometric_first_terms() -> None:
    assert take(6, geometric(3, 2)) == [3, 6, 12, 24, 48, 96]
    assert take(4, geometric(1, -2)) == [1, -2, 4, -8]


def test_three_implementations_agree() -> None:
    a = take(15, geometric(1.5, 3))
    b = take(15, geometric_accumulate(1.5, 3))
    c = take(15, geometric_count(1.5, 3))
    assert a == pytest.approx(b) and a == pytest.approx(c)


def test_up_to_threshold_stops_infinite_stream() -> None:
    assert list(up_to_threshold(geometric(3, 2), 100)) == [3, 6, 12, 24, 48, 96]
    assert list(up_to_threshold(geometric(500, 2), 100)) == []  # перший вже > порога


def test_decreasing_progression_while_above() -> None:
    assert list(while_above(geometric(100.0, 0.5), 10)) == [100, 50, 25, 12.5]


def test_skip_below() -> None:
    assert take(3, skip_below(geometric(1, 3), 50)) == [81, 243, 729]


def test_running_sum_and_product() -> None:
    terms = list(up_to_threshold(geometric(1, 2), 16))  # [1, 2, 4, 8, 16]
    assert list(running_sum(terms)) == [1, 3, 7, 15, 31]
    assert list(running_product(terms)) == [1, 2, 8, 64, 1024]


def test_sum_formula_matches_accumulate() -> None:
    for q0, r in ((3.0, 2.0), (5.0, 0.5), (2.0, -3.0), (4.0, 1.0)):
        sums = take(10, running_sum(geometric(q0, r)))
        for n, s in enumerate(sums, start=1):
            assert geometric_sum_formula(q0, r, n) == pytest.approx(s)
    with pytest.raises(ValueError):
        geometric_sum_formula(1, 2, -1)


def test_ratios_are_constant() -> None:
    assert take(5, ratios(geometric(7, 3))) == pytest.approx([3, 3, 3, 3, 3])


def test_progression_report() -> None:
    rows = list(progression_report(2, 3, 60))
    assert rows == [(1, 2, 2, 2), (2, 6, 8, 12), (3, 18, 26, 216), (4, 54, 80, 11664)]


def test_geometric_is_lazy() -> None:
    calls = {"n": 0}

    def inc() -> None:
        calls["n"] += 1

    stream = counting(geometric(1, 2), inc)
    assert calls["n"] == 0  # нічого не обчислено до запиту
    assert take(5, stream) == [1, 2, 4, 8, 16]
    assert calls["n"] == 5  # рівно стільки, скільки запросили

    calls["n"] = 0
    list(up_to_threshold(counting(geometric(1, 2), inc), 10))
    assert calls["n"] == 5  # 1, 2, 4, 8 і перший «зайвий» 16, який зупинив takewhile


# ===================== take / drop =========================================
def test_take_drop_on_count() -> None:
    xs = count(1)
    assert take(5, xs) == [1, 2, 3, 4, 5]
    assert take(3, xs) == [6, 7, 8]  # ітератор уже просунувся


def test_drop_then_take() -> None:
    assert list(islice(drop(10, count(0)), 3)) == [10, 11, 12]


def test_take_drop_edge_cases() -> None:
    assert take(0, count()) == []
    assert take(5, []) == []
    assert list(drop(10, [1, 2, 3])) == []
    assert list(drop(0, [1, 2])) == [1, 2]
    with pytest.raises(ValueError):
        take(-1, [1])
    with pytest.raises(ValueError):
        drop(-1, [1])


# ===================== sliding_window / moving_average =====================
def test_windows_basic() -> None:
    assert list(sliding_window([1, 2, 3, 4], 3)) == [(1, 2, 3), (2, 3, 4)]
    assert list(starmap(lambda *w: sum(w), sliding_window(range(5), 2))) == [1, 3, 5, 7]


def test_window_edge_cases() -> None:
    assert list(sliding_window([], 2)) == []
    assert list(sliding_window([1, 2], 5)) == []  # k > len
    assert list(sliding_window([1, 2], 2)) == [(1, 2)]
    with pytest.raises(ValueError):
        sliding_window([1, 2], 0)  # помилка одразу, а не при next()


def test_moving_average() -> None:
    assert list(moving_average([1, 2, 3, 4, 5], 2)) == [1.5, 2.5, 3.5, 4.5]
    assert take(3, moving_average(geometric(2, 2), 2)) == [3, 6, 12]


# ===================== інші потоки =========================================
def test_fib_stream() -> None:
    assert list(islice(fib_stream(), 10)) == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    assert take(8, drop(5, fib_stream())) == [5, 8, 13, 21, 34, 55, 89, 144]


def test_naturals_and_pipeline() -> None:
    assert take(3, naturals(5)) == [5, 6, 7]
    assert multiples_window_pipeline(3) == [30, 42, 54]


def test_primes() -> None:
    assert take(10, primes()) == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    assert take(100, primes())[-1] == 541


def test_chunked() -> None:
    assert list(chunked(range(7), 3)) == [(0, 1, 2), (3, 4, 5), (6,)]
    assert list(chunked([], 3)) == []
    with pytest.raises(ValueError):
        chunked([1], 0)


def test_tee_safe_independent_copies() -> None:
    a, b = tee_safe(geometric(1, 2), 2)
    assert take(3, a) == [1, 2, 4]
    assert take(5, b) == [1, 2, 4, 8, 16]
    assert take(2, a) == [8, 16]


def test_accumulate_examples() -> None:
    assert list(accumulate([1, 2, 3, 4])) == [1, 3, 6, 10]
    assert list(accumulate([1, 2, 3, 4], operator.mul)) == [1, 2, 6, 24]
    assert list(accumulate([3, 1, 4, 1, 5], max)) == [3, 3, 4, 4, 5]
