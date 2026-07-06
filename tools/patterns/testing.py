"""Testing patterns."""
from ._shared import tcs

PATTERN = {
    "level": "intermediate",
    "templates": [
        {
            "title": "Pytest Parametrize Pattern",
            "description": (
                "Bir fonksiyon icin pytest parametrized test yaz. Her test case icin "
                "aciklayici ID'ler koy (smallest_prime, even_composite gibi)."
            ),
            "starter": (
                "import pytest\n"
                "\n"
                "def is_prime(n):\n"
                "    if n < 2:\n"
                "        return False\n"
                "    for i in range(2, int(n ** 0.5) + 1):\n"
                "        if n % i == 0:\n"
                "            return False\n"
                "    return True\n"
                "\n"
                "@pytest.mark.parametrize('n,expected,case_id', [\n"
                "    # Buraya test case'ler\n"
                "])\n"
                "def test_is_prime(n, expected, case_id):\n"
                "    assert is_prime(n) == expected\n"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"cases": [[2, True, "smallest_prime"], [4, False, "even_composite"], [17, True, "prime_teen"], [1, False, "below_two"], [0, False, "zero_edge"]]}, "expected": "all_pass"},
                    {"input": {"cases": [[9, False, "perfect_square"]]}, "expected": "passes"},
                    {"input": {"cases": [[7, True, "single_digit_prime"], [11, True, "eleven"], [13, True, "thirteen"]]}, "expected": "all_pass"},
                    {"input": {"cases": [[25, False, "perfect_square_5"], [49, False, "perfect_square_7"]]}, "expected": "passes"},
                    {"input": {"cases": [[-5, False, "negative"]]}, "expected": "passes"},
                )},
                {"cases": tcs(
                    {"input": {"cases": [[97, True, "large_prime"], [100, False, "large_composite"]]}, "expected": "passes"},
                    {"input": {"cases": [[2, True, "two"], [3, True, "three"], [5, True, "five"]]}, "expected": "all_pass"},
                    {"input": {"cases": [[1000003, True, "million_prime"]]}, "expected": "passes"},
                    {"input": {"cases": [[6, False, "six_composite"]]}, "expected": "passes"},
                    {"input": {"cases": [[1, False, "unity"], [2, True, "two_again"]]}, "expected": "all_pass"},
                )},
            ],
            "hints": [
                "Parametrize ile ayni testi farkli inputlarla calistir",
                "Her test case icin anlamli case_id",
                "Edge cases (0, 1, 2, max) sarti",
            ],
            "explanation": (
                "Parametrize ile ayni testi farkli inputlarla calistir. case_id test "
                "output'unu readable yapar. Edge case'ler (0, 1, 2, max) mutlaka "
                "dahil et. pytest.mark.parametrize ids parametresi ile daha okunabilir "
                "cikti uretilir."
            ),
            "complexity": "O(sqrt(n)) per test case",
            "concepts": ["pytest", "parametrize", "testing", "TDD", "edge-case"],
            "tags": ["testing", "pytest", "intermediate"],
        },
        {
            "title": "Mock External API with unittest.mock",
            "description": (
                "External API cagrisini mock'la, side effect yok. monkeypatch (pytest) "
                "veya unittest.mock.patch kullan."
            ),
            "starter": (
                "import requests\n"
                "\n"
                "def fetch_user_profile(user_id):\n"
                "    resp = requests.get(f'https://api.example.com/users/{user_id}')\n"
                "    return resp.json()\n"
                "\n"
                "def test_fetch_user_profile(monkeypatch):\n"
                "    pass\n"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"user_id": 1}, "expected": {"id": 1, "name": "mocked"}},
                    {"input": {"user_id": 999}, "expected": {"id": 999, "name": "not_found"}},
                    {"input": {"user_id": 500}, "expected": "server_error"},
                    {"input": {"user_id": 0}, "expected": "ValueError"},
                    {"input": {"api_unavailable": True}, "expected": "raises"},
                )},
                {"cases": tcs(
                    {"input": {"user_id": 42, "expected": {"id": 42, "name": "Ali"}}, "expected": "ok"},
                    {"input": {"user_id": -1}, "expected": "ValueError"},
                    {"input": {"user_id": 1000, "timeout": True}, "expected": "timeout"},
                    {"input": {"user_id": 1001, "rate_limited": True}, "expected": "rate_limit"},
                    {"input": {"user_id": "abc"}, "expected": "TypeError"},
                )},
            ],
            "hints": [
                "monkeypatch.setattr(requests, 'get', mock_fn)",
                "Mock return value: lambda *a, **kw: MockResponse(...)",
                "Side effect icin mock.side_effect = [...]",
            ],
            "explanation": (
                "pytest fixture monkeypatch ile requests.get'i mock'la. Mock "
                "function MockResponse objesi dondurur (status_code, json vb.). "
                "side_effect ile exception firlatilabilir (timeout, rate_limit). "
                "Test izole ve hizli olur."
            ),
            "complexity": "O(1) per test",
            "concepts": ["mock", "pytest", "monkeypatch", "external-dependency"],
            "tags": ["testing", "mock", "intermediate"],
        },
        {
            "title": "Coverage-Driven Test Suite",
            "description": (
                "Bir fonksiyonun tum branch'lerini kapsayan test suite yaz. "
                "if/else, for, while, exception handling dahil."
            ),
            "starter": (
                "def process_data(data, mode='strict'):\n"
                "    if not data:\n"
                "        return []\n"
                "    result = []\n"
                "    for item in data:\n"
                "        try:\n"
                "            if mode == 'strict':\n"
                "                if not isinstance(item, int):\n"
                "                    raise ValueError\n"
                "            result.append(item * 2)\n"
                "        except (ValueError, TypeError):\n"
                "            if mode == 'strict':\n"
                "                raise\n"
                "            result.append(None)\n"
                "    return result\n"
                "\n"
                "def test_process_data_all_branches():\n"
                "    pass\n"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"data": [1, 2, 3], "mode": "strict"}, "expected": [2, 4, 6]},
                    {"input": {"data": [], "mode": "strict"}, "expected": []},
                    {"input": {"data": [1, 'x', 3], "mode": "lenient"}, "expected": [2, None, 6]},
                    {"input": {"data": [1, 'x'], "mode": "strict"}, "expected": "raises_ValueError"},
                    {"input": {"data": [1, None, 3], "mode": "lenient"}, "expected": [2, None, 6]},
                )},
                {"cases": tcs(
                    {"input": {"data": [0, 0, 0], "mode": "strict"}, "expected": [0, 0, 0]},
                    {"input": {"data": [-1, -2], "mode": "strict"}, "expected": [-2, -4]},
                    {"input": {"data": list(range(100)), "mode": "strict"}, "expected": [x * 2 for x in range(100)]},
                    {"input": {"data": [1, [1]], "mode": "lenient"}, "expected": [2, None]},
                    {"input": {"data": [1, float('inf')], "mode": "strict"}, "expected": [2, "inf_or_raises"]},
                )},
            ],
            "hints": [
                "Branch coverage: if/else, for, except, return hepsi test edilmeli",
                "Edge cases: bos liste, tek eleman, buyuk liste",
                "Error path: invalid input -> exception test",
            ],
            "explanation": (
                "Coverage-driven testing: fonksiyonun her branch'ini bir test ile "
                "kapsa. Branch coverage yuzde 100 hedef ama her zaman mumkun "
                "degil. Edge cases (bos, tek, max), error path (invalid input -> "
                "exception), ve happy path ayri testler."
            ),
            "complexity": "O(n) per test",
            "concepts": ["coverage", "branch-coverage", "edge-cases", "TDD"],
            "tags": ["testing", "coverage", "intermediate"],
        },
    ],
}