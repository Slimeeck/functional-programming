"""Функціональний конвеєр обліку працівників (ЛР7, варіант 4).

partial + reduce + operator (itemgetter / attrgetter / methodcaller).
Конвеєр: нормалізувати -> відібрати активних -> обчислити премію -> ранжувати -> Top-N.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import replace
from functools import partial, reduce
from itertools import islice
from operator import add, attrgetter, itemgetter, methodcaller
from typing import Any

from models import Employee, EmployeeOrder

# ---------------------------------------------------------------------------
# Універсальний pipeline через reduce
# ---------------------------------------------------------------------------


def pipeline(value: Any, *funcs: Callable[[Any], Any]) -> Any:
    """pipeline(x, f, g, h) == h(g(f(x)))."""
    return reduce(lambda acc, f: f(acc), funcs, value)


def mapf(fn: Callable[[Any], Any]) -> Callable[[Iterable[Any]], Iterable[Any]]:
    """mapf(fn)(xs) == map(fn, xs) — через partial."""
    return partial(map, fn)


def filterf(pred: Callable[[Any], bool]) -> Callable[[Iterable[Any]], Iterable[Any]]:
    """filterf(pred)(xs) == filter(pred, xs) — через partial."""
    return partial(filter, pred)


# ---------------------------------------------------------------------------
# Нормалізація сирих записів (itemgetter + methodcaller)
# ---------------------------------------------------------------------------
get_fields = itemgetter("name", "department", "salary", "experience", "active")
strip = methodcaller("strip")
title = methodcaller("title")
lower = methodcaller("lower")

TRUE_VALUES = frozenset({"true", "yes", "1", "так", "y"})


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return lower(strip(str(value))) in TRUE_VALUES


def normalize_name(raw: str) -> str:
    """'  iVAN   petrenko ' -> 'Ivan Petrenko'."""
    return " ".join(title(strip(raw)).split())


def normalize(record: Mapping[str, Any]) -> Employee:
    name, department, salary, experience, active = get_fields(record)
    return Employee(
        name=normalize_name(str(name)),
        department=lower(strip(str(department))),
        salary=float(salary),
        experience=int(experience),
        active=parse_bool(active),
    )


# ---------------------------------------------------------------------------
# Політики премії (налаштовуються через partial)
# ---------------------------------------------------------------------------
def experience_bonus(
    employee: Employee, *, base_rate: float, per_year: float, cap: float
) -> float:
    """Премія = salary * min(base_rate + per_year * experience, cap)."""
    rate = min(base_rate + per_year * employee.experience, cap)
    return round(employee.salary * rate, 2)


def department_bonus(
    employee: Employee, *, rates: Mapping[str, float], default: float = 0.0
) -> float:
    """Премія = salary * ставка відділу."""
    return round(employee.salary * rates.get(employee.department, default), 2)


def with_bonus(policy: Callable[[Employee], float], employee: Employee) -> Employee:
    """Новий Employee з полем bonus (frozen dataclass -> replace)."""
    return replace(employee, bonus=policy(employee))


standard_bonus = partial(experience_bonus, base_rate=0.05, per_year=0.01, cap=0.20)
it_department_bonus = partial(department_bonus, rates={"it": 0.15, "sales": 0.10})


# ---------------------------------------------------------------------------
# Етапи конвеєра
# ---------------------------------------------------------------------------
is_active: Callable[[Employee], bool] = attrgetter("active")


def min_experience(years: int, employee: Employee) -> bool:
    return employee.experience >= years


def in_department(department: str, employee: Employee) -> bool:
    return employee.department == department


def rank(employees: Iterable[Employee]) -> list[Employee]:
    """Багатокритеріальне сортування через @total_ordering-клас EmployeeOrder."""
    return [o.employee for o in sorted(map(EmployeeOrder, employees))]


def sort_by(
    *fields: str, reverse: bool = False
) -> Callable[[Iterable[Employee]], list[Employee]]:
    """Сортування за кількома атрибутами через attrgetter."""
    return partial(sorted, key=attrgetter(*fields), reverse=reverse)


def top_n(n: int, items: Iterable[Employee]) -> list[Employee]:
    return list(islice(items, max(n, 0)))


def build_pipeline(
    *,
    bonus_policy: Callable[[Employee], float] = standard_bonus,
    n: int = 3,
    min_years: int = 0,
) -> Callable[[Iterable[Mapping[str, Any]]], list[Employee]]:
    """Збирає конвеєр із налаштованих (partial) етапів."""

    def run(records: Iterable[Mapping[str, Any]]) -> list[Employee]:
        result: list[Employee] = pipeline(
            records,
            mapf(normalize),
            filterf(is_active),
            filterf(partial(min_experience, min_years)),
            mapf(partial(with_bonus, bonus_policy)),
            rank,
            partial(top_n, n),
        )
        return result

    return run


# ---------------------------------------------------------------------------
# reduce-агрегації
# ---------------------------------------------------------------------------
def total_payroll(employees: Iterable[Employee]) -> float:
    """Сумарний фонд оплати (salary + bonus)."""
    return round(reduce(add, map(attrgetter("total_pay"), employees), 0.0), 2)


def payroll_by_department(employees: Iterable[Employee]) -> dict[str, float]:
    """{відділ: фонд оплати} — згортка в НОВИЙ словник на кожному кроці."""

    def step(acc: dict[str, float], e: Employee) -> dict[str, float]:
        return {**acc, e.department: round(acc.get(e.department, 0.0) + e.total_pay, 2)}

    return reduce(step, employees, {})


def prepare_all(
    records: Iterable[Mapping[str, Any]],
    bonus_policy: Callable[[Employee], float] = standard_bonus,
) -> list[Employee]:
    """Усі активні працівники з премією (без Top-N) — для агрегацій."""
    result: list[Employee] = pipeline(
        records,
        mapf(normalize),
        filterf(is_active),
        mapf(partial(with_bonus, bonus_policy)),
        list,
    )
    return result
