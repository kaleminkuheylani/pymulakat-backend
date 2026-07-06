"""Recursion patterns."""
from ._shared import tcs

PATTERN = {
    "level": "intermediate",
    "templates": [
        {
            "title": "Tree Traversals (Pre/In/Post)",
            "description": (
                "Binary tree (dict: {val, left, right}) için 3 traversal dön: "
                "preorder, inorder, postorder. None node'lar skip edilir."
            ),
            "starter": (
                "def preorder(root):\n    pass\n\n"
                "def inorder(root):\n    pass\n\n"
                "def postorder(root):\n    pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"op": "pre", "tree": {"val": 1, "left": {"val": 2, "left": None, "right": None}, "right": {"val": 3, "left": None, "right": None}}}, "expected": [1, 2, 3]},
                    {"input": {"op": "pre", "tree": None}, "expected": []},
                    {"input": {"op": "pre", "tree": {"val": 1, "left": {"val": 2, "left": {"val": 3, "left": None, "right": None}, "right": {"val": 4, "left": None, "right": None}}, "right": {"val": 5, "left": None, "right": None}}}, "expected": [1, 2, 3, 4, 5]},
                    {"input": {"op": "in", "tree": {"val": 1, "left": {"val": 2, "left": None, "right": None}, "right": {"val": 3, "left": None, "right": None}}}, "expected": [2, 1, 3]},
                    {"input": {"op": "post", "tree": {"val": 1, "left": {"val": 2, "left": None, "right": None}, "right": {"val": 3, "left": None, "right": None}}}, "expected": [2, 3, 1]},
                )},
                {"cases": tcs(
                    {"input": {"op": "in", "tree": {"val": 5, "left": {"val": 3, "left": None, "right": None}, "right": {"val": 7, "left": None, "right": None}}}, "expected": [3, 5, 7]},
                    {"input": {"op": "post", "tree": None}, "expected": []},
                    {"input": {"op": "pre", "tree": {"val": 1, "left": None, "right": None}}, "expected": [1]},
                    {"input": {"op": "in", "tree": {"val": 1, "left": None, "right": None}}, "expected": [1]},
                    {"input": {"op": "post", "tree": {"val": 1, "left": None, "right": None}}, "expected": [1]},
                )},
            ],
            "hints": [
                "💡 Preorder: root, left, right",
                "💡 Inorder: left, root, right",
                "💡 Postorder: left, right, root",
            ],
            "explanation": (
                "Recursive her traversal farklı sırada root'u ziyaret eder. Base case: "
                "root is None → return []. None olmayan subtree'leri traverse et ve "
                "concatenate et. Iterative implementasyon stack ile yapılabilir ama "
                "recursive daha okunabilir."
            ),
            "complexity": "O(n) time, O(h) space (recursion stack)",
            "concepts": ["recursion", "tree", "traversal", "binary-tree"],
            "tags": ["recursion", "tree", "intermediate"],
        },
        {
            "title": "N-Queens Solver",
            "description": (
                "N x N satranç tahtasına N vezir yerleştir, hiçbiri birbirini tehdit "
                "etmesin. Tüm valid placement'ları döndür."
            ),
            "starter": (
                "def solve_n_queens(n):\n"
                "    # Backtracking: sırayla dene, invalid'da geri çekil\n"
                "    # Output: ['.Q..', '.Q..', ...] formatında her placement\n"
                "    pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"n": 1}, "expected_count": 1},
                    {"input": {"n": 2}, "expected_count": 0},
                    {"input": {"n": 4}, "expected_count": 2},
                    {"input": {"n": 8}, "expected_count": 92},
                    {"input": {"n": 0}, "expected_count": 1},
                )},
                {"cases": tcs(
                    {"input": {"n": 3}, "expected_count": 0},
                    {"input": {"n": 5}, "expected_count": 10},
                    {"input": {"n": 6}, "expected_count": 4},
                    {"input": {"n": 7}, "expected_count": 40},
                    {"input": {"n": -1}, "expected_count": "ValueError"},
                )},
            ],
            "hints": [
                "💡 Backtracking: sırayla dene, invalid'da geri çekil",
                "💡 Sütun, diag1 (row+col), diag2 (row-col+n) set'leri tut",
                "💡 Row-by-row yerleştir",
            ],
            "explanation": (
                "Row-by-row backtracking. Her yeni row için tüm sütunları dene. Aynı "
                "sütun, ana çapraz (row+col), yan çapraz (row-col+n) set'lerinde "
                "vezir varsa geç. Geçerliyse devam, değilse geri al. n=0 veya n=1 edge "
                "case'leri handle et."
            ),
            "complexity": "O(N!) worst case (pruning ile çok daha az)",
            "concepts": ["backtracking", "recursion", "constraint-satisfaction", "combinatorial"],
            "tags": ["recursion", "backtracking", "advanced"],
        },
        {
            "title": "Flatten Nested List Iterator",
            "description": (
                "[[1, 2, [3]], 4, [[5, 6], 7]] gibi nested list'leri düzleştiren "
                "iterator yaz. Hasnext + next API veya generator."
            ),
            "starter": (
                "def flatten(nested_list):\n"
                "    # Generator: yield her int\n"
                "    pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"data": [1, 2, 3]}, "expected": [1, 2, 3]},
                    {"input": {"data": []}, "expected": []},
                    {"input": {"data": [[1, 2, [3, 4]], 5, [[6]]]}, "expected": [1, 2, 3, 4, 5, 6]},
                    {"input": {"data": [[[[[1]]]]]}, "expected": [1]},
                    {"input": {"data": [1, [2, [3, [4, [5]]]]]}, "expected": [1, 2, 3, 4, 5]},
                )},
                {"cases": tcs(
                    {"input": {"data": [[[1]]]}, "expected": [1]},
                    {"input": {"data": [[], [[]], [[[]]]]}, "expected": []},
                    {"input": {"data": list(range(100))}, "expected": list(range(100))},
                    {"input": {"data": [None, 1, None, 2]}, "expected": [None, 1, None, 2]},
                    {"input": {"data": [[[1, 2], 3], [4, [5, 6]]]}, "expected": [1, 2, 3, 4, 5, 6]},
                )},
            ],
            "hints": [
                "💡 `yield from` recursive generator",
                "💡 isinstance(item, list) check",
                "💡 Stack-based iterative versiyon da mümkün",
            ],
            "explanation": (
                "Recursive generator: her item için eğer list ise `yield from "
                "flatten(item)`, değilse `yield item`. Base case: boş liste → yield "
                "yok. Python'un generator protokolü lazy evaluation sağlar."
            ),
            "complexity": "O(n) time, O(d) space (d = max depth)",
            "concepts": ["recursion", "generator", "iterator", "yield-from"],
            "tags": ["recursion", "generator", "intermediate"],
        },
    ],
}