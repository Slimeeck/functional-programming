# ЛР7. functools та operator — варіант 4

**Предметна область:** Облік працівників.

**Вхідні дані:** працівники — `name`, `department`, `salary`, `experience`, `active`.

**Конвеєр / reduce:** відібрати активних, нормалізувати імена, обчислити премію та ранжувати.

**singledispatch / total_ordering:** `partial` для політики премії; singledispatch loader;
`EmployeeOrder` за salary / experience / name.

## Обов'язкові вимоги

- Універсальна функція `pipeline(value, *funcs)` через `functools.reduce`.
- `functools.partial` щонайменше для двох етапів конвеєра або налаштовуваних функцій.
- Щонайменше два засоби `operator`: `itemgetter`, `attrgetter` або `methodcaller`.
- Поліморфне завантаження через `@singledispatch` щонайменше для `str`, `pathlib.Path`,
  відкритого текстового файлу та готової колекції.
- Підтримка JSON і CSV.
- Клас з `@total_ordering`, `__eq__` та `__lt__`, `NotImplemented` для чужих типів.
- Багатокритеріальне сортування та Top-N.
- pytest-тести для pipeline, partial, singledispatch, operator і всіх операторів порівняння.
- mypy, black, ruff; README.md.
