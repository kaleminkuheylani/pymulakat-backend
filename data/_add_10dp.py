"""
_add_10dp.py — CSV'ye 10 yeni eşi-olmayan DP sorusu ekler.

Mevcut 12 DP sorusu (id 142-153) korunur. 10 yeni soru 172-181 id'leri ile
eklenir. Hepsi klasik DP problemleri, CSV'de başlık/function_name bazında
eşi yok.

CSV format: QUOTE_ALL (mevcut yapıyla uyumlu).
"""
import csv
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parent / "QUESTIONS-v3.csv"

# 10 yeni DP sorusu — id 172-181
# Mevcut: climb_stairs, coin_change, knapsack, lcs, length_of_lis,
#         max_subarray, word_break, edit_distance, unique_paths,
#         rob, num_decodings, can_partition (12 tane)
# Yeni: lps, lps_substring, mcm, min_path_sum, distinct_subseq,
#       interleaving, burst_balloons, regex_match, target_sum, lcs_substring
NEW_QUESTIONS = [
    {
        "id": "172",
        "category": "dynamic-programming",
        "title": "Longest Palindromic Subsequence",
        "level": "intermediate",
        "description": "Bir string'in en uzun palindromik alt-dizisinin (subsequence) uzunluğunu bul. Karakterler arası karakter atlanabilir, sıra korunmalı.\nÖrnek: 'bbbab' → 4 ('bbbb').",
        "function_name": "longest_palindromic_subsequence",
        "starter_code": "def longest_palindromic_subsequence(text: str) -> int:\n    pass",
        "test_cases": '[{"input": "bbbab", "expected": 4}, {"input": "cbbd", "expected": 2}, {"input": "a", "expected": 1}, {"input": "racecar", "expected": 7}]',
        "hints": '["💡 İpucu 1: dp[i][j] = i..j aralığındaki en uzun palindromik subsequence uzunluğu.", "💡 İpucu 2: text[i] == text[j] ise dp[i][j] = dp[i+1][j-1] + 2, değilse max(dp[i+1][j], dp[i][j-1]).", "💡 İpucu 3: text ve text[::-1] için LCS problemine indirgenebilir."]',
    },
    {
        "id": "173",
        "category": "dynamic-programming",
        "title": "Longest Palindromic Substring",
        "level": "intermediate",
        "description": "Bir string içindeki en uzun palindromik alt-string'i (substring) bul.\nÖrnek: 'babad' → 'bab' (veya 'aba', uzunluk 3).",
        "function_name": "longest_palindromic_substring",
        "starter_code": "def longest_palindromic_substring(text: str) -> str:\n    pass",
        "test_cases": '[{"input": "babad", "expected": "bab"}, {"input": "cbbd", "expected": "bb"}, {"input": "a", "expected": "a"}, {"input": "racecar", "expected": "racecar"}]',
        "hints": '["💡 İpucu 1: dp[i][j] = text[i..j] palindrom mu (boolean).", "💡 İpucu 2: 2 uzunluk için text[i] == text[i+1] kontrolü, daha uzun için text[i] == text[j] ve dp[i+1][j-1].", "💡 İpucu 3: Expand-around-center O(n²) alternatif çözüm."]',
    },
    {
        "id": "174",
        "category": "dynamic-programming",
        "title": "Matrix Chain Multiplication",
        "level": "advanced",
        "description": "Bir matris zincirinin çarpımı için minimum skaler çarpma sayısını bul. Matrisler soldan sağa çarpılır.\nÖrnek: p = [1, 2, 3, 4] (3 matris: 1x2, 2x3, 3x4) → 18.",
        "function_name": "matrix_chain_order",
        "starter_code": "def matrix_chain_order(dims: list[int]) -> int:\n    pass",
        "test_cases": '[{"input": [1, 2, 3, 4], "expected": 18}, {"input": [10, 30, 5, 60], "expected": 4500}, {"input": [40, 20, 30, 10, 30], "expected": 26000}]',
        "hints": '["💡 İpucu 1: dp[i][j] = matris i..j çarpımı için min cost.", "💡 İpucu 2: Tüm k parçaları için böl: dp[i][j] = min(dp[i][k] + dp[k][j] + dims[i]*dims[k]*dims[j]).", "💡 İpucu 3: O(n³) DP, Knuth optimization ile O(n²) iyileştirme mümkün."]',
    },
    {
        "id": "175",
        "category": "dynamic-programming",
        "title": "Minimum Path Sum",
        "level": "intermediate",
        "description": "Sol-üst köşeden sağ-alt köşeye, sadece sağa/aşağı hareketle minimum toplam yol bul.\nÖrnek: [[1,3,1],[1,5,1],[4,2,1]] → 7 (1→3→1→1→1).",
        "function_name": "min_path_sum",
        "starter_code": "def min_path_sum(grid: list[list[int]]) -> int:\n    pass",
        "test_cases": '[{"input": [[1, 3, 1], [1, 5, 1], [4, 2, 1]], "expected": 7}, {"input": [[1, 2, 3], [4, 5, 6]], "expected": 12}, {"input": [[1]], "expected": 1}]',
        "hints": '["💡 İpucu 1: dp[i][j] = (0,0)\'den (i,j)\'ye minimum toplam.", "💡 İpucu 2: dp[i][j] = grid[i][j] + min(dp[i-1][j], dp[i][j-1]) (kenar kontrolleri ile).", "💡 İpucu 3: In-place: grid[i][j] += min(grid[i-1][j], grid[i][j-1])."]',
    },
    {
        "id": "176",
        "category": "dynamic-programming",
        "title": "Distinct Subsequences",
        "level": "advanced",
        "description": "String s, string t\'nin kaç farklı alt-dizisini (subsequence) içeriyor?\nÖrnek: s='rabbbit', t='rabbit' → 3.",
        "function_name": "num_distinct",
        "starter_code": "def num_distinct(s: str, t: str) -> int:\n    pass",
        "test_cases": '[{"input": {"s": "rabbbit", "t": "rabbit"}, "expected": 3}, {"input": {"s": "babgbag", "t": "bag"}, "expected": 5}, {"input": {"s": "abc", "t": "abc"}, "expected": 1}]',
        "hints": '["💡 İpucu 1: dp[i][j] = s[:i] içinde t[:j]\'nin kaç farklı subsequence olduğu.", "💡 İpucu 2: s[i-1] == t[j-1] ise dp[i][j] = dp[i-1][j-1] + dp[i-1][j], değilse dp[i][j] = dp[i-1][j].", "💡 İpucu 3: 1D DP\'ye indirgenebilir (O(n) bellek)."]',
    },
    {
        "id": "177",
        "category": "dynamic-programming",
        "title": "Interleaving String",
        "level": "advanced",
        "description": "s3, s1 ve s2\'nin bir interleaving\'i mi? Karakter sırası korunmalı.\nÖrnek: s1='aabcc', s2='dbbca', s3='aadbbcbcac' → True.",
        "function_name": "is_interleave",
        "starter_code": "def is_interleave(s1: str, s2: str, s3: str) -> bool:\n    pass",
        "test_cases": '[{"input": {"s1": "aabcc", "s2": "dbbca", "s3": "aadbbcbcac"}, "expected": true}, {"input": {"s1": "aabcc", "s2": "dbbca", "s3": "aadbbbaccc"}, "expected": false}, {"input": {"s1": "", "s2": "", "s3": ""}, "expected": true}]',
        "hints": '["💡 İpucu 1: dp[i][j] = s1[:i] ve s2[:j]\'nin s3[:i+j] interleaving\'i mi?", "💡 İpucu 2: s3[i+j-1] == s1[i-1] ise dp[i][j] |= dp[i-1][j]; s3[i+j-1] == s2[j-1] ise dp[i][j] |= dp[i][j-1].", "💡 İpucu 3: 1D DP yeterli (sadece önceki satır)."]',
    },
    {
        "id": "178",
        "category": "dynamic-programming",
        "title": "Burst Balloons",
        "level": "advanced",
        "description": "n balon, her patlatmada balonun sol ve sağındaki komşu balonların sayıları çarpılır. Tüm balonları patlatarak maksimum toplam puanı bul.\nÖrnek: [3,1,5,8] → 167.",
        "function_name": "max_coins",
        "starter_code": "def max_coins(nums: list[int]) -> int:\n    pass",
        "test_cases": '[{"input": [3, 1, 5, 8], "expected": 167}, {"input": [1, 5], "expected": 10}, {"input": [10], "expected": 10}]',
        "hints": '["💡 İpucu 1: Başına ve sonuna 1 ekle: [1, 3, 1, 5, 8, 1].", "💡 İpucu 2: Interval DP: dp[i][j] = (i, j) aralığındaki maksimum coin (i ve j kalan balonlar).", "💡 İpucu 3: k balonu son patlatılan: dp[i][j] = max(dp[i][k] + dp[k][j] + nums[i]*nums[k]*nums[j])."]',
    },
    {
        "id": "179",
        "category": "dynamic-programming",
        "title": "Regular Expression Matching",
        "level": "advanced",
        "description": "String s, pattern p ile eşleşiyor mu? \'.\' herhangi bir karakter, \'*\' önceki karakterin 0 veya daha fazlası.\nÖrnek: s='aab', p='c*a*b' → True.",
        "function_name": "is_match",
        "starter_code": "def is_match(s: str, p: str) -> bool:\n    pass",
        "test_cases": '[{"input": {"s": "aa", "p": "a"}, "expected": false}, {"input": {"s": "aa", "p": "a*"}, "expected": true}, {"input": {"s": "ab", "p": ".*"}, "expected": true}, {"input": {"s": "aab", "p": "c*a*b"}, "expected": true}]',
        "hints": '["💡 İpucu 1: dp[i][j] = s[:i] p[:j] ile eşleşiyor mu?", "💡 İpucu 2: p[j-1] == \'*\' ise: 0 kez (p[j-2]\'yi at) VEYA 1+ kez (s[i-1] p[j-2] ile eşleşirse dp[i-1][j]).", "💡 İpucu 3: p[j-1] == \'.\' veya p[j-1] == s[i-1] ise dp[i][j] = dp[i-1][j-1]."]',
    },
    {
        "id": "180",
        "category": "dynamic-programming",
        "title": "Target Sum",
        "level": "intermediate",
        "description": "Her sayının önüne + veya - koyarak hedef toplama ulaş. Kaç farklı yol var?\nÖrnek: nums=[1,1,1,1,1], target=3 → 5 yol.",
        "function_name": "find_target_sum_ways",
        "starter_code": "def find_target_sum_ways(nums: list[int], target: int) -> int:\n    pass",
        "test_cases": '[{"input": {"nums": [1, 1, 1, 1, 1], "target": 3}, "expected": 5}, {"input": {"nums": [1], "target": 1}, "expected": 1}, {"input": {"nums": [1, 0], "target": 1}, "expected": 2}]',
        "hints": '["💡 İpucu 1: Toplam S, pozitif toplam P ise P - (S-P) = target → 2P = S+target.", "💡 İpucu 2: Alt küme toplamı P olacak subset sayısını bul.", "💡 İpucu 3: 1D DP: dp[sum] = kaç subset bu toplama ulaşır."]',
    },
    {
        "id": "181",
        "category": "dynamic-programming",
        "title": "Longest Common Substring",
        "level": "intermediate",
        "description": "İki string arasındaki en uzun ortak alt-string\'in (substring) uzunluğunu bul. Subsequence değil, SUBSTRING (bitişik olmalı).\nÖrnek: s1='abcdef', s2='zbcdf' → 3 ('bcd').",
        "function_name": "longest_common_substring",
        "starter_code": "def longest_common_substring(s1: str, s2: str) -> int:\n    pass",
        "test_cases": '[{"input": {"s1": "abcdef", "s2": "zbcdf"}, "expected": 3}, {"input": {"s1": "abc", "s2": "xyz"}, "expected": 0}, {"input": {"s1": "hello", "s2": "yellow"}, "expected": 4}]',
        "hints": '["💡 İpucu 1: dp[i][j] = s1[:i] ve s2[:j] içinde s1[i-1]==s2[j-1] ile biten substring uzunluğu.", "💡 İpucu 2: Eşleşiyorsa dp[i][j] = dp[i-1][j-1] + 1, değilse 0 (LCS\'ten farklı!).", "💡 İpucu 3: Tüm dp[i][j] değerlerinin maksimumunu döndür."]',
    },
]


def main():
    # Yedek al
    import shutil
    from datetime import datetime
    bak = CSV_PATH.with_name(f"QUESTIONS-v3.csv.bak-{datetime.now().strftime('%H%M%S')}-pre-10dp")
    if not bak.exists():
        shutil.copy(CSV_PATH, bak)
        print(f"Yedek: {bak.name}")

    # Mevcut CSV oku
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Unique kontrol — id, title, function_name
    existing_ids = {r["id"] for r in rows}
    existing_titles = {r.get("title", "") for r in rows}
    existing_fns = {r.get("function_name", "") for r in rows}

    added = []
    skipped = []
    for q in NEW_QUESTIONS:
        if q["id"] in existing_ids:
            skipped.append((q["id"], "id zaten var"))
            continue
        if q["title"] in existing_titles:
            skipped.append((q["id"], f"title zaten var: {q['title']}"))
            continue
        if q["function_name"] in existing_fns:
            skipped.append((q["id"], f"function_name zaten var: {q['function_name']}"))
            continue
        rows.append(q)
        added.append(q["id"])
        existing_ids.add(q["id"])
        existing_titles.add(q["title"])
        existing_fns.add(q["function_name"])

    # Yaz (QUOTE_ALL mevcut formatla uyumlu)
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nEklenen: {len(added)} soru — id'ler: {added}")
    if skipped:
        print(f"Atlanan: {len(skipped)}")
        for sid, reason in skipped:
            print(f"  {sid}: {reason}")

    # Doğrulama
    with open(CSV_PATH) as f:
        rows2 = list(csv.DictReader(f))
    dp = [r for r in rows2 if r.get("category") == "dynamic-programming"]
    print(f"\nToplam DP soru: {len(dp)}")


if __name__ == "__main__":
    main()
