#!/usr/bin/env python3
"""
Tüm interview URL'lerini gerçek HTTP istekleriyle test et.
DB'den slug'ları al, hem slug hem ID URL'lerini kontrol et.
Başarılı/başarısız olanları logla.

Kullanım:
    python3 scripts/check_interviews.py
    python3 scripts/check_interviews.py --fronted-url https://www.pythonmulakat.com
    python3 scripts/check_interviews.py --sample 10   # sadece ilk 10
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.error
from typing import List, Dict, Any
from datetime import datetime


BACKEND = os.getenv("BACKEND_URL", "https://pymulakat-backend-production.up.railway.app")
FRONTEND = os.getenv("FRONTEND_URL", "https://www.pythonmulakat.com")


def fetch_json(url: str, timeout: int = 15) -> Any:
    """URL'den JSON çek."""
    req = urllib.request.Request(url, headers={"User-Agent": "check-interviews/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_status(url: str, follow_redirects: bool = True, timeout: int = 30) -> Dict[str, Any]:
    """URL'ye istek at, status kodunu ve meta bilgiyi döndür."""
    # Path kismini quote et (Turkce karakter icin)
    from urllib.parse import urlsplit, urlunsplit, quote
    parts = urlsplit(url)
    safe_path = quote(parts.path, safe="/:&?=")
    encoded_url = urlunsplit((parts.scheme, parts.netloc, safe_path, parts.query, parts.fragment))

    try:
        req = urllib.request.Request(encoded_url, headers={"User-Agent": "check-interviews/1.0"})
        # Don't follow redirects — görmek istiyoruz
        if not follow_redirects:
            class NoRedirect(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, *args, **kwargs):
                    return None
            opener = urllib.request.build_opener(NoRedirect)
            try:
                resp = opener.open(req, timeout=timeout)
                return {"status": resp.status, "url": encoded_url, "error": None}
            except urllib.error.HTTPError as e:
                # 3xx response'lar redirect izlemeden 30x olarak gelir
                return {
                    "status": e.code,
                    "url": encoded_url,
                    "error": None,
                    "location": e.headers.get("Location"),
                }
        else:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return {"status": resp.status, "url": encoded_url, "error": None}
    except urllib.error.HTTPError as e:
        return {
            "status": e.code,
            "url": encoded_url,
            "error": f"HTTP {e.code}",
            "location": e.headers.get("Location"),
        }
    except Exception as e:
        return {"status": 0, "url": encoded_url, "error": str(e)}


def get_questions_from_db(backend_url: str) -> List[Dict[str, Any]]:
    """Backend üzerinden DB'den tüm soruları al."""
    url = f"{backend_url}/api/v2/questions/all?limit=200"
    print(f"[1/3] DB'den sorular çekiliyor: {url}")
    data = fetch_json(url)
    questions = data.get("data", data.get("items", []))
    print(f"      {len(questions)} soru bulundu")
    return questions


def check_interviews(questions: List[Dict[str, Any]], frontend_url: str, sample: int = None) -> List[Dict[str, Any]]:
    """Her soru için slug + ID URL'leri test et."""
    if sample:
        questions = questions[:sample]

    print(f"\n[2/3] {len(questions)} soru test ediliyor ({frontend_url})...")

    results = []
    for i, q in enumerate(questions):
        qid = q.get("id")
        slug = q.get("slug")
        category = q.get("category", "python-basics")

        if not qid or not category:
            results.append({"id": qid, "ok": False, "error": "missing id or category"})
            continue

        result = {
            "id": qid,
            "title": q.get("title", "")[:40],
            "category": category,
            "slug": slug,
        }

        # Test 1: Slug URL (canonical)
        if slug:
            slug_url = f"{frontend_url}/interviews/{category}/{slug}"
            r = fetch_status(slug_url)
            result["slug_url"] = slug_url
            result["slug_status"] = r["status"]
            result["slug_ok"] = r["status"] == 200
        else:
            result["slug_url"] = None
            result["slug_status"] = "NO SLUG"
            result["slug_ok"] = False

        # Test 2: ID URL (should 307 redirect to slug)
        id_url = f"{frontend_url}/interviews/{category}/{qid}"
        r = fetch_status(id_url, follow_redirects=False)
        result["id_url"] = id_url
        result["id_status"] = r["status"]
        result["id_redirects"] = r["status"] in (301, 302, 307, 308)

        # Test 3: Follow redirect → final 200
        r_follow = fetch_status(id_url, follow_redirects=True)
        result["id_final_status"] = r_follow["status"]
        result["id_ok"] = r_follow["status"] == 200

        results.append(result)

        # Progress
        ok = result["slug_ok"] and result["id_ok"]
        marker = "✓" if ok else "✗"
        if (i + 1) % 10 == 0 or not ok:
            slug_status = result.get("slug_status", "?")
            id_status = result.get("id_status", "?")
            final_status = result.get("id_final_status", "?")
            print(f"  {marker} #{qid:3d} [{category:13s}] slug={slug_status} id={id_status}→{final_status} {slug or '(no slug)'}")

    return results


def print_summary(results: List[Dict[str, Any]]):
    """Özet rapor yazdır."""
    print(f"\n[3/3] SONUÇ")
    print("=" * 70)

    total = len(results)
    slug_ok = sum(1 for r in results if r.get("slug_ok"))
    id_ok = sum(1 for r in results if r.get("id_ok"))
    id_redirects = sum(1 for r in results if r.get("id_redirects"))

    print(f"  Toplam soru:           {total}")
    print(f"  Slug URL 200 OK:       {slug_ok}/{total} ({slug_ok * 100 // total}%)")
    print(f"  ID URL redirect (3xx): {id_redirects}/{total} ({id_redirects * 100 // total}%)")
    print(f"  ID URL final 200 OK:   {id_ok}/{total} ({id_ok * 100 // total}%)")
    print()

    # Başarısız olanları listele
    failed_slug = [r for r in results if not r.get("slug_ok")]
    failed_id = [r for r in results if not r.get("id_ok")]

    if failed_slug:
        print(f"  ✗ Slug URL başarısız ({len(failed_slug)}):")
        for r in failed_slug[:10]:
            print(f"    #{r.get('id')} [{r.get('category')}] {r.get('slug_url')} → {r.get('slug_status')}")

    if failed_id:
        print(f"\n  ✗ ID URL başarısız ({len(failed_id)}):")
        for r in failed_id[:10]:
            print(f"    #{r.get('id')} [{r.get('category')}] {r.get('id_url')} → {r.get('id_final_status')}")

    print()
    print(f"  Zaman: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Final verdict
    if slug_ok == total and id_ok == total:
        print(f"\n  ✅ TÜM URL'LER BAŞARILI — Canonical URL pattern tam çalışıyor")
        return 0
    else:
        print(f"\n  ⚠️  Bazı URL'ler başarısız — yukarıya bak")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Interview URL'lerini test et")
    parser.add_argument("--backend", default=BACKEND, help="Backend URL")
    parser.add_argument("--frontend", default=FRONTEND, help="Frontend URL")
    parser.add_argument("--sample", type=int, default=None, help="Sadece ilk N soru")
    parser.add_argument("--category", default=None, help="Sadece belirli kategori")
    parser.add_argument("--output", default=None, help="JSON çıktı dosyası")
    args = parser.parse_args()

    print("=" * 70)
    print("INTERVIEW URL TEST")
    print("=" * 70)
    print(f"  Backend:  {args.backend}")
    print(f"  Frontend: {args.frontend}")
    if args.sample:
        print(f"  Sample:   ilk {args.sample} soru")
    if args.category:
        print(f"  Filter:   kategori={args.category}")
    print()

    # 1. DB'den sorular
    questions = get_questions_from_db(args.backend)

    # Filtrele
    if args.category:
        questions = [q for q in questions if q.get("category") == args.category]
        print(f"      {args.category} kategorisinde {len(questions)} soru")

    # 2. Test et
    results = check_interviews(questions, args.frontend, args.sample)

    # 3. Özet
    exit_code = print_summary(results)

    # JSON çıktı
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "backend": args.backend,
                "frontend": args.frontend,
                "total": len(results),
                "results": results,
            }, f, ensure_ascii=False, indent=2)
        print(f"\n  Sonuçlar: {args.output}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()