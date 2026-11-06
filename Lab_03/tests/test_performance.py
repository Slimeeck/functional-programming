"""Порівняння часу операцій: мутабельна модель (baseline) vs незмінна (model/core).

Запуск із виводом:  pytest -q -s --durations=5
"""

from __future__ import annotations

from timeit import timeit

from baseline import (
    MutableStockRecord,
    mutable_add_tag,
    mutable_change_price,
    mutable_restock,
)
from core import add_tag, change_price, create_example_stock, restock

ITERATIONS = 5_000


def test_compare_mutable_vs_immutable_updates() -> None:
    def mutable_operation() -> None:
        r = MutableStockRecord("EL-002", "Клавіатура", 1350.0, "electronics", 3)
        mutable_restock(r, 10)
        mutable_change_price(r, 1500.0)
        mutable_add_tag(r, "promo")

    template = create_example_stock()[1]

    def immutable_operation() -> None:
        add_tag(change_price(restock(template, 10), 1500.0), "promo")

    mutable_s = timeit(mutable_operation, number=ITERATIONS)
    immutable_s = timeit(immutable_operation, number=ITERATIONS)
    print(f"\nmutable   : {mutable_s:.4f} s / {ITERATIONS} iterations")
    print(f"immutable : {immutable_s:.4f} s / {ITERATIONS} iterations")
    print(f"ratio     : x{immutable_s / mutable_s:.2f}")
    assert mutable_s > 0 and immutable_s > 0


def test_immutable_large_batch() -> None:
    record = create_example_stock()[0]
    versions = [restock(record, i + 1) for i in range(20_000)]
    assert versions[-1].quantity == record.quantity + 20_000
    assert record.quantity == 12


def test_mutable_large_batch() -> None:
    r = MutableStockRecord("EL-001", "Монітор", 8200.0, "electronics", 12)
    for i in range(20_000):
        mutable_restock(r, i + 1)
    assert r.quantity == 12 + sum(range(1, 20_001))
