"""ЛР3, варіант 4 — «Склад товарів». Незмінна модель даних.

* ``Product``     — frozen dataclass (slots=True);
* ``Movement``    — NamedTuple (рух товару: надходження / відвантаження / ціна);
* ``StockRecord`` — frozen dataclass: товар, залишок, теги (frozenset),
  метадані постачальника (MappingProxyType), історія рухів (tuple).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import Literal, NamedTuple

MovementKind = Literal["in", "out", "price"]


def make_meta(**kwargs: str) -> Mapping[str, str]:
    """Read-only метадані. Спочатку робимо КОПІЮ, щоб зовні ніхто не тримав
    посилання на «живий» dict під proxy."""
    return MappingProxyType(dict(kwargs))


@dataclass(frozen=True, slots=True)
class Product:
    sku: str
    name: str
    price: float
    category: str

    def __post_init__(self) -> None:
        if self.price < 0:
            raise ValueError("price must be non-negative")


class Movement(NamedTuple):
    kind: MovementKind
    qty: int
    note: str = ""


@dataclass(frozen=True, slots=True)
class StockRecord:
    product: Product
    quantity: int
    tags: frozenset[str] = frozenset()
    # MappingProxyType не хешується, тому поле бере участь у ==, але НЕ в hash.
    supplier: Mapping[str, str] = field(default_factory=lambda: make_meta(), hash=False)
    history: tuple[Movement, ...] = ()

    def __post_init__(self) -> None:
        if self.quantity < 0:
            raise ValueError("quantity must be non-negative")

    # --- обчислення (чисті методи) -------------------------------------
    def value(self) -> float:
        """Вартість залишку: ціна * кількість."""
        return self.product.price * self.quantity

    def needs_reorder(self, min_stock: int) -> bool:
        return self.quantity < min_stock

    # --- pure updates (повертають НОВИЙ об'єкт) -------------------------
    def with_quantity(self, quantity: int, movement: Movement) -> StockRecord:
        return replace(self, quantity=quantity, history=self.history + (movement,))

    def with_tag(self, tag: str) -> StockRecord:
        return replace(self, tags=self.tags | frozenset({tag}))
