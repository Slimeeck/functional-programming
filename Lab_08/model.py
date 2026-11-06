"""ЛР8, варіант 4 — «Геометричні фігури». Алгебраїчний тип даних (ADT).

Shape = Circle | Rectangle | Triangle | Group
    * вузли — незмінні ``@dataclass(frozen=True, slots=True)``;
    * ``Group`` — рекурсивний вузол (фігура, складена з інших фігур);
    * ``Unit`` — ``Literal`` для одиниць вимірювання;
    * ``HasArea`` — ``Protocol`` для будь-яких об'єктів із властивістю ``area``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, TypeAlias

Unit: TypeAlias = Literal["mm", "cm", "m"]
ShapeKind: TypeAlias = Literal["circle", "rectangle", "triangle", "group"]

UNIT_IN_CM: dict[Unit, float] = {"mm": 0.1, "cm": 1.0, "m": 100.0}


def _require_positive(**values: float) -> None:
    for name, value in values.items():
        if value <= 0:
            raise ValueError(f"{name} must be positive, got {value}")


@dataclass(frozen=True, slots=True)
class Circle:
    radius: float
    unit: Unit = "cm"

    def __post_init__(self) -> None:
        _require_positive(radius=self.radius)


@dataclass(frozen=True, slots=True)
class Rectangle:
    width: float
    height: float
    unit: Unit = "cm"

    def __post_init__(self) -> None:
        _require_positive(width=self.width, height=self.height)


@dataclass(frozen=True, slots=True)
class Triangle:
    a: float
    b: float
    c: float
    unit: Unit = "cm"

    def __post_init__(self) -> None:
        _require_positive(a=self.a, b=self.b, c=self.c)
        x, y, z = sorted((self.a, self.b, self.c))
        if x + y <= z:
            raise ValueError(
                f"triangle inequality violated: {self.a}, {self.b}, {self.c}"
            )


@dataclass(frozen=True, slots=True)
class Group:
    """Складена фігура (рекурсивний вузол ADT)."""

    name: str
    shapes: tuple[Shape, ...] = ()


Shape: TypeAlias = Circle | Rectangle | Triangle | Group


@dataclass(frozen=True, slots=True)
class Measurement:
    """Результат обчислень для фігури; задовольняє Protocol ``HasArea``."""

    kind: ShapeKind
    area: float
    perimeter: float
    unit: Unit


class HasArea(Protocol):
    """Структурний контракт: будь-який об'єкт із властивістю ``area``."""

    @property
    def area(self) -> float: ...
