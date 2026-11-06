"""Оболонка побічних ефектів ЛР1: лише виведення результату на екран.

Усі обчислення виконуються в ``core.py``; тут дані тільки споживаються.
"""

from __future__ import annotations

import time

from core import (
    CartItem,
    CartSummary,
    compose,
    create_default_processor,
    make_cart_processor,
    make_category_discount,
    make_fixed_coupon,
    make_min_price_filter,
    make_percent_discount,
    make_vat,
    stamp_total,
)

SAMPLE_CART: tuple[CartItem, ...] = (
    {"name": "Ноутбук", "price": 25000.0, "qty": 1, "category": "electronics"},
    {"name": "Мишка", "price": 450.0, "qty": 2, "category": "electronics"},
    {"name": "Книга Python", "price": 520.0, "qty": 1, "category": "books"},
    {"name": "Кава", "price": 310.0, "qty": 3, "category": "food"},
    {"name": "Подарунок", "price": 0.0, "qty": 1, "category": "promo"},
)


def render_report(title: str, result: CartSummary) -> None:
    """Єдине місце, де виконується print."""
    print("=" * 64)
    print(title)
    print("=" * 64)
    print(f"{'Товар':<16}{'Кат.':<13}{'Ціна':>9}{'К-ть':>6}{'Сума':>10}{'Знижка':>9}")
    for it in result["items"]:
        print(
            f"{it['name']:<16}{it['category']:<13}{it['price']:>9.2f}"
            f"{it['qty']:>6}{it['line_total']:>10.2f}{it['discount']:>9.2f}"
        )
    print("-" * 64)
    print(f"Позицій у розрахунку:   {result['count']}")
    print(f"Subtotal:               {result['subtotal']:.2f}")
    print(f"Категоріальна знижка:  -{result['category_discount']:.2f}")
    print(f"Після знижки:           {result['after_discount']:.2f}")
    print(f"Купон:                 -{result['coupon_discount']:.2f}")
    print(f"Після купона:           {result['after_coupon']:.2f}")
    print(f"ПДВ:                   +{result['vat']:.2f}")
    print(f"ДО СПЛАТИ:              {result['total']:.2f}")
    print()


def run() -> None:
    # 1) Стандартна політика
    default_result = create_default_processor()(SAMPLE_CART)
    render_report(
        "Кошик — стандартна політика (купон 5% від 1000, ПДВ 20%)", default_result
    )

    # 2) Інша політика без зміни ядра: фіксований купон, ПДВ 7%, фільтр ціни
    custom = make_cart_processor(
        accept=make_min_price_filter(400.0),
        category_discount=make_category_discount({"electronics": 0.15}),
        apply_coupon=make_fixed_coupon(500.0, min_amount=2000.0),
        vat=make_vat(0.07),
    )
    render_report(
        "Кошик — альтернативна політика (купон -500, ПДВ 7%)", custom(SAMPLE_CART)
    )

    # 3) Композиція маленьких функцій: знижка 10% + купон -100
    discount_then_coupon = compose(
        make_fixed_coupon(100.0), make_percent_discount(0.10)
    )
    print("compose(купон -100, знижка 10%)(1000) =", discount_then_coupon(1000.0))

    # 4) Інжекція часу: ядро лишається чистим, time.time — лише тут
    total, ts = stamp_total(default_result["total"], time.time)
    stamp = time.strftime("%H:%M:%S", time.localtime(ts))
    print(f"Сума {total:.2f} зафіксована о {stamp}")


if __name__ == "__main__":
    run()
