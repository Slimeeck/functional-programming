# Лабораторна робота №7

## Варіант 4 — Облік працівників

**Тема:** `functools` та `operator`: `partial`, `reduce`, `singledispatch`, `total_ordering`,
`itemgetter` / `attrgetter` / `methodcaller`.

| Вхідні дані | Конвеєр / reduce | singledispatch / total_ordering |
|---|---|---|
| Працівники: `name`, `department`, `salary`, `experience`, `active` | Відібрати активних, нормалізувати імена, обчислити премію та ранжувати | `partial` для політики премії; singledispatch-loader; `EmployeeOrder` за salary / experience / name |

### Структура проєкту

```text
Lab_07/
├── models.py          # Employee (frozen dataclass), EmployeeOrder (@total_ordering)
├── loaders.py         # load_employees — @singledispatch (str / Path / file / list / tuple), JSON + CSV
├── core.py            # pipeline, partial-політики премії, operator, reduce-агрегації
├── main.py            # демонстрація
├── sample_data.json, sample_data.csv
├── tests/test_lab07.py
├── ASSIGNMENT.md
├── report/lab7.pdf
├── demo_output.txt, test_results.txt
├── requirements.txt, pyproject.toml, mypy.ini, .gitignore
```

### Конвеєр

```python
def pipeline(value, *funcs):                       # functools.reduce
    return reduce(lambda acc, f: f(acc), funcs, value)

pipeline(
    records,
    mapf(normalize),                               # partial(map, normalize)
    filterf(is_active),                            # partial(filter, attrgetter("active"))
    filterf(partial(min_experience, min_years)),
    mapf(partial(with_bonus, bonus_policy)),       # політика премії — partial
    rank,                                          # sorted(map(EmployeeOrder, ...))
    partial(top_n, n),
)
```

| Інструмент | Де використано |
|---|---|
| `functools.partial` | `mapf`, `filterf`, `standard_bonus = partial(experience_bonus, base_rate=0.05, per_year=0.01, cap=0.20)`, `it_department_bonus = partial(department_bonus, rates=...)`, `partial(min_experience, ...)`, `partial(top_n, n)`, `sort_by` |
| `functools.reduce` | `pipeline`, `total_payroll`, `payroll_by_department` |
| `operator.itemgetter` | витяг 5 полів сирого запису в `normalize` |
| `operator.methodcaller` | `strip`, `title`, `lower` при нормалізації |
| `operator.attrgetter` | `is_active`, `sort_by("department", "name")`, `total_pay` у згортці |
| `operator.add` | сума у `total_payroll` |

### Поліморфне завантаження (`@singledispatch`)

```python
load_employees("sample_data.json")          # str: шлях (.json / .csv) або JSON-текст
load_employees(Path("sample_data.csv"))     # pathlib.Path
with open("sample_data.csv", encoding="utf-8") as fh:
    load_employees(fh)                      # відкритий текстовий файл (io.TextIOBase)
load_employees([{...}, {...}])              # готова колекція (list / tuple)
load_employees(42)                          # TypeError
```

### `@total_ordering` — `EmployeeOrder`

Ключ порядку: `salary ↓`, `experience ↓`, `name ↑`. `a < b` означає «`a` у рейтингу вище за `b`»,
тому `sorted(map(EmployeeOrder, employees))` — готовий рейтинг. Реалізовано тільки `__eq__` і `__lt__`
(для чужих типів повертають `NotImplemented`); `<=`, `>`, `>=` генерує декоратор.

### Результат (`python main.py`)

```text
Top-3 (стандартна премія: 5% + 1%/рік, макс. 20%):
  1. Iryna Kravets      it     salary=   61000 exp= 4 bonus=   5490 total=   66490
  2. Andrii Shevchenko  it     salary=   52000 exp= 9 bonus=   7280 total=   59280
  3. Ivan Petrenko      it     salary=   52000 exp= 6 bonus=   5720 total=   57720
Фонд оплати (reduce): 357130.0
За відділами (reduce): {'it': 231640.0, 'sales': 89190.0, 'hr': 36300.0}
```

### Запуск

```bash
python -m venv .venv
.venv\Scripts\activate        # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python main.py                       # JSON за замовчуванням
python main.py sample_data.csv 5     # CSV, Top-5
pytest -v
mypy .
black --check .
ruff check .
```

### Автор

Корецький Андрій, група ФеП-22, варіант 4
