#!/usr/bin/env python3
"""DB'den sitemap.xml ureten script.

Direct Supabase'den okur, XML formatinda sitemap.xml yazar, FTP/HEAD request ile
arama motoruna ping atar.

Kullanim:
    # Production (Railway cron)
    python3 scripts/generate_sitemap.py

    # Local (env ile)
    SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... \
        python3 scripts/generate_sitemap.py

    # Dry run
    python3 scripts/generate_sitemap.py --dry-run

Sitemap yapisi:
- Statik sayfalar (home, interviews, guides, about, terms)
- Kategoriler (questions tablosundan unique)
- Soru detay sayfalari (slug-based canonical URL)
- Tutorial sayfalari (tutorials tablosu, varsa)
"""

import argparse
import asyncio
import json
import os
import re
import sys
import unicodedata
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any
import xml.etree.ElementTree as ET


# ═══════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════

FRONTEND_BASE = "https://pythonmulakat.com"
SITEMAP_URLS = [
    ("/", "daily", 1.0),
    ("/interviews", "daily", 0.9),
    ("/guides", "weekly", 0.85),
    ("/about", "monthly", 0.7),
    ("/login", "monthly", 0.5),
    ("/register", "monthly", 0.6),
    ("/terms", "yearly", 0.3),
    ("/profile", "monthly", 0.4),
    ("/dashboard", "monthly", 0.5),
    ("/dashboard/forms", "daily", 0.6),
    ("/dashboard/recommendations", "daily", 0.6),
]

# Header for sitemap.xml
SITEMAP_HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
                            http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
"""

SITEMAP_FOOTER = "</urlset>\n"


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def slugify_local(text: str) -> str:
    """Slugify (Turkce + ASCII normalize)."""
    s = text.lower()
    tr = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    s = s.translate(tr)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:80] or "question"


def fetch_url(url: str, timeout: int = 8) -> tuple[int, str]:
    """URL'den HTTP status don."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "pythonmulakat-sitemap-generator/1.0",
            "Accept": "*/*",
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, ""
    except urllib.error.HTTPError as e:
        return e.code, str(e)[:200]
    except urllib.error.URLError as e:
        return -1, f"URLError: {e.reason}"
    except Exception as e:
        return -2, str(e)[:200]


def ping_search_engine(sitemap_url: str) -> Dict[str, int]:
    """Google ve Bing'e sitemap guncellemesi bildir."""
    results = {}
    ping_urls = [
        ("Google", f"https://www.google.com/ping?sitemap={sitemap_url}"),
        ("Bing", f"https://www.bing.com/ping?sitemap={sitemap_url}"),
    ]
    for engine, url in ping_urls:
        status, msg = fetch_url(url, timeout=8)
        results[engine] = status
        print(f"  Ping {engine}: {status}")
    return results


# ═══════════════════════════════════════════════════════════════
# Data sources
# ═══════════════════════════════════════════════════════════════

def get_supabase_client_or_exit():
    """Supabase client'i kur, yoksa exit."""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL veya SUPABASE_SERVICE_ROLE_KEY env gerekli")
        sys.exit(1)

    try:
        from supabase import create_client
        return create_client(supabase_url, supabase_key)
    except ImportError:
        print("❌ supabase-py yuklu degil: pip install supabase")
        sys.exit(1)


def get_questions_from_db(sb) -> List[Dict[str, Any]]:
    """DB'den sorulari al."""
    try:
        # Once schema cache kontrolu
        sb.table("questions").select("id").limit(1).execute()
        result = sb.table("questions").select(
            "id, slug, category, title, updated_at, is_published"
        ).eq("is_published", True).order("id").execute()
        return result.data or []
    except Exception as e:
        print(f"⚠️ DB'den soru cekilemedi: {e}")
        return []


def get_tutorials_from_db(sb) -> List[Dict[str, Any]]:
    """Tutorial varsa DB'den al (graceful fail)."""
    try:
        result = sb.table("tutorials").select("slug, updated_at, published_at, is_published").eq("is_published", True).execute()
        return result.data or []
    except Exception:
        # Tablo yoksa skip
        return []


def get_question_urls_from_v3() -> List[Dict[str, Any]]:
    """QUESTIONS-v3.py fallback (DB erisim yoksa)."""
    import importlib.util
    v3_path = Path(__file__).parent.parent / "data" / "QUESTIONS-v3.py"
    spec = importlib.util.spec_from_file_location("v3_fallback", v3_path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        print(f"⚠️ QUESTIONS-v3.py yuklenemedi: {e}")
        return []

    rows = []
    for q in mod.QUESTIONS:
        rows.append({
            "id": getattr(q, "id", 0),
            "slug": slugify_local(getattr(q, "title", "")),
            "category": getattr(q, "category", "python-basics"),
            "title": getattr(q, "title", ""),
            "updated_at": None,
            "is_published": True,
        })
    return rows


# ═══════════════════════════════════════════════════════════════
# Sitemap generation
# ═══════════════════════════════════════════════════════════════

def build_sitemap_xml(rows: List[Dict[str, Any]], tutorials: List[Dict[str, Any]]) -> str:
    """Sitemap XML içerigi uret (frontend sitemap.ts ile uyumlu format)."""
    now_iso = datetime.now(timezone.utc).isoformat()
    urls = []

    # Statik sayfalar
    for path, freq, prio in SITEMAP_URLS:
        urls.append({
            "loc": f"{FRONTEND_BASE}{path}",
            "lastmod": now_iso,
            "changefreq": freq,
            "priority": f"{prio:.1f}",
        })

    # Sorular (slug-based canonical)
    for r in rows:
        slug = r.get("slug")
        category = r.get("category")
        if not slug or not category:
            continue
        urls.append({
            "loc": f"{FRONTEND_BASE}/interviews/{category}/{slug}",
            "lastmod": r.get("updated_at") or now_iso,
            "changefreq": "weekly",
            "priority": "0.7",
        })

    # Tutorial sayfalari
    for t in tutorials:
        slug = t.get("slug")
        if not slug:
            continue
        updated = t.get("updated_at") or t.get("published_at") or now_iso
        urls.append({
            "loc": f"{FRONTEND_BASE}/guides/{slug}",
            "lastmod": updated,
            "changefreq": "weekly",
            "priority": "0.65",
        })

    # XML olustur
    root = ET.Element("urlset")
    root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    for u in urls:
        url_el = ET.SubElement(root, "url")
        ET.SubElement(url_el, "loc").text = u["loc"]
        ET.SubElement(url_el, "lastmod").text = u["lastmod"]
        ET.SubElement(url_el, "changefreq").text = u["changefreq"]
        ET.SubElement(url_el, "priority").text = u["priority"]

    # Pretty print
    ET.indent(root, space="  ")
    xml_str = ET.tostring(root, encoding="unicode", xml_declaration=False)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str + "\n"


def write_sitemap_to_db(sb, xml_content: str, url_count: int) -> bool:
    """Sitemap.xml'i DB'nin 'meta' tablosuna yaz (opsiyonel cache)."""
    try:
        sb.table("sitemap_cache").upsert({
            "key": "main",
            "content": xml_content,
            "url_count": url_count,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }, on_conflict="key").execute()
        return True
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Sitemap generator (DB-based, Railway cron-ready)")
    parser.add_argument("--dry-run", action="store_true", help="Sitemap uret ama yazma")
    parser.add_argument("--ping", action="store_true", help="Google/Bing'e ping at")
    parser.add_argument("--output", default="/tmp/sitemap.xml", help="Cikti dosya yolu")
    parser.add_argument("--fallback-v3", action="store_true", help="DB yoksa QUESTIONS-v3.py fallback")
    args = parser.parse_args()

    print("=" * 70)
    print("SITEMAP GENERATOR")
    print("=" * 70)

    # 1. Data source
    print("\n[1/4] Veri kaynagi seciliyor...")
    sb = None
    rows = []
    tutorials = []

    # Once DB dene
    try:
        sb = get_supabase_client_or_exit()
        rows = get_questions_from_db(sb)
        tutorials = get_tutorials_from_db(sb)
        print(f"  DB'den {len(rows)} soru, {len(tutorials)} tutorial")
    except SystemExit:
        if not args.fallback_v3:
            raise

    if not rows:
        if args.fallback_v3:
            rows = get_question_urls_from_v3()
            print(f"  V3 fallback: {len(rows)} soru")
        else:
            print("❌ DB erisim yok, --fallback-v3 ekleyerek tekrar deneyin")
            sys.exit(1)

    if not rows:
        print("❌ Soru bulunamadi")
        sys.exit(1)

    # 2. Sitemap XML uret
    print("\n[2/4] Sitemap XML uretiliyor...")
    xml = build_sitemap_xml(rows, tutorials)

    url_count = rows.count("")
    # Gercek URL sayisi
    from xml.etree.ElementTree import fromstring
    parsed = fromstring(xml)
    url_count = len(parsed.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}url"))

    print(f"  {url_count} URL eklendi")
    print(f"  Boyut: {len(xml)} bytes")

    # 3. Yaz
    print("\n[3/4] Cikti yaziliyor...")
    if args.dry_run:
        print("  [DRY RUN] Dosyaya yazmadi")
        # Ilk 500 karakteri goster
        print("  Preview:")
        print("  " + xml[:500].replace("\n", "\n  "))
    else:
        try:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(xml)
            print(f"  Dosya yazildi: {output_path}")
            print(f"  Boyut: {output_path.stat().st_size} bytes")
        except Exception as e:
            print(f"  ❌ Dosya yazma hatasi: {e}")
            sys.exit(1)

    # DB cache (opsiyonel, content hash ile versiyon)
    if sb is not None and not args.dry_run:
        import hashlib
        xml_hash = hashlib.md5(xml.encode()).hexdigest()[:12]
        old_hash = None
        try:
            old = sb.table("sitemap_cache").select("content_hash").eq("key", "main").execute()
            if old.data:
                old_hash = old.data[0].get("content_hash")
        except Exception:
            pass

        # Yeni content_hash ile yaz
        try:
            sb.table("sitemap_cache").upsert({
                "key": "main",
                "content": xml,
                "content_hash": xml_hash,
                "url_count": url_count,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }, on_conflict="key").execute()
            print(f"  DB cache guncelledi (hash: {xml_hash})")
        except Exception as e:
            print(f"  ⚠️ DB cache write hatasi: {e}")

        # Ping sadece hash degisti ise
        if old_hash and old_hash == xml_hash:
            print(f"  Content hash ayni, ping atlanacak (skip)")
        else:
            args.ping = True

    # 4. Ping (opsiyonel)
    if args.ping and not args.dry_run:
        print("\n[4/4] Arama motoru ping")
        sitemap_url = f"{FRONTEND_BASE}/sitemap.xml"
        results = ping_search_engine(sitemap_url)
        success = sum(1 for s in results.values() if s == 200)
        print(f"  {success}/{len(results)} basarili")

    print("\n" + "=" * 70)
    print("OZET")
    print("=" * 70)
    print(f"Sorular: {len(rows)}")
    print(f"Tutorials: {len(tutorials)}")
    print(f"Toplam URL: {url_count}")
    print(f"Frontende deploy: {'/tmp/sitemap.xml' if args.dry_run else args.output}")


if __name__ == "__main__":
    main()
