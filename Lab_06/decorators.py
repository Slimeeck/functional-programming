"""ЛР6, варіант 4 — параметризовані декоратори авторизації.

* ``@require_role(*roles, mode=..., logger=..., expand=...)`` — доступ лише для
  користувачів з потрібною роллю (користувач — перший аргумент функції);
* ``@require_session_role(current_user, *roles)`` — те саме, але користувач
  береться з ін'єктованого постачальника сесії;
* ``@timed(label, unit=..., logger=..., clock=...)`` — вимір часу;
* ``@logged(level, logger=...)`` — журнал викликів: аргументи, результат/виняток;
* ``compose_decorators`` — композиція декораторів.

Усі декоратори використовують ``functools.wraps`` та ``ParamSpec``/``TypeVar``.
Залежності (logger, clock, current_user) передаються як Callable.
"""

from __future__ import annotations

import functools
import time
from collections.abc import Callable, Iterable
from typing import Any, Concatenate, Literal, ParamSpec, TypeVar

from closures import Logger, User, make_role_checker

P = ParamSpec("P")
R = TypeVar("R")

AnyDecorator = Callable[[Callable[..., Any]], Callable[..., Any]]
RoleExpander = Callable[[Iterable[str]], frozenset[str]]


def _silent(_: str) -> None:
    """Логер за замовчуванням: нічого не виводить."""


class AuthorizationError(PermissionError):
    """Власний виняток: у користувача немає потрібної ролі."""

    def __init__(self, user: str, required: frozenset[str], func_name: str) -> None:
        self.user = user
        self.required = required
        self.func_name = func_name
        need = ", ".join(sorted(required))
        super().__init__(f"user '{user}' needs role [{need}] to call {func_name}()")


class AuthenticationError(PermissionError):
    """Немає залогіненого користувача."""


# ---------------------------------------------------------------------------
# @require_role
# ---------------------------------------------------------------------------
def require_role(
    *roles: str,
    mode: Literal["any", "all"] = "any",
    logger: Logger = _silent,
    expand: RoleExpander | None = None,
) -> Callable[[Callable[Concatenate[User, P], R]], Callable[Concatenate[User, P], R]]:
    """Фабрика декоратора: дозволяє виклик лише користувачу з роллю ``roles``.

    Перший позиційний аргумент декорованої функції — ``User``.
    ``expand`` — політика ієрархії ролей (наприклад, admin включає editor).
    """
    if not roles:
        raise ValueError("at least one role is required")
    required = frozenset(roles)
    check = make_role_checker(required, mode=mode)  # замикання над ролями

    def decorator(
        func: Callable[Concatenate[User, P], R],
    ) -> Callable[Concatenate[User, P], R]:
        @functools.wraps(func)
        def wrapper(user: User, /, *args: P.args, **kwargs: P.kwargs) -> R:
            effective = expand(user.roles) if expand else user.roles
            if not check(effective):
                logger(f"DENY {user.name} -> {func.__name__}")
                raise AuthorizationError(user.name, required, func.__name__)
            logger(f"ALLOW {user.name} -> {func.__name__}")
            return func(user, *args, **kwargs)

        return wrapper

    return decorator


def require_session_role(
    current_user: Callable[[], User | None],
    *roles: str,
    mode: Literal["any", "all"] = "any",
    logger: Logger = _silent,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Варіант для функцій без параметра ``user``: користувач — із сесії (DI)."""
    required = frozenset(roles)
    check = make_role_checker(required, mode=mode)

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            user = current_user()
            if user is None:
                logger(f"ANON -> {func.__name__}")
                raise AuthenticationError(f"login required for {func.__name__}()")
            if not check(user.roles):
                logger(f"DENY {user.name} -> {func.__name__}")
                raise AuthorizationError(user.name, required, func.__name__)
            logger(f"ALLOW {user.name} -> {func.__name__}")
            return func(*args, **kwargs)

        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# @timed
# ---------------------------------------------------------------------------
_FACTORS: dict[str, float] = {"s": 1.0, "ms": 1e3, "us": 1e6}


def timed(
    label: str | None = None,
    *,
    unit: Literal["s", "ms", "us"] = "ms",
    logger: Logger = print,
    clock: Callable[[], float] = time.perf_counter,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Вимір часу виконання; лог пишеться навіть якщо функція кинула виняток."""
    factor = _FACTORS[unit]

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        name = label or func.__name__

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start = clock()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed = (clock() - start) * factor
                logger(f"[timed] {name} took {elapsed:.3f} {unit}")

        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# @logged
# ---------------------------------------------------------------------------
def logged(
    level: Literal["DEBUG", "INFO", "WARNING"] = "INFO",
    *,
    logger: Logger = print,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Журнал виклику: ім'я, аргументи, результат або виняток."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            shown = ", ".join(
                [*map(repr, args), *(f"{k}={v!r}" for k, v in kwargs.items())]
            )
            logger(f"{level} call {func.__name__}({shown})")
            try:
                result = func(*args, **kwargs)
            except Exception as err:
                logger(f"{level} {func.__name__} raised {type(err).__name__}: {err}")
                raise
            logger(f"{level} {func.__name__} -> {result!r}")
            return result

        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# Композиція
# ---------------------------------------------------------------------------
def compose_decorators(
    *decorators: AnyDecorator,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """compose_decorators(a, b, c)(f) == a(b(c(f))) — як запис @a @b @c над f."""

    def apply(func: Callable[P, R]) -> Callable[P, R]:
        return functools.reduce(lambda acc, dec: dec(acc), reversed(decorators), func)

    return apply
