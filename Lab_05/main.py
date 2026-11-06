"""Демонстрація ЛР5 (варіант 4 — геометрична прогресія): python main.py"""

from __future__ import annotations

from itertools import islice

from streams import (
    chunked,
    drop,
    fib_stream,
    geometric,
    geometric_accumulate,
    geometric_count,
    geometric_sum_formula,
    moving_average,
    multiples_window_pipeline,
    primes,
    progression_report,
    ratios,
    running_product,
    running_sum,
    skip_below,
    sliding_window,
    take,
    up_to_threshold,
    while_above,
)


def main() -> None:
    q0, r, threshold = 3.0, 2.0, 1000.0
    print(f"=== Геометрична прогресія q0={q0}, r={r} ===")
    print("Перші 8 членів (yield)      :", take(8, geometric(q0, r)))
    print("Перші 8 (accumulate+repeat) :", take(8, geometric_accumulate(q0, r)))
    print("Перші 8 (count)             :", take(8, geometric_count(q0, r)))

    print(f"\nЧлени до порога {threshold} (takewhile):")
    upto = list(up_to_threshold(geometric(q0, r), threshold))
    print("  ", upto)
    print("Накопичена сума   (accumulate add):", list(running_sum(upto)))
    print("Накопичений добуток (accumulate mul):", list(running_product(upto)))
    print(
        "Перевірка формулою S_n:",
        geometric_sum_formula(q0, r, len(upto)),
        "==",
        sum(upto),
    )
    print("Відношення сусідніх членів:", take(5, ratios(geometric(q0, r))))

    print("\nТаблиця (n, член, сума, добуток):")
    for n, term, s, p in progression_report(q0, r, 100.0):
        print(f"  {n:>2} {term:>8.1f} {s:>8.1f} {p:>14.1f}")

    print("\nСпадна прогресія 100 * 0.5^n, поки член >= 1:")
    print("  ", list(while_above(geometric(100.0, 0.5), 1.0)))
    print(
        "Пропустити члени < 50 (dropwhile), взяти 4:",
        take(4, skip_below(geometric(1.0, 3.0), 50)),
    )
    print("drop(3) + take(4):", take(4, drop(3, geometric(1.0, 10.0))))
    print("Ковзні вікна k=3:", take(3, sliding_window(geometric(1.0, 2.0), 3)))
    print("Рухоме середнє k=2:", take(5, moving_average(geometric(2.0, 2.0), 2)))

    print("\n=== Базові потоки ===")
    print("fib_stream: drop 5, take 8 :", take(8, drop(5, fib_stream())))
    print("primes, перші 10           :", take(10, primes()))
    print("вікна сусідніх простих     :", take(3, sliding_window(primes(), 2)))
    print("кратні 3 -> суми вікон по 4:", multiples_window_pipeline(10))
    print("chunked(range(10), 4)      :", list(chunked(range(10), 4)))
    print("islice нескінченного потоку:", list(islice(geometric(1, -2), 6)))


if __name__ == "__main__":
    main()
