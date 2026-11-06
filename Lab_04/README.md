# Лабораторна робота №4

## Варіант 4 — Рекурсивний пошук у списку

**Тема:** Рекурсія та мемоізація в Python (`functools.lru_cache`, ліміт стеку, відсутність TCO).

| Основне завдання | Додаткове дослідження |
|---|---|
| Рекурсивний бінарний пошук у відсортованій **незмінній** послідовності | Порівняння з ітеративним пошуком; тести знайдених / відсутніх значень |

Також виконано базову частину ЛР (quicksort, обходи дерев, `fib` з `lru_cache`), «плюс»-завдання
(3-шляховий quicksort, гібридний sort, висота дерева рекурсивно + ітеративно) та виклик (trampoline).

### Структура проєкту

```text
Lab_04/
├── algorithms.py          # усі алгоритми
├── main.py                # демонстрація
├── benchmark.py           # заміри часу -> benchmark_results.json
├── tests/
│   ├── test_search.py     # бінарний пошук (варіант)
│   ├── test_quicksort.py
│   ├── test_tree.py
│   ├── test_fib.py
│   └── test_performance.py
├── report/lab4.pdf
├── demo_output.txt, test_results.txt, benchmark_output.txt, benchmark_results.json
├── requirements.txt, pyproject.toml, mypy.ini, .gitignore
```

### Рекурсивний бінарний пошук

```python
def binary_search_recursive(seq, target, lo=0, hi=None) -> int:
    if hi is None:
        hi = len(seq) - 1
    if lo > hi:                      # БАЗА 1: діапазон порожній -> не знайдено
        return -1
    mid = (lo + hi) // 2
    if target < seq[mid]:            # КРОК: шукаємо в лівій половині
        return binary_search_recursive(seq, target, lo, mid - 1)
    if seq[mid] < target:            # КРОК: шукаємо в правій половині
        return binary_search_recursive(seq, target, mid + 1, hi)
    return mid                       # БАЗА 2: знайдено
```

- **Базовий випадок:** `lo > hi` (порожній діапазон) → `-1`; `seq[mid] == target` → `mid`.
- **Рекурсивний крок:** задача зменшується вдвічі — пошук лише в одній половині.
- **Чистота:** послідовність не копіюється (немає зрізів) і не змінюється — передаються лише межі `lo`/`hi`.
  Працює з будь-якою `Sequence` порівнюваних елементів (`int`, `str`, …); тип описано `Protocol` `SupportsLessThan`.
- **Складність:** O(log n) часу, глибина рекурсії ⌈log₂ n⌉ + 1 (для 1 000 000 елементів — 20 кадрів).

| Функція | Опис |
|---|---|
| `binary_search_recursive` | основна рекурсивна версія |
| `binary_search_iterative` | ітеративна альтернатива (O(1) пам'яті) |
| `lower_bound_recursive`, `find_first` | рекурсивний `bisect_left` — перше входження для дублікатів |
| `binary_search_with_depth` | повертає `(індекс, глибина)` — для аналізу стеку |
| `binary_search_cached` | `@lru_cache` над `tuple` — демонстрація `cache_info()` / `cache_clear()` |
| `binary_search_tramp` + `trampoline` | версія без росту стеку (моделювання TCO) |
| `linear_search_recursive` | лінійна рекурсія O(n) — показує, як рекурсія впирається в ліміт |

### Мемоізація

- `fib` — `@lru_cache(maxsize=None)`: з O(φⁿ) до O(n). `fib.cache_info()`, `fib.cache_clear()`.
- `binary_search_cached` — `@lru_cache(maxsize=1024)`, ключ `(tuple, target)`; виграє на повторних запитах.

### Ліміт рекурсії CPython і відсутність TCO

- CPython обмежує глибину стеку викликів: `sys.getrecursionlimit()` → зазвичай **1000**.
  Перевищення — `RecursionError`. Піднімати ліміт (`sys.setrecursionlimit`) ризиковано — можна отримати аварійне завершення інтерпретатора.
- **TCO (tail-call optimization) у CPython немає** за задумом розробників (зберігаються повні traceback-и).
  Тому навіть хвостова рекурсія `fact_tail(n, acc)` росте у стеку: `fact_tail(5000)` → `RecursionError`.
- Бінарний пошук безпечний для рекурсії, бо глибина лише O(log n). Лінійна рекурсія (`linear_search_recursive`)
  на 5000 елементах падає з `RecursionError` — тут **ітеративна версія безпечніша**.
- `trampoline` — функції повертають «наступний крок» (`lambda`), а цикл їх виконує: стек не росте.

### Порівняння часу (`python benchmark.py`, 2000 пошуків)

| Розмір | recursive, s | iterative, s | cached (warm), s | `bisect`, s |
|---:|---:|---:|---:|---:|
| 100 | 0.00135 | 0.00107 | 0.00015 | 0.00024 |
| 10 000 | 0.00442 | 0.00255 | 0.00342 | 0.00046 |
| 1 000 000 | 0.00867 | 0.00614 | 0.00718 | 0.00190 |

`fib(25)`: naive ≈ 0.013 s, `lru_cache` ≈ 0.00004 s, ітеративний ≈ 0.000004 s.

**Висновок:** ітеративний пошук швидший за рекурсивний на ~30–40 % (немає накладних витрат на кадри стеку),
асимптотика однакова O(log n). Кеш має сенс лише для повторних запитів. Мемоізація Фібоначчі дає прискорення
на кілька порядків. (Числа залежать від ПК та версії Python.)

### Запуск

```bash
python -m venv .venv
.venv\Scripts\activate        # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python main.py
python benchmark.py
pytest -v
pytest -q -s tests/test_performance.py
mypy .
black --check .
ruff check .
```

### Автор

Корецький Андрій, група ФеП-22, варіант 4
