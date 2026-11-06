# Функціональне програмування — лабораторні роботи

**Студент:** Корецький Андрій Вікторович
**Група:** ФеП-22
**Варіант:** 4

| № | Тема | Варіант 4 | Папка |
|---|---|---|---|
| 1 | Основи ФП: чисті функції, побічні ефекти, `Callable` | Кошик покупця | [Lab_01](Lab_01) |
| 2 | Функції вищого порядку, `lambda`, `map`/`filter`/`reduce`, композиція | Замовлення ресторану | [Lab_02](Lab_02) |
| 3 | Незмінні структури даних (`tuple`, `frozenset`, frozen dataclass, `MappingProxyType`) | Склад товарів | [Lab_03](Lab_03) |
| 4 | Рекурсія та мемоізація (`lru_cache`, ліміт стеку, TCO) | Рекурсивний бінарний пошук | [Lab_04](Lab_04) |
| 5 | Ліниві обчислення: генератори та `itertools` | Геометрична прогресія | [Lab_05](Lab_05) |
| 6 | Замикання та декоратори | Авторизація користувачів | [Lab_06](Lab_06) |
| 7 | `functools` та `operator` (`partial`, `reduce`, `singledispatch`, `total_ordering`) | Облік працівників | [Lab_07](Lab_07) |
| 8 | Алгебраїчні типи даних, `Protocol`, `Literal`, `match/case` | Геометричні фігури | [Lab_08](Lab_08) |

Кожна папка містить код, тести `pytest`, `README.md`, конфіги `mypy` / `black` / `ruff`,
результати запуску (`demo_output.txt`, `test_results.txt`) та звіт `report/labN.pdf`.

## Запуск будь-якої роботи

```bash
cd Lab_01
python -m venv .venv
.venv\Scripts\activate        # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python main.py
pytest -v
mypy .
black --check .
ruff check .
```

Потрібен Python ≥ 3.10 (для Lab_08 — ≥ 3.11).
