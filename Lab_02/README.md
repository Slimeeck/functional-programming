# Лабораторна робота №2

## Варіант 4 — Замовлення ресторану

**Тема:** Функції вищого порядку, `lambda`, `map` / `filter` / `reduce`, функціональна композиція.

### Постановка задачі

Запис замовлення: `id`, `waiter`, `table`, `items` (позиції `name`, `price`, `qty`).
Конвеєр (без мутацій вхідних даних):

1. нормалізувати ім'я офіціанта (Title Case) — `map`;
2. визначити зону залу за столиком (`1–10 hall`, `11–20 terrace`, `21+ vip`) — `map`;
3. обчислити суму чека `check = Σ price·qty` — `map`;
4. застосувати сервісний коефіцієнт для вибраної зони (`--zone terrace --factor 1.1`) — `map`;
5. відфільтрувати малі чеки (`check < min_check`) — `filter`;
6. відсортувати: `check` спадно, тай-брейкер `id` зростанням — `sorted`;
7. взяти Top-N — `itertools.islice`.

Агрегація через `functools.reduce`: `count`, `sum_checks`, `avg_check`, `max_check`.

### Структура проєкту

```text
Lab_02/
├── core.py            # чисті трансформації, compose / pipe / juxt, reduce_stats, build_pipeline
├── app.py             # CLI (argparse), читання JSON, друк
├── main.py            # точка входу
├── sample_data.json   # приклад вхідних даних
├── tests/test_core.py # pytest
├── ASSIGNMENT.md      # завдання варіанта
├── report/lab2.pdf    # звіт
├── demo_output.txt, test_results.txt
├── requirements.txt, pyproject.toml, mypy.ini
```

### Ключові елементи

- `Record`, `OrderItem`, `Stats` — `TypedDict`.
- Етапи конвеєра — фабрики, що повертають чисту функцію `Iterable[Record] -> Iterable[Record]`:
  `normalize_waiters`, `with_zone`, `with_check`, `apply_service`, `drop_small_checks`,
  `sort_by_check_desc`, `take`.
- Кожен етап створює **нові** словники `{**r, ...}`; вхідний список не змінюється.
- `compose(f, g, h)(x) == f(g(h(x)))`, `pipe(x, f, g, h) == h(g(f(x)))`, `juxt(f, g)(x) == (f(x), g(x))`
  — реалізовані через `reduce`.
- `lambda` використано у `map`, `filter`, ключі сортування, `juxt`.
- Конвеєр лінивий (генератори) до етапу `sorted` — це перевіряє окремий тест.

```python
def build_pipeline(top_n=3, zone="terrace", factor=1.1, min_check=300.0):
    return compose(
        take(top_n),
        sort_by_check_desc(),
        drop_small_checks(min_check),
        apply_service(zone, factor),
        with_check(),
        with_zone(),
        normalize_waiters(),
    )
```

### Запуск

```bash
python -m venv .venv
.venv\Scripts\activate        # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python main.py --top 3 --zone terrace --factor 1.1 --min-check 300
```

Приклад виводу:

```text
Top-3 чеків (зона 'terrace' x1.1, мін. чек 300.0):
  1. #3   Iryna        стіл 25  vip      чек = 2200.00
  2. #6   Andrii       стіл 18  terrace  чек = 550.00
  3. #2   Taras        стіл 12  terrace  чек = 440.00
Агрегація (reduce) по всіх допущених чеках:
  count      = 6
  sum_checks = 4440.00
  avg_check  = 740.00
  max_check  = 2200.00
```

### Тести та перевірки

```bash
pytest -v
mypy .
black --check .
ruff check .
```

Тести: коректність Top-N і тай-брейкера, `n = 0` / `n > len`, відсутність мутацій, кожен етап окремо,
`reduce_stats` (у т.ч. порожній вхід), `compose` / `pipe` / `juxt`, лінивість конвеєра.

### Автор

Корецький Андрій, група ФеП-22, варіант 4
