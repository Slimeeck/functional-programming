"""Мутабельна версія моделі складу — ТІЛЬКИ для порівняння «до / після».

Тут навмисно використано list / set / dict і in-place зміни.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MutableStockRecord:
    sku: str
    name: str
    price: float
    category: str
    quantity: int
    tags: set[str] = field(default_factory=set)
    supplier: dict[str, str] = field(default_factory=dict)
    history: list[tuple[str, int, str]] = field(default_factory=list)


def mutable_restock(record: MutableStockRecord, qty: int) -> MutableStockRecord:
    record.quantity += qty
    record.history.append(("in", qty, ""))
    return record


def mutable_change_price(
    record: MutableStockRecord, price: float
) -> MutableStockRecord:
    record.history.append(("price", 0, f"{record.price} -> {price}"))
    record.price = price
    return record


def mutable_add_tag(record: MutableStockRecord, tag: str) -> MutableStockRecord:
    record.tags.add(tag)
    return record
