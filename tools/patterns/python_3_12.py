"""Python 3.10+ modern features patterns."""
from ._shared import tcs

PATTERN = {
    "level": "intermediate",
    "templates": [
        {
            "title": "Pattern Matching (match/case)",
            "description": (
                "Verilen HTTP response objesini pattern matching ile parse et. "
                "Status code'a göre farklı field'lar dön."
            ),
            "starter": (
                "def parse_response(response):\n"
                "    match response:\n"
                "        # case patterns\n"
                "        pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"response": {"status": 200, "data": {"id": 1}}}, "expected": "ok"},
                    {"input": {"response": {"status": 404}}, "expected": "not_found"},
                    {"input": {"response": {"status": 500, "error": "boom"}}, "expected": "server_error"},
                    {"input": {"response": {"status": 204}}, "expected": "no_content"},
                    {"input": {"response": {"status": 999}}, "expected": "unknown"},
                )},
                {"cases": tcs(
                    {"input": {"response": {"status": 200, "data": {"x": 1}}}, "expected": "ok"},
                    {"input": {"response": {"status": 201, "data": {"created": True}}}, "expected": "created"},
                    {"input": {"response": {"status": 400}}, "expected": "bad_request"},
                    {"input": {"response": {"status": 401, "error": "auth"}}, "expected": "unauthorized"},
                    {"input": {"response": None}, "expected": "invalid"},
                )},
            ],
            "hints": [
                "💡 match obj: case pattern if condition:",
                "💡 `{...}` rest pattern (tüm key'ler)",
                "💡 `|` OR pattern: `case 200 | 201 | 204:`",
            ],
            "explanation": (
                "match/case yapısal pattern matching sağlar (Python 3.10+). Dict "
                "pattern'leri: `case {\"status\": 200, \"data\": data}:`. OR, capture, "
                "rest pattern hepsi desteklenir. Default case `_:` ile."
            ),
            "complexity": "O(1) per match",
            "concepts": ["match-case", "pattern-matching", "python-3-10"],
            "tags": ["python-3-10", "modern-python", "intermediate"],
        },
        {
            "title": "Exception Groups (Python 3.11+)",
            "description": (
                "Verilen task listesi paralel çalıştır, hataları `ExceptionGroup` "
                "olarak topla. Tüm başarılar ve tüm hataları dön."
            ),
            "starter": (
                "def run_with_exceptions(tasks):\n"
                "    # Tüm task'leri çalıştır, hataları grupla\n"
                "    pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"tasks": ["a", "b", "c"]}, "expected": "(results, None)"},
                    {"input": {"tasks": []}, "expected": "([], None)"},
                    {"input": {"tasks": ["ok", "raise"]}, "expected": "group_with_errors"},
                    {"input": {"tasks": ["raise1", "raise2"]}, "expected": "group_with_multiple_errors"},
                    {"input": {"tasks": ["all_raise"]}, "expected": "group_only_errors"},
                )},
                {"cases": tcs(
                    {"input": {"tasks": ["x"], "mode": "fail_fast"}, "expected": "first_error"},
                    {"input": {"tasks": ["ok"], "mode": "fail_fast"}, "expected": "ok"},
                    {"input": {"tasks": ["raise"], "except": "ValueError"}, "expected": "handled"},
                    {"input": {"tasks": ["raise"], "except": "KeyError"}, "expected": "unhandled"},
                    {"input": {"tasks": list(range(100)), "mode": "all"}, "expected_count": 100},
                )},
            ],
            "hints": [
                "💡 `BaseExceptionGroup` Python 3.11+",
                "💡 `except*` sadece belirli exception'ları yakalar",
                "💡 `raise ExceptionGroup(...)` ile fırlat",
            ],
            "explanation": (
                "ExceptionGroup birden fazla exception'ı taşır. except* ile gruptan "
                "belirli tipleri seç. Task'leri çalıştır, başarılar liste, hatalar "
                "group. BaseExceptionGroup tüm exception'ları, ExceptionGroup sadece "
                "Exception subclasses'ları içerir."
            ),
            "complexity": "O(n) task execution",
            "concepts": ["exception-group", "python-3-11", "error-handling"],
            "tags": ["python-3-11", "modern-python", "advanced"],
        },
        {
            "title": "Type Hints: Self & ParamSpec",
            "description": (
                "Decorator factory için ParamSpec kullan: decorated fonksiyonun "
                "signature'ını koru. Self için typing.Self."
            ),
            "starter": (
                "from typing import Callable, ParamSpec, TypeVar, Self\n"
                "from functools import wraps\n"
                "import time\n\n"
                "P = ParamSpec('P')\n"
                "R = TypeVar('R')\n\n"
                "def timing(fn: Callable[P, R]) -> Callable[P, R]:\n"
                "    # ParamSpec: orijinal signature'ı koru\n"
                "    pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"fn": "add", "args": [1, 2]}, "expected": 3},
                    {"input": {"fn": "greet", "args": ["Ali"]}, "expected": "Hello, Ali"},
                    {"input": {"fn": "no_args"}, "expected": None},
                    {"input": {"fn": "kwargs", "kwargs": {"x": 1}}, "expected": "ok"},
                    {"input": {"fn": "raises"}, "expected": "propagates"},
                )},
                {"cases": tcs(
                    {"input": {"fn": "sleep_add", "args": [1, 2], "sleep": 0.01}, "expected": 3},
                    {"input": {"fn": "string_op", "args": ["abc"]}, "expected": "ABC"},
                    {"input": {"fn": "list_op", "args": [[1, 2, 3]]}, "expected": [2, 4, 6]},
                    {"input": {"fn": "mixed", "args": [1], "kwargs": {"y": 2}}, "expected": 3},
                    {"input": {"fn": "returns_none"}, "expected": None},
                )},
            ],
            "hints": [
                "💡 `ParamSpec('P')` callable signature capture",
                "💡 `@wraps(fn)` metadata kopyala",
                "💡 `typing.Self` class'ın kendisini type olarak",
            ],
            "explanation": (
                "ParamSpec decorator'da orijinal signature'ı korur (type checker "
                "için). @wraps metadata (docstring, name) kopyalar. Self class "
                "method return type için. timing decorator fonksiyonu sarar, "
                "süre ölçer, döner."
            ),
            "complexity": "O(fn complexity)",
            "concepts": ["type-hints", "paramspec", "typing", "self"],
            "tags": ["python-3-10", "type-hints", "advanced"],
        },
    ],
}