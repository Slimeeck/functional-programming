# Лабораторна робота №5

## Варіант 4 — Геометрична прогресія

**Тема:** Ліниві обчислення: генератори (`yield`, `yield from`), ітератори, `itertools`
(`islice`, `takewhile`, `dropwhile`, `accumulate`, `count`, `repeat`, `starmap`, `tee`).

| Вхідний потік | Основне завдання | Обов'язкові інструменти |
|---|---|---|
| Початкове значення `q0` і множник `r` | Нескінченний генератор; взяти значення до порога та обчислити накопичений добуток / суму | `yield`, `takewhile`, `accumulate` |

### Структура проєкту

```text
Lab_05/
├── streams.py           # усі генератори та утиліти
├── main.py              # демонстрація
├── tests/test_streams.py
├── ASSIGNMENT.md
├── report/lab5.pdf
├── demo_output.txt, test_results.txt
├── requirements.txt, pyproject.toml, mypy.ini, .gitignore
```

### Геометрична прогресія

```python
def geometric(q0: float, r: float) -> Iterator[float]:
    value = q0
    while True:          # нескінченний потік — обчислюється лише на запит
        yield value
        value *= r
```

| Функція | Інструмент | Що робить |
|---|---|---|
| `geometric(q0, r)` | власний `yield` | нескінченний потік `q0, q0·r, q0·r², …` |
| `geometric_accumulate(q0, r)` | `accumulate(repeat(r), mul, initial=q0)` | та сама прогресія через itertools |
| `geometric_count(q0, r)` | `count` + генераторний вираз | `q0 · rⁿ` |
| `up_to_threshold(it, t)` | `takewhile` | члени, поки `|x| ≤ t` (зупиняє нескінченний потік) |
| `while_above(it, eps)` | `takewhile` | для спадної прогресії (`|r| < 1`) |
| `skip_below(it, t)` | `dropwhile` | пропустити малі початкові члени |
| `running_sum(it)` | `accumulate(add)` | накопичена сума `S₁, S₂, …` |
| `running_product(it)` | `accumulate(mul)` | накопичений добуток `P₁, P₂, …` |
| `geometric_sum_formula(q0, r, n)` | — | `Sₙ = q0·(1 − rⁿ)/(1 − r)` для перевірки |
| `ratios(it)` | `sliding_window` + `starmap` | відношення сусідніх членів (= r) |
| `progression_report(q0, r, t)` | `tee` + `zip` + `count` | ліниві рядки `(n, член, сума, добуток)` |

Приклад (`q0 = 3`, `r = 2`, поріг 1000):

```text
члени до порога : [3, 6, 12, 24, 48, 96, 192, 384, 768]
накопичена сума : [3, 9, 21, 45, 93, 189, 381, 765, 1533]
добуток         : [3, 18, 216, 5184, 248832, ...]
S_9 за формулою : 1533.0 == 1533.0
```

### Базові утиліти

- `take(n, it)` — `list(islice(it, n))`; `drop(n, it)` — `next(islice(it, n, n), None)`;
- `sliding_window(it, k)` — `deque(maxlen=k)`, без матеріалізації потоку;
- `moving_average(it, k)`, `chunked(it, size)` (через `iter(callable, sentinel)`);
- `naturals()` (`yield from count`), `fib_stream()`, `primes()` (лінивий потік простих);
- `tee_safe(it, n)` — навчальний аналог `itertools.tee` на буферах `deque`;
- `multiples_window_pipeline()` — натуральні → кратні 3 → суми вікон по 4 → перші N.

### Лінивість і крайні випадки

- Нескінченні потоки завжди обмежуються `take` / `islice` / `takewhile`; `list(...)` — лише у фіналі.
- Тест `test_geometric_is_lazy` рахує звернення до потоку: обчислено **рівно** стільки елементів, скільки запитано.
- Крайні випадки: порожнє джерело, `n = 0`, `k > len`, `k ≤ 0` / `n < 0` → `ValueError`
  (у `sliding_window` помилка виникає одразу, а не при першому `next`).
- Генератор вичерпується після одного проходу — для кількох споживачів використовується `tee`.

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
