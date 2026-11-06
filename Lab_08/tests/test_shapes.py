from __future__ import annotations

import math
from dataclasses import FrozenInstanceError, dataclass

import pytest

from evaluator import (
    area,
    classify,
    convert,
    count_shapes,
    depth,
    kind_of,
    largest,
    length_factor,
    measure,
    perimeter,
    scale,
    total_area,
)
from model import Circle, Group, HasArea, Measurement, Rectangle, Triangle
from pretty import render, render_tree

HOUSE = Group(
    "house",
    (
        Rectangle(4, 3, "m"),
        Triangle(4, 2.5, 2.5, "m"),
        Group("windows", (Rectangle(80, 80), Circle(30))),
    ),
)


# ===================== кожен варіант ADT ====================================
def test_circle() -> None:
    c = Circle(2)
    assert area(c) == pytest.approx(math.pi * 4)
    assert perimeter(c) == pytest.approx(4 * math.pi)
    assert classify(c) == "circle"


def test_rectangle_and_square() -> None:
    r = Rectangle(4, 3)
    assert area(r) == 12 and perimeter(r) == 14
    assert classify(r) == "rectangle"
    assert classify(Rectangle(5, 5)) == "square"


@pytest.mark.parametrize(
    ("tri", "expected_area", "kind"),
    [
        (Triangle(3, 4, 5), 6.0, "right triangle"),
        (Triangle(2, 2, 2), math.sqrt(3), "equilateral triangle"),
        (Triangle(5, 5, 8), 12.0, "isosceles triangle"),
        (Triangle(4, 5, 6), 9.921567416492215, "scalene triangle"),
    ],
)
def test_triangles(tri: Triangle, expected_area: float, kind: str) -> None:
    assert area(tri) == pytest.approx(expected_area)
    assert perimeter(tri) == tri.a + tri.b + tri.c
    assert classify(tri) == kind


# ===================== одиниці (Literal) ====================================
def test_units_conversion() -> None:
    assert length_factor("m", "cm") == 100
    assert length_factor("mm", "cm") == pytest.approx(0.1)
    sq_m = Rectangle(1, 1, "m")
    assert area(sq_m, "cm") == pytest.approx(10_000)
    assert area(sq_m, "mm") == pytest.approx(1_000_000)
    assert perimeter(sq_m, "cm") == pytest.approx(400)
    assert area(Rectangle(10, 10, "mm")) == pytest.approx(1.0)


def test_convert_returns_new_equivalent_shape() -> None:
    r = Rectangle(4, 3, "m")
    cm = convert(r, "cm")
    assert cm == Rectangle(400, 300, "cm")
    assert area(cm, "m") == pytest.approx(area(r, "m"))
    assert r.unit == "m"  # оригінал не змінився


# ===================== вкладені структури ===================================
def test_nested_group() -> None:
    expected = 12 + 3.0 + 0.64 + math.pi * 0.09  # m²: стіна, дах, вікно, кругле вікно
    assert area(HOUSE, "m") == pytest.approx(expected)
    assert count_shapes(HOUSE) == 4
    assert depth(HOUSE) == 3
    assert classify(HOUSE) == "group of 3"
    assert kind_of(HOUSE) == "group"


def test_empty_group_edge_case() -> None:
    empty = Group("empty")
    assert area(empty) == 0 and perimeter(empty) == 0
    assert count_shapes(empty) == 0 and depth(empty) == 1
    assert classify(empty) == "empty group"


def test_scale_is_pure_and_recursive() -> None:
    bigger = scale(HOUSE, 2)
    assert area(bigger, "m") == pytest.approx(4 * area(HOUSE, "m"))
    assert HOUSE.shapes[0] == Rectangle(4, 3, "m")  # оригінал без змін
    assert bigger is not HOUSE
    with pytest.raises(ValueError):
        scale(Circle(1), 0)


# ===================== незмінність ==========================================
def test_nodes_are_frozen_and_hashable() -> None:
    c = Circle(1)
    with pytest.raises(FrozenInstanceError):
        c.radius = 5  # type: ignore[misc]
    assert {Circle(1), Circle(1), Rectangle(1, 2)} == {Circle(1), Rectangle(1, 2)}
    assert hash(HOUSE) == hash(scale(HOUSE, 1))


# ===================== помилкові дані =======================================
@pytest.mark.parametrize(
    "factory",
    [
        lambda: Circle(0),
        lambda: Circle(-2),
        lambda: Rectangle(0, 5),
        lambda: Triangle(1, 2, 3),  # вироджений
        lambda: Triangle(1, 2, 10),  # нерівність трикутника
        lambda: Triangle(-3, 4, 5),
    ],
)
def test_invalid_shapes(factory: object) -> None:
    with pytest.raises(ValueError):
        factory()  # type: ignore[operator]


# ===================== Protocol HasArea =====================================
@dataclass(frozen=True)
class Plot:
    """Сторонній клас: не успадковує нічого, але має властивість area."""

    owner: str
    area: float


def test_protocol_structural_typing() -> None:
    items: list[HasArea] = [measure(Rectangle(2, 3)), Plot("Ivan", 10.0)]
    assert total_area(items) == pytest.approx(16.0)
    assert largest(items) == Plot("Ivan", 10.0)
    assert largest([]) is None


def test_measure() -> None:
    m = measure(Rectangle(4, 3, "m"), "m")
    assert m == Measurement(kind="rectangle", area=12.0, perimeter=14.0, unit="m")


# ===================== pretty-print =========================================
def test_render() -> None:
    assert render(Circle(2)) == "Circle(r=2 cm)"
    assert render(Rectangle(4, 3, "m")) == "Rectangle(4x3 m)"
    assert render(Triangle(3, 4, 5)) == "Triangle(3, 4, 5 cm)"
    assert render(Group("g", (Circle(1, "mm"),))) == "Group[g: Circle(r=1 mm)]"


def test_render_tree_is_nested() -> None:
    lines = render_tree(HOUSE, "m").splitlines()
    assert lines[0].startswith("house/ (group of 3")
    assert lines[3].startswith("  windows/")
    assert lines[4].startswith("    - Rectangle(80x80 cm)")
    assert len(lines) == 6
