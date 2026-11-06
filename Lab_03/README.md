# Лабораторна робота №3

## Варіант 4 — Склад товарів

**Тема:** Незмінні (immutable) структури даних у Python: `tuple`, `frozenset`,
`@dataclass(frozen=True, slots=True)`, `NamedTuple`, `MappingProxyType`, pure updates.

### Постановка задачі

| Предметна область | Незмінна модель | Pure-оновлення | Що перевірити |
|---|---|---|---|
| Склад товарів | `Product`, `StockRecord`, tags, supplier meta | поповнення залишку, зміна ціни, додавання тегу | кожна операція повертає **новий** `StockRecord` |

### Структура проєкту

```text
Lab_03/
├── model.py                 # Product, Movement, StockRecord, make_meta
├── core.py                  # pure updates, запити, lru_cache, freeze()
├── baseline.py              # мутабельна версія (тільки для порівняння часу)
├── main.py                  # демонстрація
├── tests/
│   ├── test_immutability.py # немутація, read-only, хешованість, freeze
│   └── test_performance.py  # mutable vs immutable (timeit)
├── report/lab3.pdf
├── demo_output.txt, test_results.txt, perf_results.txt
├── requirements.txt, pyproject.toml, mypy.ini, .gitignore
```

### Модель (`model.py`)

```python
@dataclass(frozen=True, slots=True)
class Product:
    sku: str; name: str; price: float; category: str

class Movement(NamedTuple):          # запис історії руху товару
    kind: Literal["in", "out", "price"]; qty: int; note: str = ""

@dataclass(frozen=True, slots=True)
class StockRecord:
    product: Product
    quantity: int
    tags: frozenset[str]                       # НЕ set
    supplier: Mapping[str, str]                # MappingProxyType, hash=False
    history: tuple[Movement, ...]              # НЕ list
```

| Замість | Використано | Навіщо |
|---|---|---|
| `list` історії | `tuple[Movement, ...]` | немає `append`, хешується |
| `set` тегів | `frozenset[str]` | операції множин `\|`, `-`, хешується |
| `dict` постачальника | `MappingProxyType` (з копією джерела) | read-only view, `TypeError` при записі |
| звичайний клас | `@dataclass(frozen=True, slots=True)` | `FrozenInstanceError`, `__eq__`/`__hash__`, економія пам'яті |

### Pure updates (`core.py`)

| Функція | Як створюється нова копія |
|---|---|
| `restock(record, qty)` | `replace(...)` + конкатенація `history + (Movement,)` |
| `ship(record, qty)` | те саме, з перевіркою залишку |
| `change_price(record, price)` | новий `Product` через `replace` усередині нового `StockRecord` |
| `add_tag` / `remove_tag` | `tags \| frozenset({tag})` / `tags - frozenset({tag})` |
| `update_supplier(record, **changes)` | нова `MappingProxyType` з об'єднаних даних |
| `apply_clearance_discount(record, p)` | «правило знижки» — новий запис лише для тегу `clearance` |

Додатково: `records_to_reorder`, `by_tag`, `top_by_value` (приймають `Sequence`, повертають `tuple`),
`total_inventory_value` з `@lru_cache` (ключ — `tuple` хешованих записів),
`index_by_record` (запис як ключ `dict`), `freeze(obj)` — глибоке заморожування.

### Хешованість

`StockRecord` хешований: `@dataclass(frozen=True)` генерує `__hash__`.
Єдине поле, що **заважає** хешуванню, — `supplier` (`MappingProxyType` не хешується),
тому воно оголошене як `field(hash=False)`: воно бере участь у `==`, але не в `hash()`.
Це коректно, бо рівні об'єкти все одно мають рівні хеші. Тест `test_mappingproxy_itself_is_not_hashable` це демонструє.

### Вимірювання «до / після»

```bash
pytest -q -s --durations=5
```

Результат на моєму ПК (Python 3.14, Windows 11), 5000 ітерацій сценарію «поповнення + зміна ціни + тег»:

| Модель | Час |
|---|---|
| мутабельна (`baseline.py`) | ≈ 0.007 s |
| незмінна (`model.py` / `core.py`) | ≈ 0.064 s |

Повний вивід — у `perf_results.txt`. Усі 21 тест виконуються менш ніж за 0.3 s.

### Висновок

Незмінна модель трохи повільніша на мікробенчмарку (кожне оновлення створює новий об'єкт і новий tuple/frozenset),
але різниця в абсолютних числах мізерна (десятки мікросекунд на операцію). Натомість отримуємо:
відсутність прихованих змін стану, повну історію версій (кожна стара версія лишається валідною),
прості тести без захисних `deepcopy`, можливість використати записи як ключі `dict`/`set` та кешувати
чисті функції через `lru_cache`. Накладні витрати — додаткова пам'ять на копії та неможливість `deepcopy`
для `MappingProxyType` (для незмінних об'єктів вона й не потрібна).

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

### Автор

Корецький Андрій, група ФеП-22, варіант 4
