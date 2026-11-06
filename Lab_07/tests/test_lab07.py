from __future__ import annotations

import io
from functools import partial
from operator import attrgetter, itemgetter, methodcaller
from pathlib import Path
from typing import Any

import pytest

from core import (
    build_pipeline,
    department_bonus,
    experience_bonus,
    filterf,
    in_department,
    is_active,
    mapf,
    normalize,
    normalize_name,
    parse_bool,
    payroll_by_department,
    pipeline,
    prepare_all,
    rank,
    sort_by,
    standard_bonus,
    top_n,
    total_payroll,
    with_bonus,
)
from loaders import load_employees, parse_text
from models import Employee, EmployeeOrder

DATA_DIR = Path(__file__).resolve().parent.parent
JSON_PATH = DATA_DIR / "sample_data.json"
CSV_PATH = DATA_DIR / "sample_data.csv"


@pytest.fixture
def records() -> list[dict[str, Any]]:
    return load_employees(JSON_PATH)


def emp(name: str, salary: float, experience: int, dept: str = "it") -> Employee:
    return Employee(name, dept, salary, experience, True)


# ===================== pipeline / partial ===================================
def test_pipeline_applies_left_to_right() -> None:
    assert pipeline(2, lambda x: x + 1, lambda x: x * 10) == 30
    assert pipeline("x") == "x"  # без функцій — identity


def test_partial_helpers() -> None:
    square = partial(pow, exp=2)
    assert pipeline(range(4), mapf(square), filterf(lambda x: x > 1), list) == [4, 9]


def test_partial_bonus_policies() -> None:
    e = emp("A", 10_000, 4)
    assert standard_bonus(e) == 900.0  # 5% + 4*1% = 9%
    assert standard_bonus(emp("B", 10_000, 30)) == 2000.0  # cap 20%
    custom = partial(experience_bonus, base_rate=0.0, per_year=0.02, cap=1.0)
    assert custom(e) == 800.0
    dept = partial(department_bonus, rates={"it": 0.5})
    assert dept(e) == 5000.0
    assert dept(emp("C", 100, 1, "hr")) == 0.0
    assert isinstance(standard_bonus, partial)
    assert standard_bonus.keywords == {"base_rate": 0.05, "per_year": 0.01, "cap": 0.2}


def test_with_bonus_returns_new_object() -> None:
    e = emp("A", 1000, 0)
    new = with_bonus(lambda _: 50.0, e)
    assert new is not e and e.bonus == 0.0 and new.bonus == 50.0
    assert new.total_pay == 1050.0


# ===================== operator =============================================
def test_operator_tools() -> None:
    row = {"name": "  aLiCe  ", "age": 20}
    assert itemgetter("name", "age")(row) == ("  aLiCe  ", 20)
    assert methodcaller("title")(methodcaller("strip")(row["name"])) == "Alice"
    people = [emp("B", 1, 2), emp("A", 1, 1)]
    assert [e.name for e in sorted(people, key=attrgetter("experience"))] == ["A", "B"]
    assert [e.name for e in sort_by("salary", "name")(people)] == ["A", "B"]


def test_normalization() -> None:
    assert normalize_name("  iVAN   petrenko ") == "Ivan Petrenko"
    assert [parse_bool(v) for v in (True, "yes", "1", "TRUE", "no", "0", False)] == [
        True,
        True,
        True,
        True,
        False,
        False,
        False,
    ]
    e = normalize(
        {
            "name": " bob ",
            "department": " IT ",
            "salary": "10",
            "experience": "2",
            "active": "yes",
        }
    )
    assert e == Employee("Bob", "it", 10.0, 2, True)


# ===================== конвеєр та Top-N =====================================
def test_top_n_pipeline(records: list[dict[str, Any]]) -> None:
    top = build_pipeline(n=3)(records)
    assert [e.name for e in top] == [
        "Iryna Kravets",
        "Andrii Shevchenko",
        "Ivan Petrenko",
    ]
    assert [e.bonus for e in top] == [5490.0, 7280.0, 5720.0]


def test_inactive_filtered_and_tie_by_name(records: list[dict[str, Any]]) -> None:
    everyone = build_pipeline(n=100)(records)
    names = [e.name for e in everyone]
    assert "Maria Bondar" not in names  # неактивна
    assert names.index("Sofia Lysenko") < names.index(
        "Taras Melnyk"
    )  # однакові salary/exp
    assert len(everyone) == 7


def test_min_years_and_n_edge_cases(records: list[dict[str, Any]]) -> None:
    assert all(e.experience >= 5 for e in build_pipeline(n=10, min_years=5)(records))
    assert build_pipeline(n=0)(records) == []
    assert build_pipeline()([]) == []
    assert top_n(-1, [emp("A", 1, 1)]) == []


def test_input_records_not_mutated(records: list[dict[str, Any]]) -> None:
    snapshot = [dict(r) for r in records]
    build_pipeline()(records)
    assert records == snapshot


def test_reduce_aggregations(records: list[dict[str, Any]]) -> None:
    staff = prepare_all(records)
    assert total_payroll(staff) == 357130.0
    assert payroll_by_department(staff) == {
        "it": 231640.0,
        "sales": 89190.0,
        "hr": 36300.0,
    }
    assert total_payroll([]) == 0.0
    assert payroll_by_department([]) == {}


def test_predicates() -> None:
    e = emp("A", 1, 1)
    assert is_active(e) is True
    assert in_department("it", e) and not in_department("hr", e)


# ===================== singledispatch =======================================
def test_load_from_path_and_str(records: list[dict[str, Any]]) -> None:
    assert len(load_employees(JSON_PATH)) == 8
    assert load_employees(str(JSON_PATH)) == records
    assert len(load_employees(CSV_PATH)) == 8
    assert len(load_employees(str(CSV_PATH))) == 8


def test_load_from_open_file() -> None:
    with CSV_PATH.open(encoding="utf-8") as fh:
        rows = load_employees(fh)
    assert rows[1]["name"] == "olena koval"
    with JSON_PATH.open(encoding="utf-8") as fh:
        assert len(load_employees(fh)) == 8


def test_load_from_stringio_and_text() -> None:
    csv_text = io.StringIO("name,department,salary,experience,active\nA,it,1,1,true\n")
    assert load_employees(csv_text) == [
        {
            "name": "A",
            "department": "it",
            "salary": "1",
            "experience": "1",
            "active": "true",
        }
    ]
    assert load_employees('[{"name": "B"}]') == [{"name": "B"}]
    assert parse_text('{"employees": [{"name": "C"}]}') == [{"name": "C"}]


def test_load_from_collections(records: list[dict[str, Any]]) -> None:
    assert load_employees(records) == records
    assert load_employees(tuple(records)) == records
    with pytest.raises(ValueError):
        load_employees([1, 2])


def test_csv_and_json_give_same_result() -> None:
    from_json = build_pipeline(n=10)(load_employees(JSON_PATH))
    from_csv = build_pipeline(n=10)(load_employees(CSV_PATH))
    assert from_json == from_csv


def test_unsupported_type_and_bad_json() -> None:
    with pytest.raises(TypeError):
        load_employees(42)
    with pytest.raises(ValueError):
        parse_text("[1, 2]", ".json")


# ===================== total_ordering =======================================
def test_all_comparison_operators() -> None:
    hi = EmployeeOrder(emp("A", 900, 1))
    lo = EmployeeOrder(emp("B", 100, 1))
    same = EmployeeOrder(emp("A", 900, 1))
    assert hi < lo and hi <= lo and hi <= same
    assert lo > hi and lo >= hi and hi >= same
    assert hi == same and hi != lo
    assert not (hi > lo) and not (lo < hi)


def test_ordering_tie_breakers() -> None:
    a = EmployeeOrder(emp("Zed", 500, 10))
    b = EmployeeOrder(emp("Amy", 500, 3))
    c = EmployeeOrder(emp("Bob", 500, 3))
    assert sorted([c, b, a]) == [a, b, c]  # experience ↓, потім name ↑
    assert [e.name for e in rank([c.employee, b.employee, a.employee])] == [
        "Zed",
        "Amy",
        "Bob",
    ]


def test_not_implemented_for_foreign_types() -> None:
    o = EmployeeOrder(emp("A", 1, 1))
    assert o.__eq__("x") is NotImplemented
    assert o.__lt__(5) is NotImplemented
    assert (o == "x") is False
    with pytest.raises(TypeError):
        _ = o < 5
    with pytest.raises(TypeError):
        _ = o >= "x"


def test_order_is_hashable() -> None:
    assert len({EmployeeOrder(emp("A", 1, 1)), EmployeeOrder(emp("A", 1, 1))}) == 1
