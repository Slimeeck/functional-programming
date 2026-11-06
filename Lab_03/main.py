"""Демонстрація ЛР3 (варіант 4 — склад товарів): python main.py"""

from __future__ import annotations

from core import (
    add_tag,
    apply_clearance_discount,
    change_price,
    create_example_stock,
    records_to_reorder,
    restock,
    supplier_name,
    top_by_value,
    total_inventory_value,
    update_supplier,
)
from model import StockRecord


def show(title: str, r: StockRecord) -> None:
    tags = ", ".join(sorted(r.tags)) or "-"
    print(
        f"{title:<22} {r.product.sku} {r.product.name:<14} ціна={r.product.price:>8.2f}"
        f" к-ть={r.quantity:>4} теги=[{tags}]"
    )


def main() -> None:
    stock = create_example_stock()
    keyboard = stock[1]

    print("=== Pure updates: кожна операція повертає НОВИЙ StockRecord ===")
    show("Початковий запис:", keyboard)
    v1 = restock(keyboard, 20, "поставка №17")
    show("Після restock(+20):", v1)
    v2 = change_price(v1, 1500.0)
    show("Після change_price:", v2)
    v3 = add_tag(v2, "Promo")
    show("Після add_tag:", v3)
    v4 = apply_clearance_discount(v3, 0.2)
    show("Після знижки 20%:", v4)
    show("Оригінал (без змін):", keyboard)
    print("keyboard is v4:", keyboard is v4, "| keyboard == v4:", keyboard == v4)
    print("Історія v4:", [tuple(m) for m in v4.history])

    print("\n=== Read-only метадані постачальника ===")
    print("Постачальник:", supplier_name(keyboard.supplier), dict(keyboard.supplier))
    try:
        keyboard.supplier["name"] = "Hacker"  # type: ignore[index]
    except TypeError as err:
        print("Спроба змінити meta ->", type(err).__name__, ":", err)
    v5 = update_supplier(keyboard, phone="+380500000000")
    print("Нові meta:", dict(v5.supplier))
    print("Старі meta:", dict(keyboard.supplier))

    print("\n=== Хешованість ===")
    index = {keyboard: "v0", v4: "v4"}
    print("StockRecord як ключ dict:", list(index.values()))
    print("hash(v0) != hash(v4):", hash(keyboard) != hash(v4))

    print("\n=== Запити над складом ===")
    print(
        "Потрібне дозамовлення (< 5 шт.):",
        [r.product.sku for r in records_to_reorder(stock, 5)],
    )
    print("Top-2 за вартістю:", [r.product.sku for r in top_by_value(stock, 2)])
    print("Вартість складу:", total_inventory_value(stock))
    print("Вартість складу (з кешу):", total_inventory_value(stock))
    print("lru_cache:", total_inventory_value.cache_info())


if __name__ == "__main__":
    main()
