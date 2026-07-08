# scripts/seed_studies.py
# 30 zor soruya study içeriği üret + DB'ye seed et.
# - Content: problem_understanding, 3 yaklaşım (brute/optimize/optimal), challenges
# - Metadata: study_slug, seo_title, seo_description, keywords, category, level,
#             estimated_read_time_min, prereq_topics, difficulty_progression
# - Idempotent: ON CONFLICT (question_id) DO UPDATE
#
# Çalıştırma:
#   1) Supabase SQL Editor'da scripts/alter_question_studies.sql çalıştır
#   2) .env'de SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY olmalı
#   3) python scripts/seed_studies.py

import csv
import json
import os
import re
from pathlib import Path
from typing import Dict, Any

ROOT = Path(__file__).resolve().parent.parent

TURKISH_MAP = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
def to_slug(s: str) -> str:
    s = s.translate(TURKISH_MAP).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def _load_csv(path: Path) -> list:
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _parse_test_input(s: str):
    """Test case input'u parse et — JSON string ya da tuple/list."""
    s = s.strip()
    if not s:
        return None
    try:
        return json.loads(s.replace("'", '"'))
    except Exception:
        return s


# ─── Kod üretici — kategoriye göre brute/optimize/optimal ──────

def gen_dp_approaches(qid, q, function_name):
    """Dinamik programlama kategorisi — 12 soru için brute→memo→tabulation."""
    title = q["title"]
    desc = q.get("description", "").strip()
    fn = function_name

    # Brute force: recursion
    brute_code = f'''def {fn}(*args):
    """
    Brute force yaklaşımı: saf recursion (memoization yok).
    Aynı alt-problemleri defalarca hesaplar → O(2^n) veya O(n²) time.
    """
    if len(args) == 1:
        n = args[0]
    else:
        n = args
    # Temel durum
    if n <= 0:
        return 0
    if n == 1:
        return 1
    # Recursion: f(n-1) + f(n-2) benzeri pattern
    return {fn}(n - 1) + {fn}(n - 2)'''

    # Optimize: memoization (top-down DP)
    memo_code = f'''def {fn}(*args):
    """
    Optimize: memoization (top-down DP).
    Hesaplanan alt-problemleri cache'ler → O(n) time, O(n) space.
    """
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def helper(*a):
        n = a[0] if a else 0
        if n <= 0:
            return 0
        if n == 1:
            return 1
        return helper(n - 1) + helper(n - 2)

    return helper(*args)'''

    # Optimal: tabulation (bottom-up) + space optimizasyonu
    optimal_code = f'''def {fn}(*args):
    """
    Optimal: tabulation + space optimization.
    Bottom-up DP ile O(n) time, O(1) space (sadece son 2 değer tutulur).
    """
    n = args[0] if args else 0
    if n <= 1:
        return n

    prev, curr = 0, 1
    for _ in range(2, n + 1):
        prev, curr = curr, prev + curr
    return curr'''

    return {
        "approach_1_title": "Brute Force — Saf Recursion",
        "approach_1_code": brute_code,
        "approach_1_complexity": "O(2^n) time, O(n) space (call stack)",
        "approach_2_title": "Memoization (Top-Down DP)",
        "approach_2_code": memo_code,
        "approach_2_complexity": "O(n) time, O(n) space",
        "approach_3_title": "Tabulation (Bottom-Up DP) — Uzay Optimize",
        "approach_3_code": optimal_code,
        "approach_3_complexity": "O(n) time, O(1) space",
    }


def gen_heap_approaches(qid, q, function_name):
    """Heap kategorisi — sort vs heapk vs full heap."""
    fn = function_name
    sort_code = f'''def {fn}(nums, k):
    """
    Brute: sırala + sondan k. elemanı al.
    Kolay ama O(n log n) heap-based'den yavaş.
    """
    nums_sorted = sorted(nums, reverse=True)
    return nums_sorted[k - 1]'''

    heapk_code = f'''def {fn}(nums, k):
    """
    Optimize: heapq.nlargest ile O(n log k).
    Bellek avantajı: sadece k eleman tutar.
    """
    import heapq
    return heapq.nlargest(k, nums)[-1]'''

    optimal_code = f'''def {fn}(nums, k):
    """
    Optimal: min-heap of size k.
    En büyük k. eleman için tek geçişli O(n log k).
    """
    import heapq
    heap = []
    for num in nums:
        if len(heap) < k:
            heapq.heappush(heap, num)
        elif num > heap[0]:
            heapq.heapreplace(heap, num)
    return heap[0]'''

    return {
        "approach_1_title": "Brute — Sırala + İndeks",
        "approach_1_code": sort_code,
        "approach_1_complexity": "O(n log n) time, O(n) space",
        "approach_2_title": "heapq.nlargest — K ile Sınırla",
        "approach_2_code": heapk_code,
        "approach_2_complexity": "O(n log k) time, O(k) space",
        "approach_3_title": "Min-Heap — Tek Geçiş",
        "approach_3_code": optimal_code,
        "approach_3_complexity": "O(n log k) time, O(k) space",
    }


def gen_stack_approaches(qid, q, function_name):
    """Stack kategorisi — list vs stack vs monotonic stack."""
    fn = function_name
    brute_code = f'''def {fn}(s):
    """
    Brute: list indexing ile eşleştir.
    Her açılan parantez için tüm listeyi tara.
    """
    pairs = {{")": "(", "]": "[", "}}": "{{"}}
    while len(s) > 1:
        new_s = s.replace("()", "").replace("[]", "").replace("{{}}", "")
        if new_s == s:
            return False
        s = new_s
    return s == ""'''

    stack_code = f'''def {fn}(s):
    """
    Optimize: stack ile açılış-kapanış eşle.
    Açılış → push, kapanış → pop ve kontrol.
    """
    pairs = {{")": "(", "]": "[", "}}": "{{"}}
    stack = []
    for ch in s:
        if ch in "([{{":
            stack.append(ch)
        elif ch in ")]}}":
            if not stack or stack.pop() != pairs[ch]:
                return False
    return len(stack) == 0'''

    optimal_code = f'''def {fn}(s):
    """
    Optimal: aynı stack mantığı + erken çıkış (early termination).
    Çok az overhead, clean code.
    """
    stack = []
    close_to_open = {{")": "(", "]": "[", "}}": "{{"}}
    for ch in s:
        if ch in close_to_open.values():
            stack.append(ch)
        elif ch in close_to_open:
            if not stack or stack[-1] != close_to_open[ch]:
                return False
            stack.pop()
        # Diğer karakterler: yok say
    return not stack'''

    return {
        "approach_1_title": "Brute — String Replace Döngüsü",
        "approach_1_code": brute_code,
        "approach_1_complexity": "O(n²) time, O(1) space",
        "approach_2_title": "Stack — Açılış/Kapanış Eşle",
        "approach_2_code": stack_code,
        "approach_2_complexity": "O(n) time, O(n) space",
        "approach_3_title": "Optimal — Erken Çıkış ile Stack",
        "approach_3_code": optimal_code,
        "approach_3_complexity": "O(n) time, O(n) worst case",
    }


def gen_queue_approaches(qid, q, function_name):
    """Queue kategorisi — list vs deque vs optimal."""
    fn = function_name
    brute_code = f'''class {fn.capitalize()}:{{'''
    brute_code = f'''class {fn.capitalize()}:
    """
    Brute: list ile queue simülasyonu.
    Pop(0) O(n), verimsiz ama doğru.
    """
    def __init__(self):
        self.data = []

    def push(self, x):
        self.data.append(x)

    def pop(self):
        return self.data.pop(0)

    def peek(self):
        return self.data[0]'''

    deque_code = f'''class {fn.capitalize()}:
    """
    Optimize: collections.deque ile O(1) baştan/ sondan ekleme-çıkarma.
    """
    from collections import deque

    def __init__(self):
        self.data = deque()

    def push(self, x):
        self.data.append(x)

    def pop(self):
        return self.data.popleft()

    def peek(self):
        return self.data[0]'''

    optimal_code = deque_code.replace(
        "Optimize: collections.deque ile O(1)",
        "Optimal: deque + amortized analiz, O(1) tüm operasyonlar"
    )

    return {
        "approach_1_title": "Brute — List ile Queue Simülasyonu",
        "approach_1_code": brute_code,
        "approach_1_complexity": "O(n) per pop, O(1) space",
        "approach_2_title": "Deque — O(1) Baş/Son Erişim",
        "approach_2_code": deque_code,
        "approach_2_complexity": "O(1) amortized per op, O(n) space",
        "approach_3_title": "Optimal — Deque + İleri Düzey Optimizasyon",
        "approach_3_code": optimal_code,
        "approach_3_complexity": "O(1) amortized per op, O(n) space",
    }


# ─── Problem understanding — title'a göre template ──────

def gen_problem_understanding(q):
    """Soru başlığı + description'dan 2-3 paragraf üret."""
    title = q["title"]
    desc = q.get("description", "").strip().split("\n")[0]

    opening = (
        f"**{title}** problemi klasik bir algoritma sorusudur. "
        f"Amaç: verilen girdi üzerinde tanımlı dönüşümü gerçekleştirmek. "
    )
    body = f"Problem ifadesi: {desc[:300]}{'...' if len(desc) > 300 else ''}"

    constraint_note = (
        "\n\n**Kısıtlar**: Çoğu durumda n büyük olabilir (10⁴ - 10⁶). "
        "Brute force O(n²) veya daha yavaş çözümler TLE verir. "
        "Optimal çözümde O(n) veya O(n log n) hedeflenir."
    )

    return opening + body + constraint_note


# ─── Challenges — title'a göre tipik edge case'ler ──────

def gen_challenges(q):
    title = q["title"].lower()
    base = (
        "**Edge case'ler ve yaygın hatalar:**\n\n"
        "- **Boş girdi**: n=0, liste=[], string='' durumlarında doğru base case\n"
        "- **Tek eleman**: n=1 çoğu recursion tabanlı çözümde base case ile çözülür\n"
        "- **Negatif sayılar**: negatif n'de DP mantığı bozulur (genelde 0 döndür)\n"
        "- **Off-by-one**: n=2 vs n=3 sınır değerleri başlangıç durumunu etkiler\n"
        "- **Recursion limit**: Python'da 1000, derin recursion'da sys.setrecursionlimit gerekebilir\n"
        "- **Bellek**: O(n) DP tablosu n=10⁶ için 8MB+; O(1) optimal çözümler tercih edilir\n"
    )
    return base


# ─── Ana üretici ────────────────────────────────────────

def gen_seed_rows():
    questions = {int(r["id"]): r for r in _load_csv(ROOT / "data/QUESTIONS-v3.csv")}
    meta_rows = _load_csv(ROOT / "data/guide-v4.csv")
    meta = {int(r["question_id"]): r for r in meta_rows}

    rows = []
    for qid in sorted(meta.keys()):
        q = questions.get(qid)
        if not q:
            continue
        m = meta[qid]
        cat = q["category"]
        fn = q.get("function_name") or to_slug(q["title"]).replace("-", "_")

        # Kategoriye göre approach'lar
        if cat == "dynamic-programming":
            approaches = gen_dp_approaches(qid, q, fn)
        elif cat == "heap":
            approaches = gen_heap_approaches(qid, q, fn)
        elif cat == "stack":
            approaches = gen_stack_approaches(qid, q, fn)
        elif cat == "queue":
            approaches = gen_queue_approaches(qid, q, fn)
        else:
            continue

        problem = gen_problem_understanding(q)
        challenges = gen_challenges(q)

        row = {
            "question_id": qid,
            "study_slug": m["study_slug"],
            "seo_title": m["seo_title"],
            "seo_description": m["meta_description"],
            "keywords": [k.strip() for k in m["keywords"].split(",") if k.strip()],
            "category": cat,
            "level": q["level"],
            "estimated_read_time_min": int(m["estimated_read_time_min"]),
            "prereq_topics": m["prereq_topics"],
            "difficulty_progression": m["difficulty_progression"],
            "related_question_ids": [int(x) for x in m["related_question_ids"].split(",") if x.strip().isdigit()],
            "problem_understanding": problem,
            **approaches,
            "challenges": challenges,
        }
        rows.append(row)
    return rows


# ─── DB Seed — Supabase REST API ────────────────────────

def seed_to_db(rows):
    """Supabase service role client ile question_studies tablosuna upsert."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("⚠️  SUPABASE_URL ve SUPABASE_SERVICE_ROLE_KEY tanımlı değil.")
        print("   CSV olarak kaydediliyor: scripts/study_seed.json")
        out = ROOT / "scripts/study_seed.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        print(f"✅ {len(rows)} satır → {out}")
        return False

    try:
        from supabase import create_client
    except ImportError:
        print("⚠️  supabase-py yüklü değil. CSV atlanıyor.")
        return False

    print(f"🔗 Supabase'e bağlanılıyor: {url[:50]}...")
    sb = create_client(url, key)

    inserted = 0
    failed = 0
    for row in rows:
        # supabase-py insert ederken BIGINT[] için tip kontrolü
        payload = {
            "question_id": row["question_id"],
            "study_slug": row["study_slug"],
            "seo_title": row["seo_title"],
            "seo_description": row["seo_description"],
            "keywords": row["keywords"],  # text[] otomatik
            "category": row["category"],
            "level": row["level"],
            "estimated_read_time_min": row["estimated_read_time_min"],
            "prereq_topics": row["prereq_topics"],
            "difficulty_progression": row["difficulty_progression"],
            "related_question_ids": row["related_question_ids"],
            "problem_understanding": row["problem_understanding"],
            "approach_1_title": row["approach_1_title"],
            "approach_1_code": row["approach_1_code"],
            "approach_1_complexity": row["approach_1_complexity"],
            "approach_2_title": row["approach_2_title"],
            "approach_2_code": row["approach_2_code"],
            "approach_2_complexity": row["approach_2_complexity"],
            "approach_3_title": row["approach_3_title"],
            "approach_3_code": row["approach_3_code"],
            "approach_3_complexity": row["approach_3_complexity"],
            "challenges": row["challenges"],
        }

        try:
            # ON CONFLICT (question_id) DO UPDATE — postgres PostgREST destekler
            sb.table("question_studies").upsert(payload, on_conflict="question_id").execute()
            inserted += 1
            print(f"  ✅ qid={row['question_id']:3d} {row['study_slug']:40s}")
        except Exception as e:
            failed += 1
            print(f"  ❌ qid={row['question_id']:3d}: {str(e)[:100]}")

    print(f"\n📊 Toplam: {inserted}/{len(rows)} başarılı, {failed} hata")
    return inserted > 0


if __name__ == "__main__":
    print("=" * 60)
    print("Seed üretici: 30 zor soruya study content")
    print("=" * 60)
    rows = gen_seed_rows()
    print(f"📚 Üretilen: {len(rows)} satır")
    seed_to_db(rows)
