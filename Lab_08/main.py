"""Демонстрація ЛР8 (варіант 4 — геометричні фігури): python main.py"""

from __future__ import annotations

from evaluator import (
    area,
    classify,
    convert,
    count_shapes,
    depth,
    largest,
    measure,
    perimeter,
    scale,
    total_area,
)
from expr import Add, Mul, Num, eval_expr, render_expr
from model import Circle, Group, Rectangle, Shape, Triangle
from pretty import render, render_tree


def main() -> None:
    shapes: tuple[Shape, ...] = (
        Circle(2),
        Rectangle(4, 3),
        Rectangle(5, 5, "mm"),
        Triangle(3, 4, 5),
        Triangle(2, 2, 2, "m"),
        Triangle(5, 5, 8),
    )
    print("=== Прості фігури (площа та периметр у cm) ===")
    for s in shapes:
        print(
            f"  {render(s):<28} {classify(s):<22}"
            f" S={area(s):>10.2f}  P={perimeter(s):>7.2f}"
        )

    house = Group(
        "house",
        (
            Rectangle(4, 3, "m"),  # стіна
            Triangle(4, 2.5, 2.5, "m"),  # дах
            Group("windows", (Rectangle(80, 80), Rectangle(80, 80), Circle(30))),
        ),
    )
    print("\n=== Вкладена структура (Group — рекурсивний вузол) ===")
    print(render_tree(house, unit="m"))
    print("  render:", render(house))
    print("  фігур:", count_shapes(house), "| глибина:", depth(house))
    print("  площа, m²:", round(area(house, "m"), 4))
    print("  measure  :", measure(house, "m"))

    print("\n=== Pure-перетворення ===")
    big = scale(Circle(2), 3)
    print("  scale(Circle(2), 3) ->", render(big), "| оригінал:", render(Circle(2)))
    print(
        "  convert(Rectangle(4x3 m), 'cm') ->",
        render(convert(Rectangle(4, 3, "m"), "cm")),
    )

    print("\n=== Protocol HasArea ===")
    measurements = [measure(s) for s in shapes]
    print("  total_area(measurements) =", round(total_area(measurements), 2))
    print("  largest(measurements)    =", largest(measurements))

    print("\n=== Помилкові дані ===")
    for make in (lambda: Triangle(1, 2, 10), lambda: Circle(-1)):
        try:
            make()
        except ValueError as err:
            print("  ValueError:", err)

    print("\n=== Базове завдання: Expr = Num | Add | Mul ===")
    expr = Mul(Add(Num(2), Num(3)), Num(4))
    print(f"  {render_expr(expr)} = {eval_expr(expr)}")


if __name__ == "__main__":
    main()
