from __future__ import annotations

import pytest

from expr import Add, EvalOverflow, Mul, Num, eval_expr, render_expr


def test_eval_basic() -> None:
    assert eval_expr(Num(5)) == 5
    assert eval_expr(Add(Num(2), Num(3))) == 5
    assert eval_expr(Mul(Num(2), Num(3))) == 6


def test_eval_nested() -> None:
    ast = Mul(Add(Num(2), Num(3)), Num(4))  # (2+3)*4
    assert eval_expr(ast) == 20


def test_render() -> None:
    assert render_expr(Mul(Add(Num(2), Num(3)), Num(4))) == "((2 + 3) * 4)"


def test_overflow() -> None:
    with pytest.raises(EvalOverflow):
        eval_expr(Mul(Num(1000), Num(1000)))
