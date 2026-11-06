"""Базове завдання ЛР8: вирази Expr = Num | Add | Mul, eval та render через match."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal, TypeAlias, assert_never


@dataclass(frozen=True, slots=True)
class Num:
    value: int


@dataclass(frozen=True, slots=True)
class Add:
    left: Expr
    right: Expr


@dataclass(frozen=True, slots=True)
class Mul:
    left: Expr
    right: Expr


Expr: TypeAlias = Num | Add | Mul

Op: TypeAlias = Literal["+", "*"]

MAX_ABS: Final[int] = 10_000


class EvalOverflow(ValueError):
    """Результат вийшов за межі |x| <= MAX_ABS."""


def _check_range(x: int) -> int:
    if abs(x) > MAX_ABS:
        raise EvalOverflow(f"overflow: {x}")
    return x


def eval_expr(e: Expr) -> int:
    match e:
        case Num(value=v):
            return _check_range(v)
        case Add(left=a, right=b):
            return _check_range(eval_expr(a) + eval_expr(b))
        case Mul(left=a, right=b):
            return _check_range(eval_expr(a) * eval_expr(b))
        case _:
            assert_never(e)


def render_expr(e: Expr) -> str:
    match e:
        case Num(value=v):
            return str(v)
        case Add(left=a, right=b):
            return f"({render_expr(a)} + {render_expr(b)})"
        case Mul(left=a, right=b):
            return f"({render_expr(a)} * {render_expr(b)})"
        case _:
            assert_never(e)
