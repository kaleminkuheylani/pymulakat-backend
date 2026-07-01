# services/question_scheduler.py
# Gemini ile otomatik soru üretimi — cron schedule.
# Railway'de veya FastAPI background scheduler ile çalışır.

import os
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Schedule storage — Supabase'de
# ═══════════════════════════════════════════════════════════

def get_supabase():
    from supabase_client import get_supabase_admin
    return get_supabase_admin()


def get_schedule() -> Dict:
    """Aktif schedule'ı getir. Yoksa default oluştur."""
    sb = get_supabase()
    try:
        result = sb.table("question_schedule").select("*").limit(1).execute()
        rows = result.data or []
        if rows:
            return rows[0]
    except Exception as e:
        logger.warning("Schedule getirilemedi: %s", e)

    # Default schedule
    default = {
        "enabled": False,
        "interval_days": 7,  # her 7 günde bir
        "n_questions": 5,    # her seferinde 5 soru
        "target_per_type": 12,
        "dry_run": False,
        "last_run_at": None,
        "next_run_at": None,
        "last_run_count": 0,
        "last_run_ids": [],
    }

    # INSERT
    try:
        sb.table("question_schedule").insert(default).execute()
    except Exception as e:
        logger.warning("Default schedule oluşturulamadı: %s", e)
    return default


def update_schedule(updates: Dict) -> Dict:
    """Schedule'ı güncelle."""
    sb = get_supabase()
    try:
        result = sb.table("question_schedule").select("id").limit(1).execute()
        rows = result.data or []
        if rows:
            sid = rows[0]["id"]
            sb.table("question_schedule").update(updates).eq("id", sid).execute()
        else:
            sb.table("question_schedule").insert(updates).execute()
        return get_schedule()
    except Exception as e:
        logger.exception("update_schedule failed: %s", e)
        return {}


def compute_next_run(interval_days: int) -> str:
    """Bir sonraki çalışma zamanını hesapla."""
    return (datetime.now(timezone.utc) + timedelta(days=interval_days)).isoformat()


# ═══════════════════════════════════════════════════════════
# Run logic — schedule tetiklendiğinde çalışır
# ═══════════════════════════════════════════════════════════

def run_scheduled_generation() -> Dict:
    """Schedule'a göre Gemini ile yeni sorular üret + DB'ye INSERT.

    Akış:
    1. Schedule'ı oku
    2. enabled değilse skip
    3. next_run_at <= now ise tetikle
    4. question_distribution modülünü kullan (zaten var)
    5. Supabase'e INSERT
    6. last_run_at + next_run_at güncelle
    """
    schedule = get_schedule()
    if not schedule.get("enabled"):
        return {"skipped": True, "reason": "schedule disabled"}

    # Zaman kontrolü
    next_run_str = schedule.get("next_run_at")
    if next_run_str:
        try:
            next_run = datetime.fromisoformat(next_run_str.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) < next_run:
                return {
                    "skipped": True,
                    "reason": f"next_run_at={next_run_str} henüz gelmedi",
                }
        except Exception as e:
            logger.warning("next_run_at parse error: %s", e)

    n = schedule.get("n_questions", 5)
    target_per_type = schedule.get("target_per_type", 12)
    dry_run = schedule.get("dry_run", False)

    try:
        result = _generate_and_insert(n, target_per_type, dry_run)
    except Exception as e:
        logger.exception("Scheduled generation failed: %s", e)
        return {"ok": False, "error": str(e)}

    # Schedule güncelle
    interval = schedule.get("interval_days", 7)
    update_schedule({
        "last_run_at": datetime.now(timezone.utc).isoformat(),
        "next_run_at": compute_next_run(interval),
        "last_run_count": len(result.get("inserted_ids", [])),
        "last_run_ids": result.get("inserted_ids", []),
    })

    return result


def _generate_and_insert(n: int, target_per_type: int, dry_run: bool) -> Dict:
    """Core generation + insert logic (admin endpoint'inden kopyalandı, sade)."""
    from services.question_distribution import (
        analyze_questions_py, identify_gaps,
        select_questions_to_generate, get_next_id,
        build_distribution_prompt,
    )
    from data.QUESTIONS import QUESTIONS as FALLBACK_QS

    # DB'den oku
    sb = get_supabase()
    try:
        db_questions = sb.table("interwiews").select(
            "id, title, category, level, test_cases"
        ).execute().data or []
    except Exception:
        db_questions = []

    # Dağılım analizi
    if db_questions:
        class _Q:
            def __init__(self, d):
                self.id = d.get("id", 0)
                self.title = d.get("title", "")
                self.category = d.get("category", "")
                self.level = d.get("level", "")
                self.test_cases = d.get("test_cases") or []
                self.starter_code = d.get("starter_code", "")
        qs = [_Q(d) for d in db_questions]
        distribution = analyze_questions_py(qs)
    else:
        distribution = analyze_questions_py(FALLBACK_QS)

    gaps = identify_gaps(distribution, target_per_type=target_per_type)
    plan = select_questions_to_generate(gaps, n=n)
    if not plan:
        return {"ok": False, "message": "no gaps", "gaps": gaps}

    # Sample
    sample = FALLBACK_QS[:1]
    if sample:
        q = sample[0]
        existing_questions_sample = (
            f'Question(id={q.id}, title={q.title!r}, category={q.category!r}, '
            f'level={q.level!r}, description="""...""", starter_code="""...""", '
            f'test_cases=[...], hints=["💡 ..."])'
        )
    else:
        existing_questions_sample = "(no sample)"

    # Prompt + Gemini
    prompt = build_distribution_prompt(plan, existing_questions_sample)
    from services.gemini import AIQuestionGenerator
    import google.generativeai as genai_mod
    gen = AIQuestionGenerator()

    try:
        response = gen.model.generate_content(
            prompt,
            generation_config=genai_mod.GenerationConfig(
                response_mime_type="application/json"
            ),
        )
        raw_text = response.text.strip()
        import re
        raw_text = re.sub(r"^```(?:json)?\s*\n?", "", raw_text, flags=re.IGNORECASE)
        raw_text = re.sub(r"\n?```\s*$", "", raw_text, flags=re.IGNORECASE)
        raw_text = raw_text.strip()

        generated = json.loads(raw_text)
        if isinstance(generated, dict):
            generated = [generated]
    except Exception as e:
        return {"ok": False, "error": f"Gemini: {e}"}

    # Validate + ID ata
    existing_ids = distribution["existing_ids"]
    next_id = get_next_id(existing_ids)

    valid = []
    for item in generated:
        if not all(k in item for k in ("title", "category", "level", "description",
                                        "starter_code", "test_cases", "hints")):
            continue
        item["id"] = next_id
        next_id += 1
        item.setdefault("complexity", "O(n)")
        item.setdefault("tutorial_slug", None)
        item.setdefault("slug", None)
        item.pop("output_type", None)
        valid.append(item)

    # Mevcut slug'ları oku
    try:
        existing_slugs_res = sb.table("interwiews").select("slug").execute()
        existing_slugs = {r["slug"] for r in (existing_slugs_res.data or []) if r.get("slug")}
    except Exception:
        existing_slugs = set()

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "generated": valid,
            "next_id": next_id,
        }

    # INSERT
    inserted_ids = []
    for item in valid:
        try:
            item.setdefault("day", 1)
            item.setdefault("week", 1)
            item.setdefault("theme", item["category"])
            item.setdefault("difficulty", "medium")
            item.setdefault("related_concepts", [])
            item.setdefault("related_question_ids", [])
            if not item.get("slug"):
                from services.slug_helper import slugify_tr
                try:
                    base = slugify_tr(item["title"])
                except Exception:
                    import re as _re
                    base = _re.sub(r"[^a-z0-9]+", "-", item["title"].lower()).strip("-")[:80]
                base = base.replace("ı", "i").replace("ğ", "g").replace("ü", "u").replace("ş", "s").replace("ö", "o").replace("ç", "c")
                slug_candidate = f"{base}-{item['id']}" if base else f"q{item['id']}"
                counter = 1
                final = slug_candidate
                while final in existing_slugs:
                    final = f"{slug_candidate}-{counter}"
                    counter += 1
                item["slug"] = final
                existing_slugs.add(final)

            result = sb.table("interwiews").insert(item).execute()
            if result.data:
                inserted_ids.append(item["id"])
        except Exception as e:
            logger.exception("Insert q%d: %s", item.get("id"), e)

    return {
        "ok": True,
        "inserted_ids": inserted_ids,
        "count": len(inserted_ids),
    }