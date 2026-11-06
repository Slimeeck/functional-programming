from __future__ import annotations

from copy import deepcopy

import pytest

from core import (
    CartItem,
    CartSummary,
    CategoryDiscountFn,
    CouponFn,
    TaxFn,
    cart_subtotal,
    compose,
    create_default_processor,
    double_quantities,
    is_valid_item,
    line_total,
    make_cart_processor,
    make_category_discount,
    make_fixed_coupon,
    make_min_price_filter,
    make_multiplier,
    make_percent_coupon,
    make_percent_discount,
    make_vat,
    no_coupon,
    only_category,
    process_cart_pure,
    stamp_total,
    with_pricing,
)


@pytest.fixture
def sample_cart() -> list[CartItem]:
    return [
        {"name": "Ноутбук", "price": 1000.0, "qty": 1, "category": "electronics"},
        {"name": "Книга", "price": 200.0, "qty": 2, "category": "books"},
        {"name": "Кава", "price": 50.0, "qty": 4, "category": "food"},
        {"name": "Брак", "price": 0.0, "qty": 3, "category": "promo"},
    ]


def pure(items: list[CartItem]) -> CartSummary:
    """Обробка з явно переданими параметрами (без глобалів)."""
    return process_cart_pure(
        items,
        category_rates={"electronics": 0.10, "books": 0.05},
        coupon_percent=0.05,
        coupon_min=1000.0,
        vat_rate=0.20,
    )


# --- базові чисті функції -------------------------------------------------
def test_line_total_and_subtotal(sample_cart: list[CartItem]) -> None:
    assert line_total(sample_cart[1]) == 400.0
    assert cart_subtotal(sample_cart) == 1600.0
    assert cart_subtotal([]) == 0.0


def test_with_pricing_returns_new_dict(sample_cart: list[CartItem]) -> None:
    item = sample_cart[0]
    priced = with_pricing(item, 100.0)
    assert priced is not item
    assert priced["discounted_total"] == 900.0
    assert "line_total" not in item  # вхідний словник не змінився


def test_is_valid_item(sample_cart: list[CartItem]) -> None:
    assert [is_valid_item(it) for it in sample_cart] == [True, True, True, False]


# --- референтна прозорість та відсутність мутацій -------------------------
def test_referential_transparency(sample_cart: list[CartItem]) -> None:
    r1 = pure(sample_cart)
    r2 = pure(sample_cart)
    assert r1 == r2  # той самий вхід -> той самий вихід


def test_no_mutation(sample_cart: list[CartItem]) -> None:
    original = deepcopy(sample_cart)
    pure(sample_cart)
    create_default_processor()(sample_cart)
    double_quantities(sample_cart)
    assert sample_cart == original  # вхід не змінюється


def test_result_items_are_new_objects(sample_cart: list[CartItem]) -> None:
    result = create_default_processor()(sample_cart)
    for new, old in zip(result["items"], sample_cart, strict=False):
        assert new is not old


# --- правильність розрахунку -----------------------------------------------
def test_full_calculation(sample_cart: list[CartItem]) -> None:
    r = pure(sample_cart)
    assert r["count"] == 3  # «Брак» з ціною 0 відфільтровано
    assert r["subtotal"] == pytest.approx(1600.0)
    assert r["category_discount"] == pytest.approx(120.0)  # 100 + 20 + 0
    assert r["after_discount"] == pytest.approx(1480.0)
    assert r["coupon_discount"] == pytest.approx(74.0)  # 5% від 1480
    assert r["after_coupon"] == pytest.approx(1406.0)
    assert r["vat"] == pytest.approx(281.2)
    assert r["total"] == pytest.approx(1687.2)


def test_coupon_not_applied_below_minimum() -> None:
    cart: list[CartItem] = [
        {"name": "Ручка", "price": 10.0, "qty": 5, "category": "office"}
    ]
    r = pure(cart)
    assert r["coupon_discount"] == 0.0
    assert r["total"] == pytest.approx(60.0)


def test_empty_cart() -> None:
    r = create_default_processor()([])
    assert r["count"] == 0
    assert r["total"] == 0.0


# --- Callable-політики -----------------------------------------------------
def test_callable_policies(sample_cart: list[CartItem]) -> None:
    def books_half_price(item: CartItem, amount: float) -> float:
        return amount * 0.5 if item["category"] == "books" else 0.0

    category_discount: CategoryDiscountFn = books_half_price

    def minus_ten(amount: float) -> float:
        return amount - 10

    def vat_10(amount: float) -> float:
        return amount * 0.1

    apply_coupon: CouponFn = minus_ten
    vat: TaxFn = vat_10
    processor = make_cart_processor(
        accept=lambda it: it["price"] >= 100,
        category_discount=category_discount,
        apply_coupon=apply_coupon,
        vat=vat,
    )
    r = processor(sample_cart)
    # приймаються Ноутбук (1000) і Книга (400); знижка 50% на книги = 200
    assert r["count"] == 2
    assert r["subtotal"] == pytest.approx(1400.0)
    assert r["after_discount"] == pytest.approx(1200.0)
    assert r["after_coupon"] == pytest.approx(1190.0)
    assert r["total"] == pytest.approx(1309.0)


def test_policy_factories() -> None:
    item: CartItem = {"name": "x", "price": 100.0, "qty": 1, "category": "books"}
    assert make_category_discount({"books": 0.2})(item, 100.0) == pytest.approx(20.0)
    assert make_category_discount({})(item, 100.0) == 0.0
    assert make_percent_coupon(0.1)(200.0) == pytest.approx(180.0)
    assert make_percent_coupon(0.1, 500.0)(200.0) == 200.0
    assert make_fixed_coupon(50.0)(30.0) == 0.0
    assert make_vat(0.2)(100.0) == pytest.approx(20.0)
    assert no_coupon(123.0) == 123.0
    assert make_min_price_filter(150.0)(item) is False


def test_policy_does_not_depend_on_external_dict_changes() -> None:
    rates = {"books": 0.2}
    policy = make_category_discount(rates)
    rates["books"] = 0.9  # зміна оригіналу після створення політики
    item: CartItem = {"name": "x", "price": 100.0, "qty": 1, "category": "books"}
    assert policy(item, 100.0) == pytest.approx(20.0)


# --- додаткові вправи -----------------------------------------------------
def test_compose_and_multiplier() -> None:
    discount_then_coupon = compose(
        make_fixed_coupon(100.0), make_percent_discount(0.10)
    )
    assert discount_then_coupon(1000.0) == pytest.approx(800.0)
    triple = make_multiplier(3)
    assert triple(5) == 15
    assert compose(triple, make_multiplier(2))(1) == 6


def test_map_filter_helpers(sample_cart: list[CartItem]) -> None:
    assert [it["qty"] for it in double_quantities(sample_cart)] == [2, 4, 8, 6]
    assert [it["name"] for it in only_category(sample_cart, "books")] == ["Книга"]


def test_stamp_total_uses_injected_clock() -> None:
    assert stamp_total(99.5, lambda: 1234.0) == (99.5, 1234.0)
