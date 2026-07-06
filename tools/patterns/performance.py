"""Performance optimization patterns."""
from ._shared import tcs

PATTERN = {
    "level": "advanced",
    "templates": [
        {
            "title": "Memoize with functools.lru_cache",
            "description": (
                "Fibonacci'yi memoization ile optimize et: O(2^n) → O(n). "
                "`functools.lru_cache` veya manuel dict kullan."
            ),
            "starter": (
                "def fib(n):\n"
                "    # Memoize: her n'i 1 kez hesapla\n"
                "    pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"n": 10}, "expected": 55},
                    {"input": {"n": 0}, "expected": 0},
                    {"input": {"n": 30}, "expected": 832040},
                    {"input": {"n": 1}, "expected": 1},
                    {"input": {"n": -1}, "expected": "ValueError"},
                )},
                {"cases": tcs(
                    {"input": {"n": 2}, "expected": 1},
                    {"input": {"n": 5}, "expected": 5},
                    {"input": {"n": 20}, "expected": 6765},
                    {"input": {"n": 35}, "expected": 9227465},
                    {"input": {"n": 100}, "expected": 354224848179261915075},
                )},
            ],
            "hints": [
                "💡 `@lru_cache(maxsize=None)` decorator",
                "💡 Veya manuel dict: cache[n] = fib(n-1)+fib(n-2)",
                "💡 Base case: n < 2 → n",
            ],
            "explanation": (
                "Naive fib O(2^n) çünkü her çağrı 2 alt çağrı yapıyor. Memoization "
                "ile her n sadece 1 kez hesaplanır → O(n). @lru_cache decorator en "
                "kolay yol. n<0 → ValueError."
            ),
            "complexity": "O(n) time, O(n) space (memoized)",
            "concepts": ["memoization", "DP", "optimization", "functools"],
            "tags": ["performance", "memoization", "advanced"],
        },
        {
            "title": "Sorted List Maintenance (bisect)",
            "description": (
                "Heap veya sorted list'te insert/delete O(log n). `bisect` ile "
                "sorted list maintain et, insert/delete O(n) ama search O(log n)."
            ),
            "starter": (
                "from bisect import bisect_left, insort\n\n"
                "class SortedList:\n"
                "    def __init__(self):\n"
                "        self._data = []\n\n"
                "    def add(self, value):\n"
                "        pass\n\n"
                "    def remove(self, value):\n"
                "        pass\n\n"
                "    def contains(self, value):\n"
                "        pass\n\n"
                "    def index(self, value):\n"
                "        pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"op": "add_seq", "values": [3, 1, 4, 1, 5, 9, 2, 6]}, "expected": [1, 1, 2, 3, 4, 5, 6, 9]},
                    {"input": {"op": "contains", "values": [5], "target": 5}, "expected": True},
                    {"input": {"op": "contains_miss", "target": 99}, "expected": False},
                    {"input": {"op": "remove", "target": 5}, "expected": "removed"},
                    {"input": {"op": "remove_missing"}, "expected": "ValueError"},
                )},
                {"cases": tcs(
                    {"input": {"op": "add_large", "values": list(range(100, 0, -1))}, "expected": list(range(1, 101))},
                    {"input": {"op": "index", "values": [10, 20, 30], "target": 20}, "expected": 1},
                    {"input": {"op": "index_miss", "target": 99}, "expected": "ValueError"},
                    {"input": {"op": "duplicate_add", "values": [5, 5, 5]}, "expected": [5, 5, 5]},
                    {"input": {"op": "negative_values", "values": [-3, -1, -2]}, "expected": [-3, -2, -1]},
                )},
            ],
            "hints": [
                "💡 `bisect_left` O(log n) index bul",
                "💡 `insort` otomatik insert at correct position",
                "💡 `list.pop(idx)` ile remove",
            ],
            "explanation": (
                "SortedList: add → insort(data, value), remove → bisect_left + pop, "
                "contains → idx >= 0 and idx < len and data[idx]==value. "
                "Average O(n) insert ama sorted maintain eder, search O(log n)."
            ),
            "complexity": "O(log n) search, O(n) insert/remove",
            "concepts": ["bisect", "sorted-list", "search", "insertion"],
            "tags": ["performance", "bisect", "intermediate"],
        },
        {
            "title": "String Builder (io.StringIO)",
            "description": (
                "String concatenation O(n²) (her += yeni string oluşturur). "
                "`io.StringIO` ile O(n) string builder."
            ),
            "starter": (
                "import io\n\n"
                "class StringBuilder:\n"
                "    def __init__(self):\n"
                "        self._buf = io.StringIO()\n\n"
                "    def append(self, s):\n"
                "        pass\n\n"
                "    def build(self):\n"
                "        pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"op": "simple", "parts": ["a", "b", "c"]}, "expected": "abc"},
                    {"input": {"op": "empty"}, "expected": ""},
                    {"input": {"op": "large", "n": 10000}, "expected_len": 10000},
                    {"input": {"op": "with_separator", "parts": ["a", "b"], "sep": "-"}, "expected": "a-b"},
                    {"input": {"op": "reset_reuse"}, "expected": "fresh_each_time"},
                )},
                {"cases": tcs(
                    {"input": {"op": "append_int", "parts": [1, 2, 3]}, "expected": "123"},
                    {"input": {"op": "append_none"}, "expected": "None"},
                    {"input": {"op": "unicode", "parts": ["Türkçe", "ĞÜŞ"]}, "expected": "TürkçeĞÜŞ"},
                    {"input": {"op": "newlines", "parts": ["a", "b"]}, "expected_multiline": True},
                    {"input": {"op": "huge_concat", "n": 100000, "expected_len": 100000}, "expected_len": 100000},
                )},
            ],
            "hints": [
                "💡 `io.StringIO()` buffer oluştur",
                "💡 `buf.write(s)` append, `buf.getvalue()` build",
                "💡 String += her seferinde yeni string (O(n²))",
            ],
            "explanation": (
                "StringIO buffer'a append eder, O(1) per append. build() getvalue() "
                "ile tüm buffer'ı string olarak dön. Toplam O(n). Naive concatenation "
                "O(n²) çünkü her += yeni string."
            ),
            "complexity": "O(1) amortized per append, O(n) build",
            "concepts": ["string-builder", "io", "performance", "optimization"],
            "tags": ["performance", "string", "optimization"],
        },
    ],
}