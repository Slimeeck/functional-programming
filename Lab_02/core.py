"""ЛР2, варіант 4 — «Замовлення ресторану».

Функціональний конвеєр над записами замовлень без мутацій:
map / filter / sorted / islice + compose / pipe / juxt + reduce-агрегація.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator, Mapping
from functools import reduce
from itertools import islice
from typing import Any, TypedDict


# ---------------------------------------------------------------------------
# Модель
# ---------------------------------------------------------------------------
class OrderItem(TypedDict):
    name: str
    price: float
    qty: int


class Record(TypedDict, total=False):
    """Замовлення: id, waiter, table, items (+ розрахункові поля)."""

    id: int
    waiter: str
    table: int
    items: list[OrderItem]
    zone: str
    check: float


class Stats(TypedDict):
    count: int
    sum_checks: float
    avg_check: float
    max_check: float


Stage = Callable[[Iterable[Record]], Iterable[Record]]


# ---------------------------------------------------------------------------
# Композиція
# ---------------------------------------------------------------------------
def compose(*funcs: Callable[[Any], Any]) -> Callable[[Any], Any]:
    """compose(f, g, h)(x) == f(g(h(x))) — застосування справа наліво."""

    def composed(x: Any) -> Any:
        return reduce(lambda acc, f: f(acc), reversed(funcs), x)

    return composed


def pipe(value: Any, *funcs: Callable[[Any], Any]) -> Any:
    """pipe(x, f, g, h) == h(g(f(x))) — застосування зліва направо."""
    return reduce(lambda acc, f: f(acc), funcs, value)


def juxt(*funcs: Callable[[Any], Any]) -> Callable[[Any], tuple[Any, ...]]:
    """juxt(f, g)(x) == (f(x), g(x)) — кілька функцій над одним значенням."""
    return lambda x: tuple(f(x) for f in funcs)


# ---------------------------------------------------------------------------
# Чисті допоміжні функції
# ---------------------------------------------------------------------------
def table_zone(table: int) -> str:
    """Зона залу за номером столика: 1–10 hall, 11–20 terrace, 21+ vip."""
    if table <= 10:
        return "hall"
    if table <= 20:
        return "terrace"
    return "vip"


def check_total(items: Iterable[OrderItem]) -> float:
    """Сума чека: sum(price * qty) через map."""
    return float(sum(map(lambda it: it["price"] * it["qty"], items)))


# ---------------------------------------------------------------------------
# Етапи конвеєра (кожен — фабрика, що повертає чисту трансформацію)
# ---------------------------------------------------------------------------
def normalize_waiters() -> Stage:
    """Ім'я офіціанта в Title Case (map, новий словник)."""
    return lambda recs: map(
        lambda r: {**r, "waiter": str(r.get("waiter", "")).strip().title()}, recs
    )


def with_zone(zone_of: Callable[[int], str] = table_zone) -> Stage:
    """Додає поле ``zone``, обчислене з номера столика."""
    return lambda recs: ({**r, "zone": zone_of(int(r.get("table", 0)))} for r in recs)


def with_check() -> Stage:
    """Додає поле ``check`` = сума чека."""
    return lambda recs: (
        {**r, "check": round(check_total(r.get("items", [])), 2)} for r in recs
    )


def apply_service(zone: str, factor: float) -> Stage:
    """Сервісний коефіцієнт для обраної зони (інші чеки без змін)."""

    def stage(recs: Iterable[Record]) -> Iterator[Record]:
        for r in recs:
            check = float(r.get("check", 0.0))
            new_check = check * factor if r.get("zone") == zone else check
            yield {**r, "check": round(new_check, 2)}

    return stage


def drop_small_checks(min_check: float) -> Stage:
    """Відфільтровує малі чеки (filter)."""
    return lambda recs: filter(lambda r: float(r.get("check", 0.0)) >= min_check, recs)


def sort_by_check_desc() -> Callable[[Iterable[Record]], list[Record]]:
    """Сортування за двома ключами: check спадно, id зростанням."""
    return lambda recs: sorted(
        recs, key=lambda r: (-float(r.get("check", 0.0)), int(r.get("id", 0)))
    )


def take(n: int) -> Callable[[Iterable[Record]], list[Record]]:
    """Top-N через itertools.islice."""
    return lambda recs: list(islice(recs, max(n, 0)))


# ---------------------------------------------------------------------------
# reduce-агрегація
# ---------------------------------------------------------------------------
def reduce_stats(recs: Iterable[Record]) -> Stats:
    """count, sum_checks, avg_check, max_check через functools.reduce."""
    init: Mapping[str, float] = {"count": 0, "sum_checks": 0.0, "max_check": 0.0}

    def step(acc: Mapping[str, float], r: Record) -> Mapping[str, float]:
        check = float(r.get("check", 0.0))
        return {
            "count": acc["count"] + 1,
            "sum_checks": acc["sum_checks"] + check,
            "max_check": max(acc["max_check"], check),
        }

    acc = reduce(step, recs, init)
    count = int(acc["count"])
    total = round(acc["sum_checks"], 2)
    return {
        "count": count,
        "sum_checks": total,
        "avg_check": round(total / count, 2) if count else 0.0,
        "max_check": acc["max_check"],
    }


# ---------------------------------------------------------------------------
# Складання конвеєра
# ---------------------------------------------------------------------------
def build_pipeline(
    top_n: int = 3,
    zone: str = "terrace",
    factor: float = 1.1,
    min_check: float = 300.0,
) -> Callable[[Iterable[Record]], list[Record]]:
    """Конвеєр (читається знизу вгору, бо compose — справа наліво)."""
    return compose(
        take(top_n),
        sort_by_check_desc(),
        drop_small_checks(min_check),
        apply_service(zone, factor),
        with_check(),
        with_zone(),
        normalize_waiters(),
    )


def prepare(
    zone: str = "terrace", factor: float = 1.1, min_check: float = 300.0
) -> Callable[[Iterable[Record]], list[Record]]:
    """Ті самі етапи без Top-N — для агрегації по всіх допущених чеках."""
    return compose(
        list,
        drop_small_checks(min_check),
        apply_service(zone, factor),
        with_check(),
        with_zone(),
        normalize_waiters(),
    )
