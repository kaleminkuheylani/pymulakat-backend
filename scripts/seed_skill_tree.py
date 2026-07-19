#!/usr/bin/env python3
"""Seed related_concepts for questions from data/QUESTIONS.py into Supabase.

Requires environment variables:
    SUPABASE_URL       Supabase project URL
    SUPABASE_ANON_KEY  Supabase anon key (write permission must be allowed by RLS)

Matches local data.QUESTIONS entries to DB rows by normalized title and PATCHes
questions.related_concepts. Idempotent: re-runs overwrite the same values.
"""
import csv
import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path


SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")


def normalize(text: str) -> str:
    s = text or ""
    return "".join(c for c in s.strip().lower() if c.isalnum())


def api_request(method: str, path: str, body: bytes | None = None) -> urllib.request.addinfourl:
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise RuntimeError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Prefer": "return=minimal",
        },
    )
    return urllib.request.urlopen(req, timeout=30)


def main() -> int:
    scripts_dir = Path(__file__).resolve().parent
    backend_dir = scripts_dir.parent
    sys.path.insert(0, str(backend_dir))

    try:
        from data.QUESTIONS import QUESTIONS
    except Exception as e:
        print(f"Could not import data.QUESTIONS: {e}")
        return 1

    # data.QUESTIONS id -> related_concepts
    id_to_concepts: dict[int, list[str]] = {
        q.id: q.related_concepts for q in QUESTIONS if q.related_concepts
    }

    # CSV maps id -> slug
    csv_path = backend_dir / "data" / "QUESTIONS-v3.csv"
    local_map: dict[str, list[str]] = {}
    try:
        with open(csv_path, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                raw_id = (row.get("id") or "").strip()
                slug = (row.get("slug") or "").strip()
                if raw_id.isdigit() and slug:
                    concepts = id_to_concepts.get(int(raw_id))
                    if concepts:
                        local_map[slug] = concepts
    except Exception as e:
        print(f"Could not read CSV: {e}")
        return 1

    # Fetch DB rows
    try:
        res = api_request("GET", "questions?select=id,slug&limit=500")
        db_rows = json.loads(res.read())
    except urllib.error.HTTPError as e:
        print(f"DB fetch failed: {e.code} {e.read().decode()[:200]}")
        return 1

    matched = 0
    patched = 0
    failed = 0
    for row in db_rows:
        slug = row.get("slug", "").strip()
        if not slug or slug not in local_map:
            continue
        matched += 1
        payload = json.dumps({"related_concepts": local_map[slug]}).encode()
        try:
            api_request("PATCH", f"questions?id=eq.{row['id']}", payload)
            patched += 1
            print(f"  patched id={row['id']} slug={slug} concepts={len(local_map[slug])}")
        except urllib.error.HTTPError as e:
            failed += 1
            print(f"  FAILED id={row['id']}: {e.code} {e.read().decode()[:200]}")

    print(f"\nSummary: local_questions={len(id_to_concepts)}, csv_keys={len(local_map)}, db={len(db_rows)}, matched={matched}, patched={patched}, failed={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
