from __future__ import annotations

import pytest

from closures import (
    User,
    make_counter,
    make_logger,
    make_memory_sink,
    make_role_checker,
    make_role_hierarchy,
    make_session,
)


def test_counter_keeps_state_in_closure() -> None:
    c = make_counter(10)
    assert (c(), c(), c()) == (11, 12, 13)
    other = make_counter()
    assert other() == 1  # окремий екземпляр — окремий стан
    assert c() == 14
    assert c.__closure__ is not None  # змінна value захоплена замиканням


def test_logger_with_injected_sink() -> None:
    sink = make_memory_sink()
    log = make_logger("AUTH", sink.write)
    log("hello")
    log("bye")
    assert sink.lines() == ("[AUTH] hello", "[AUTH] bye")
    sink.clear()
    assert sink.lines() == ()


def test_role_checker_any_and_all() -> None:
    any_check = make_role_checker(["admin", "editor"])
    all_check = make_role_checker(["admin", "security"], mode="all")
    assert any_check({"editor"}) is True
    assert any_check({"viewer"}) is False
    assert any_check(set()) is False
    assert all_check({"admin", "security", "x"}) is True
    assert all_check({"admin"}) is False
    with pytest.raises(ValueError):
        make_role_checker(["a"], mode="some")


def test_role_checker_copies_roles() -> None:
    roles = ["admin"]
    check = make_role_checker(roles)
    roles.append("viewer")  # зміна списку після створення не впливає
    assert check({"viewer"}) is False


def test_role_hierarchy_is_transitive() -> None:
    expand = make_role_hierarchy({"admin": ["editor"], "editor": ["viewer"]})
    assert expand({"admin"}) == {"admin", "editor", "viewer"}
    assert expand({"editor"}) == {"editor", "viewer"}
    assert expand({"guest"}) == {"guest"}
    assert expand(set()) == frozenset()


def test_role_hierarchy_handles_cycles() -> None:
    expand = make_role_hierarchy({"a": ["b"], "b": ["a"]})
    assert expand({"a"}) == {"a", "b"}


def test_session_state() -> None:
    s = make_session()
    assert s.current() is None
    u = User("bob", frozenset({"editor"}))
    s.login(u)
    assert s.current() == u
    s.logout()
    assert s.current() is None
    s.login(u)
    assert s.logins_count() == 2


def test_user_is_immutable_and_hashable() -> None:
    u = User("x", frozenset({"a"}))
    assert {u: 1}[User("x", frozenset({"a"}))] == 1
