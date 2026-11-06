"""Текстове представлення фігур (pretty-print) через match/case."""

from __future__ import annotations

from typing import assert_never

from evaluator import area, classify
from model import Circle, Group, Rectangle, Shape, Triangle, Unit


def _num(x: float) -> str:
    return f"{x:g}"


def render(shape: Shape) -> str:
    """Однорядкове представлення: Group[house: Rectangle(4x3 m), Triangle(...)]."""
    match shape:
        case Circle(radius=r, unit=u):
            return f"Circle(r={_num(r)} {u})"
        case Rectangle(width=w, height=h, unit=u):
            return f"Rectangle({_num(w)}x{_num(h)} {u})"
        case Triangle(a=a, b=b, c=c, unit=u):
            return f"Triangle({_num(a)}, {_num(b)}, {_num(c)} {u})"
        case Group(name=name, shapes=items):
            return f"Group[{name}: " + ", ".join(render(i) for i in items) + "]"
        case _:
            assert_never(shape)


def render_tree(shape: Shape, unit: Unit = "cm", indent: int = 0) -> str:
    """Багаторядкове дерево з площею кожного вузла."""
    pad = "  " * indent
    match shape:
        case Group(name=name, shapes=items):
            head = (
                f"{pad}{name}/ ({classify(shape)}, S={area(shape, unit):.2f} {unit}²)"
            )
            children = [render_tree(item, unit, indent + 1) for item in items]
            return "\n".join([head, *children])
        case Circle() | Rectangle() | Triangle():
            return (
                f"{pad}- {render(shape)}  [{classify(shape)}]"
                f"  S={area(shape, unit):.2f} {unit}²"
            )
        case _:
            assert_never(shape)
