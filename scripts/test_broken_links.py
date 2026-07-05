#!/usr/bin/env python3
"""Sitemap + internal link test eden script.

CI/CD'de veya local'de calistirilir:
- Sitemap'teki URL'lerden HTTP status kontrol (404, 500, timeout)
- DB'den 82 sorunun slug URL'leri 200 dondurmeli
- Backend /health 200 olmali

Kullanim:
    python3 scripts/test_broken_links.py [--base https://pythonmulakat.com]
"""

import argparse
import sys
import re
import urllib.request
import urllib.error
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def fetch_url(url: str, timeout: int = 5) -> tuple[int, str]:
    """URL'den HTTP status don. (status, content_type)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "broken-link-tester/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        return e.code, str(e)
    except urllib.error.URLError as e:
        return -1, f"URLError: {e.reason}"
    except Exception as e:
        return -2, f"Exception: {e}"


def get_sitemap_urls(base: str) -> list[str]:
    """Sitemap'ten URL listesi al."""
    sitemap_url = f"{base}/sitemap.xml"
    try:
        with urllib.request.urlopen(sitemap_url, timeout=10) as resp:
            xml = resp.read().decode("utf-8")
    except Exception as e:
        print(f"⚠️ Sitemap alinamadi: {e}")
        return []

    # <loc>URL</loc> patternini cikar
    urls = re.findall(r"<loc>(.*?)</loc>", xml)
    return [u.strip() for u in urls]


def get_question_urls_from_db_or_v3(base: str) -> list[tuple[str, int]]:
    """DB veya QUESTIONS-v3.py'den soru URL'leri uret."""
    urls = []
    try:
        # Once DB
        import os
        if os.environ.get("SUPABASE_URL"):
            from supabase import create_client
            sb = create_client(
                os.environ["SUPABASE_URL"],
                os.environ["SUPABASE_SERVICE_ROLE_KEY"],
            )
            data = sb.table("questions").select("slug, category").execute()
            for q in (data.data or []):
                if q.get("slug") and q.get("category"):
                    urls.append((f"{base}/interviews/{q['category']}/{q['slug']}", 0))
            return urls
    except Exception as e:
        print(f"⚠️ DB'ye baglanilamadi, QUESTIONS-v3.py fallback: {e}")

    # Fallback: QUESTIONS-v3.py
    import importlib.util
    v3 = ROOT / "data" / "QUESTIONS-v3.py"
    spec = importlib.util.spec_from_file_location("v3", v3)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    for q in mod.QUESTIONS:
        slug = slugify(q.title)
        urls.append((f"{base}/interviews/{q.category}/{slug}", q.id))

    return urls


def slugify(text: str) -> str:
    s = text.lower()
    tr = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    s = s.translate(tr)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:80] or "question"


# Bizim unicode import'u unuttuk, ekleyelim
import unicodedata


def check_url(url_with_id: tuple[str, int]) -> tuple[str, int, str, int]:
    """Tek URL test et, (url, qid, status_msg, status_code) don."""
    url, qid = url_with_id
    status, msg = fetch_url(url)
    return url, qid, msg, status


def main():
    parser = argparse.ArgumentParser(description="Broken link + URL smoke test")
    parser.add_argument("--base", default="https://pythonmulakat.com",
                        help="Frontend base URL")
    parser.add_argument("--backend", default="",
                        help="Backend base URL (e.g. https://pymulakat-backend.vercel.app)")
    parser.add_argument("--workers", type=int, default=20)
    parser.add_argument("--timeout", type=int, default=8)
    args = parser.parse_args()

    print("=" * 70)
    print(f"BROKEN LINK + URL TEST")
    print(f"Frontend: {args.base}")
    print(f"Backend:  {args.backend or '(skipping backend tests)'}")
    print("=" * 70)

    all_results = []

    # 1. Backend health
    if args.backend:
        print("\n[1/3] Backend health check")
        print(f"  GET {args.backend}/health")
        status, msg = fetch_url(f"{args.backend}/health", timeout=args.timeout)
        ok = "✅" if status == 200 else "❌"
        print(f"  {ok} /health {status} {msg[:60]}")
        all_results.append(("backend-health", f"{args.backend}/health", -1, status, msg))

    # 2. Sitemap URL'ler
    print(f"\n[2/3] Sitemap URLs")
    sitemap_urls = get_sitemap_urls(args.base)
    print(f"  Bulunan URL sayisi: {len(sitemap_urls)}")

    if sitemap_urls:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(check_url, (u, 0)): u for u in sitemap_urls}
            for future in as_completed(futures):
                url, qid, msg, status = future.result()
                ok = "✅" if status == 200 else "❌"
                print(f"  {ok} {status} {url[:80]}{'...' if len(url) > 80 else ''}")
                all_results.append(("sitemap", url, qid, status, msg))

    # 3. Question URLs (DB veya v3)
    print(f"\n[3/3] Question detail URLs")
    q_urls = get_question_urls_from_db_or_v3(args.base)
    print(f"  Test edilecek soru: {len(q_urls)}")

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(check_url, x): x for x in q_urls}
        for future in as_completed(futures):
            url, qid, msg, status = future.result()
            ok = "✅" if status == 200 else "❌"
            qid_str = f"q#{qid:>3}" if qid else "-----"
            print(f"  {ok} {status} [{qid_str}] {url[60:]}")
            all_results.append(("question", url, qid, status, msg))

    # Summary
    print("\n" + "=" * 70)
    print("OZET")
    print("=" * 70)

    by_status = {}
    for r in all_results:
        src, url, qid, status, msg = r
        by_status.setdefault(status, []).append((src, url, qid, msg))

    success = sum(len(urls) for s, urls in by_status.items() if s == 200)
    failed = sum(len(urls) for s, urls in by_status.items() if s not in (200, -1, -2))
    warnings = sum(len(urls) for s, urls in by_status.items() if s in (-1, -2))

    total = success + failed + warnings

    print(f"\nToplam:  {total}")
    print(f"Basarili (200):  {success} ({success * 100 // max(total, 1)}%)")
    print(f"Basarisiz (non-200):  {failed}")
    print(f"Timeout/Hata:    {warnings}")

    if by_status:
        for status in sorted(by_status.keys(), key=lambda s: (s if s >= 0 else 999)):
            urls = by_status[status]
            if status >= 0 and status == 200:
                continue
            print(f"\n  Status {status}: {len(urls)} URL")
            for src, url, qid, msg in urls[:10]:
                qid_str = f"q#{qid:>3}" if qid else "-----"
                print(f"    [{qid_str}] {url[:80]} - {msg[:60]}")

    sys.exit(0 if failed == 0 and warnings == 0 else 1)


if __name__ == "__main__":
    main()
