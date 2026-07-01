# services/reports.py
# Kişisel hata raporları — 7 günlük retention, user_id scoped.
# Her attempt için rapor satırı: hangi hata, hangi kategoride, ne zaman.
# ±5dk korelasyon, skill graph bağlantısı.

import logging
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from supabase_client import get_supabase_admin
from .error_analyzer import (
    classify_error, difficulty_of_error, correlate_nearby_errors,
    CATEGORY_LABELS_TR, ErrorCategory,
)

logger = logging.getLogger(__name__)

# 7 gün retention
RETENTION_DAYS = 7


def _supabase():
    return get_supabase_admin()


# ── Attempt → Report dönüşümü ────────────────────────────

def build_report_from_attempt(attempt: Dict, question_topics: List[str] = None) -> Dict:
    """
    Bir interview_attempts satırından coach_reports satırı oluştur.
    Başarısız attempt'ler için error_text oluşturulur (kullanıcının user_code'undan).
    """
    user_code = attempt.get("user_code") or ""
    passed = attempt.get("passed_tests", 0)
    total = attempt.get("total_tests", 0)
    success = attempt.get("success", False)

    if success:
        error_text = None
        category, label = ("success", "Başarılı")
        difficulty = 0
    else:
        # Synthetic error_text — user_code'dan inferred
        # (gerçek hata mesajı Pyodide'den gelir ama bizde yok, heuristic kullanıyoruz)
        error_text = attempt.get("error_text") or _synthesize_error_text(user_code, passed, total)
        category, label = classify_error(error_text, user_code)
        difficulty = difficulty_of_error(category)

    return {
        "id": str(uuid.uuid4()),
        "user_id": attempt["user_id"],
        "attempt_id": str(attempt.get("id", "")),
        "question_id": attempt.get("question_id"),
        "category": category,
        "category_label": label,
        "difficulty": difficulty,
        "error_text": error_text,
        "user_code_excerpt": (user_code[:200] + "...") if len(user_code) > 200 else user_code,
        "passed": passed,
        "total": total,
        "success": success,
        "topics": question_topics or [],
        "created_at": attempt.get("created_at") or datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=RETENTION_DAYS)).isoformat(),
    }


def _synthesize_error_text(user_code: str, passed: int, total: int) -> str:
    """Gerçek Pyodide output'u elimizde yok, basit heuristic."""
    if not user_code.strip() or user_code.strip() == "pass":
        return "Boş kod — sadece 'pass' var"
    if passed == 0 and total > 0:
        return f"Tüm {total} test başarısız — temel çözüm eksik"
    if passed > 0 and passed < total:
        return f"{passed}/{total} test geçti — bazı edge case'lerde hata"
    return f"Bilinmeyen hata — {passed}/{total} geçti"


# ── Reports kaydetme (cron'da çağrılır) ─────────────────

def upsert_reports_from_attempts(user_id: str, days: int = 1) -> int:
    """
    Son `days` gündeki attempt'leri oku, report oluştur, yaz.
    user_id scoped — başka kullanıcı göremez.
    """
    sb = _supabase()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    # Yeni attempt'leri çek
    try:
        result = (
            sb.table("interview_attempts")
            .select("*")
            .eq("user_id", user_id)
            .gte("created_at", cutoff)
            .execute()
        )
        attempts = result.data or []
    except Exception as e:
        logger.exception("reports.fetch failed user=%s", user_id)
        return 0

    # Mevcut report'ları kontrol et (idempotent)
    try:
        existing = (
            sb.table("coach_reports")
            .select("attempt_id")
            .eq("user_id", user_id)
            .execute()
        )
        existing_attempt_ids = {r["attempt_id"] for r in (existing.data or [])}
    except Exception:
        existing_attempt_ids = set()

    # Her attempt için topic'leri batch-fetch (cached)
    cache: Dict[int, List[str]] = {}
    def get_topics(qid: int) -> List[str]:
        if qid in cache:
            return cache[qid]
        try:
            res = sb.table("interwiews").select("topics").eq("id", qid).execute()
            topics = (res.data[0].get("topics") or []) if res.data else []
        except Exception:
            topics = []
        cache[qid] = topics
        return topics

    new_reports = []
    for a in attempts:
        aid = str(a.get("id", ""))
        if aid in existing_attempt_ids:
            continue
        topics = get_topics(a.get("question_id", 0))
        report = build_report_from_attempt(a, topics)
        new_reports.append(report)

    if not new_reports:
        return 0

    # Batch insert
    try:
        sb.table("coach_reports").insert(new_reports).execute()
        return len(new_reports)
    except Exception as e:
        logger.exception("reports.insert failed user=%s count=%d", user_id, len(new_reports))
        return 0


# ── 7 günlük retention cleanup ─────────────────────────

def cleanup_expired_reports() -> int:
    """Süresi dolmuş report'ları sil (cron)."""
    sb = _supabase()
    try:
        cutoff = datetime.now(timezone.utc).isoformat()
        result = (
            sb.table("coach_reports")
            .delete()
            .lt("expires_at", cutoff)
            .execute()
        )
        count = len(result.data or []) if result.data else 0
        if count:
            logger.info("reports.cleanup deleted=%d", count)
        return count
    except Exception as e:
        logger.exception("reports.cleanup failed")
        return 0


# ── Dashboard data aggregation ─────────────────────────

def get_user_dashboard_data(user_id: str) -> Dict:
    """
    Kullanıcının dashboard verisi:
    - Son 7 gün hata özeti (kategori dağılımı)
    - En sık yapılan hatalar
    - Skill graph progress (her topic için)
    - ±5dk korelasyon kümeleri
    - Trend (bugün vs dün vs geçen hafta)
    - Recent attempts (son 10)
    - Lint (skill graph tutarlılık)
    """
    sb = _supabase()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)).isoformat()

    # Reports son 7 gün
    try:
        res = (
            sb.table("coach_reports")
            .select("*")
            .eq("user_id", user_id)
            .gte("created_at", cutoff)
            .order("created_at", desc=True)
            .execute()
        )
        reports = res.data or []
    except Exception:
        reports = []

    if not reports:
        # Hala attempts'ten oluşturmamız gerekebilir
        upsert_reports_from_attempts(user_id, days=RETENTION_DAYS)
        try:
            res = (
                sb.table("coach_reports")
                .select("*")
                .eq("user_id", user_id)
                .gte("created_at", cutoff)
                .order("created_at", desc=True)
                .execute()
            )
            reports = res.data or []
        except Exception:
            reports = []

    # ── Kategori dağılımı ──
    cat_counter = Counter(r["category"] for r in reports if not r.get("success"))
    category_breakdown = []
    for cat, count in cat_counter.most_common():
        category_breakdown.append({
            "category": cat,
            "label": CATEGORY_LABELS_TR.get(cat, cat),
            "count": count,
            "pct": round(100 * count / max(sum(cat_counter.values()), 1)),
        })

    # ── En sık yapılan hatalar (top 5) ──
    top_errors = [
        {"category": e["category"], "label": e["category_label"], "count": c, "difficulty": e["difficulty"]}
        for e, c in [(r, cat_counter[r["category"]]) for r in reports]
    ][:5]

    # ── Skill graph progress ──
    skill_progress = _aggregate_skill_progress(reports)

    # ── ±5dk korelasyon ──
    nearby = correlate_nearby_errors(reports, window_minutes=5)

    # ── Trend (bugün / dün / bu hafta) ──
    now = datetime.now(timezone.utc)
    today = [r for r in reports if _iso_to_dt(r["created_at"]).date() == now.date()]
    yesterday = [r for r in reports if _iso_to_dt(r["created_at"]).date() == (now - timedelta(days=1)).date()]
    last_week = [r for r in reports if _iso_to_dt(r["created_at"]).date() >= (now - timedelta(days=7)).date()]

    trend = {
        "today": {"attempts": len(today), "errors": len([r for r in today if not r["success"]])},
        "yesterday": {"attempts": len(yesterday), "errors": len([r for r in yesterday if not r["success"]])},
        "this_week": {"attempts": len(last_week), "errors": len([r for r in last_week if not r["success"]])},
    }

    # ── Son attempt'ler ──
    recent = []
    for r in reports[:10]:
        qid = r.get("question_id")
        qtitle = None
        if qid:
            try:
                qres = sb.table("interwiews").select("title").eq("id", qid).execute()
                qtitle = qres.data[0]["title"] if qres.data else None
            except Exception:
                pass
        recent.append({
            "id": r["id"],
            "question_id": qid,
            "question_title": qtitle,
            "category": r["category"],
            "category_label": r["category_label"],
            "success": r["success"],
            "passed": r["passed"],
            "total": r["total"],
            "created_at": r["created_at"],
        })

    # ── Lint durumu (skill graph tutarlılık, kullanıcıya SADE bilgi) ──
    from .skills_lint import lint_quick
    lint_ok, orphan_topics = lint_quick()
    lint_summary = {
        "ok": lint_ok,
        "orphan_topics_count": len(orphan_topics),
        "message": "Tüm topic'ler sorularda kullanılıyor" if lint_ok else f"{len(orphan_topics)} topic hiçbir soruda kullanılmıyor (admin'e bildirildi)",
    }

    return {
        "retention_days": RETENTION_DAYS,
        "category_breakdown": category_breakdown,
        "top_errors": top_errors,
        "skill_progress": skill_progress,
        "nearby_clusters": [
            {"size": len(c), "from": c[0]["created_at"], "to": c[-1]["created_at"], "categories": list(set(r["category"] for r in c))}
            for c in nearby[:5]
        ],
        "trend": trend,
        "recent": recent,
        "lint": lint_summary,
    }


def _aggregate_skill_progress(reports: List[Dict]) -> Dict[str, Dict]:
    """Skill graph progress — topics bazında attempt/error count."""
    progress: Dict[str, Dict[str, int]] = {}
    for r in reports:
        for t in r.get("topics") or []:
            d = progress.setdefault(t, {"attempted": 0, "solved": 0, "errors": 0})
            d["attempted"] += 1
            if r.get("success"):
                d["solved"] += 1
            else:
                d["errors"] += 1
    return progress


def _iso_to_dt(iso: str) -> datetime:
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)