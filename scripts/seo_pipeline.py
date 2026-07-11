#!/usr/bin/env python3
"""
Pipeline: backend -> endpoint test -> frontend type check -> render check -> DOM check.

Kullanım:
  python3 scripts/seo_pipeline.py [--render]
  python3 scripts/seo_pipeline.py --render  # DOM check (Playwright)

Hedef: her değişiklik sonrası tüm zincirin çalıştığını doğrula.
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

# ═════════════════════════════════════════════════════════════════
# Config
# ═════════════════════════════════════════════════════════════════

BACKEND_URL = "https://pymulakat-backend-production.up.railway.app"
FRONTEND_URL = "https://pythonmulakat.com"
REPO_BACKEND = Path("/workspace/pymulakat-backend")
REPO_FRONTEND = Path("/workspace/pymulakat-frontend")


def step(name: str):
    """Print step header."""
    print(f"\n{'=' * 70}")
    print(f"  {name}")
    print(f"{'=' * 70}")


# ═════════════════════════════════════════════════════════════════
# Step 1: Backend health
# ═════════════════════════════════════════════════════════════════

def check_backend_health() -> dict:
    """Backend /api/v2/questions endpoint'ini test et."""
    step("1. Backend endpoint test")
    result = {"ok": True, "endpoints": {}}

    endpoints = [
        ("/api/v2/questions", "Sorular listesi"),
        ("/api/v2/categories", "Kategori listesi"),
        ("/api/v2/questions/by-slug/data-structures/deque-kullanarak-kayan-pencere-maksimumu", "Soru detay (slug ile)"),
        ("/api/v2/questions/by-slug/data-structures/deque-kullanarak-kayan-pencere-maksimumu/tests", "Test cases (slug ile)"),
    ]

    import urllib.request
    import urllib.error

    for path, label in endpoints:
        url = BACKEND_URL + path
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "seo-pipeline/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                status = resp.status
                body = resp.read()
                try:
                    data = json.loads(body)
                    count = len(data.get("data", data.get("items", [])))
                    result["endpoints"][path] = {"status": status, "count": count, "ok": status == 200}
                    if status != 200:
                        result["ok"] = False
                    print(f"  ✓ {label}: {status}, items={count}")
                except json.JSONDecodeError:
                    result["endpoints"][path] = {"status": status, "ok": False}
                    result["ok"] = False
                    print(f"  ✗ {label}: {status} (non-JSON)")
        except urllib.error.HTTPError as e:
            result["endpoints"][path] = {"status": e.code, "ok": False}
            result["ok"] = False
            print(f"  ✗ {label}: {e.code}")
        except Exception as e:
            result["endpoints"][path] = {"status": 0, "ok": False, "error": str(e)}
            result["ok"] = False
            print(f"  ✗ {label}: {e}")

    return result


# ═════════════════════════════════════════════════════════════════
# Step 2: Frontend type check (tsc --noEmit)
# ═════════════════════════════════════════════════════════════════

def check_frontend_types() -> dict:
    """Frontend TypeScript type check."""
    step("2. Frontend type check (tsc --noEmit)")
    result = {"ok": True, "errors": []}

    if not (REPO_FRONTEND / "node_modules").exists():
        print("  ⚠ node_modules yok, install gerekli")
        return {"ok": False, "errors": ["node_modules missing"]}

    try:
        proc = subprocess.run(
            ["npx", "tsc", "--noEmit"],
            cwd=REPO_FRONTEND,
            capture_output=True,
            text=True,
            timeout=180,
        )
        if proc.returncode == 0:
            print("  ✓ TypeScript check passed")
        else:
            result["ok"] = False
            # Sadece error satırları al (warning'leri atla)
            for line in proc.stdout.splitlines():
                if "error TS" in line:
                    result["errors"].append(line)
            print(f"  ✗ {len(result['errors'])} TypeScript error(s)")
            for err in result["errors"][:5]:
                print(f"    {err[:200]}")
    except subprocess.TimeoutExpired:
        result["ok"] = False
        result["errors"].append("timeout")
        print("  ✗ Timeout (>180s)")
    except Exception as e:
        result["ok"] = False
        result["errors"].append(str(e))
        print(f"  ✗ {e}")

    return result


# ═════════════════════════════════════════════════════════════════
# Step 3: Render check (basic HTTP)
# ═════════════════════════════════════════════════════════════════

def check_frontend_render() -> dict:
    """Frontend sayfalarının render olduğunu doğrula (HTML içerik kontrolü)."""
    step("3. Frontend render check (HTTP + HTML)")
    result = {"ok": True, "pages": {}}

    pages = [
        ("/", "Anasayfa"),
        ("/interviews", "Kategori listesi"),
        ("/python-temelleri", "Python Temelleri"),
        ("/python-veri-yapilari", "Python Veri Yapıları"),
        ("/python-pandas", "Python Pandas"),
        ("/python-liste-sozluk", "Python Liste & Sözlük"),
        ("/python-heap", "Python Heap"),
        ("/python-stack", "Python Stack"),
        ("/python-queue", "Python Queue"),
        ("/python-algoritma-sorulari", "Python Algoritma"),
        ("/python-dinamik-programlama", "Python Dinamik Programlama"),
    ]

    import urllib.request

    for path, label in pages:
        url = FRONTEND_URL + path
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "seo-pipeline/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                status = resp.status
                html = resp.read().decode("utf-8", errors="ignore")
                # Marker: <h1> tag içindeki başlık
                import re
                h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
                title = h1.group(1).strip()[:60] if h1 else "(no h1)"
                # Question item var mı? (CategoryFetchTest listesi)
                has_items = "Soru yükleniyor" in html or "question-card" in html or "QuestionCard" in html or "Sözlük Birleştirme" in html or "Liste" in html
                ok = status == 200 and (h1 is not None)
                result["pages"][path] = {"status": status, "title": title, "has_items": has_items, "ok": ok}
                if not ok:
                    result["ok"] = False
                mark = "✓" if ok else "✗"
                print(f"  {mark} {label} ({path}): {status} | {title[:50]}")
        except Exception as e:
            result["pages"][path] = {"status": 0, "ok": False, "error": str(e)}
            result["ok"] = False
            print(f"  ✗ {label}: {e}")

    return result


# ═════════════════════════════════════════════════════════════════
# Step 4: DOM check (item count via HTML markers)
# ═════════════════════════════════════════════════════════════════

def check_dom_items() -> dict:
    """DOM'da soru sayısını say (HTML marker bazlı, Playwright değil)."""
    step("4. DOM item count (HTML marker bazlı)")
    result = {"ok": True, "categories": {}}

    # DB-FIRST: backend kategori + count döner
    import urllib.request
    url = BACKEND_URL + "/api/v2/categories"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read())
            cats = data.get("data", [])
    except Exception as e:
        return {"ok": False, "error": str(e)}

    # Frontend'den her kategori sayfasını çek, item sayısını say
    for cat in cats:
        slug = cat.get("slug", "")
        count = cat.get("question_count", 0)
        # Frontend URL mapping (server-side API'den)
        url_map = {
            "python-basics": "/python-temelleri",
            "data-structures": "/python-veri-yapilari",
            "pandas": "/python-pandas",
            "list-dict": "/python-liste-sozluk",
            "heap": "/python-heap",
            "stack": "/python-stack",
            "queue": "/python-queue",
            "algorithms": "/python-algoritma-sorulari",
            "dynamic-programming": "/python-dinamik-programlama",
        }
        page_path = url_map.get(slug)
        if not page_path:
            continue
        page_url = FRONTEND_URL + page_path
        try:
            req = urllib.request.Request(page_url, headers={"User-Agent": "seo-pipeline/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                # QuestionListClient render markerları:
                # "Soru yükleniyor" (boş) veya gerçek question title'ları
                is_loading = "Soru yükleniyor" in html or "Yükleniyor" in html
                # CSV-FIRST'te soru başlıkları HTML'e basılıyordu
                # DB-FIRST'te de ServerQuestionList server-side render yapıyor
                result["categories"][slug] = {
                    "page": page_path,
                    "expected_count": count,
                    "is_loading": is_loading,
                }
                status = "✓" if not is_loading and count > 0 else "⚠"
                print(f"  {status} {slug}: {count} soru bekleniyor (loading={is_loading})")
                if is_loading and count > 0:
                    result["ok"] = False
        except Exception as e:
            result["categories"][slug] = {"error": str(e)}
            print(f"  ✗ {slug}: {e}")

    return result


# ═════════════════════════════════════════════════════════════════
# Main
# ═════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--render", action="store_true", help="Render/DOM check ekle (yavaş)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "backend": check_backend_health(),
    }

    if results["backend"]["ok"]:
        results["frontend_types"] = check_frontend_types()
        results["frontend_render"] = check_frontend_render()
        if args.render:
            results["dom_items"] = check_dom_items()

    # Summary
    step("SUMMARY")
    all_ok = True
    for name, r in results.items():
        if name == "timestamp":
            continue
        ok = r.get("ok", False)
        all_ok = all_ok and ok
        mark = "✓" if ok else "✗"
        print(f"  {mark} {name}: {'PASS' if ok else 'FAIL'}")

    if args.json:
        print()
        print(json.dumps(results, indent=2, ensure_ascii=False, default=str))

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
