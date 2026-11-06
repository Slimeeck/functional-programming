"""Поліморфне завантаження працівників через ``functools.singledispatch``.

Підтримувані джерела:
* ``str``            — шлях до .json / .csv АБО сам JSON-текст;
* ``pathlib.Path``   — файл .json / .csv;
* відкритий текстовий файл (``io.TextIOBase``) — формат за розширенням ``name``
  або за вмістом;
* готова колекція (``list`` / ``tuple``) словників.
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Mapping
from functools import singledispatch
from pathlib import Path
from typing import Any

RawRecord = dict[str, Any]


def parse_text(text: str, fmt: str = "") -> list[RawRecord]:
    """Розбір JSON або CSV. ``fmt`` — розширення ('.json' / '.csv') або ''."""
    fmt = fmt.lower()
    stripped = text.lstrip()
    if fmt == ".csv" or (not fmt and not stripped.startswith(("[", "{"))):
        return [dict(row) for row in csv.DictReader(io.StringIO(text))]
    data = json.loads(text)
    if isinstance(data, Mapping):  # {"employees": [...]}
        data = data.get("employees", [])
    if not isinstance(data, list) or not all(isinstance(r, Mapping) for r in data):
        raise ValueError("expected a JSON array of objects")
    return [dict(r) for r in data]


@singledispatch
def load_employees(source: object) -> list[RawRecord]:
    """Генерична функція: реалізація обирається за типом ``source``."""
    raise TypeError(f"unsupported source type: {type(source).__name__}")


@load_employees.register
def _(source: str) -> list[RawRecord]:
    if source.lstrip().startswith(("[", "{")):
        return parse_text(source, ".json")
    return load_employees(Path(source))


@load_employees.register
def _(source: Path) -> list[RawRecord]:
    return parse_text(source.read_text(encoding="utf-8"), source.suffix)


@load_employees.register
def _(source: io.TextIOBase) -> list[RawRecord]:
    suffix = Path(str(getattr(source, "name", ""))).suffix
    return parse_text(source.read(), suffix)


@load_employees.register(list)
@load_employees.register(tuple)
def _(source: list[Any] | tuple[Any, ...]) -> list[RawRecord]:
    if not all(isinstance(r, Mapping) for r in source):
        raise ValueError("expected a collection of mappings")
    return [dict(r) for r in source]
