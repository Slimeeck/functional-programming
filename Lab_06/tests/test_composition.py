"""Порядок декораторів має значення: перевіряємо різницю тестами."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from closures import User, make_memory_sink
from decorators import (
    AuthorizationError,
    compose_decorators,
    logged,
    require_role,
    timed,
)

ADMIN = User("alice", frozenset({"admin"}))
GUEST = User("guest", frozenset({"viewer"}))


def ticking_clock() -> Callable[[], float]:
    t = [0.0]

    def clock() -> float:
        t[0] += 0.5
        return t[0]

    return clock


def test_timed_outside_measures_denied_calls_too() -> None:
    sink = make_memory_sink()

    @timed("op", logger=sink.write, clock=ticking_clock())
    @require_role("admin")
    def op(user: User) -> str:
        return "ok"

    with pytest.raises(AuthorizationError):
        op(GUEST)
    assert sink.lines() == ("[timed] op took 500.000 ms",)  # спроба теж виміряна


def test_timed_inside_is_skipped_when_denied() -> None:
    sink = make_memory_sink()

    @require_role("admin")
    @timed("op", logger=sink.write, clock=ticking_clock())
    def op(user: User) -> str:
        return "ok"

    with pytest.raises(AuthorizationError):
        op(GUEST)
    assert sink.lines() == ()  # перевірка ролі зупинила виклик ДО таймера
    assert op(ADMIN) == "ok"
    assert len(sink.lines()) == 1


def test_compose_decorators_equals_stacking() -> None:
    sink = make_memory_sink()

    def body(user: User, x: int) -> int:
        """Body."""
        return x + 1

    stacked = logged(logger=sink.write)(require_role("admin")(body))
    composed = compose_decorators(logged(logger=sink.write), require_role("admin"))(
        body
    )
    assert stacked(ADMIN, 1) == composed(ADMIN, 1) == 2
    lines = sink.lines()
    assert lines[:2] == lines[2:]
    assert composed.__name__ == "body"


def test_logged_outside_logs_authorization_error() -> None:
    sink = make_memory_sink()

    def secret(user: User) -> str:
        return "secret"

    secured = compose_decorators(
        logged("WARNING", logger=sink.write), require_role("admin")
    )(secret)
    with pytest.raises(AuthorizationError):
        secured(GUEST)
    assert sink.lines()[-1].startswith("WARNING secret raised AuthorizationError")
