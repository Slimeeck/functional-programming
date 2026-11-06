"""ЛР6, варіант 4 — «Авторизація користувачів». Замикання (closures).

* ``make_counter``        — лічильник зі станом через ``nonlocal``;
* ``make_logger``         — логер-замикання з префіксом і підміною виводу (sink);
* ``make_memory_sink``    — «пам'ять» для логів у тестах (замкнений список);
* ``make_role_checker``   — замикання над НАБОРОМ ДОЗВОЛЕНИХ РОЛЕЙ;
* ``make_role_hierarchy`` — розгортання ролей за ієрархією (admin ⊃ editor ⊃ viewer);
* ``make_session``        — поточний користувач сесії (``nonlocal``-стан).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import NamedTuple

Logger = Callable[[str], None]


@dataclass(frozen=True, slots=True)
class User:
    name: str
    roles: frozenset[str] = frozenset()


def make_counter(start: int = 0) -> Callable[[], int]:
    """Кожен виклик повертає наступне значення; стан ``value`` живе в замиканні."""
    value = start

    def inc() -> int:
        nonlocal value
        value += 1
        return value

    return inc


def make_logger(prefix: str, sink: Logger = print) -> Logger:
    """Логер з префіксом; ``sink`` — залежність (print або список у тестах)."""

    def log(message: str) -> None:
        sink(f"[{prefix}] {message}")

    return log


class MemorySink(NamedTuple):
    write: Logger
    lines: Callable[[], tuple[str, ...]]
    clear: Callable[[], None]


def make_memory_sink() -> MemorySink:
    """Замикання над списком рядків — зручно перевіряти логи в тестах."""
    buffer: list[str] = []

    def write(line: str) -> None:
        buffer.append(line)

    def lines() -> tuple[str, ...]:
        return tuple(buffer)

    def clear() -> None:
        buffer.clear()

    return MemorySink(write, lines, clear)


def make_role_checker(
    allowed: Iterable[str], *, mode: str = "any"
) -> Callable[[Iterable[str]], bool]:
    """Замикання над дозволеними ролями.

    mode="any" — достатньо однієї з ролей; mode="all" — потрібні всі.
    """
    allowed_set = frozenset(allowed)
    if mode not in ("any", "all"):
        raise ValueError("mode must be 'any' or 'all'")

    def check(user_roles: Iterable[str]) -> bool:
        roles = frozenset(user_roles)
        if mode == "all":
            return allowed_set <= roles
        return bool(allowed_set & roles)

    return check


def make_role_hierarchy(
    parents: Mapping[str, Iterable[str]],
) -> Callable[[Iterable[str]], frozenset[str]]:
    """Повертає функцію, що розгортає ролі за ієрархією (транзитивно).

    {"admin": ["editor"], "editor": ["viewer"]}: admin -> {admin, editor, viewer}.
    """
    graph = {role: frozenset(children) for role, children in parents.items()}

    def expand(roles: Iterable[str]) -> frozenset[str]:
        result: set[str] = set()
        stack = list(roles)
        while stack:
            role = stack.pop()
            if role not in result:
                result.add(role)
                stack.extend(graph.get(role, ()))
        return frozenset(result)

    return expand


class Session(NamedTuple):
    login: Callable[[User], None]
    logout: Callable[[], None]
    current: Callable[[], User | None]
    logins_count: Callable[[], int]


def make_session() -> Session:
    """Сесія: поточний користувач і кількість входів зберігаються в замиканні."""
    current_user: User | None = None
    logins = 0

    def login(user: User) -> None:
        nonlocal current_user, logins
        current_user = user
        logins += 1

    def logout() -> None:
        nonlocal current_user
        current_user = None

    def current() -> User | None:
        return current_user

    def logins_count() -> int:
        return logins

    return Session(login, logout, current, logins_count)
