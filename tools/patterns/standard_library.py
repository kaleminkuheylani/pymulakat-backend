"""Standard library patterns."""
from ._shared import tcs

PATTERN = {
    "level": "intermediate",
    "templates": [
        {
            "title": "Group By with itertools",
            "description": (
                "Verilen iterable'ı key fonksiyonuna göre grupla, dict[Key, list] "
                "dön. itertools.groupby kullan (sorted input gerekir)."
            ),
            "starter": (
                "from itertools import groupby\n\n"
                "def group_by(items, key_fn):\n"
                "    pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"data": [1, 2, 3, 4, 5, 6], "key": "parity"}, "expected": {"odd": [1, 3, 5], "even": [2, 4, 6]}},
                    {"input": {"data": [], "key": "id"}, "expected": {}},
                    {"input": {"data": list(range(100)), "key": "mod10"}, "expected": {str(i): list(range(i, 100, 10)) for i in range(10)}},
                    {"input": {"data": ["apple", "banana", "cherry"], "key": "first_letter"}, "expected": {"a": ["apple"], "b": ["banana"], "c": ["cherry"]}},
                    {"input": {"data": [1, 1, 1], "key": "identity"}, "expected": {1: [1, 1, 1]}},
                )},
                {"cases": tcs(
                    {"input": {"data": ["a", "bb", "ccc", "dd", "e"], "key": "length"}, "expected": {1: ["a", "e"], 2: ["bb", "dd"], 3: ["ccc"]}},
                    {"input": {"data": [True, False, True], "key": "identity"}, "expected": {True: [True, True], False: [False]}},
                    {"input": {"data": [(1, "a"), (1, "b"), (2, "c")], "key": "first"}, "expected": {1: [(1, "a"), (1, "b")], 2: [(2, "c")]}},
                    {"input": {"data": [1.1, 2.2, 1.1], "key": "int_part"}, "expected": {1: [1.1, 1.1], 2: [2.2]}},
                    {"input": {"data": [], "key": "any"}, "expected": {}},
                )},
            ],
            "hints": [
                "💡 `groupby` sıralı input gerektirir",
                "💡 `sorted(items, key=key_fn)` önce sırala",
                "💡 `dict[key].append(value)` accumulator",
            ],
            "explanation": (
                "groupby ardışık eşit key'leri gruplar. Önce sırala, sonra groupby "
                "uygula. Her grup için accumulator dict'e append. defaultdict(list) "
                "ile daha temiz: `d[key].append(value)`."
            ),
            "complexity": "O(n log n) time (sort), O(n) space",
            "concepts": ["itertools", "groupby", "sorting", "stdlib"],
            "tags": ["stdlib", "itertools", "intermediate"],
        },
        {
            "title": "LRU Cache (OrderedDict)",
            "description": (
                "`functools.lru_cache` ama manuel OrderedDict ile implement et. "
                "Capacity dolunca en az kullanılanı çıkar."
            ),
            "starter": (
                "from collections import OrderedDict\n\n"
                "class LRUCache:\n"
                "    def __init__(self, capacity):\n"
                "        pass\n\n"
                "    def get(self, key):\n"
                "        # -1 if not found\n"
                "        pass\n\n"
                "    def put(self, key, value):\n"
                "        # Capacity aşılırsa LRU çıkar\n"
                "        pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"op": "put_get", "cap": 2, "key": 1, "val": 1}, "expected": 1},
                    {"input": {"op": "get_miss", "cap": 2, "key": 99}, "expected": -1},
                    {"input": {"op": "evict", "cap": 2, "ops": [("put",1,1),("put",2,2),("get",1),("put",3,3),("get",2)]}, "expected": -1},
                    {"input": {"op": "update", "cap": 2, "ops": [("put",1,1),("put",1,2),("get",1)]}, "expected": 2},
                    {"input": {"op": "zero_cap", "cap": 0, "ops": [("put",1,1),("get",1)]}, "expected": "ValueError_or_-1"},
                )},
                {"cases": tcs(
                    {"input": {"op": "put_get", "cap": 3, "key": 5, "val": 50}, "expected": 50},
                    {"input": {"op": "evict_lru", "cap": 3, "ops": [("put",1,1),("put",2,2),("put",3,3),("get",1),("put",4,4),("get",2)]}, "expected": -1},
                    {"input": {"op": "recent_promoted", "cap": 2, "ops": [("put",1,1),("put",2,2),("get",1),("put",3,3),("get",2)]}, "expected": -1},
                    {"input": {"op": "evict_oldest", "cap": 1, "ops": [("put",1,1),("put",2,2),("get",1)]}, "expected": -1},
                    {"input": {"op": "negative_cap", "cap": -1}, "expected": "ValueError"},
                )},
            ],
            "hints": [
                "💡 OrderedDict.move_to_end() recent access işaretler",
                "💡 `popitem(last=False)` ilk elemanı çıkarır (LRU)",
                "💡 get'te key varsa move_to_end + return value",
            ],
            "explanation": (
                "OrderedDict sırayı korur. get'te: key varsa move_to_end + return "
                "value; yoksa -1. put'ta: key varsa update + move_to_end; yoksa ekle. "
                "len > capacity ise popitem(last=False) ile LRU çıkar. capacity <= 0 "
                "ise ValueError."
            ),
            "complexity": "O(1) amortized per op",
            "concepts": ["OrderedDict", "LRU", "cache", "design"],
            "tags": ["stdlib", "design", "intermediate"],
        },
        {
            "title": "CSV to Dict with csv Module",
            "description": (
                "CSV string'ini oku, her satırı dict olarak dön. İlk satır header. "
                "Tip-safe conversion (int, float, bool auto-detect)."
            ),
            "starter": (
                "import csv\nfrom io import StringIO\n\n"
                "def csv_to_dicts(csv_string):\n"
                "    pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"csv": "name,age,active\\nAli,30,true\\nAyşe,25,false"}, "expected": [{"name": "Ali", "age": 30, "active": True}, {"name": "Ayşe", "age": 25, "active": False}]},
                    {"input": {"csv": "x,y\\n1,2"}, "expected": [{"x": 1, "y": 2}]},
                    {"input": {"csv": "a,b,c\\n" + "\\n".join([f"{i},{i*2},{i*3}" for i in range(100)])}, "expected_count": 100},
                    {"input": {"csv": "k\\nval"}, "expected": [{"k": "val"}]},
                    {"input": {"csv": ""}, "expected": "ValueError"},
                )},
                {"cases": tcs(
                    {"input": {"csv": "id,price\\n1,9.99\\n2,19.99"}, "expected": [{"id": 1, "price": 9.99}, {"id": 2, "price": 19.99}]},
                    {"input": {"csv": "name\\nali\\nveli"}, "expected": [{"name": "ali"}, {"name": "veli"}]},
                    {"input": {"csv": "a,b\\n" + ",".join(["x"]*500)}, "expected_count": 1},
                    {"input": {"csv": "k1,k2\\n,empty"}, "expected": [{"k1": "", "k2": "empty"}]},
                    {"input": {"csv": "a\\nb"}, "expected": [{"a": "b"}]},
                )},
            ],
            "hints": [
                "💡 `csv.DictReader` ile otomatik header parse",
                "💡 `StringIO` ile string'i file gibi oku",
                "💡 Tip conversion: try int → float → bool → str",
            ],
            "explanation": (
                "csv.DictReader(StringIO(csv_string)) her satırı OrderedDict olarak "
                "döner (DictReader default). Tip conversion: value.isdigit() → int, "
                "replace('.','',1).isdigit() → float, value.lower() in true/false → "
                "bool, yoksa str."
            ),
            "complexity": "O(n) time, O(n) space",
            "concepts": ["csv", "stdlib", "parsing", "type-conversion"],
            "tags": ["stdlib", "csv", "parsing"],
        },
    ],
}