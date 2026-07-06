"""DP algorithms patterns."""
from ._shared import tcs

PATTERN = {
    "level": "advanced",
    "templates": [
        {
            "title": "Coin Change (Min Coins)",
            "description": (
                "Para üstü: 41 TL = 25+10+5+1, 4 coin. Verilen coin denominations ve "
                "target amount için en az sayıda coin kullanarak toplamı oluştur. "
                "Mümkün değilse -1."
            ),
            "starter": (
                "def coin_change(coins, amount):\n"
                "    # DP: dp[i] = amount i için min coin sayısı\n"
                "    pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"coins": [1, 5, 10, 25], "amount": 41}, "expected": 4},
                    {"input": {"coins": [2], "amount": 3}, "expected": -1},
                    {"input": {"coins": [1], "amount": 0}, "expected": 0},
                    {"input": {"coins": [1, 3, 4], "amount": 6}, "expected": 2},
                    {"input": {"coins": [], "amount": 5}, "expected": -1},
                )},
                {"cases": tcs(
                    {"input": {"coins": [1, 2, 5], "amount": 11}, "expected": 3},
                    {"input": {"coins": [3, 7], "amount": 1}, "expected": -1},
                    {"input": {"coins": [1], "amount": 1000}, "expected": 1000},
                    {"input": {"coins": [1, 5, 10, 25], "amount": 30}, "expected": 2},
                    {"input": {"coins": [2, 5, 10], "amount": -1}, "expected": "ValueError"},
                )},
            ],
            "hints": [
                "💡 `dp[i] = min(dp[i], dp[i-coin] + 1)` her coin için",
                "💡 `dp[0] = 0`, diğerleri `float('inf')`",
                "💡 Bottom-up: amount 0'dan target'a kadar",
            ],
            "explanation": (
                "Bottom-up DP: dp[0]=0, dp[>0]=infinity başlat. Her coin için i "
                "aralığında: dp[i] = min(mevcut dp[i], dp[i-coin]+1) eğer i>=coin. "
                "Sonuç dp[amount]. infinity kalırsa mümkün değil → -1. amount<0 veya "
                "coins=[] defensive validation."
            ),
            "complexity": "O(amount × len(coins)) time, O(amount) space",
            "concepts": ["DP", "coin-change", "optimization", "bottom-up"],
            "tags": ["dp", "algorithms", "optimization"],
        },
        {
            "title": "Longest Common Subsequence",
            "description": (
                "Diff tool: iki dosya versiyonu arasındaki en uzun ortak kısmı bul. "
                "İki string'in en uzun ortak subsequence uzunluğunu dön."
            ),
            "starter": (
                "def lcs(s1, s2):\n"
                "    # DP: dp[i][j] = s1[:i] ve s2[:j] için LCS uzunluğu\n"
                "    pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"s1": "abcde", "s2": "ace"}, "expected": 3},
                    {"input": {"s1": "abc", "s2": "def"}, "expected": 0},
                    {"input": {"s1": "AGGTAB", "s2": "GXTXAYB"}, "expected": 4},
                    {"input": {"s1": "abc", "s2": "abc"}, "expected": 3},
                    {"input": {"s1": "", "s2": "abc"}, "expected": 0},
                )},
                {"cases": tcs(
                    {"input": {"s1": "abcbdab", "s2": "bdcaba"}, "expected": 4},
                    {"input": {"s1": "a", "s2": "b"}, "expected": 0},
                    {"input": {"s1": "abcdefghij" * 5, "s2": "acegi" * 5}, "expected": 25},
                    {"input": {"s1": "abc", "s2": ""}, "expected": 0},
                    {"input": {"s1": "xyz", "s2": "xyz"}, "expected": 3},
                )},
            ],
            "hints": [
                "💡 Eşitse çapraz+1, değilse max(üst, sol)",
                "💡 (0, *) ve (*, 0) = 0 base case",
                "💡 Memory: 2 satır yeterli (rolling array)",
            ],
            "explanation": (
                "2D DP tablosu: eşitse çapraz+1, değilse üst/sol max. dp[0][*] ve "
                "dp[*][0] = 0 (boş string LCS). Son hücre cevap. Memory optimize: "
                "sadece önceki satırı tutmak yeterli, O(min(m,n)) space."
            ),
            "complexity": "O(m×n) time, O(m×n) space (or O(min(m,n)))",
            "concepts": ["DP", "LCS", "string", "2D-table", "optimization"],
            "tags": ["dp", "algorithms", "string"],
        },
        {
            "title": "0/1 Knapsack",
            "description": (
                "Kargo aracı: weight kapasitesi 7 kg, 4 ürün (her biri tek). "
                "Max value'yu alacak subset'i bul. Her item sadece 1 kez (0/1 knapsack)."
            ),
            "starter": (
                "def knapsack(weights, values, capacity):\n"
                "    # DP: dp[i][w] = i item'e kadar w kapasiteyle max value\n"
                "    pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"weights": [1, 3, 4, 5], "values": [1, 4, 5, 7], "capacity": 7}, "expected": 9},
                    {"input": {"weights": [], "values": [], "capacity": 10}, "expected": 0},
                    {"input": {"weights": [2, 3, 4, 5], "values": [3, 4, 5, 6], "capacity": 5}, "expected": 7},
                    {"input": {"weights": [1, 2, 3], "values": [10, 20, 30], "capacity": 6}, "expected": 60},
                    {"input": {"weights": [5, 10], "values": [10, 20], "capacity": -1}, "expected": "ValueError"},
                )},
                {"cases": tcs(
                    {"input": {"weights": [10, 20, 30], "values": [60, 100, 120], "capacity": 50}, "expected": 220},
                    {"input": {"weights": [1], "values": [1], "capacity": 0}, "expected": 0},
                    {"input": {"weights": [5, 5, 5], "values": [10, 10, 10], "capacity": 100}, "expected": 30},
                    {"input": {"weights": [2, 4, 6], "values": [3, 5, 7], "capacity": 10}, "expected": 10},
                    {"input": {"weights": [1, 2], "values": [3], "capacity": 5}, "expected": "ValueError"},
                )},
            ],
            "hints": [
                "💡 `dp[i][w] = max(dp[i-1][w], dp[i-1][w-w_i] + v_i)`",
                "💡 1D'ye optimize: `for w in range(W, weight[i]-1, -1)` (ters)",
                "💡 Base: dp[0][*] = 0",
            ],
            "explanation": (
                "2D DP: her item için iki seçenek — alma (üst satır dp[i-1][w]) veya "
                "al (dp[i-1][w-weight] + value). Optimize: 1D array, w capacity'den "
                "tersine iterate et. capacity < 0 → ValueError. len(weights) != "
                "len(values) → ValueError."
            ),
            "complexity": "O(n×W) time, O(n×W) space (or O(W))",
            "concepts": ["DP", "knapsack", "optimization", "2D-table"],
            "tags": ["dp", "algorithms", "optimization"],
        },
    ],
}