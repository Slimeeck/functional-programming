# Лабораторна робота №1

## Варіант 4 — Кошик покупця

**Тема:** Основи функціонального програмування у Python (чисті функції, референтна прозорість, ізоляція побічних ефектів, `typing.Callable`).

### Постановка задачі

Вхідні дані — товари кошика: `name`, `price`, `qty`, `category`.
Потрібно обчислити **subtotal**, **категоріальну знижку**, **купон** і **ПДВ**.
Правила знижки/купона/податку передаються через `Callable`; результат — **новий кошик** (вхідні дані не змінюються).

Порядок розрахунку:

```text
subtotal -> категоріальна знижка -> купон -> ПДВ -> total
```

### Структура проєкту

```text
Lab_01/
├── core.py            # ЧИСТЕ ядро: модель, політики, make_cart_processor
├── app.py             # оболонка I/O: render_report(), run()
├── main.py            # точка входу
├── tests/
│   └── test_core.py   # pytest-тести
├── report/lab1.pdf    # звіт
├── demo_output.txt    # вивід python main.py
├── test_results.txt   # вивід pytest -v
├── requirements.txt   # pytest, mypy, black, ruff
├── pyproject.toml     # налаштування black / ruff / pytest
└── mypy.ini           # mypy --strict
```

### Що реалізовано у `core.py`

| Функція | Призначення |
|---|---|
| `line_total(item)` | вартість позиції `price * qty` |
| `cart_subtotal(items)` | subtotal кошика |
| `with_pricing(item, discount)` | повертає **новий** словник з полями `line_total`, `discount`, `discounted_total` |
| `is_valid_item(item)` | фільтр: ціна та кількість > 0 |
| `make_category_discount(rates)` | фабрика політики категоріальної знижки (`CategoryDiscountFn`) |
| `make_percent_coupon(p, min)` / `make_fixed_coupon(v, min)` / `no_coupon` | політики купона (`CouponFn`) |
| `make_vat(rate)` | політика ПДВ (`TaxFn`) |
| `make_min_price_filter(min_price)` | політика фільтра позицій (`ItemFilterFn`) |
| `make_cart_processor(...)` | **функція вищого порядку** — повертає налаштований обробник кошика |
| `process_cart_pure(items, *, ...)` | версія з явною передачею всіх числових параметрів |
| `compose(f, g)`, `make_multiplier(k)`, `make_percent_discount(p)` | додаткові вправи (композиція, фабрики) |
| `double_quantities`, `only_category` | приклади «новий список замість мутації» (map / filter) |
| `stamp_total(total, now)` | інжекція залежності часу через `Callable[[], float]` |

Типи політик:

```python
ItemFilterFn = Callable[[CartItem], bool]
CategoryDiscountFn = Callable[[CartItem, float], float]
CouponFn = Callable[[float], float]
TaxFn = Callable[[float], float]
NowFn = Callable[[], float]
```

### Принципи ФП, що застосовані

- **Чисті функції** — однаковий вхід → однаковий вихід, жодного `print`, `time`, `random` у ядрі.
- **Референтна прозорість** — виклик `process_cart_pure(cart, ...)` можна замінити його значенням.
- **Відсутність мутацій** — замість `item["total"] = ...` створюється новий словник `{**item, ...}`.
- **Немає глобалів у обчисленнях** — ставки, купони та ПДВ передаються явно (у фабрики / як аргументи).
- **Ізоляція побічних ефектів** — `print` і `time.time` лише в `app.py`.
- **Callable / HOF** — політики передаються як функції, `make_cart_processor` повертає обробник.

### Запуск

```bash
python -m venv .venv
.venv\Scripts\activate        # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Тести та перевірки якості

```bash
pytest -v
mypy .
black --check .
ruff check .
```

Тести перевіряють: референтну прозорість, відсутність мутацій, правильність розрахунку (subtotal → знижка → купон → ПДВ), Callable-політики, граничні випадки (порожній кошик, купон нижче порогу), `compose`, `make_multiplier`, інжекцію часу.

### Автор

Корецький Андрій, група ФеП-22, варіант 4
