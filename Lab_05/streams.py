"""ЛР5. Ліниві обчислення: генератори та itertools.

Варіант 4 — «Геометрична прогресія»:
    вхід — початкове значення q0 і множник r;
    створити НЕСКІНЧЕННИЙ генератор, взяти значення до порога (takewhile)
    та обчислити накопичений добуток / суму (accumulate).

Також реалізовано базові утиліти ЛР: take, drop, sliding_window, moving_average,
fib_stream, naturals, chunked, tee_safe, primes.
"""

from __future__ import annotations

import operator
from collections import deque
from collections.abc import Callable, Iterable, Iterator
from functools import partial
from itertools import (
    accumulate,
    count,
    dropwhile,
    islice,
    repeat,
    starmap,
    takewhile,
    tee,
)
from math import isqrt
from typing import TypeVar

T = TypeVar("T")
Number = TypeVar("Number", int, float)


# ===========================================================================
# 1. Геометрична прогресія (варіант 4)
# ===========================================================================
def geometric(q0: float, r: float) -> Iterator[float]:
    """Нескінченний генератор q0, q0*r, q0*r^2, ... (власний yield)."""
    value = q0
    while True:
        yield value
        value *= r


def geometric_accumulate(q0: float, r: float) -> Iterator[float]:
    """Та сама прогресія через itertools: accumulate(repeat(r), mul, initial=q0)."""
    return accumulate(repeat(r), operator.mul, initial=q0)


def geometric_count(q0: float, r: float) -> Iterator[float]:
    """Та сама прогресія через count: q0 * r**n для n = 0, 1, 2, ..."""
    return (q0 * r**n for n in count())


def up_to_threshold(it: Iterable[float], threshold: float) -> Iterator[float]:
    """Брати значення, поки |x| <= threshold (takewhile): зупиняє потік."""
    return takewhile(lambda x: abs(x) <= threshold, it)


def while_above(it: Iterable[float], eps: float) -> Iterator[float]:
    """Для спадної прогресії (|r| < 1): брати значення, поки |x| >= eps."""
    return takewhile(lambda x: abs(x) >= eps, it)


def skip_below(it: Iterable[float], threshold: float) -> Iterator[float]:
    """Пропустити початкові значення, менші за поріг (dropwhile)."""
    return dropwhile(lambda x: abs(x) < threshold, it)


def running_sum(it: Iterable[Number]) -> Iterator[Number]:
    """Накопичена сума S1, S2, ... (accumulate з operator.add)."""
    return accumulate(it, operator.add)


def running_product(it: Iterable[Number]) -> Iterator[Number]:
    """Накопичений добуток P1, P2, ... (accumulate з operator.mul)."""
    return accumulate(it, operator.mul)


def geometric_sum_formula(q0: float, r: float, n: int) -> float:
    """Сума перших n членів за формулою S_n = q0 * (1 - r^n) / (1 - r)."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if r == 1:
        return q0 * n
    return q0 * (1 - r**n) / (1 - r)


def ratios(it: Iterable[float]) -> Iterator[float]:
    """Відношення сусідніх членів b / a (для перевірки, що це прогресія)."""
    return starmap(lambda a, b: b / a, sliding_window(it, 2))


def progression_report(
    q0: float, r: float, threshold: float
) -> Iterator[tuple[int, float, float, float]]:
    """Ліниві рядки звіту: (n, член, накопичена сума, накопичений добуток)."""
    a, b, c = tee(up_to_threshold(geometric(q0, r), threshold), 3)
    return zip(count(1), a, running_sum(b), running_product(c))


# ===========================================================================
# 2. Базові утиліти
# ===========================================================================
def take(n: int, it: Iterable[T]) -> list[T]:
    """Перші n елементів (фінальна матеріалізація)."""
    if n < 0:
        raise ValueError("n must be non-negative")
    return list(islice(it, n))


def drop(n: int, it: Iterable[T]) -> Iterator[T]:
    """Пропустити перші n елементів, повернути ітератор на решту (ліниво)."""
    if n < 0:
        raise ValueError("n must be non-negative")
    iterator = iter(it)
    next(islice(iterator, n, n), None)  # «промотати» n елементів
    return iterator


def sliding_window(it: Iterable[T], k: int) -> Iterator[tuple[T, ...]]:
    """Ковзні вікна розміру k через deque(maxlen=k) — без матеріалізації потоку.

    Перевірка k виконується ОДРАЗУ (а не при першому next), тому функція —
    звичайна, а генератор — внутрішній.
    """
    if k <= 0:
        raise ValueError("window size must be positive")

    def gen() -> Iterator[tuple[T, ...]]:
        iterator = iter(it)
        window: deque[T] = deque(islice(iterator, k), maxlen=k)
        if len(window) < k:
            return  # елементів менше за k — жодного вікна
        yield tuple(window)
        for x in iterator:
            window.append(x)
            yield tuple(window)

    return gen()


def moving_average(it: Iterable[float], k: int) -> Iterator[float]:
    """Рухоме середнє по вікну k."""
    return (sum(w) / k for w in sliding_window(it, k))


def chunked(it: Iterable[T], size: int) -> Iterator[tuple[T, ...]]:
    """Порції фіксованого розміру (остання може бути коротшою)."""
    if size <= 0:
        raise ValueError("chunk size must be positive")
    iterator = iter(it)
    return iter(lambda: tuple(islice(iterator, size)), ())


def naturals(start: int = 1) -> Iterator[int]:
    """Нескінченний потік натуральних чисел (yield from count)."""
    yield from count(start)


def fib_stream() -> Iterator[int]:
    """Нескінченний стрім Фібоначчі."""
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b


def primes() -> Iterator[int]:
    """Нескінченний потік простих чисел (без попереднього великого списку)."""
    found: list[int] = []
    for n in count(2):
        limit = isqrt(n)
        if all(n % p for p in takewhile(partial(operator.ge, limit), found)):
            found.append(n)
            yield n


def tee_safe(it: Iterable[T], n: int = 2) -> tuple[Iterator[T], ...]:
    """Навчальний аналог itertools.tee: n незалежних «копій» з буферами deque."""
    if n < 0:
        raise ValueError("n must be non-negative")
    source = iter(it)
    buffers: list[deque[T]] = [deque() for _ in range(n)]

    def gen(buf: deque[T]) -> Iterator[T]:
        while True:
            if not buf:
                try:
                    value = next(source)
                except StopIteration:
                    return
                for b in buffers:
                    b.append(value)
            yield buf.popleft()

    return tuple(gen(b) for b in buffers)


def counting(it: Iterable[T], counter: Callable[[], None]) -> Iterator[T]:
    """Обгортка для тестів лінивості: викликає ``counter`` на кожному елементі."""
    for x in it:
        counter()
        yield x


def multiples_window_pipeline(n: int = 10) -> list[int]:
    """Пайплайн: натуральні -> кратні 3 -> ковзні суми по 4 -> перші n."""
    multiples_of_3 = (x for x in naturals(1) if x % 3 == 0)
    return take(n, starmap(lambda *w: sum(w), sliding_window(multiples_of_3, 4)))
