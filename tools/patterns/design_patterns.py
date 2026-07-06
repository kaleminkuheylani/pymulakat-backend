"""Design pattern templates."""
from ._shared import tcs

PATTERN = {
    "level": "advanced",
    "templates": [
        {
            "title": "Repository Pattern (in-memory)",
            "description": (
                "Generic repository pattern: in-memory CRUD. find, find_by_id, save, "
                "delete. Type-safe with generics."
            ),
            "starter": (
                "from typing import Generic, TypeVar, Optional, List\n"
                "from dataclasses import dataclass\n\n"
                "T = TypeVar('T')\n\n"
                "class Repository(Generic[T]):\n"
                "    def __init__(self):\n"
                "        self._items = {}\n"
                "        self._next_id = 1\n\n"
                "    def find(self):\n"
                "        pass\n\n"
                "    def find_by_id(self, id):\n"
                "        pass\n\n"
                "    def save(self, item):\n"
                "        pass\n\n"
                "    def delete(self, id):\n"
                "        pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"op": "save_new"}, "expected": "id_assigned"},
                    {"input": {"op": "find_by_id_existing"}, "expected": "returns_item"},
                    {"input": {"op": "find_by_id_missing"}, "expected": "None"},
                    {"input": {"op": "save_update_existing"}, "expected": "no_new_id"},
                    {"input": {"op": "delete_missing"}, "expected": "False"},
                )},
                {"cases": tcs(
                    {"input": {"op": "find_empty"}, "expected": []},
                    {"input": {"op": "save_100"}, "expected_count": 100},
                    {"input": {"op": "delete_then_find"}, "expected": "not_found"},
                    {"input": {"op": "save_twice_same_id"}, "expected": "updated"},
                    {"input": {"op": "delete_existing"}, "expected": "True"},
                )},
            ],
            "hints": [
                "💡 dict[id, item] O(1) lookup",
                "💡 `item.id` attribute varsa kullan",
                "💡 Counter'ı repo içinde tut",
            ],
            "explanation": (
                "In-memory store: dict[id, item]. Save: eğer item.id varsa update, "
                "yoksa yeni id ata ve ekle. Find tüm item'ları liste olarak dön. "
                "Delete var ise sil ve True dön, yoksa False."
            ),
            "complexity": "O(1) get/delete, O(n) find",
            "concepts": ["design-pattern", "repository", "OOP", "type-safety", "CRUD"],
            "tags": ["design-pattern", "OOP", "advanced"],
        },
        {
            "title": "Observer Pattern (Event Emitter)",
            "description": (
                "Event emitter: subscribe(callback) → unsubscribe_token, emit(event) "
                "tüm subscriber'ları çağırır. Token ile unsubscribe."
            ),
            "starter": (
                "class EventEmitter:\n"
                "    def __init__(self):\n"
                "        pass\n\n"
                "    def subscribe(self, callback):\n"
                "        # token dön (unsubscribe için)\n"
                "        pass\n\n"
                "    def emit(self, event):\n"
                "        pass\n\n"
                "    def unsubscribe(self, token):\n"
                "        pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"op": "subscribe_emit", "n_subs": 1, "events": ["e1"]}, "expected": "called_once"},
                    {"input": {"op": "subscribe_emit", "n_subs": 0, "events": ["e1"]}, "expected": "no_call"},
                    {"input": {"op": "subscribe_emit", "n_subs": 100, "events": ["e"]}, "expected": "called_100_times"},
                    {"input": {"op": "unsubscribe", "n_subs": 3, "events": ["e"]}, "expected": "unsubscribed_not_called"},
                    {"input": {"op": "unsubscribe_invalid_token"}, "expected": "False"},
                )},
                {"cases": tcs(
                    {"input": {"op": "multi_emit", "n_subs": 2, "events": ["a", "b", "c"]}, "expected": "called_per_event"},
                    {"input": {"op": "subscribe_after_emit", "n_subs": 1, "events": ["e1", "subscribe", "e2"]}, "expected": "late_subscriber_no_first"},
                    {"input": {"op": "unsubscribe_one_keep_others", "n_subs": 3, "events": ["e"]}, "expected": "two_called"},
                    {"input": {"op": "callback_error_isolation", "n_subs": 2, "events": ["e"]}, "expected": "error_in_one_other_called"},
                    {"input": {"op": "token_uniqueness", "n_subs": 1000}, "expected": "all_unique"},
                )},
            ],
            "hints": [
                "💡 Token = uuid4 veya incremental id",
                "💡 Callback'leri dict[token, callback] tut",
                "💡 emit'te try/except ile bir callback hatası diğerlerini bloklamamalı",
            ],
            "explanation": (
                "EventEmitter: subscribe token döner, callback dict'te saklanır. "
                "emit'te tüm callback'leri çağır, try/except ile hata izolasyonu. "
                "unsubscribe token ile callback'i çıkarır."
            ),
            "complexity": "O(n) emit (n = subscribers), O(1) subscribe/unsubscribe",
            "concepts": ["observer", "event-emitter", "design-pattern", "callback"],
            "tags": ["design-pattern", "observer", "advanced"],
        },
        {
            "title": "Strategy Pattern with Callable",
            "description": (
                "Strategy pattern: algoritmayı runtime'da değiştir. callable ile "
                "sakla, swap et."
            ),
            "starter": (
                "class TextProcessor:\n"
                "    def __init__(self, strategy):\n"
                "        pass\n\n"
                "    def process(self, text):\n"
                "        pass\n\n"
                "    def set_strategy(self, strategy):\n"
                "        pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"strategy": "upper", "text": "hello"}, "expected": "HELLO"},
                    {"input": {"strategy": "lower", "text": "HELLO"}, "expected": "hello"},
                    {"input": {"strategy": "swap", "text": "Hello"}, "expected": "hELLO"},
                    {"input": {"strategy": "reverse", "text": "abc"}, "expected": "cba"},
                    {"input": {"strategy": "invalid", "text": "x"}, "expected": "ValueError"},
                )},
                {"cases": tcs(
                    {"input": {"strategy": "identity", "text": "test"}, "expected": "test"},
                    {"input": {"strategy": "upper", "text": ""}, "expected": ""},
                    {"input": {"strategy": "length", "text": "hello"}, "expected": 5},
                    {"input": {"strategy": "upper", "text": "Türkçe"}, "expected": "TÜRKÇE"},
                    {"input": {"strategy": "swap_after_set", "text": "AB"}, "expected": "ab"},
                )},
            ],
            "hints": [
                "💡 Strategy'yi self.strategy = strategy olarak sakla",
                "💡 process'te `return self.strategy(text)` çağır",
                "💡 Strategy'ler dışarıdan callable olarak inject edilir",
            ],
            "explanation": (
                "Strategy pattern callable ile: __init__ stratejiyi saklar, process "
                "onu çağırır. set_strategy ile runtime'da değiştir. Strategy'ler "
                "lambda, function, veya callable instance olabilir."
            ),
            "complexity": "O(1) swap, O(strategy_complexity) process",
            "concepts": ["strategy", "design-pattern", "callable", "DI"],
            "tags": ["design-pattern", "strategy"],
        },
    ],
}