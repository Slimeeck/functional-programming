from __future__ import annotations

from algorithms import (
    Node,
    bfs_level_order,
    bst_contains,
    build_bst,
    dfs_preorder_iter,
    height_iterative,
    height_recursive,
    inorder,
    postorder,
    preorder,
)


def sample_tree() -> Node:
    #      4
    #     / \
    #    2   6
    #   / \   \
    #  1   3   7
    return Node(4, left=Node(2, Node(1), Node(3)), right=Node(6, None, Node(7)))


def test_traversals() -> None:
    t = sample_tree()
    assert list(preorder(t)) == [4, 2, 1, 3, 6, 7]
    assert list(inorder(t)) == [1, 2, 3, 4, 6, 7]
    assert list(postorder(t)) == [1, 3, 2, 7, 6, 4]
    assert bfs_level_order(t) == [4, 2, 6, 1, 3, 7]
    assert dfs_preorder_iter(t) == [4, 2, 1, 3, 6, 7]


def test_empty_tree() -> None:
    assert list(preorder(None)) == []
    assert bfs_level_order(None) == []
    assert dfs_preorder_iter(None) == []
    assert height_recursive(None) == height_iterative(None) == 0


def test_height() -> None:
    t = sample_tree()
    assert height_recursive(t) == height_iterative(t) == 3


def test_build_bst_and_search() -> None:
    keys = tuple(range(0, 31))
    bst = build_bst(keys)
    assert list(inorder(bst)) == list(keys)
    assert height_recursive(bst) == 5  # збалансоване: ceil(log2(32))
    assert all(bst_contains(bst, k) for k in keys)
    assert not bst_contains(bst, 100)
