"""Демонстраційний сервіс документів з авторизацією за ролями (ЛР6, варіант 4)."""

from __future__ import annotations

import time

from closures import User, make_counter, make_logger, make_role_hierarchy, make_session
from decorators import (
    AuthenticationError,
    AuthorizationError,
    logged,
    require_role,
    require_session_role,
    timed,
)

audit = make_logger("AUDIT")
perf = make_logger("PERF")
next_doc_id = make_counter(100)
hierarchy = make_role_hierarchy({"admin": ["editor"], "editor": ["viewer"]})
session = make_session()


@timed("view_report", unit="ms", logger=perf, clock=time.perf_counter)
@require_role("viewer", logger=audit, expand=hierarchy)
def view_report(user: User, report: str) -> str:
    """Переглянути звіт (viewer, editor, admin)."""
    return f"{user.name} переглядає звіт '{report}'"


@require_role("editor", logger=audit, expand=hierarchy)
def create_document(user: User, title: str) -> int:
    """Створити документ (editor або admin); id — з лічильника-замикання."""
    doc_id = next_doc_id()
    return doc_id


@logged("WARNING", logger=audit)
@require_role("admin", logger=audit)
def delete_document(user: User, doc_id: int) -> str:
    """Видалити документ (тільки admin)."""
    return f"документ #{doc_id} видалено користувачем {user.name}"


@require_role("admin", "security", mode="all", logger=audit)
def rotate_keys(user: User) -> str:
    """Потрібні ОБИДВІ ролі: admin і security."""
    return "ключі оновлено"


@require_session_role(session.current, "admin", logger=audit)
def reset_cache() -> str:
    """Користувач береться з сесії (ін'єкція current_user)."""
    return "кеш скинуто"


def try_call(title: str, action: object) -> None:
    try:
        result = action() if callable(action) else action
        print(f"  OK   {title}: {result}")
    except (AuthorizationError, AuthenticationError) as err:
        print(f"  FAIL {title}: {type(err).__name__}: {err}")


def main() -> None:
    alice = User("alice", frozenset({"admin"}))
    bob = User("bob", frozenset({"editor"}))
    eve = User("eve", frozenset({"viewer"}))
    root = User("root", frozenset({"admin", "security"}))

    print("=== require_role + ієрархія ролей ===")
    for user in (alice, bob, eve):
        try_call(f"{user.name}.view_report", lambda u=user: view_report(u, "Q3"))
    try_call("bob.create_document", lambda: create_document(bob, "План"))
    try_call("alice.create_document", lambda: create_document(alice, "Бюджет"))
    try_call("eve.create_document", lambda: create_document(eve, "Нотатка"))

    print("\n=== тільки admin + @logged ===")
    try_call("alice.delete_document", lambda: delete_document(alice, 101))
    try_call("bob.delete_document", lambda: delete_document(bob, 101))

    print("\n=== mode='all' ===")
    try_call("alice.rotate_keys", lambda: rotate_keys(alice))
    try_call("root.rotate_keys", lambda: rotate_keys(root))

    print("\n=== роль із сесії ===")
    try_call("anonymous.reset_cache", reset_cache)
    session.login(bob)
    try_call("bob(session).reset_cache", reset_cache)
    session.login(alice)
    try_call("alice(session).reset_cache", reset_cache)
    print("  входів у сесії:", session.logins_count())

    print("\n=== метадані після декорування ===")
    print("  __name__   :", delete_document.__name__)
    print("  __doc__    :", delete_document.__doc__)
    print("  __wrapped__:", hasattr(delete_document, "__wrapped__"))
