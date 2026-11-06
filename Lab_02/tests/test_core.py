from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import cast

import pytest

from core import (
    OrderItem,
    Record,
    apply_service,
    build_pipeline,
    check_total,
    compose,
    drop_small_checks,
    juxt,
    normalize_waiters,
    pipe,
    prepare,
    reduce_stats,
    sort_by_check_desc,
    table_zone,
    take,
    with_check,
    with_zone,
)

DATA = Path(__file__).resolve().parent.parent / "sample_data.json"


@pytest.fixture
def records() -> list[Record]:
    with DATA.open(encoding="utf-8") as fh:
        return cast(list[Record], json.load(fh))


def test_check_total() -> None:
    items: list[OrderItem] = [
        {"name": "a", "price": 10.0, "qty": 3},
        {"name": "b", "price": 5.5, "qty": 2},
    ]
    assert check_total(items) == pytest.approx(41.0)
    assert check_total([]) == 0.0


def test_table_zone_boundaries() -> None:
    assert [table_zone(t) for t in (1, 10, 11, 20, 21)] == [
        "hall",
        "hall",
        "terrace",
        "terrace",
        "vip",
    ]


def test_top_n(records: list[Record]) -> None:
    top = build_pipeline(top_n=3, zone="terrace", factor=1.1, min_check=300)(records)
    assert [r["id"] for r in top] == [3, 6, 2]
    assert [r["check"] for r in top] == [2200.0, 550.0, 440.0]


def test_tie_break_by_id(records: list[Record]) -> None:
    # чеки 2, 5, 8 рівні (440) -> порядок за id зростанням
    top = build_pipeline(top_n=6, zone="terrace", factor=1.1, min_check=300)(records)
    assert [r["id"] for r in top] == [3, 6, 2, 5, 8, 1]


def test_top_n_zero_and_larger_than_data(records: list[Record]) -> None:
    assert build_pipeline(top_n=0)(records) == []
    assert len(build_pipeline(top_n=100, min_check=0)(records)) == len(records)


def test_no_mutation(records: list[Record]) -> None:
    original = deepcopy(records)
    build_pipeline()(records)
    reduce_stats(prepare()(records))
    assert records == original


def test_stages_individually(records: list[Record]) -> None:
    norm = list(normalize_waiters()(records))
    assert norm[1]["waiter"] == "Taras"
    zoned = list(with_zone()(norm))
    assert [r["zone"] for r in zoned][:3] == ["hall", "terrace", "vip"]
    checked = list(with_check()(zoned))
    assert checked[0]["check"] == 370.0
    boosted = list(apply_service("vip", 2.0)(checked))
    assert boosted[2]["check"] == 4400.0
    assert boosted[0]["check"] == 370.0  # інша зона — без змін
    small_removed = list(drop_small_checks(300)(checked))
    assert {r["id"] for r in small_removed} == {1, 2, 3, 5, 6, 8}


def test_sort_and_take() -> None:
    recs: list[Record] = [{"id": 2, "check": 5.0}, {"id": 1, "check": 5.0}, {"id": 3}]
    assert [r["id"] for r in sort_by_check_desc()(recs)] == [1, 2, 3]
    assert take(2)(iter(recs)) == recs[:2]
    assert take(-1)(recs) == []


def test_reduce_stats(records: list[Record]) -> None:
    stats = reduce_stats(prepare("terrace", 1.1, 300)(records))
    assert stats == {
        "count": 6,
        "sum_checks": 4440.0,
        "avg_check": 740.0,
        "max_check": 2200.0,
    }


def test_reduce_stats_empty() -> None:
    assert reduce_stats([]) == {
        "count": 0,
        "sum_checks": 0.0,
        "avg_check": 0.0,
        "max_check": 0.0,
    }


def test_compose_pipe_juxt() -> None:
    inc = lambda x: x + 1  # noqa: E731
    dbl = lambda x: x * 2  # noqa: E731
    assert compose(inc, dbl)(5) == 11  # inc(dbl(5))
    assert pipe(5, inc, dbl) == 12  # dbl(inc(5))
    assert compose()(7) == 7  # порожня композиція = identity
    assert juxt(inc, dbl, str)(3) == (4, 6, "3")


def test_pipeline_is_lazy_until_materialized(records: list[Record]) -> None:
    seen: list[int] = []

    def spy(recs: list[Record]) -> object:
        for r in recs:
            seen.append(int(r["id"]))
            yield r

    stage = compose(with_check(), spy)
    gen = stage(records)
    assert seen == []  # ще нічого не обчислено
    next(iter(gen))
    assert seen == [1]
