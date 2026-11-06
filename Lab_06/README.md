# Лабораторна робота №6

## Варіант 4 — Авторизація користувачів

**Тема:** Замикання (closures) та декоратори як функції вищого порядку (HOF).

| Обов'язкові компоненти | Завдання | Спеціальні вимоги |
|---|---|---|
| Closure для списку ролей; параметризований `@require_role`; `@timed` | Дозволяти виклик функції лише користувачам потрібної ролі | `@wraps`; власний виняток; логер як залежність |

### Структура проєкту

```text
Lab_06/
├── closures.py              # User, make_counter, make_logger, make_role_checker, ...
├── decorators.py            # require_role, require_session_role, timed, logged, compose_decorators
├── app.py                   # демонстраційний «сервіс документів»
├── main.py                  # точка входу
├── tests/
│   ├── test_closures.py
│   ├── test_decorators.py
│   └── test_composition.py  # порядок декораторів
├── ASSIGNMENT.md
├── report/lab6.pdf
├── demo_output.txt, test_results.txt
├── requirements.txt, pyproject.toml, mypy.ini, .gitignore
```

### Замикання (`closures.py`)

| Замикання | Що «пам'ятає» |
|---|---|
| `make_counter(start)` | змінний стан `value` через **`nonlocal`** (генератор id документів) |
| `make_logger(prefix, sink)` | префікс і залежність виводу `sink` |
| `make_memory_sink()` | список рядків логу (для тестів) |
| `make_role_checker(allowed, mode)` | **набір дозволених ролей** (`frozenset`, копія); режим `any` / `all` |
| `make_role_hierarchy(parents)` | граф ролей: `admin ⊃ editor ⊃ viewer` |
| `make_session()` | поточного користувача та кількість входів (`nonlocal`) |

### Параметризовані декоратори (`decorators.py`)

```python
@require_role("admin", "security", mode="all", logger=audit, expand=hierarchy)
def rotate_keys(user: User) -> str: ...
```

- `require_role(*roles, mode="any"|"all", logger, expand)` — фабрика декоратора; перший аргумент
  функції — `User`. Якщо ролі немає — `AuthorizationError` (власний виняток, підклас `PermissionError`,
  з полями `user`, `required`, `func_name`), тіло функції **не виконується**. Типізовано через `Concatenate[User, P]`.
- `require_session_role(current_user, *roles)` — користувач береться з ін'єктованого постачальника
  (`session.current`); без входу — `AuthenticationError`.
- `timed(label, unit="s"|"ms"|"us", logger, clock)` — час виконання; `clock` ін'єктується, лог у `finally`.
- `logged(level, logger)` — ім'я, аргументи, результат або виняток.
- `compose_decorators(a, b, c)(f) == a(b(c(f)))`.

Усі обгортки — з `@functools.wraps` (зберігаються `__name__`, `__doc__`, `__wrapped__`)
і типізовані `ParamSpec` / `TypeVar`. Логер, годинник і сесія — залежності типу `Callable`,
тому тести детерміновані (фейковий `clock`, `make_memory_sink`) і не мають реальних затримок.

### Порядок декораторів

```python
@timed(...)              # зовнішній: вимірює навіть заборонені спроби
@require_role("admin")   # внутрішній
def op(user): ...
```

Якщо поміняти місцями, то при відмові таймер не запускається взагалі — це перевіряють тести
`test_timed_outside_measures_denied_calls_too` і `test_timed_inside_is_skipped_when_denied`.

### Запуск

```bash
python -m venv .venv
.venv\Scripts\activate        # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python main.py
pytest -v
mypy .
black --check .
ruff check .
```

Тести: стан замикань (`nonlocal`), режими `any`/`all`, ієрархія ролей (зокрема цикли), користувач без ролей,
власні винятки, тіло функції не виконується при відмові, фейковий годинник, лог при винятку, метадані після
`@wraps`, порядок і композиція декораторів.

### Автор

Корецький Андрій, група ФеП-22, варіант 4
