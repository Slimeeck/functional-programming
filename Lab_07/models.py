"""ЛР7, варіант 4 — «Облік працівників». Предметні класи."""

from __future__ import annotations

from dataclasses import dataclass
from functools import total_ordering


@dataclass(frozen=True, slots=True)
class Employee:
    name: str
    department: str
    salary: float
    experience: int
    active: bool
    bonus: float = 0.0

    @property
    def total_pay(self) -> float:
        return round(self.salary + self.bonus, 2)


@total_ordering
class EmployeeOrder:
    """Порядок працівників у рейтингу: salary ↓, experience ↓, name ↑.

    ``a < b`` означає «a стоїть у рейтингу ВИЩЕ за b», тому
    ``sorted(map(EmployeeOrder, employees))`` одразу дає рейтинг.
    Реалізовано лише ``__eq__`` та ``__lt__``; ``<=``, ``>``, ``>=``
    генерує ``@total_ordering``.
    """

    __slots__ = ("employee",)

    def __init__(self, employee: Employee) -> None:
        self.employee = employee

    def _key(self) -> tuple[float, int, str]:
        e = self.employee
        return (-e.salary, -e.experience, e.name.casefold())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EmployeeOrder):
            return NotImplemented
        return self._key() == other._key()

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, EmployeeOrder):
            return NotImplemented
        return self._key() < other._key()

    def __hash__(self) -> int:
        return hash(self._key())

    def __repr__(self) -> str:
        e = self.employee
        return (
            f"EmployeeOrder({e.name!r}, salary={e.salary}, experience={e.experience})"
        )
