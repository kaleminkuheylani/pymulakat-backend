"""OOP-Advanced patterns."""
from ._shared import tcs

PATTERN = {
    "level": "intermediate",
    "templates": [
        {
            "title": "Singleton via Metaclass",
            "description": (
                "App config (DB URL, API key) tek olmalı — birden fazla instance "
                "inconsistency yaratır. Metaclass ile Singleton: 2. kez instantiate "
                "edilirse aynı instance'ı dön."
            ),
            "starter": (
                "class Singleton(type):\n"
                "    _instances = {}\n\n"
                "    def __call__(cls, *args, **kwargs):\n"
                "        pass\n\n"
                "class AppConfig(metaclass=Singleton):\n"
                "    def __init__(self):\n"
                "        self.value = 42"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"op": "identity", "cls": "AppConfig"}, "expected": True},
                    {"input": {"op": "first_attr", "cls": "AppConfig"}, "expected": 42},
                    {"input": {"op": "mutate_persists", "cls": "AppConfig", "new_val": 100}, "expected": 100},
                    {"input": {"op": "args_ignored", "cls": "AppConfig"}, "expected": "single_instance"},
                    {"input": {"op": "reset_check", "cls": "AppConfig"}, "expected": "persists_across_calls"},
                )},
                {"cases": tcs(
                    {"input": {"op": "identity", "cls": "Database"}, "expected": True},
                    {"input": {"op": "first_attr", "cls": "Database"}, "expected": "default"},
                    {"input": {"op": "mutate_persists", "cls": "Database", "new_val": "new"}, "expected": "new"},
                    {"input": {"op": "args_ignored", "cls": "Database"}, "expected": "single_instance"},
                    {"input": {"op": "reset_check", "cls": "Database"}, "expected": "persists_across_calls"},
                )},
            ],
            "hints": [
                "💡 `metaclass.__call__` instance oluşturma hook'u",
                "💡 Class attribute'da instance cache tut (dict)",
                "💡 `if cls not in instances: instances[cls] = super().__call__(*args, **kwargs)`",
            ],
            "explanation": (
                "Metaclass.__call__ normalde cls.__new__ + cls.__init__ çağırır. Biz bunu "
                "intercept edip: cache'te varsa dön, yoksa oluştur ve cache'le. `_instances` "
                "metaclass'ta tutulur ki farklı Singleton sınıfları birbirini ezmesin. Test "
                "edilebilirlik zor olduğu için production'da dependency injection tercih "
                "edilir, Singleton genelde legacy pattern."
            ),
            "complexity": "O(1) per call (dict lookup)",
            "concepts": ["metaclass", "singleton", "OOP", "design-pattern", "instantiation"],
            "tags": ["oop", "metaclass", "design-pattern"],
        },
        {
            "title": "Descriptor with Validation",
            "description": (
                "ORM'de model field'ları tip validate etmeli. Descriptor yaz: atanan "
                "değer pozitif int olmalı, aksi halde ValueError (negatif) veya "
                "TypeError (int değil) fırlat."
            ),
            "starter": (
                "class PositiveInt:\n"
                "    def __set_name__(self, owner, name):\n"
                "        self.name = name\n"
                "        self.private = '_' + name\n\n"
                "    def __get__(self, obj, objtype=None):\n"
                "        pass\n\n"
                "    def __set__(self, obj, value):\n"
                "        pass\n\n"
                "class Product:\n"
                "    price = PositiveInt()\n"
                "    quantity = PositiveInt()"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"attr": "price", "value": 10, "expect": "ok"}, "expected": 10},
                    {"input": {"attr": "price", "value": 1, "expect": "ok"}, "expected": 1},
                    {"input": {"attr": "price", "value": 999999, "expect": "ok"}, "expected": 999999},
                    {"input": {"attr": "price", "value": -5, "expect": "error"}, "expected": "ValueError"},
                    {"input": {"attr": "price", "value": "abc", "expect": "error"}, "expected": "TypeError"},
                )},
                {"cases": tcs(
                    {"input": {"attr": "quantity", "value": 50, "expect": "ok"}, "expected": 50},
                    {"input": {"attr": "quantity", "value": 1, "expect": "ok"}, "expected": 1},
                    {"input": {"attr": "quantity", "value": 10000, "expect": "ok"}, "expected": 10000},
                    {"input": {"attr": "quantity", "value": 0, "expect": "error"}, "expected": "ValueError"},
                    {"input": {"attr": "quantity", "value": 3.14, "expect": "error"}, "expected": "TypeError"},
                )},
            ],
            "hints": [
                "💡 `__set_name__` descriptor adını otomatik alır (PEP 487)",
                "💡 `instance.__dict__[self.private]` private storage",
                "💡 `isinstance(value, int) and not isinstance(value, bool)` (bool is int!)",
            ],
            "explanation": (
                "Descriptor protocol: __get__ ve __set__. __set_name__ descriptor adını ve "
                "private storage key'ini otomatik alır. __set__'te tip ve değer validate et "
                "(bool is int, ayrı kontrol gerek), sonra `obj.__dict__[key] = value` ile "
                "depola. __get__'te dict'ten dön. Validation hatasında anlamlı exception "
                "(ValueError vs TypeError) fırlatmak iyi practice."
            ),
            "complexity": "O(1) per access",
            "concepts": ["descriptor", "OOP", "validation", "protocol", "PEP-487"],
            "tags": ["oop", "descriptor", "validation"],
        },
        {
            "title": "Cached Property with TTL",
            "description": (
                "Insider'da product recommendations cache'le, ama 5 dakikada bir "
                "tazele (user behavior değişiyor). `@cached_property` + TTL: ilk "
                "erişimde hesapla, TTL dolunca yeniden hesapla."
            ),
            "starter": (
                "import time\n\n"
                "def ttl_cached_property(ttl_seconds):\n"
                "    class TTLCachedProperty:\n"
                "        def __init__(self, func):\n"
                "            self.func = func\n"
                "            self.ttl = ttl_seconds\n"
                "            self.attr = '_' + func.__name__\n"
                "            self.ts_attr = '_' + func.__name__ + '_ts'\n\n"
                "        def __get__(self, obj, objtype=None):\n"
                "            if obj is None: return self\n"
                "            now = time.monotonic()\n"
                "            ts = getattr(obj, self.ts_attr, 0)\n"
                "            if (now - ts) < self.ttl:\n"
                "                return getattr(obj, self.attr)\n"
                "            value = self.func(obj)\n"
                "            setattr(obj, self.attr, value)\n"
                "            setattr(obj, self.ts_attr, now)\n"
                "            return value\n"
                "    return TTLCachedProperty"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"ttl": 1.0, "wait": 0.0, "n": 1}, "expected": "compute_called_once"},
                    {"input": {"ttl": 1.0, "wait": 0.0, "n": 5}, "expected": "compute_called_once"},
                    {"input": {"ttl": 0.05, "wait": 0.0, "n": 100}, "expected": "cached_within_ttl"},
                    {"input": {"ttl": 0.1, "wait": 0.5, "n": 1}, "expected": "recalculated"},
                    {"input": {"ttl": 0.0, "wait": 0.0, "n": 3}, "expected": "recalculated_every_time"},
                )},
                {"cases": tcs(
                    {"input": {"ttl": 10.0, "wait": 0.0, "n": 1}, "expected": "compute_called_once"},
                    {"input": {"ttl": 10.0, "wait": 0.0, "n": 10}, "expected": "compute_called_once"},
                    {"input": {"ttl": 0.2, "wait": 0.0, "n": 50}, "expected": "cached_within_ttl"},
                    {"input": {"ttl": 0.05, "wait": 1.0, "n": 1}, "expected": "recalculated"},
                    {"input": {"ttl": -1, "wait": 0.0, "n": 1}, "expected": "ValueError"},
                )},
            ],
            "hints": [
                "💡 `time.monotonic()` wall clock'tan bağımsız",
                "💡 Timestamp + value'yu ayrı instance attribute'larında sakla",
                "💡 TTL <= 0 durumunda her zaman yeniden hesapla",
            ],
            "explanation": (
                "Descriptor benzeri decorator: __init__'te func'ı al. __get__'te: "
                "instance'a bak, timestamp varsa ve (now - ts) < ttl ise cache'lenen "
                "value'yu dön. Yoksa func(obj) hesapla, hem value hem ts sakla. ttl <= 0 "
                "→ her zaman yeniden hesapla. Multi-thread ortamda threading.Lock "
                "eklemek gerekebilir."
            ),
            "complexity": "O(1) cached, O(compute) on miss",
            "concepts": ["decorator", "descriptor", "caching", "TTL", "memoization"],
            "tags": ["oop", "decorator", "caching", "TTL"],
        },
    ],
}