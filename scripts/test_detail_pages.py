# scripts/test_detail_pages.py
# Tum detay sayfalarini test eder. Railway'de periodic olarak calistirilabilir.
# Kullanim: python scripts/test_detail_pages.py
# Env:     API_BASE, FRONTEND_BASE, REPORT_DIR, JSON_OUTPUT_PATH

import os
import sys
import json
import time
import urllib.request
import urllib.error
from typing import Dict, List, Tuple, Optional

API_BASE = os.getenv("API_BASE", "https://pymulakat-backend-production.up.railway.app")
FRONTEND_BASE = os.getenv("FRONTEND_BASE", "https://www.pythonmulakat.com")
TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "15"))
JSON_OUT = os.getenv("JSON_OUTPUT_PATH")

passed = 0
failed = 0
skipped = 0
errors: List[dict] = []


def http_get(url: str, headers: Optional[Dict] = None) -> Tuple[int, str, dict]:
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = resp.read().decode("utf-8", errors="ignore")
            try:
                j = json.loads(data) if data else {}
            except Exception:
                j = {}
            return resp.status, data, j
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="ignore"), {}
    except Exception as e:
        return 0, str(e), {}


def test(name: str, url: str, expected_status: int = 200,
         must_contain: Optional[List[str]] = None,
         must_have_keys: Optional[List[str]] = None,
         json_path: Optional[str] = None,
         skip_if: Optional[List[str]] = None) -> bool:
    global passed, failed, skipped
    status, body, j = http_get(url)
    ok = True
    reasons = []

    if skip_if and any(s in url for s in skip_if):
        skipped += 1
        print(f"  ⊘ {name}")
        return True

    if status != expected_status:
        ok = False
        reasons.append(f"status={status} (expected {expected_status})")

    if ok and must_contain:
        for s in must_contain:
            if s not in body:
                ok = False
                reasons.append(f"missing text: {s!r}")

    if ok and must_have_keys and json_path:
        # json_path: örn "data.0.slug" veya "data" veya "id"
        target = j
        for part in json_path.split("."):
            if isinstance(target, list):
                try:
                    idx = int(part)
                    target = target[idx]
                except (ValueError, IndexError):
                    target = None
                    break
            elif isinstance(target, dict):
                target = target.get(part)
            else:
                target = None
                break
        if target is None:
            ok = False
            reasons.append(f"missing path: {json_path}")
        else:
            for k in must_have_keys:
                if isinstance(target, dict) and k not in target:
                    ok = False
                    reasons.append(f"missing key at {json_path}.{k!r}")

    if ok:
        passed += 1
        print(f"  ✓ {name}")
    else:
        failed += 1
        msg = f"  ✗ {name} — {'; '.join(reasons)}"
        print(msg)
        errors.append({"test": name, "url": url, "status": status, "reasons": reasons})
    return ok


# ═══════════════════════════════════════════════════════════
# Testler
# ═══════════════════════════════════════════════════════════

def test_backend_health():
    print("\n[1] Backend Health")
    test("health", f"{API_BASE}/health", 200, must_have_keys=["status"], json_path="")


def test_categories():
    print("\n[2] Kategoriler")
    test("tum kategoriler", f"{API_BASE}/api/v2/categories",
         expected_status=200, json_path="data", must_have_keys=["slug", "label"])
    # Bireysel kategoriler icin ayrı endpoint var mi? Test et
    cats_data = http_get(f"{API_BASE}/api/v2/categories")[2].get("data", [])
    if isinstance(cats_data, list):
        for cat in cats_data[:3]:
            slug = cat.get("slug", "?") if isinstance(cat, dict) else "?"
            test(f"  /categories/{slug}", f"{API_BASE}/api/v2/categories/{slug}",
                 expected_status=200, skip_if=["/v2/categories/python-basics"])


def test_questions():
    print("\n[3] Sorular — Detay (1-73)")
    test_ids = [1, 7, 47, 50, 59, 67, 68, 69, 70, 71, 72, 73]
    for qid in test_ids:
        ok = test(f"  soru #{qid}", f"{API_BASE}/api/v2/questions/{qid}",
                  expected_status=200,
                  must_have_keys=["id", "title", "hints", "test_count"])
    # Detay endpoint'inde starter_code ve test_cases olmali (gercek bug raporlama)
    print("\n    [3a] Bug Check — Detay Endpoint Veri Butunlugu")
    status, _, j = http_get(f"{API_BASE}/api/v2/questions/1")
    if status == 200:
        missing = []
        if "starter_code" not in j or j.get("starter_code") is None:
            missing.append("starter_code")
        if "test_cases" not in j or not j.get("test_cases"):
            missing.append("test_cases")
        if "related_question_ids" not in j:
            missing.append("related_question_ids")
        if missing:
            print(f"    ⚠ BUG: /api/v2/questions/1 eksik alanlar: {missing}")
            errors.append({"test": "questions/detail integrity", "url": "/questions/1",
                          "missing_fields": missing})
        else:
            print(f"    ✓ /questions/1 tum alanlar tam")


def test_tutorials():
    print("\n[4] Tutorials")
    test_slugs = [
        "python-palindrome-cozum",
        "python-fizzbuzz-algoritma",
        "python-binary-search",
        "python-asal-sayi-algoritma",
        "python-obeb-oklid",
        "python-two-sum",
        "pandas-groupby-rehberi",
    ]
    for slug in test_slugs:
        test(f"  tutorial/{slug}", f"{API_BASE}/api/v2/tutorials/{slug}",
             expected_status=200, json_path="data",
             must_have_keys=["slug", "title", "content_md"])


def test_auth_endpoints():
    print("\n[5] Frontend Auth Sayfalari")
    test("register", f"{FRONTEND_BASE}/register", 200)
    test("login", f"{FRONTEND_BASE}/login", 200)


def test_frontend_pages():
    print("\n[6] Frontend Public")
    test("landing /", f"{FRONTEND_BASE}/", 200)
    test("/interviews", f"{FRONTEND_BASE}/interviews", 200)
    test("/guides", f"{FRONTEND_BASE}/guides", 200)


def test_frontend_question_detail():
    print("\n[7] Frontend Soru Detay")
    # 3 farkli eski/yeni soru
    questions = [
        ("python-basics", "1"),    # Palindrome - mevcut
        ("algorithms", "68"),     # Q68 merge sort - yeni
        ("list-dict", "69"),      # Q69 - yeni
        ("python-basics", "70"),  # Q70 - yeni
        ("strings", "71"),        # Q71 - yeni
        ("list-dict", "72"),      # Q72 - yeni
        ("algorithms", "73"),     # Q73 - yeni
    ]
    for cat, qid in questions:
        test(f"  /interviews/{cat}/{qid}",
             f"{FRONTEND_BASE}/interviews/{cat}/{qid}",
             expected_status=200)


def test_frontend_tutorial_detail():
    print("\n[8] Frontend Tutorial Detay")
    slugs = ["python-palindrome-cozum", "python-fizzbuzz-algoritma",
             "python-asal-sayi-algoritma"]
    for slug in slugs:
        test(f"  /guides/{slug}",
             f"{FRONTEND_BASE}/guides/{slug}",
             expected_status=200)


def test_response_times():
    global passed, failed
    print("\n[9] Response Time Benchmarks")
    endpoints = [
        "/health",
        "/api/v2/categories",
        "/api/v2/questions/all",
        "/api/v2/questions/68",
        "/api/v2/questions/69",
        "/api/v2/tutorials/python-fizzbuzz-algoritma",
        "/api/v2/tutorials/python-palindrome-cozum",
    ]
    for path in endpoints:
        start = time.time()
        status, _, _ = http_get(f"{API_BASE}{path}")
        elapsed = (time.time() - start) * 1000
        mark = "✓" if status == 200 else "✗"
        print(f"  {mark} {path:55s} {elapsed:6.0f}ms (HTTP {status})")
        if status != 200:
            failed += 1


def test_broken_pages():
    """Frontend 404 sayfalari — hizli tarama"""
    global passed, failed
    print("\n[10] Broken Page Scan")
    # Tum kategorileri ve sorulari gez, 404 olanlari bul
    status_cats, _, cj = http_get(f"{API_BASE}/api/v2/categories")
    cats = cj.get("data", []) if status_cats == 200 else []
    bad_pages = []
    for cat in cats[:5]:
        slug = cat.get("slug", "?") if isinstance(cat, dict) else "?"
        # Bu kategorinin ilk sorusunu test et
        status, _, qj = http_get(f"{API_BASE}/api/v2/questions/all?category={slug}")
        qs = qj.get("data", []) if status == 200 else []
        if qs:
            first_id = qs[0].get("id", "?") if isinstance(qs[0], dict) else "?"
            page_url = f"{FRONTEND_BASE}/interviews/{slug}/{first_id}"
            ps, _, _ = http_get(page_url)
            if ps != 200:
                bad_pages.append({"path": page_url, "status": ps, "category": slug, "question_id": first_id})

    if bad_pages:
        print(f"  ⚠ {len(bad_pages)} kırık sayfa bulundu:")
        for p in bad_pages:
            print(f"    - {p['path']} (HTTP {p['status']})")
            errors.append({"test": "frontend broken page", "url": p["path"],
                          "status": p["status"]})
        failed += len(bad_pages)
    else:
        passed += 1
        print(f"  ✓ Taranan 5 kategorinin ilk sorusu aciliyor")


# ═══════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════

def run_all(as_endpoint: bool = False):
    """Testlerin hepsini çalıştır. Sonuçları döndür.
    as_endpoint=True ise sys.exit yapmaz, dict döndürür.
    """
    print(f"═" * 60)
    print(f"Detay Sayfa Testleri — Pymulakat")
    print(f"API:      {API_BASE}")
    print(f"Frontend: {FRONTEND_BASE}")
    print(f"═" * 60)
    start = time.time()

    test_backend_health()
    test_categories()
    test_questions()
    test_tutorials()
    test_auth_endpoints()
    test_frontend_pages()
    test_frontend_question_detail()
    test_frontend_tutorial_detail()
    test_response_times()
    test_broken_pages()

    elapsed = time.time() - start
    print(f"\n{'═' * 60}")
    print(f"SONUÇ: {passed} passed, {failed} failed, {skipped} skipped ({elapsed:.1f}s)")
    print(f"{'═' * 60}")

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "elapsed_seconds": round(elapsed, 2),
        "api_base": API_BASE,
        "frontend_base": FRONTEND_BASE,
        "errors": errors,
    }
    out_path = JSON_OUT or "/tmp/pymulakat_test_report.json"
    try:
        with open(out_path, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\nRapor: {out_path}")
    except Exception as e:
        print(f"Rapor yazilamadi: {e}")
    return report


def main():
    report = run_all()
    sys.exit(0 if report["failed"] == 0 else 1)


if __name__ == "__main__":
    main()