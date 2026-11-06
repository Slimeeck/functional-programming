"""Pure-оновлення та бізнес-функції складу (ЛР3, варіант 4).

Жодна функція не змінює вхідний ``StockRecord`` — усі повертають нову копію
через ``dataclasses.replace``, конкатенацію tuple або операції frozenset.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import replace
from functools import lru_cache
from types import MappingProxyType
from typing import Any

from model import Movement, Product, StockRecord, make_meta


# ---------------------------------------------------------------------------
# Pure updates
# ---------------------------------------------------------------------------
def restock(record: StockRecord, qty: int, note: str = "") -> StockRecord:
    """Поповнення залишку."""
    if qty <= 0:
        raise ValueError("restock quantity must be positive")
    return record.with_quantity(record.quantity + qty, Movement("in", qty, note))


def ship(record: StockRecord, qty: int, note: str = "") -> StockRecord:
    """Відвантаження (списання) товару."""
    if qty <= 0:
        raise ValueError("ship quantity must be positive")
    if qty > record.quantity:
        raise ValueError("not enough stock")
    return record.with_quantity(record.quantity - qty, Movement("out", qty, note))


def change_price(record: StockRecord, new_price: float) -> StockRecord:
    """Зміна ціни: новий Product усередині нового StockRecord."""
    new_product = replace(record.product, price=new_price)  # валідація у Product
    movement = Movement("price", 0, f"{record.product.price} -> {new_price}")
    return replace(record, product=new_product, history=record.history + (movement,))


def add_tag(record: StockRecord, tag: str) -> StockRecord:
    """Додавання тегу (frozenset |)."""
    clean = tag.strip().lower()
    if not clean:
        raise ValueError("tag must not be empty")
    return record.with_tag(clean)


def remove_tag(record: StockRecord, tag: str) -> StockRecord:
    """Видалення тегу (frozenset -)."""
    return replace(record, tags=record.tags - frozenset({tag}))


def update_supplier(record: StockRecord, **changes: str) -> StockRecord:
    """Нові метадані постачальника = копія старих + зміни, знову read-only."""
    return replace(record, supplier=make_meta(**{**record.supplier, **changes}))


def apply_clearance_discount(record: StockRecord, percent: float) -> StockRecord:
    """Правило знижки як чиста функція: лише для товарів з тегом ``clearance``."""
    if not 0 <= percent < 1:
        raise ValueError("percent must be in [0, 1)")
    if "clearance" not in record.tags:
        return record
    return change_price(record, round(record.product.price * (1 - percent), 2))


# ---------------------------------------------------------------------------
# Запити над колекцією (Sequence -> tuple)
# ---------------------------------------------------------------------------
def records_to_reorder(
    records: Sequence[StockRecord], min_stock: int
) -> tuple[StockRecord, ...]:
    return tuple(r for r in records if r.needs_reorder(min_stock))


def by_tag(records: Iterable[StockRecord], tag: str) -> tuple[StockRecord, ...]:
    return tuple(r for r in records if tag in r.tags)


def top_by_value(records: Sequence[StockRecord], n: int = 3) -> tuple[StockRecord, ...]:
    return tuple(sorted(records, key=lambda r: r.value(), reverse=True)[:n])


def supplier_name(meta: Mapping[str, str]) -> str:
    return meta.get("name", "unknown")


@lru_cache(maxsize=128)
def total_inventory_value(records: tuple[StockRecord, ...]) -> float:
    """Кешована чиста функція: tuple з хешованих StockRecord — валідний ключ."""
    return round(sum(r.value() for r in records), 2)


def index_by_record(records: Iterable[StockRecord]) -> dict[StockRecord, str]:
    """StockRecord хешований, тож може бути ключем dict."""
    return {r: r.product.sku for r in records}


# ---------------------------------------------------------------------------
# Глибоке заморожування
# ---------------------------------------------------------------------------
def freeze(obj: Any) -> Any:
    """Рекурсивно: dict -> MappingProxyType, set -> frozenset, list -> tuple."""
    if isinstance(obj, Mapping):
        return MappingProxyType({k: freeze(v) for k, v in obj.items()})
    if isinstance(obj, (set, frozenset)):
        return frozenset(freeze(x) for x in obj)
    if isinstance(obj, (list, tuple)):
        return tuple(freeze(x) for x in obj)
    return obj


# ---------------------------------------------------------------------------
# Приклад даних
# ---------------------------------------------------------------------------
def create_example_stock() -> tuple[StockRecord, ...]:
    supplier_a = make_meta(name="ТОВ Техно", country="UA", phone="+380441112233")
    supplier_b = make_meta(name="Office Group", country="PL")
    return (
        StockRecord(
            Product("EL-001", "Монітор 27''", 8200.0, "electronics"),
            quantity=12,
            tags=frozenset({"popular"}),
            supplier=supplier_a,
        ),
        StockRecord(
            Product("EL-002", "Клавіатура", 1350.0, "electronics"),
            quantity=3,
            tags=frozenset({"clearance"}),
            supplier=supplier_a,
        ),
        StockRecord(
            Product("OF-010", "Папір A4", 260.0, "office"),
            quantity=140,
            tags=frozenset({"bulk"}),
            supplier=supplier_b,
        ),
        StockRecord(
            Product("OF-011", "Степлер", 180.0, "office"),
            quantity=2,
            supplier=supplier_b,
        ),
    )
