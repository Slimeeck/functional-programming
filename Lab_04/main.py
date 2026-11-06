"""Демонстрація ЛР4 (варіант 4 — рекурсивний бінарний пошук): python main.py"""

from __future__ import annotations

import random
import sys

from algorithms import (
    Node,
    bfs_level_order,
    binary_search_cached,
    binary_search_iterative,
    binary_search_recursive,
    binary_search_tramp,
    binary_search_with_depth,
    bst_contains,
    build_bst,
    dfs_preorder_iter,
    fact_tail,
    fact_tramp,
    fib,
    fib_iter,
    find_first,
    height_iterative,
    height_recursive,
    inorder,
    linear_search_recursive,
    postorder,
    preorder,
    quicksort,
    quicksort_3way,
    trampoline,
)


def demo_search() -> None:
    print("=== 1. Бінарний пошук у незмінній відсортованій послідовності ===")
    prices = (15, 23, 42, 42, 42, 57, 64, 78, 91, 105)  # tuple — незмінна
    print("Послідовність:", prices)
    for target in (57, 15, 105, 42, 50, 0, 200):
        rec = binary_search_recursive(prices, target)
        it = binary_search_iterative(prices, target)
        idx, depth = binary_search_with_depth(prices, target)
        status = "знайдено" if rec != -1 else "відсутнє"
        print(
            f"  шукаємо {target:>3}: recursive={rec:>2}  iterative={it:>2}"
            f"  глибина={depth}  ({status})"
        )
    print("  перше входження 42 (lower_bound):", find_first(prices, 42))

    words = ("apple", "banana", "cherry", "kiwi", "mango")
    print(
        "  рядки:",
        words,
        "-> 'kiwi' на індексі",
        binary_search_recursive(words, "kiwi"),
    )

    big = tuple(range(0, 2_000_000, 2))
    idx, depth = binary_search_with_depth(big, 1_999_998)
    print(f"  1 000 000 елементів: індекс={idx}, глибина рекурсії={depth} (≈ log2 n)")
    print(
        "  trampoline-версія:",
        trampoline(binary_search_tramp(big, 1_999_998, 0, len(big) - 1)),
    )

    binary_search_cached.cache_clear()
    for t in (42, 42, 57, 42, 999):
        binary_search_cached(prices, t)
    print("  lru_cache:", binary_search_cached.cache_info())


def demo_limits() -> None:
    print("\n=== 2. Ліміт рекурсії та відсутність TCO ===")
    print("  sys.getrecursionlimit() =", sys.getrecursionlimit())
    seq = tuple(range(5000))
    try:
        linear_search_recursive(seq, 4999)
    except RecursionError:
        print("  linear_search_recursive на 5000 елементів -> RecursionError")
    print(
        "  binary_search_recursive на тих самих даних ->",
        binary_search_recursive(seq, 4999),
    )
    try:
        fact_tail(5000)
    except RecursionError:
        print("  fact_tail(5000) (хвостова рекурсія) -> RecursionError: TCO немає")
    print(
        "  trampoline(fact_tramp(5000)) має",
        trampoline(fact_tramp(5000)).bit_length(),
        "біт",
    )


def demo_sort_tree_fib() -> None:
    print("\n=== 3. Quicksort ===")
    xs = [5, 3, 8, 1, 9, 2, 5, 5, 0]
    print("  вхід:", xs)
    print("  quicksort:", quicksort(xs, random.Random(1)))
    print("  quicksort_3way:", quicksort_3way(xs))
    print("  вхід після сортування (не змінився):", xs)

    print("\n=== 4. Дерево ===")
    t = Node(4, Node(2, Node(1), Node(3)), Node(6, None, Node(7)))
    print("  preorder :", list(preorder(t)))
    print("  inorder  :", list(inorder(t)))
    print("  postorder:", list(postorder(t)))
    print("  BFS      :", bfs_level_order(t))
    print("  DFS iter :", dfs_preorder_iter(t))
    print("  висота rec/iter:", height_recursive(t), height_iterative(t))
    bst = build_bst((10, 20, 30, 40, 50, 60, 70))
    print(
        "  BST з tuple, inorder:",
        list(inorder(bst)),
        "| містить 50:",
        bst_contains(bst, 50),
    )

    print("\n=== 5. Фібоначчі ===")
    fib.cache_clear()
    print("  fib(0..10):", [fib(i) for i in range(11)])
    print("  fib(90) == fib_iter(90):", fib(90) == fib_iter(90))
    print("  fib.cache_info():", fib.cache_info())


def main() -> None:
    demo_search()
    demo_limits()
    demo_sort_tree_fib()


if __name__ == "__main__":
    main()
