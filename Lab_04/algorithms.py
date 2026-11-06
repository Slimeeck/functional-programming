"""ЛР4. Рекурсія та мемоізація. Варіант 4 — рекурсивний бінарний пошук.

Основне завдання варіанта:
    * рекурсивний бінарний пошук у відсортованій НЕЗМІННІЙ послідовності;
    * порівняння з ітеративним пошуком; знайдені / відсутні значення.

Базова частина ЛР (обов'язкова для всіх):
    * quicksort (випадковий pivot) + 3-шляховий і гібридний варіанти;
    * рекурсивні обходи дерева + ітеративні BFS / DFS, висота дерева;
    * fib з @lru_cache + fib_iter.

Виклик: trampoline — моделювання TCO без росту стеку.
"""

from __future__ import annotations

import random
from collections import deque
from collections.abc import Callable, Generator, Sequence
from dataclasses import dataclass
from functools import cache, lru_cache
from typing import Any, Protocol, TypeVar


class SupportsLessThan(Protocol):
    def __lt__(self, other: Any, /) -> bool: ...


T = TypeVar("T", bound=SupportsLessThan)


# ===========================================================================
# 1. Бінарний пошук (варіант 4)
# ===========================================================================
def binary_search_recursive(
    seq: Sequence[T], target: T, lo: int = 0, hi: int | None = None
) -> int:
    """Індекс ``target`` у відсортованій ``seq`` або -1.

    База рекурсії:  порожній діапазон (lo > hi) -> -1; seq[mid] == target -> mid.
    Крок рекурсії:  шукаємо в лівій АБО правій половині (задача зменшується вдвічі).
    Послідовність не копіюється й не змінюється — передаються лише межі lo/hi,
    тому глибина рекурсії O(log n), а пам'ять O(log n) на стек.
    """
    if hi is None:
        hi = len(seq) - 1
    if lo > hi:  # база: діапазон порожній
        return -1
    mid = (lo + hi) // 2
    value = seq[mid]
    if target < value:
        return binary_search_recursive(seq, target, lo, mid - 1)
    if value < target:
        return binary_search_recursive(seq, target, mid + 1, hi)
    return mid  # база: знайдено


def binary_search_iterative(seq: Sequence[T], target: T) -> int:
    """Ітеративна альтернатива: той самий алгоритм, але O(1) додаткової пам'яті."""
    lo, hi = 0, len(seq) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        value = seq[mid]
        if target < value:
            hi = mid - 1
        elif value < target:
            lo = mid + 1
        else:
            return mid
    return -1


def lower_bound_recursive(
    seq: Sequence[T], target: T, lo: int = 0, hi: int | None = None
) -> int:
    """Перша позиція, куди можна вставити ``target`` (аналог bisect_left).

    Корисно для послідовностей з дублікатами: повертає ПЕРШЕ входження.
    """
    if hi is None:
        hi = len(seq)
    if lo >= hi:
        return lo
    mid = (lo + hi) // 2
    if seq[mid] < target:
        return lower_bound_recursive(seq, target, mid + 1, hi)
    return lower_bound_recursive(seq, target, lo, mid)


def find_first(seq: Sequence[T], target: T) -> int:
    """Індекс першого входження або -1 (через lower_bound_recursive)."""
    i = lower_bound_recursive(seq, target)
    found = i < len(seq) and not (target < seq[i]) and not (seq[i] < target)
    return i if found else -1


def binary_search_with_depth(
    seq: Sequence[T], target: T, lo: int = 0, hi: int | None = None, depth: int = 1
) -> tuple[int, int]:
    """Те саме, що binary_search_recursive, але повертає (індекс, глибина рекурсії)."""
    if hi is None:
        hi = len(seq) - 1
    if lo > hi:
        return -1, depth
    mid = (lo + hi) // 2
    if target < seq[mid]:
        return binary_search_with_depth(seq, target, lo, mid - 1, depth + 1)
    if seq[mid] < target:
        return binary_search_with_depth(seq, target, mid + 1, hi, depth + 1)
    return mid, depth


@lru_cache(maxsize=1024)
def binary_search_cached(seq: tuple[int, ...], target: int) -> int:
    """Мемоізований пошук: tuple хешується, тож (seq, target) — ключ кешу.

    Виграш — для повторних запитів того самого значення в тій самій послідовності.
    Демонструє cache_info() / cache_clear().
    """
    return binary_search_recursive(seq, target)


# ===========================================================================
# 2. Quicksort
# ===========================================================================
def quicksort(xs: Sequence[T], rng: random.Random | None = None) -> list[T]:
    """Чистий рекурсивний quicksort з випадковим pivot (вхід не змінюється)."""
    if len(xs) <= 1:  # база
        return list(xs)
    pivot = (rng or random).choice(xs)
    left = [x for x in xs if x < pivot]
    mid = [x for x in xs if not (x < pivot) and not (pivot < x)]
    right = [x for x in xs if pivot < x]
    return quicksort(left, rng) + mid + quicksort(right, rng)


def median_of_three(a: T, b: T, c: T) -> T:
    """Медіана трьох значень (pivot для quicksort_3way)."""
    if a < b:
        if b < c:
            return b
        return c if a < c else a
    if a < c:
        return a
    return c if b < c else b


def quicksort_3way(xs: Sequence[T]) -> list[T]:
    """3-шляховий quicksort (Дейкстра) — ефективний для багатьох дублікатів.

    pivot — медіана з трьох (перший, середній, останній).
    """
    if len(xs) <= 1:
        return list(xs)
    pivot = median_of_three(xs[0], xs[len(xs) // 2], xs[-1])
    less = [x for x in xs if x < pivot]
    equal = [x for x in xs if not (x < pivot) and not (pivot < x)]
    greater = [x for x in xs if pivot < x]
    return quicksort_3way(less) + equal + quicksort_3way(greater)


def insertion_sort(xs: Sequence[T]) -> list[T]:
    """Сортування вставками (повертає новий список)."""
    out: list[T] = []
    for x in xs:
        i = len(out)
        while i > 0 and x < out[i - 1]:
            i -= 1
        out.insert(i, x)
    return out


def hybrid_sort(xs: Sequence[T], threshold: int = 32) -> list[T]:
    """Гібрид: quicksort, а для малих підмасивів (< threshold) — вставки."""
    if len(xs) < threshold:
        return insertion_sort(xs)
    pivot = random.choice(xs)
    left = [x for x in xs if x < pivot]
    mid = [x for x in xs if not (x < pivot) and not (pivot < x)]
    right = [x for x in xs if pivot < x]
    return hybrid_sort(left, threshold) + mid + hybrid_sort(right, threshold)


# ===========================================================================
# 3. Дерева
# ===========================================================================
@dataclass(frozen=True, slots=True)
class Node:
    key: int
    left: Node | None = None
    right: Node | None = None


def preorder(t: Node | None) -> Generator[int, None, None]:
    if t is None:
        return
    yield t.key
    yield from preorder(t.left)
    yield from preorder(t.right)


def inorder(t: Node | None) -> Generator[int, None, None]:
    if t is None:
        return
    yield from inorder(t.left)
    yield t.key
    yield from inorder(t.right)


def postorder(t: Node | None) -> Generator[int, None, None]:
    if t is None:
        return
    yield from postorder(t.left)
    yield from postorder(t.right)
    yield t.key


def bfs_level_order(t: Node | None) -> list[int]:
    """Ітеративний обхід у ширину (черга)."""
    if t is None:
        return []
    queue: deque[Node] = deque([t])
    out: list[int] = []
    while queue:
        n = queue.popleft()
        out.append(n.key)
        if n.left:
            queue.append(n.left)
        if n.right:
            queue.append(n.right)
    return out


def dfs_preorder_iter(t: Node | None) -> list[int]:
    """Ітеративний DFS (власний стек): спершу правий, щоб лівий пішов першим."""
    if t is None:
        return []
    stack, out = [t], []
    while stack:
        n = stack.pop()
        out.append(n.key)
        if n.right:
            stack.append(n.right)
        if n.left:
            stack.append(n.left)
    return out


def height_recursive(t: Node | None) -> int:
    if t is None:
        return 0
    return 1 + max(height_recursive(t.left), height_recursive(t.right))


def height_iterative(t: Node | None) -> int:
    """Висота через BFS по рівнях — без рекурсії."""
    if t is None:
        return 0
    level, height = [t], 0
    while level:
        height += 1
        level = [c for n in level for c in (n.left, n.right) if c is not None]
    return height


def build_bst(sorted_keys: Sequence[int]) -> Node | None:
    """Збалансоване BST з відсортованої послідовності (рекурсивно, ділення навпіл)."""
    if not sorted_keys:
        return None
    mid = len(sorted_keys) // 2
    return Node(
        sorted_keys[mid],
        build_bst(sorted_keys[:mid]),
        build_bst(sorted_keys[mid + 1 :]),
    )


def bst_contains(t: Node | None, key: int) -> bool:
    """Рекурсивний пошук у BST — той самий принцип «відкинути половину»."""
    if t is None:
        return False
    if key < t.key:
        return bst_contains(t.left, key)
    if key > t.key:
        return bst_contains(t.right, key)
    return True


# ===========================================================================
# 4. Фібоначчі та мемоізація
# ===========================================================================
def fib_naive(n: int) -> int:
    """Експоненційна рекурсія O(phi^n) — для порівняння."""
    if n < 0:
        raise ValueError("n must be non-negative")
    return n if n < 2 else fib_naive(n - 1) + fib_naive(n - 2)


@cache
def fib(n: int) -> int:
    """Мемоізований Фібоначчі: O(n) часу, O(n) глибини стеку."""
    if n < 0:
        raise ValueError("n must be non-negative")
    return n if n < 2 else fib(n - 1) + fib(n - 2)


def fib_iter(n: int) -> int:
    """DP без рекурсії — безпечно для будь-якого n."""
    if n < 0:
        raise ValueError("n must be non-negative")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


# ===========================================================================
# 5. Хвостова рекурсія і trampoline
# ===========================================================================
def fact_tail(n: int, acc: int = 1) -> int:
    """Хвостова рекурсія. У CPython НЕМАЄ TCO — стек усе одно росте."""
    if n <= 1:
        return acc
    return fact_tail(n - 1, acc * n)


Thunk = Callable[[], Any]


def trampoline(result: Any) -> Any:
    """Виконує «кроки», поки функція повертає thunk (callable без аргументів)."""
    while callable(result):
        result = result()
    return result


def binary_search_tramp(seq: Sequence[T], target: T, lo: int, hi: int) -> Any:
    """Бінарний пошук у стилі trampoline: замість виклику повертає lambda."""
    if lo > hi:
        return -1
    mid = (lo + hi) // 2
    if target < seq[mid]:
        return lambda: binary_search_tramp(seq, target, lo, mid - 1)
    if seq[mid] < target:
        return lambda: binary_search_tramp(seq, target, mid + 1, hi)
    return mid


def fact_tramp(n: int, acc: int = 1) -> Any:
    if n <= 1:
        return acc
    return lambda: fact_tramp(n - 1, acc * n)


def linear_search_recursive(seq: Sequence[T], target: T, i: int = 0) -> int:
    """Лінійна рекурсія — глибина O(n): на великих даних дає RecursionError."""
    if i >= len(seq):
        return -1
    if not (seq[i] < target) and not (target < seq[i]):
        return i
    return linear_search_recursive(seq, target, i + 1)
