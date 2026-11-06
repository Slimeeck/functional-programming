"""Оболонка ЛР2: читання JSON, аргументи CLI, друк результату.

Приклад:
    python app.py --top 3 --zone terrace --factor 1.1 --min-check 300
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from core import Record, Stats, build_pipeline, prepare, reduce_stats

DEFAULT_DATA = Path(__file__).with_name("sample_data.json")


def load_records(path: Path) -> list[Record]:
    """I/O: читання записів із JSON-файлу."""
    with path.open(encoding="utf-8") as fh:
        return cast(list[Record], json.load(fh))


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ЛР2 — замовлення ресторану")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--top", type=int, default=3, help="кількість чеків у Top-N")
    parser.add_argument("--zone", default="terrace", help="hall / terrace / vip")
    parser.add_argument("--factor", type=float, default=1.1, help="сервісний коеф.")
    parser.add_argument("--min-check", type=float, default=300.0)
    return parser.parse_args(argv)


def render(top: list[Record], stats: Stats, args: argparse.Namespace) -> None:
    print(
        f"Top-{args.top} чеків (зона '{args.zone}' x{args.factor}, "
        f"мін. чек {args.min_check}):"
    )
    for place, r in enumerate(top, start=1):
        print(
            f"  {place}. #{r['id']:<3} {r['waiter']:<12} стіл {r['table']:<3}"
            f" {r['zone']:<8} чек = {r['check']:.2f}"
        )
    print("Агрегація (reduce) по всіх допущених чеках:")
    print(f"  count      = {stats['count']}")
    print(f"  sum_checks = {stats['sum_checks']:.2f}")
    print(f"  avg_check  = {stats['avg_check']:.2f}")
    print(f"  max_check  = {stats['max_check']:.2f}")


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    records = load_records(args.data)
    top = build_pipeline(args.top, args.zone, args.factor, args.min_check)(records)
    stats = reduce_stats(prepare(args.zone, args.factor, args.min_check)(records))
    render(top, stats, args)


if __name__ == "__main__":
    main()
