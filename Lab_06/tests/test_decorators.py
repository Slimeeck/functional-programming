from __future__ import annotations

from collections.abc import Callable, Iterator

import pytest

from closures import User, make_memory_sink, make_role_hierarchy, make_session
from decorators import (
    AuthenticationError,
    AuthorizationError,
    logged,
    require_role,
    require_session_role,
    timed,
)

ADMIN = User("alice", frozenset({"admin"}))
EDITOR = User("bob", frozenset({"editor"}))
VIEWER = User("eve", frozenset({"viewer"}))
NOBODY = User("anon")


def fake_clock(*ticks: float) -> Callable[[], float]:
    """Детермінований годинник: повертає задані значення по черзі."""
    it: Iterator[float] = iter(ticks)
    return lambda: next(it)


# --- @require_role ----------------------------------------------------------
def test_require_role_allows_and_denies() -> None:
    sink = make_memory_sink()

    @require_role("admin", logger=sink.write)
    def delete(user: User, doc_id: int) -> str:
        return f"deleted {doc_id}"

    assert delete(ADMIN, 7) == "deleted 7"
    with pytest.raises(AuthorizationError) as info:
        delete(EDITOR, 7)
    assert info.value.user == "bob"
    assert info.value.required == frozenset({"admin"})
    assert info.value.func_name == "delete"
    assert isinstance(info.value, PermissionError)  # власний виняток — підклас
    assert sink.lines() == ("ALLOW alice -> delete", "DENY bob -> delete")


def test_denied_function_body_is_not_executed() -> None:
    calls: list[str] = []

    @require_role("admin")
    def action(user: User) -> None:
        calls.append(user.name)

    with pytest.raises(AuthorizationError):
        action(VIEWER)
    assert calls == []


def test_require_role_any_vs_all_mode() -> None:
    @require_role("admin", "editor")
    def any_of(user: User) -> bool:
        return True

    @require_role("admin", "security", mode="all")
    def all_of(user: User) -> bool:
        return True

    assert any_of(EDITOR) and any_of(ADMIN)
    with pytest.raises(AuthorizationError):
        any_of(VIEWER)
    assert all_of(User("root", frozenset({"admin", "security"})))
    with pytest.raises(AuthorizationError):
        all_of(ADMIN)


def test_require_role_with_hierarchy() -> None:
    expand = make_role_hierarchy({"admin": ["editor"], "editor": ["viewer"]})

    @require_role("viewer", expand=expand)
    def read(user: User) -> str:
        return "ok"

    assert read(ADMIN) == read(EDITOR) == read(VIEWER) == "ok"
    with pytest.raises(AuthorizationError):
        read(NOBODY)  # користувач без ролей — граничний випадок


def test_require_role_needs_at_least_one_role() -> None:
    with pytest.raises(ValueError):
        require_role()


def test_require_session_role() -> None:
    session = make_session()

    @require_session_role(session.current, "admin")
    def reset() -> str:
        return "done"

    with pytest.raises(AuthenticationError):
        reset()
    session.login(EDITOR)
    with pytest.raises(AuthorizationError):
        reset()
    session.login(ADMIN)
    assert reset() == "done"


# --- @timed -------------------------------------------------------------------
def test_timed_uses_injected_clock() -> None:
    sink = make_memory_sink()

    @timed("calc", unit="ms", logger=sink.write, clock=fake_clock(1.0, 1.25))
    def calc(x: int) -> int:
        return x * 2

    assert calc(21) == 42
    assert sink.lines() == ("[timed] calc took 250.000 ms",)


def test_timed_logs_even_on_exception() -> None:
    sink = make_memory_sink()

    @timed(unit="s", logger=sink.write, clock=fake_clock(0.0, 2.0))
    def boom() -> None:
        raise RuntimeError("x")

    with pytest.raises(RuntimeError):
        boom()
    assert sink.lines() == ("[timed] boom took 2.000 s",)


def test_timed_units() -> None:
    sink = make_memory_sink()

    @timed(unit="us", logger=sink.write, clock=fake_clock(0.0, 0.000003))
    def f() -> int:
        return 1

    f()
    assert sink.lines()[0].endswith("3.000 us")


# --- @logged ----------------------------------------------------------------
def test_logged_result_and_exception() -> None:
    sink = make_memory_sink()

    @logged("DEBUG", logger=sink.write)
    def div(a: int, b: int = 1) -> float:
        return a / b

    assert div(6, b=3) == 2.0
    with pytest.raises(ZeroDivisionError):
        div(1, b=0)
    assert sink.lines() == (
        "DEBUG call div(6, b=3)",
        "DEBUG div -> 2.0",
        "DEBUG call div(1, b=0)",
        "DEBUG div raised ZeroDivisionError: division by zero",
    )


# --- метадані ---------------------------------------------------------------
def test_wraps_preserves_metadata() -> None:
    def original(user: User, x: int) -> int:
        """Docstring of original."""
        return x

    decorated_variants = [
        require_role("admin")(original),
        timed(logger=lambda _: None)(original),
        logged(logger=lambda _: None)(original),
    ]
    for decorated in decorated_variants:
        assert decorated.__name__ == "original"
        assert decorated.__doc__ == "Docstring of original."
        assert decorated.__wrapped__ is original  # type: ignore[attr-defined]
