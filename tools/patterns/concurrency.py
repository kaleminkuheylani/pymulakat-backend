"""Concurrency patterns."""
from ._shared import tcs

PATTERN = {
    "level": "advanced",
    "templates": [
        {
            "title": "Async Batch Processor",
            "description": (
                "Trendyol scrape: 1000 ürünü eş zamanlı çek, rate limit 5 req/s. "
                "Verilen async `fetch(item)` için N öğeyi `max_concurrent` ile sınırlı "
                "işleyip sonuçları orijinal sırada dönen async fonksiyon yaz."
            ),
            "starter": (
                "import asyncio\nfrom typing import Callable, Awaitable, TypeVar, List\n\n"
                "T = TypeVar('T')\n\n"
                "async def batch_process(items, fetch, max_concurrent=5):\n"
                "    pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"items": [1, 2, 3], "max_concurrent": 2}, "expected": [1, 2, 3]},
                    {"input": {"items": [], "max_concurrent": 5}, "expected": []},
                    {"input": {"items": list(range(100)), "max_concurrent": 10}, "expected": list(range(100))},
                    {"input": {"items": ["x"], "max_concurrent": 1}, "expected": ["x"]},
                    {"input": {"items": [1, 2], "max_concurrent": 0}, "expected": "ValueError"},
                )},
                {"cases": tcs(
                    {"input": {"items": list(range(50)), "max_concurrent": 5}, "expected": list(range(50))},
                    {"input": {"items": ["a", "b"], "max_concurrent": 100}, "expected": ["a", "b"]},
                    {"input": {"items": list(range(1000)), "max_concurrent": 50}, "expected": list(range(1000))},
                    {"input": {"items": [42], "max_concurrent": 1}, "expected": [42]},
                    {"input": {"items": list(range(10)), "max_concurrent": -1}, "expected": "ValueError"},
                )},
                {"cases": tcs(
                    {"input": {"items": ["TY001", "TY002"], "max_concurrent": 2}, "expected": ["TY001", "TY002"]},
                    {"input": {"items": [], "max_concurrent": 3}, "expected": []},
                    {"input": {"items": [f"TY{i:04d}" for i in range(100)], "max_concurrent": 10}, "expected": [f"TY{i:04d}" for i in range(100)]},
                    {"input": {"items": ["single"], "max_concurrent": 1}, "expected": ["single"]},
                    {"input": {"items": ["a", "b"], "max_concurrent": 0}, "expected": "ValueError"},
                )},
            ],
            "hints": [
                "💡 `asyncio.Semaphore(max_concurrent)` ile sınırla",
                "💡 Sırayı korumak için enumerate ile index ata",
                "💡 `asyncio.gather(*tasks)` paralel çalıştırır ve sırayı korur",
            ],
            "explanation": (
                "asyncio.Semaphore ile semaphore counter tut. Her fetch öncesi "
                "`async with sem:`, sonra release (with bloğu otomatik). Sırayı korumak "
                "için enumerate ile index ata, sonuçları `results[idx] = value` ile "
                "yerleştir. gather paralel çalıştırır ve sırayı korur. max_concurrent <= 0 "
                "durumunda ValueError fırlatmak defensive programming gereği."
            ),
            "complexity": "O(n/c) wall time (c=max_concurrent), O(n) memory",
            "concepts": ["asyncio", "semaphore", "concurrency", "async-await", "rate-limiting"],
            "tags": ["async", "concurrency", "advanced", "rate-limit"],
        },
        {
            "title": "Thread-safe Rate Limiter",
            "description": (
                "Paraşüt API'sinde fatura gönderirken saniyede max 3 istek izni var. "
                "Thread-safe rate limiter: `acquire()` izin varsa True, yoksa False. "
                "`max_calls` per `period_seconds` periyodunda izin ver."
            ),
            "starter": (
                "import threading\nimport time\nfrom collections import deque\n\n"
                "class RateLimiter:\n"
                "    def __init__(self, max_calls, period_seconds=1.0):\n"
                "        pass\n\n"
                "    def acquire(self):\n"
                "        pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"max_calls": 2, "period": 1.0, "n": 3}, "expected": [True, True, False]},
                    {"input": {"max_calls": 5, "period": 1.0, "n": 1}, "expected": [True]},
                    {"input": {"max_calls": 100, "period": 1.0, "n": 50}, "expected": [True] * 50},
                    {"input": {"max_calls": 1, "period": 1.0, "n": 5}, "expected": [True, False, False, False, False]},
                    {"input": {"max_calls": 0, "period": 1.0}, "expected": "ValueError"},
                )},
                {"cases": tcs(
                    {"input": {"max_calls": 3, "period": 2.0, "n": 4}, "expected": [True, True, True, False]},
                    {"input": {"max_calls": 1, "period": 0.1, "n": 1}, "expected": [True]},
                    {"input": {"max_calls": 1000, "period": 1.0, "n": 500}, "expected": [True] * 500},
                    {"input": {"max_calls": 10, "period": 1.0, "n": 12}, "expected": [True]*10 + [False]*2},
                    {"input": {"max_calls": -1, "period": 1.0}, "expected": "ValueError"},
                )},
            ],
            "hints": [
                "💡 `threading.Lock` ile kritik bölümü koru",
                "💡 Çağrı zamanlarını `deque(maxlen=max_calls)` tut",
                "💡 `time.monotonic()` threading için güvenli",
            ],
            "explanation": (
                "Lock altında: eski (period'dan eski) zamanları deque'dan çıkar. Eğer "
                "len(deque) < max_calls ise `now` ekle ve True dön; yoksa False. "
                "deque(maxlen=max_calls) otomatik eviction sağlar. time.monotonic() "
                "sistem saatinden etkilenmez. max_calls <= 0 ise __init__'te ValueError."
            ),
            "complexity": "O(c) per acquire (c=max_calls), O(c) memory",
            "concepts": ["threading", "lock", "rate-limiting", "deque", "monotonic-clock"],
            "tags": ["threading", "concurrency", "rate-limit"],
        },
        {
            "title": "GIL-Aware CPU-Bound Worker Pool",
            "description": (
                "Sahibinden'de 100K ilan için feature extraction (image hash + NLP) "
                "yapıyorsun, CPU-bound. Threading GIL'de bloke olur. "
                "`multiprocessing.Pool` ile paralel map, sonuçları sırayla topla."
            ),
            "starter": (
                "import multiprocessing\nfrom typing import Callable, List, TypeVar\n\n"
                "T = TypeVar('T')\n\n"
                "def parallel_map(fn, items, workers=4):\n"
                "    pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"items": [1, 2, 3, 4], "workers": 2}, "expected": [2, 4, 6, 8]},
                    {"input": {"items": [], "workers": 4}, "expected": []},
                    {"input": {"items": list(range(100)), "workers": 8}, "expected": [x*2 for x in range(100)]},
                    {"input": {"items": [42], "workers": 1}, "expected": [84]},
                    {"input": {"items": [1, 2], "workers": 0}, "expected": "ValueError"},
                )},
                {"cases": tcs(
                    {"input": {"items": [0, 5, 10], "workers": 2}, "expected": [0, 10, 20]},
                    {"input": {"items": [1], "workers": 1}, "expected": [2]},
                    {"input": {"items": list(range(500)), "workers": 4}, "expected": [x*2 for x in range(500)]},
                    {"input": {"items": [-1, 0, 1], "workers": 2}, "expected": [-2, 0, 2]},
                    {"input": {"items": [1], "workers": -1}, "expected": "ValueError"},
                )},
            ],
            "hints": [
                "💡 `multiprocessing.Pool(processes=workers)` pool oluştur",
                "💡 `pool.map(fn, items)` sırayı korur",
                "💡 `with` statement pool'u otomatik kapatır",
            ],
            "explanation": (
                "GIL CPU-bound task'ları kısıtladığı için threading değil multiprocessing "
                "gerekli (her process ayrı Python interpreter). Pool(processes=n) ile "
                "n worker oluştur, pool.map(fn, items) sırayı koruyarak paralel çalıştırır. "
                "with statement ile pool'u otomatik kapat. workers <= 0 → ValueError."
            ),
            "complexity": "O(n/w) wall time (w=workers), O(n) memory",
            "concepts": ["multiprocessing", "GIL", "cpu-bound", "parallelism", "pool"],
            "tags": ["multiprocessing", "concurrency", "GIL"],
        },
    ],
}