"""Чисте обчислювальне ядро ЛР1, варіант 4 — «Кошик покупця».

У цьому модулі немає I/O, глобального змінного стану та мутацій вхідних даних.
Усі політики (фільтр, категоріальна знижка, купон, ПДВ) передаються явно
як функції типу ``typing.Callable``.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from types import MappingProxyType
from typing import TypedDict, TypeVar

A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")


# ---------------------------------------------------------------------------
# Модель даних
# ---------------------------------------------------------------------------
class CartItem(TypedDict):
    """Позиція кошика: назва, ціна за одиницю, кількість, категорія."""

    name: str
    price: float
    qty: int
    category: str


class PricedItem(CartItem):
    """НОВА позиція кошика з розрахованими полями (вхідна не змінюється)."""

    line_total: float
    discount: float
    discounted_total: float


class CartSummary(TypedDict):
    """Результат обробки кошика — новий кошик із підсумками."""

    items: list[PricedItem]
    count: int
    subtotal: float
    category_discount: float
    after_discount: float
    coupon_discount: float
    after_coupon: float
    vat: float
    total: float


# ---------------------------------------------------------------------------
# Типи політик (typing.Callable)
# ---------------------------------------------------------------------------
ItemFilterFn = Callable[[CartItem], bool]  # чи враховувати позицію
CategoryDiscountFn = Callable[[CartItem, float], float]  # (позиція, сума) -> знижка
CouponFn = Callable[[float], float]  # сума -> сума після купона
TaxFn = Callable[[float], float]  # сума без ПДВ -> сума ПДВ
NowFn = Callable[[], float]  # постачальник часу (інжекція залежності)
CartProcessor = Callable[[Iterable[CartItem]], CartSummary]


# ---------------------------------------------------------------------------
# Чисті функції предметної області
# ---------------------------------------------------------------------------
def round_money(value: float) -> float:
    """Округлення грошової суми до копійок."""
    return round(value + 0.0, 2)


def line_total(item: CartItem) -> float:
    """Вартість однієї позиції: price * qty."""
    return item["price"] * item["qty"]


def cart_subtotal(items: Iterable[CartItem]) -> float:
    """Subtotal кошика — сума вартостей усіх позицій."""
    return sum(line_total(it) for it in items)


def with_pricing(item: CartItem, discount: float) -> PricedItem:
    """Повертає НОВИЙ словник з розрахунковими полями (без мутації ``item``)."""
    total = line_total(item)
    return {
        "name": item["name"],
        "price": item["price"],
        "qty": item["qty"],
        "category": item["category"],
        "line_total": round_money(total),
        "discount": round_money(discount),
        "discounted_total": round_money(total - discount),
    }


def is_valid_item(item: CartItem) -> bool:
    """Стандартний фільтр: позиція з додатною ціною та кількістю."""
    return item["price"] > 0 and item["qty"] > 0


# ---------------------------------------------------------------------------
# Фабрики політик (функції вищого порядку, що повертають Callable)
# ---------------------------------------------------------------------------
def make_category_discount(rates: Mapping[str, float]) -> CategoryDiscountFn:
    """Категоріальна знижка: ``rates`` — частка знижки для кожної категорії.

    Копія словника робиться всередині, тож зміна оригіналу ззовні не впливає
    на вже створену політику (референтна прозорість).
    """
    frozen_rates = dict(rates)

    def discount(item: CartItem, amount: float) -> float:
        return amount * frozen_rates.get(item["category"], 0.0)

    return discount


def make_percent_coupon(percent: float, min_amount: float = 0.0) -> CouponFn:
    """Купон на відсоток від суми, діє якщо сума >= ``min_amount``."""

    def coupon(amount: float) -> float:
        return amount * (1 - percent) if amount >= min_amount else amount

    return coupon


def make_fixed_coupon(value: float, min_amount: float = 0.0) -> CouponFn:
    """Купон на фіксовану суму (сума не може стати від'ємною)."""

    def coupon(amount: float) -> float:
        return max(amount - value, 0.0) if amount >= min_amount else amount

    return coupon


def make_percent_discount(percent: float) -> Callable[[float], float]:
    """Проста знижка на ``percent`` від суми (будівельний блок для compose)."""
    return lambda amount: amount * (1 - percent)


def no_coupon(amount: float) -> float:
    """Нейтральна політика: купона немає."""
    return amount


def make_vat(rate: float) -> TaxFn:
    """ПДВ як функція: повертає суму податку для заданої бази."""
    return lambda amount: amount * rate


def make_min_price_filter(min_price: float) -> ItemFilterFn:
    """Фільтр позицій за мінімальною ціною одиниці товару."""
    return lambda item: is_valid_item(item) and item["price"] >= min_price


# ---------------------------------------------------------------------------
# Композиція та допоміжні HOF
# ---------------------------------------------------------------------------
def compose(f: Callable[[B], C], g: Callable[[A], B]) -> Callable[[A], C]:
    """compose(f, g)(x) == f(g(x))."""
    return lambda x: f(g(x))


def make_multiplier(k: int) -> Callable[[int], int]:
    """Фабрика множників: make_multiplier(3)(5) == 15."""
    return lambda x: x * k


def double_quantities(items: Iterable[CartItem]) -> list[CartItem]:
    """Приклад «без мутацій»: новий список з подвоєною кількістю (map)."""
    return [{**it, "qty": it["qty"] * 2} for it in items]


def only_category(items: Iterable[CartItem], category: str) -> list[CartItem]:
    """Новий список лише з позиціями обраної категорії (filter)."""
    return list(filter(lambda it: it["category"] == category, items))


def stamp_total(total: float, now: NowFn) -> tuple[float, float]:
    """Чиста щодо ``total``; час «приходить ззовні» через Callable."""
    return total, now()


# ---------------------------------------------------------------------------
# Головний обробник
# ---------------------------------------------------------------------------
def make_cart_processor(
    *,
    accept: ItemFilterFn,
    category_discount: CategoryDiscountFn,
    apply_coupon: CouponFn,
    vat: TaxFn,
) -> CartProcessor:
    """Функція вищого порядку: повертає налаштований обробник кошика.

    Порядок розрахунку:
    subtotal -> категоріальна знижка -> купон -> ПДВ -> total.
    """

    def process(items: Iterable[CartItem]) -> CartSummary:
        accepted = [it for it in items if accept(it)]
        priced = [
            with_pricing(it, category_discount(it, line_total(it))) for it in accepted
        ]
        subtotal = sum(p["line_total"] for p in priced)
        cat_discount = sum(p["discount"] for p in priced)
        after_discount = subtotal - cat_discount
        after_coupon = apply_coupon(after_discount)
        vat_amount = vat(after_coupon)
        return {
            "items": priced,
            "count": len(priced),
            "subtotal": round_money(subtotal),
            "category_discount": round_money(cat_discount),
            "after_discount": round_money(after_discount),
            "coupon_discount": round_money(after_discount - after_coupon),
            "after_coupon": round_money(after_coupon),
            "vat": round_money(vat_amount),
            "total": round_money(after_coupon + vat_amount),
        }

    return process


def process_cart_pure(
    items: Iterable[CartItem],
    *,
    category_rates: Mapping[str, float],
    coupon_percent: float,
    coupon_min: float,
    vat_rate: float,
) -> CartSummary:
    """Варіант без Callable-параметрів: усі числові параметри передаються явно."""
    processor = make_cart_processor(
        accept=is_valid_item,
        category_discount=make_category_discount(category_rates),
        apply_coupon=make_percent_coupon(coupon_percent, coupon_min),
        vat=make_vat(vat_rate),
    )
    return processor(items)


# Конфігурація за замовчуванням (тільки для читання). Ядро її не використовує —
# вона лише передається явно у фабрику нижче.
DEFAULT_CATEGORY_RATES: Mapping[str, float] = MappingProxyType(
    {"electronics": 0.10, "books": 0.05, "food": 0.0}
)


def create_default_processor() -> CartProcessor:
    """Стандартна конфігурація: знижки за категоріями, купон 5% від 1000, ПДВ 20%."""
    return make_cart_processor(
        accept=is_valid_item,
        category_discount=make_category_discount(DEFAULT_CATEGORY_RATES),
        apply_coupon=make_percent_coupon(0.05, min_amount=1000.0),
        vat=make_vat(0.20),
    )
