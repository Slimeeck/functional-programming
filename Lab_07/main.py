"""Демонстрація ЛР7 (варіант 4 — облік працівників).

python main.py [шлях до .json/.csv] [N]
"""

from __future__ import annotations

import sys
from functools import partial
from pathlib import Path

from core import (
    build_pipeline,
    department_bonus,
    it_department_bonus,
    payroll_by_department,
    prepare_all,
    sort_by,
    total_payroll,
)
from loaders import load_employees
from models import Employee

HERE = Path(__file__).parent


def show(title: str, employees: list[Employee]) -> None:
    print(title)
    for place, e in enumerate(employees, start=1):
        print(
            f"  {place}. {e.name:<18} {e.department:<6} salary={e.salary:>8.0f}"
            f" exp={e.experience:>2} bonus={e.bonus:>7.0f} total={e.total_pay:>8.0f}"
        )


def main() -> None:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "sample_data.json"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    records = load_employees(source)  # singledispatch: Path
    print(f"Завантажено {len(records)} записів з {source.name}")

    top = build_pipeline(n=n)(records)
    show(f"\nTop-{n} (стандартна премія: 5% + 1%/рік, макс. 20%):", top)

    top_it = build_pipeline(bonus_policy=it_department_bonus, n=n, min_years=3)(records)
    show(
        f"\nTop-{n}, стаж >= 3, премія за відділом (partial(department_bonus)):", top_it
    )

    hr_policy = partial(department_bonus, rates={"hr": 0.3})
    everyone = prepare_all(records, hr_policy)
    show(
        "\nУсі активні, сортування attrgetter('department', 'name'):",
        sort_by("department", "name")(everyone),
    )

    staff = prepare_all(records)
    print("\nФонд оплати (reduce):", total_payroll(staff))
    print("За відділами (reduce):", payroll_by_department(staff))

    print("\nІнші джерела singledispatch:")
    with (HERE / "sample_data.csv").open(encoding="utf-8") as fh:
        print("  відкритий CSV-файл  :", len(load_employees(fh)), "записів")
    print("  str-шлях до CSV     :", len(load_employees(str(HERE / "sample_data.csv"))))
    print("  JSON-рядок          :", load_employees('[{"name": "x"}]'))
    print("  готовий list        :", len(load_employees(list(records))))


if __name__ == "__main__":
    main()
