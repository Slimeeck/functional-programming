"""Чисті функції над ADT ``Shape`` — лише ``match/case``, без ланцюгів isinstance.

area / perimeter / scale / convert / classify / count_shapes / depth / measure.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import replace
from typing import assert_never

from model import (
    UNIT_IN_CM,
    Circle,
    Group,
    HasArea,
    Measurement,
    Rectangle,
    Shape,
    ShapeKind,
    Triangle,
    Unit,
)


def length_factor(src: Unit, dst: Unit) -> float:
    """Коефіцієнт переведення довжини з ``src`` у ``dst`` (mm -> cm = 0.1)."""
    return UNIT_IN_CM[src] / UNIT_IN_CM[dst]


def area(shape: Shape, unit: Unit = "cm") -> float:
    """Площа фігури в квадратних ``unit``."""
    match shape:
        case Circle(radius=r, unit=u):
            raw = math.pi * r**2
        case Rectangle(width=w, height=h, unit=u):
            raw = w * h
        case Triangle(a=a, b=b, c=c, unit=u):
            s = (a + b + c) / 2
            raw = math.sqrt(s * (s - a) * (s - b) * (s - c))  # формула Герона
        case Group(shapes=items):
            return sum(area(item, unit) for item in items)
        case _:
            assert_never(shape)
    return raw * length_factor(u, unit) ** 2


def perimeter(shape: Shape, unit: Unit = "cm") -> float:
    """Периметр (для Group — сума периметрів складових)."""
    match shape:
        case Circle(radius=r, unit=u):
            raw = 2 * math.pi * r
        case Rectangle(width=w, height=h, unit=u):
            raw = 2 * (w + h)
        case Triangle(a=a, b=b, c=c, unit=u):
            raw = a + b + c
        case Group(shapes=items):
            return sum(perimeter(item, unit) for item in items)
        case _:
            assert_never(shape)
    return raw * length_factor(u, unit)


def scale(shape: Shape, k: float) -> Shape:
    """НОВА фігура, збільшена в k разів (вхідна не змінюється)."""
    if k <= 0:
        raise ValueError("scale factor must be positive")
    match shape:
        case Circle(radius=r):
            return replace(shape, radius=r * k)
        case Rectangle(width=w, height=h):
            return replace(shape, width=w * k, height=h * k)
        case Triangle(a=a, b=b, c=c):
            return replace(shape, a=a * k, b=b * k, c=c * k)
        case Group(shapes=items):
            return replace(shape, shapes=tuple(scale(item, k) for item in items))
        case _:
            assert_never(shape)


def convert(shape: Shape, unit: Unit) -> Shape:
    """НОВА фігура в інших одиницях (рекурсивно для Group)."""
    match shape:
        case Group(shapes=items):
            return replace(shape, shapes=tuple(convert(item, unit) for item in items))
        case Circle(radius=r, unit=u):
            return Circle(r * length_factor(u, unit), unit)
        case Rectangle(width=w, height=h, unit=u):
            f = length_factor(u, unit)
            return Rectangle(w * f, h * f, unit)
        case Triangle(a=a, b=b, c=c, unit=u):
            f = length_factor(u, unit)
            return Triangle(a * f, b * f, c * f, unit)
        case _:
            assert_never(shape)


def _is_right(a: float, b: float, c: float) -> bool:
    x, y, z = sorted((a, b, c))
    return math.isclose(x * x + y * y, z * z)


def classify(shape: Shape) -> str:
    """Класифікація фігури через match з guard-умовами."""
    match shape:
        case Circle():
            return "circle"
        case Rectangle(width=w, height=h) if math.isclose(w, h):
            return "square"
        case Rectangle():
            return "rectangle"
        case Triangle(a=a, b=b, c=c) if math.isclose(a, b) and math.isclose(b, c):
            return "equilateral triangle"
        case Triangle(a=a, b=b, c=c) if _is_right(a, b, c):
            return "right triangle"
        case Triangle(a=a, b=b, c=c) if len({a, b, c}) == 2:
            return "isosceles triangle"
        case Triangle():
            return "scalene triangle"
        case Group(shapes=()):
            return "empty group"
        case Group(shapes=items):
            return f"group of {len(items)}"
        case _:
            assert_never(shape)


def kind_of(shape: Shape) -> ShapeKind:
    match shape:
        case Circle():
            return "circle"
        case Rectangle():
            return "rectangle"
        case Triangle():
            return "triangle"
        case Group():
            return "group"
        case _:
            assert_never(shape)


def count_shapes(shape: Shape) -> int:
    """Кількість простих фігур (листків) у дереві."""
    match shape:
        case Group(shapes=items):
            return sum(count_shapes(item) for item in items)
        case Circle() | Rectangle() | Triangle():
            return 1
        case _:
            assert_never(shape)


def depth(shape: Shape) -> int:
    """Глибина вкладеності (проста фігура = 1)."""
    match shape:
        case Group(shapes=items):
            return 1 + max((depth(item) for item in items), default=0)
        case Circle() | Rectangle() | Triangle():
            return 1
        case _:
            assert_never(shape)


def measure(shape: Shape, unit: Unit = "cm") -> Measurement:
    """Площа + периметр у вигляді незмінного Measurement (задовольняє HasArea)."""
    return Measurement(
        kind=kind_of(shape),
        area=round(area(shape, unit), 4),
        perimeter=round(perimeter(shape, unit), 4),
        unit=unit,
    )


# --- функції над Protocol HasArea -------------------------------------------
def total_area(items: Iterable[HasArea]) -> float:
    """Працює з БУДЬ-ЯКИМИ об'єктами, що мають властивість area (structural typing)."""
    return sum(item.area for item in items)


def largest(items: Iterable[HasArea]) -> HasArea | None:
    return max(items, key=lambda item: item.area, default=None)
