"""Real-world patterns (Türk şirketleri context)."""
from ._shared import tcs

PATTERN = {
    "level": "intermediate",
    "templates": [
        {
            "title": "Trendyol Sliding Window Recommendation",
            "description": (
                "Trendyol'da bir kullanıcının son N dakikada gezdiği kategorilerden "
                "en sık görülen K tanesini bul (sliding window). "
                "Output: [(category, count), ...] count azalan sırada."
            ),
            "starter": (
                "from collections import Counter\n"
                "from datetime import datetime, timedelta\n\n"
                "def trending_categories(events, window_minutes, top_k):\n"
                "    # events: [(timestamp_iso, category), ...]\n"
                "    pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"events": [("2026-01-01T10:00:00", "elektronik"), ("2026-01-01T10:05:00", "elektronik"), ("2026-01-01T10:30:00", "moda")], "window_minutes": 30, "top_k": 2}, "expected": [("elektronik", 2), ("moda", 1)]},
                    {"input": {"events": [], "window_minutes": 30, "top_k": 5}, "expected": []},
                    {"input": {"events": [(f"2026-01-01T10:{i:02d}:00", f"cat_{i%5}") for i in range(60)], "window_minutes": 60, "top_k": 3}, "expected_count": 3},
                    {"input": {"events": [("2026-01-01T10:00:00", "x")], "window_minutes": 1, "top_k": 1}, "expected": [("x", 1)]},
                    {"input": {"events": [("invalid", "x")], "window_minutes": 30}, "expected": "ValueError"},
                )},
                {"cases": tcs(
                    {"input": {"events": [("2026-01-01T10:00:00", "a"), ("2026-01-01T10:01:00", "b"), ("2026-01-01T10:02:00", "a")], "window_minutes": 5, "top_k": 1}, "expected": [("a", 2)]},
                    {"input": {"events": [("2026-01-01T10:00:00", "x"), ("2026-01-01T11:00:00", "x")], "window_minutes": 30, "top_k": 1}, "expected": [("x", 1)]},
                    {"input": {"events": [(f"2026-01-01T10:00:{i:02d}", "fast") for i in range(60)], "window_minutes": 1, "top_k": 5}, "expected": [("fast", 60)]},
                    {"input": {"events": [("2026-01-01T10:00:00", "")], "window_minutes": 1, "top_k": 1}, "expected": [("", 1)]},
                    {"input": {"events": [("2026-13-01T10:00:00", "x")], "window_minutes": 30}, "expected": "ValueError"},
                )},
            ],
            "hints": [
                "💡 `datetime.fromisoformat` parse",
                "💡 `datetime.now() - timedelta(minutes=N)` cutoff",
                "💡 `Counter.most_common(k)` top-k",
            ],
            "explanation": (
                "Datetime parse, cutoff'tan yenileri filtrele, Counter ile sayım, "
                "most_common(k) ile top-k. Sıralama otomatik count azalan. "
                "Invalid timestamp → ValueError."
            ),
            "complexity": "O(n log n) time, O(n) space",
            "concepts": ["datetime", "Counter", "sliding-window", "real-world"],
            "tags": ["real-world", "data-processing", "trendyol"],
        },
        {
            "title": "TC Kimlik No Doğrulama",
            "description": (
                "T.C. kimlik numarası 11 haneli, son 2 hane algoritma doğrulamalı. "
                "Verilen string geçerli mi?"
            ),
            "starter": (
                "def validate_tc_kimlik(tc):\n"
                "    # 11 haneli, son 2 hane algoritma\n"
                "    pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"tc": "10000000146"}, "expected": True},
                    {"input": {"tc": "12345678901"}, "expected": False},
                    {"input": {"tc": "00000000000"}, "expected": False},  # 1. hane 0 olamaz
                    {"input": {"tc": "11111111110"}, "expected": True},  # valid example
                    {"input": {"tc": "abc"}, "expected": "ValueError_or_False"},
                )},
                {"cases": tcs(
                    {"input": {"tc": "1234567890"}, "expected": False},  # 10 hane
                    {"input": {"tc": "123456789012"}, "expected": False},  # 12 hane
                    {"input": {"tc": "12345abc789"}, "expected": "ValueError_or_False"},
                    {"input": {"tc": "10000000146"}, "expected": True},  # canonical valid
                    {"input": {"tc": "99999999999"}, "expected": False},  # invalid checksum
                )},
            ],
            "hints": [
                "💡 1. hane 0 olamaz",
                "💡 10. hane = (1,3,5,7,9 toplam * 7 - 2,4,6,8 toplam) mod 10",
                "💡 11. hane = ilk 10 hane toplamı mod 10",
            ],
            "explanation": (
                "T.C. kimlik no algoritması: 1. hane 0 olmamalı, 10. ve 11. hane "
                "matematiksel olarak hesaplanır. Bu iki kural + 11 hane uzunluk = "
                "validation. 11 hane değilse veya int değilse False (veya ValueError)."
            ),
            "complexity": "O(1) — sabit 11 hane",
            "concepts": ["validation", "algorithm", "turkish"],
            "tags": ["real-world", "turkish", "validation"],
        },
        {
            "title": "İBAN Doğrulama (TR)",
            "description": (
                "Türkiye IBAN'ı: TR + 2 check digit + 5 bank code + 1 reserve + "
                "16 account. Toplam 26 karakter. MOD-97-10 algoritması ile doğrula."
            ),
            "starter": (
                "def validate_iban_tr(iban):\n"
                "    # TR + 24 digits = 26 char\n"
                "    # MOD-97-10: ilk 4'ü sona taşı, mod 97 = 1 ise geçerli\n"
                "    pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"iban": "TR330006100519786457841326"}, "expected": True},
                    {"input": {"iban": "TR000000000000000000000000"}, "expected": False},  # invalid checksum
                    {"input": {"iban": "TR12"}, "expected": False},  # too short
                    {"input": {"iban": "DE89370400440532013000"}, "expected": False},  # not TR
                    {"input": {"iban": "TR33000610051978645784132"}, "expected": False},  # 25 chars
                )},
                {"cases": tcs(
                    {"input": {"iban": "TR330006100519786457841326"}, "expected": True},
                    {"input": {"iban": "tr330006100519786457841326"}, "expected": False},  # lowercase
                    {"input": {"iban": "TR 3300 0610 0519 7864 5784 1326"}, "expected": "ValueError"},  # spaces
                    {"input": {"iban": ""}, "expected": False},
                    {"input": {"iban": "TR330006100519786457841327"}, "expected": False},  # last digit wrong
                )},
            ],
            "hints": [
                "💡 TR prefix zorunlu",
                "💡 26 karakter (TR + 24 rakam)",
                "💡 MOD-97-10: ilk 4'ü sona taşı, kalan string'i int yap, mod 97",
            ],
            "explanation": (
                "IBAN doğrulama: TR prefix + 24 rakam = 26 karakter. MOD-97-10 "
                "algoritması: ilk 4 karakteri sona taşı, kalan string'i int'e çevir, "
                "mod 97 = 1 ise geçerli. Boşluk ve lowercase handle et (strip + "
                "upper)."
            ),
            "complexity": "O(1) — sabit 26 karakter",
            "concepts": ["iban", "validation", "mod-97", "real-world"],
            "tags": ["real-world", "validation", "iban"],
        },
    ],
}