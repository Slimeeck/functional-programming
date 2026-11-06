# Лабораторна робота №8

## Варіант 4 — Геометричні фігури

**Тема:** Алгебраїчні типи даних (ADT) «по-Python'івськи»: `@dataclass(frozen=True)`, `Union` / `TypeAlias`,
`Literal`, `Protocol`, структурний pattern matching `match/case`, `mypy --strict`.

| ADT / вузли | Основне завдання | Додаткові вимоги |
|---|---|---|
| `Circle`, `Rectangle`, `Triangle` (+ рекурсивний `Group`) | Чистими функціями обчислювати площу та периметр | `Literal` для одиниць вимірювання; `Protocol` для об'єктів із властивістю `area` |

### Структура проєкту

```text
Lab_08/
├── model.py       # ADT: Circle, Rectangle, Triangle, Group; Unit (Literal); HasArea (Protocol)
├── evaluator.py   # чисті функції з match/case: area, perimeter, scale, convert, classify, ...
├── pretty.py      # render(), render_tree()
├── expr.py        # базове завдання: Expr = Num | Add | Mul, eval_expr, render_expr
├── main.py        # демонстрація
├── tests/
│   ├── test_shapes.py
│   └── test_expr.py
├── report/lab8.pdf
├── demo_output.txt, test_results.txt
├── mypy.ini (strict), pyproject.toml, requirements.txt, .gitignore
```

### Модель

```python
Unit: TypeAlias = Literal["mm", "cm", "m"]

@dataclass(frozen=True, slots=True)
class Circle:    radius: float; unit: Unit = "cm"
class Rectangle: width: float; height: float; unit: Unit = "cm"
class Triangle:  a: float; b: float; c: float; unit: Unit = "cm"
class Group:     name: str; shapes: tuple[Shape, ...] = ()     # рекурсивний вузол

Shape: TypeAlias = Circle | Rectangle | Triangle | Group

class HasArea(Protocol):
    @property
    def area(self) -> float: ...
```

- Вузли незмінні (`frozen=True`), хешовані, валідуються в `__post_init__` (додатні розміри, нерівність трикутника).
- `Measurement(kind, area, perimeter, unit)` — результат обчислень, структурно задовольняє `HasArea`.
- `total_area(items: Iterable[HasArea])` і `largest(...)` працюють з **будь-якими** об'єктами з `area`
  (у тестах — сторонній клас `Plot`, який нічого не успадковує).

### Операції над ADT (`evaluator.py`)

```python
def area(shape: Shape, unit: Unit = "cm") -> float:
    match shape:
        case Circle(radius=r, unit=u):            raw = math.pi * r**2
        case Rectangle(width=w, height=h, unit=u): raw = w * h
        case Triangle(a=a, b=b, c=c, unit=u):      raw = heron(a, b, c)
        case Group(shapes=items):                  return sum(area(i, unit) for i in items)
        case _:                                    assert_never(shape)
    return raw * length_factor(u, unit) ** 2
```

| Функція | Опис |
|---|---|
| `area`, `perimeter` | площа / периметр у заданих одиницях (рекурсивно для `Group`) |
| `scale(shape, k)` | нова фігура, збільшена в k разів |
| `convert(shape, unit)` | нова фігура в інших одиницях |
| `classify(shape)` | `match` з guard-умовами: square, right / equilateral / isosceles / scalene triangle, ... |
| `count_shapes`, `depth` | статистика дерева фігур |
| `measure(shape, unit)` | `Measurement` |
| `render`, `render_tree` (`pretty.py`) | текстове представлення, дерево з площами |

`case _: assert_never(shape)` — перевірка вичерпності: якщо додати новий вузол і забути його обробити,
`mypy --strict` видасть помилку.

### Приклад (`python main.py`)

```text
house/ (group of 3, S=16.56 m²)
  - Rectangle(4x3 m)  [rectangle]  S=12.00 m²
  - Triangle(4, 2.5, 2.5 m)  [isosceles triangle]  S=3.00 m²
  windows/ (group of 3, S=1.56 m²)
    - Rectangle(80x80 cm)  [square]  S=0.64 m²
    - Rectangle(80x80 cm)  [square]  S=0.64 m²
    - Circle(r=30 cm)  [circle]  S=0.28 m²
```

### Запуск

```bash
python -m venv .venv
.venv\Scripts\activate        # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python main.py
pytest -v
mypy --strict .
black --check .
ruff check .
```

Тести: кожен вузол ADT, усі типи трикутників, одиниці `mm`/`cm`/`m`, вкладені групи, порожня група,
`scale`/`convert` без мутацій, `FrozenInstanceError`, хешованість, некоректні фігури (`ValueError`),
`Protocol` зі стороннім класом, `render`/`render_tree`, базове завдання `Expr`.

Потрібен Python ≥ 3.11 (`typing.assert_never`).

### Автор

Корецький Андрій, група ФеП-22, варіант 4
