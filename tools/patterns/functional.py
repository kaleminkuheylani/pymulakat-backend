"""Functional programming patterns."""
from ._shared import tcs

PATTERN = {
    "level": "intermediate",
    "templates": [
        {
            "title": "Pipe Function",
            "description": (
                "Verilen fonksiyonları soldan sağa sırayla uygulayan `pipe` yaz: "
                "`pipe(f, g, h)(x) == h(g(f(x)))`."
            ),
            "starter": (
                "from functools import reduce\n\n"
                "def pipe(*fns):\n"
                "    # pipe(f, g, h)(x) = h(g(f(x)))\n"
                "    pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"fns": ["double", "increment", "square"], "x": 3}, "expected": 49},
                    {"input": {"fns": ["identity"], "x": 42}, "expected": 42},
                    {"input": {"fns": ["neg", "neg"], "x": 5}, "expected": 5},
                    {"input": {"fns": ["double", "neg", "abs"], "x": -3}, "expected": 6},
                    {"input": {"fns": [], "x": 1}, "expected": "ValueError"},
                )},
                {"cases": tcs(
                    {"input": {"fns": ["increment", "double"], "x": 10}, "expected": 22},
                    {"input": {"fns": ["str", "len"], "x": 12345}, "expected": 5},
                    {"input": {"fns": ["square", "increment", "double"], "x": 4}, "expected": 34},
                    {"input": {"fns": ["abs"], "x": -7}, "expected": 7},
                    {"input": {"fns": ["double"] * 10, "x": 1}, "expected": 1024},
                )},
            ],
            "hints": [
                "💡 `reduce` ile sırayla uygula",
                "💡 Lambda: `lambda acc, f: f(acc)`",
                "💡 pipe() kısmi uygulama için, pipe() bir callable dönmeli",
            ],
            "explanation": (
                "reduce ile initial value'yu her fn'den geçir. Sonuçta pipe() bir "
                "callable döner: pipe(*fns)(x) = reduce(lambda acc, f: f(acc), fns, "
                "x). Boş fns listesi → ValueError."
            ),
            "complexity": "O(n) for n fns",
            "concepts": ["functional", "reduce", "higher-order", "composition"],
            "tags": ["functional", "higher-order"],
        },
        {
            "title": "Compose (Right-to-Left)",
            "description": (
                "Pipe'ın tersi: `compose(f, g, h)(x) == f(g(h(x)))`. Sağdan sola "
                "uygulama. Matematiksel fonksiyon kompozisyonu."
            ),
            "starter": (
                "from functools import reduce\n\n"
                "def compose(*fns):\n"
                "    # compose(f, g, h)(x) = f(g(h(x)))\n"
                "    pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"fns": ["increment", "double"], "x": 5}, "expected": 11},
                    {"input": {"fns": ["identity"], "x": 42}, "expected": 42},
                    {"input": {"fns": ["neg", "neg"], "x": 5}, "expected": 5},
                    {"input": {"fns": ["square", "double"], "x": 3}, "expected": 18},
                    {"input": {"fns": [], "x": 1}, "expected": "ValueError"},
                )},
                {"cases": tcs(
                    {"input": {"fns": ["str", "len"], "x": 1234}, "expected": 4},
                    {"input": {"fns": ["increment", "increment", "increment"], "x": 0}, "expected": 3},
                    {"input": {"fns": ["abs", "neg"], "x": -5}, "expected": -5},
                    {"input": {"fns": ["double", "square"], "x": 4}, "expected": 64},
                    {"input": {"fns": ["double"] * 5, "x": 1}, "expected": 32},
                )},
            ],
            "hints": [
                "💡 `reduce` ile sağdan sola (ters)",
                "💡 Lambda: `lambda acc, f: f(acc)` (aynı, ama initial değer son fn)",
                "💡 `compose(f, g)(x) = f(g(x))` (sağdan)",
            ],
            "explanation": (
                "Pipe'dan farkı: initial value x, son fn'den başla. reduce(lambda acc, "
                "f: f(acc), fns, x) ile fns[0] en sonra uygulanır. Veya reversed(fns) "
                "ile pipe.compose karışımı."
            ),
            "complexity": "O(n) for n fns",
            "concepts": ["functional", "reduce", "composition", "higher-order"],
            "tags": ["functional", "higher-order"],
        },
        {
            "title": "Curry Function",
            "description": (
                "f(a, b, c) → f(a)(b)(c). Multi-arg fonksiyonu tek-arg fonksiyonlar "
                "zincirine çevir."
            ),
            "starter": (
                "def curry(fn):\n"
                "    pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"fn": "add", "args": [1, 2]}, "expected": 3},
                    {"input": {"fn": "add", "args": []}, "expected": "partial"},
                    {"input": {"fn": "mul", "args": [3, 4, 5]}, "expected": 60},
                    {"input": {"fn": "concat3", "args": ["a", "b", "c"]}, "expected": "abc"},
                    {"input": {"fn": "div", "args": [10, 0]}, "expected": "ValueError"},
                )},
                {"cases": tcs(
                    {"input": {"fn": "sub", "args": [10, 3]}, "expected": 7},
                    {"input": {"fn": "mod", "args": [10, 3]}, "expected": 1},
                    {"input": {"fn": "pow", "args": [2, 10]}, "expected": 1024},
                    {"input": {"fn": "and_op", "args": [True, False]}, "expected": False},
                    {"input": {"fn": "or_op", "args": [False, True]}, "expected": True},
                )},
            ],
            "hints": [
                "💡 `inspect.signature(fn).parameters` ile argüman sayısı",
                "💡 Partial application: yeterli argüman birikince çağır",
                "💡 Veya: `lambda a: lambda b: fn(a, b)` recursive",
            ],
            "explanation": (
                "Recursive: eğer fn tek argümanlıysa direkt dön. Değilse, ilk argümanı "
                "al ve kalan için recursive. inspect ile parametre sayısını öğren, ya "
                "da positional argüman sayısını takip et."
            ),
            "complexity": "O(n) for n-arg fn",
            "concepts": ["functional", "currying", "partial-application", "higher-order"],
            "tags": ["functional", "currying"],
        },
    ],
}