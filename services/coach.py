# services/coach.py
# Kural tabanlı email koçu — AI YOK.
# Her kullanıcının attempt/success pattern'ini analiz edip,
# uygun email template'i tetikler.

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple

from .coach_templates import (
    first_solve, milestone, streak, inactive,
    difficulty_progression, new_category, category_struggle,
    id_chain_recommendation, concept_gap, gentle_nudge,
    BRAND,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
# Veri toplama (Supabase'den, servis_admin ile)
# ═══════════════════════════════════════════════════════════

def _supabase():
    """Lazy import — circular dependency'yi önler."""
    from supabase_client import get_supabase_admin
    return get_supabase_admin()


@dataclass
class UserActivity:
    """Bir kullanıcının tüm analiz için gerekli verileri."""
    user_id: str
    email: str
    username: str
    points: int
    created_at: Optional[str]
    last_active: Optional[datetime]
    attempts: List[Dict[str, Any]]   # tüm interview_attempts satırları
    solved_ids: List[int]            # başarıyla çözülen question_id'ler
    attempted_ids: List[int]         # denenmiş (başarılı+başarısız)
    failed_ids: List[int]            # başarısız denemeler

    @property
    def total_solved(self) -> int:
        return len(self.solved_ids)

    @property
    def total_attempted(self) -> int:
        return len(set(self.attempted_ids))

    @property
    def days_since_active(self) -> int:
        if not self.last_active:
            return 999
        now = datetime.now(timezone.utc)
        diff = (now - self.last_active).days
        return max(diff, 0)


def load_user_activity(user_id: str) -> Optional[UserActivity]:
    """Bir kullanıcının tüm attempt + profile bilgisini çek."""
    sb = _supabase()
    try:
        prof = sb.table("profiles").select("*").eq("id", user_id).execute()
        if not prof.data:
            return None
        profile = prof.data[0]
        atts = (
            sb.table("interview_attempts")
            .select("question_id, success, passed_tests, total_tests, created_at, hints_used")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        attempts = atts.data or []
        solved = list({a["question_id"] for a in attempts if a.get("success")})
        attempted = list({a["question_id"] for a in attempts})
        failed = list({a["question_id"] for a in attempts if not a.get("success")})
        last_active = None
        if attempts:
            try:
                last_active = datetime.fromisoformat(attempts[0]["created_at"].replace("Z", "+00:00"))
            except Exception:
                pass
        return UserActivity(
            user_id=user_id,
            email=profile.get("email", ""),
            username=profile.get("username", "user"),
            points=profile.get("points", 0) or 0,
            created_at=profile.get("created_at"),
            last_active=last_active,
            attempts=attempts,
            solved_ids=sorted(solved),
            attempted_ids=sorted(attempted),
            failed_ids=sorted(failed),
        )
    except Exception as e:
        logger.exception("load_user_activity failed user=%s", user_id)
        return None


def load_all_active_users(days_window: int = 30) -> List[Dict]:
    """Son N gün içinde aktivitesi olan kullanıcıları getir."""
    sb = _supabase()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days_window)).isoformat()
    try:
        result = (
            sb.table("interview_attempts")
            .select("user_id")
            .gte("created_at", cutoff)
            .execute()
        )
        user_ids = list({r["user_id"] for r in (result.data or [])})
        if not user_ids:
            return []
        profs = sb.table("profiles").select("id, email, username, points").in_("id", user_ids).execute()
        return profs.data or []
    except Exception as e:
        logger.exception("load_all_active_users failed")
        return []


# ═══════════════════════════════════════════════════════════
# Question/tutorial yardımcıları
# ═══════════════════════════════════════════════════════════

def get_question(qid: int) -> Optional[Dict[str, Any]]:
    sb = _supabase()
    try:
        res = sb.table("interwiews").select("*").eq("id", qid).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None


def get_questions_by_category(category: str, limit: int = 5) -> List[Dict]:
    sb = _supabase()
    try:
        res = (
            sb.table("interwiews")
            .select("id, title, category, level, slug, difficulty, related_concepts")
            .eq("category", category)
            .limit(limit)
            .execute()
        )
        return res.data or []
    except Exception:
        return []


def get_tutorial_by_slug(slug: str) -> Optional[Dict]:
    sb = _supabase()
    try:
        res = sb.table("tutorials").select("*").eq("slug", slug).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None


def get_tutorial_for_concept(concept: str) -> Optional[Dict]:
    """Kavrama göre tutorial bul (related_concepts veya title içinde arar)."""
    sb = _supabase()
    try:
        res = (
            sb.table("tutorials")
            .select("*")
            .or_(f"title.ilike.%{concept}%,description.ilike.%{concept}%")
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════
# Kural motoru — her kural bir fonksiyon
# ═══════════════════════════════════════════════════════════

# Frequency cap: aynı kural için bir kullanıcıya 7 günde max 1 mail
FREQ_CAP_DAYS = 7
RECENT_SENT_KEY = "coach_recent_sent"  # Supabase'de profiles tablosuna eklenebilir

# Her kategorideki toplam soru sayısı (basit harita, gerçek DB'den çekilebilir)
CATEGORY_TOTALS = {
    "python-basics": 24, "strings": 12, "list-dict": 14, "algorithms": 18,
    "oop": 10, "data-types": 8, "pandas": 12, "numpy": 6,
    "sklearn": 8, "matplotlib": 5,
}

ALL_CATEGORIES = list(CATEGORY_TOTALS.keys())


def _user_recently_mailed(user_id: str, rule_name: str) -> bool:
    """Aynı kural için son 7 gün içinde mail gitti mi kontrol et."""
    sb = _supabase()
    try:
        prof = sb.table("profiles").select("coach_recent_sent").eq("id", user_id).execute()
        if not prof.data:
            return False
        recent = prof.data[0].get("coach_recent_sent") or {}
        last_iso = recent.get(rule_name)
        if not last_iso:
            return False
        last = datetime.fromisoformat(last_iso.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - last).days < FREQ_CAP_DAYS
    except Exception:
        return False


def _mark_mailed(user_id: str, rule_name: str) -> None:
    sb = _supabase()
    try:
        prof = sb.table("profiles").select("coach_recent_sent").eq("id", user_id).execute()
        recent = (prof.data[0].get("coach_recent_sent") or {}) if prof.data else {}
        recent[rule_name] = datetime.now(timezone.utc).isoformat()
        # Eski kayıtları temizle (>30 gün)
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        for k in list(recent.keys()):
            try:
                t = datetime.fromisoformat(recent[k].replace("Z", "+00:00"))
                if t < cutoff:
                    del recent[k]
            except Exception:
                pass
        sb.table("profiles").update({"coach_recent_sent": recent}).eq("id", user_id).execute()
    except Exception as e:
        logger.warning("mark_mailed failed user=%s: %s", user_id, e)


def _calc_streak_days(attempts: List[Dict]) -> int:
    """Attempt tarihlerinden ardışık gün streak'i hesapla."""
    if not attempts:
        return 0
    days = set()
    for a in attempts:
        try:
            d = datetime.fromisoformat(a["created_at"].replace("Z", "+00:00")).date()
            days.add(d)
        except Exception:
            pass
    streak = 0
    today = datetime.now(timezone.utc).date()
    cur = today
    while cur in days:
        streak += 1
        cur -= timedelta(days=1)
    return streak


def _by_category(attempts: List[Dict]) -> Dict[str, Dict[str, int]]:
    """Attempt'leri kategori bazında grupla (success/fail/count)."""
    # qid → question (cached)
    cache: Dict[int, Dict] = {}
    out: Dict[str, Dict[str, int]] = {}
    for a in attempts:
        qid = a.get("question_id")
        if qid not in cache:
            cache[qid] = get_question(qid) or {}
        q = cache[qid]
        cat = q.get("category") or "unknown"
        d = out.setdefault(cat, {"total": 0, "success": 0, "fail": 0})
        d["total"] += 1
        if a.get("success"):
            d["success"] += 1
        else:
            d["fail"] += 1
    return out


def _by_level(attempts: List[Dict]) -> Dict[str, set]:
    cache: Dict[int, Dict] = {}
    out: Dict[str, set] = {}
    for a in attempts:
        qid = a.get("question_id")
        if qid not in cache:
            cache[qid] = get_question(qid) or {}
        q = cache[qid]
        lvl = (q.get("level") or "unknown").lower()
        bucket = out.setdefault(lvl, set())
        if a.get("success"):
            bucket.add(qid)
    return out


# ═══════════════════════════════════════════════════════════
# Ana kural fonksiyonları (her biri dict[str, Any] döner veya None)
# ═══════════════════════════════════════════════════════════

def rule_first_solve(act: UserActivity) -> Optional[Dict[str, Any]]:
    if act.total_solved != 1:
        return None
    q = get_question(act.solved_ids[0])
    if not q:
        return None
    return {"rule": "first_solve", "email": first_solve({"username": act.username}, q), "user": {"id": act.user_id, "email": act.email}}


def rule_milestone(act: UserActivity) -> Optional[Dict[str, Any]]:
    MILESTONES = [10, 25, 50, 100]
    for m in MILESTONES:
        if act.total_solved == m:
            return {"rule": f"milestone_{m}", "email": milestone({"username": act.username}, m, m * 2),
                    "user": {"id": act.user_id, "email": act.email}}
    return None


def rule_streak(act: UserActivity) -> Optional[Dict[str, Any]]:
    streak = _calc_streak_days(act.attempts)
    if streak in (7, 14, 30, 60, 100):
        return {"rule": f"streak_{streak}", "email": streak({"username": act.username}, streak),
                "user": {"id": act.user_id, "email": act.email}}
    return None


def rule_inactive(act: UserActivity) -> Optional[Dict[str, Any]]:
    days = act.days_since_active
    if days < 7:
        return None
    # Suggest highest-difficulty unsolved question
    suggestion = None
    candidates = get_questions_by_category("python-basics", limit=10)
    for q in candidates:
        if q["id"] not in act.solved_ids:
            suggestion = q
            break
    return {"rule": f"inactive_{days}d", "email": inactive({"username": act.username}, days, suggestion),
            "user": {"id": act.user_id, "email": act.email}}


def rule_difficulty_progression(act: UserActivity) -> Optional[Dict[str, Any]]:
    by_level = _by_level(act.attempts)
    beginner_solved = len(by_level.get("beginner", set()) | by_level.get("başlangıç", set()))
    intermediate_attempted = bool(by_level.get("intermediate") or by_level.get("orta"))
    beginner_total = 15
    if beginner_solved >= beginner_total * 0.8 and not intermediate_attempted:
        return {"rule": "difficulty_progression",
                "email": difficulty_progression({"username": act.username}, beginner_solved, beginner_total),
                "user": {"id": act.user_id, "email": act.email}}
    return None


def rule_new_category(act: UserActivity) -> Optional[Dict[str, Any]]:
    by_cat = _by_category(act.attempts)
    attempted_cats = set(by_cat.keys())
    for cat in ALL_CATEGORIES:
        if cat not in attempted_cats:
            qs = get_questions_by_category(cat, limit=2)
            if qs:
                label = cat.replace("-", " ").title()
                return {"rule": f"new_category_{cat}", "email": new_category({"username": act.username}, cat, label, qs),
                        "user": {"id": act.user_id, "email": act.email}}
    return None


def rule_category_struggle(act: UserActivity) -> Optional[Dict[str, Any]]:
    by_cat = _by_category(act.attempts)
    for cat, counts in by_cat.items():
        if counts["fail"] >= 3 and counts["success"] / max(counts["total"], 1) < 0.5:
            qs = get_questions_by_category(cat, limit=3)
            tutorial_slug = None
            tutorial = None
            if qs:
                tutorial_slug = qs[0].get("tutorial_slug")
            if tutorial_slug:
                tutorial = get_tutorial_by_slug(tutorial_slug)
            label = cat.replace("-", " ").title()
            return {"rule": f"category_struggle_{cat}",
                    "email": category_struggle({"username": act.username}, cat, label, counts["fail"], tutorial),
                    "user": {"id": act.user_id, "email": act.email}}
    return None


def rule_id_chain(act: UserActivity) -> Optional[Dict[str, Any]]:
    # Son çözülen sorunun related_question_ids içinden denenmemiş birini öner
    if not act.solved_ids:
        return None
    last_solved = None
    for a in act.attempts:
        if a.get("success"):
            last_solved = get_question(a["question_id"])
            if last_solved:
                break
    if not last_solved:
        return None
    related = last_solved.get("related_question_ids") or []
    for rid in related:
        if rid not in act.attempted_ids:
            rec = get_question(rid)
            if rec:
                return {"rule": f"id_chain_{last_solved['id']}_{rid}",
                        "email": id_chain_recommendation({"username": act.username}, last_solved, rec),
                        "user": {"id": act.user_id, "email": act.email}}
    return None


def rule_concept_gap(act: UserActivity) -> Optional[Dict[str, Any]]:
    # Çözülmüş soruların related_concepts'lerini topla,
    # eksik tamamlayıcı kavramları bul.
    sb = _supabase()
    mastered = set()
    attempted_concepts = set()
    for qid in act.solved_ids + act.attempted_ids:
        q = get_question(qid)
        if not q:
            continue
        for c in q.get("related_concepts") or []:
            attempted_concepts.add(c.lower())
        if qid in act.solved_ids:
            for c in q.get("related_concepts") or []:
                mastered.add(c.lower())
    if not mastered:
        return None
    # Concept pairing (manuel olarak en sık birlikte sorulanlar)
    PAIRS = {
        "string": ["regex", "slicing"],
        "regex": ["string"],
        "recursion": ["dynamic-programming", "memoization"],
        "loop": ["list-comprehension"],
        "list": ["dict", "set"],
        "dict": ["list", "tuple"],
        "sorting": ["searching", "big-o"],
        "searching": ["sorting"],
        "pandas": ["numpy", "dataframe"],
        "numpy": ["pandas"],
    }
    for m in mastered:
        for missing in PAIRS.get(m, []):
            if missing not in attempted_concepts:
                tutorial = get_tutorial_for_concept(missing)
                return {"rule": f"concept_gap_{m}_{missing}",
                        "email": concept_gap({"username": act.username}, m, missing, tutorial),
                        "user": {"id": act.user_id, "email": act.email}}
    return None


def rule_gentle_nudge(act: UserActivity) -> Optional[Dict[str, Any]]:
    """Sadece çok aktif kullanıcılar için günlük hafif hatırlatma."""
    if act.days_since_active > 2:
        return None
    if act.total_solved < 3:
        return None
    # Aktivite saat ortalaması (UTC)
    hours = []
    for a in act.attempts:
        try:
            t = datetime.fromisoformat(a["created_at"].replace("Z", "+00:00"))
            hours.append(t.hour)
        except Exception:
            pass
    if not hours:
        return None
    avg_hour = sum(hours) / len(hours)
    return {"rule": "gentle_nudge", "email": gentle_nudge({"username": act.username}, avg_hour),
            "user": {"id": act.user_id, "email": act.email}}


# ═══════════════════════════════════════════════════════════
# Hata-tabanlı kurallar (error_classifier'dan beslenir)
# ═══════════════════════════════════════════════════════════

ERROR_RULE_THRESHOLD = 3  # Aynı hatadan 3 kez → tetikle
ERROR_RULE_WINDOW_DAYS = 14  # Son 14 gün içinde


def _count_recent_errors(user_id: str) -> Dict[str, int]:
    """Son 14 gündeki hata kategori sayıları."""
    from .error_classifier import get_recent_error_counts
    return get_recent_error_counts(user_id, days=ERROR_RULE_WINDOW_DAYS)


def _make_error_recommendation(user_id: str, error_category: str) -> Optional[Dict[str, Any]]:
    """Hata kategorisi için recommendation objesi oluştur.

    Çıktı formatı (diğer kurallarla uyumlu):
      {
        "rule": "error_index_bounds",
        "user": {"id": ..., "username": ..., "email": ...},
        "email": {"subject": ..., "html": ...},
        "data": {...}  # template'e geçirilecek ek bilgi
      }
    """
    from .error_classifier import CATEGORY_TO_TOPIC, CATEGORY_LABELS
    from .coach_templates import ERROR_TEMPLATES

    topic_path, topic_name = CATEGORY_TO_TOPIC[error_category]
    label = CATEGORY_LABELS[error_category]

    user = _supabase().table("profiles").select("id, username, email").eq("id", user_id).execute()
    if not user.data:
        return None
    profile = user.data[0]

    # Hata sayısını bul
    counts = _count_recent_errors(user_id)
    count = counts.get(error_category, 0)

    # Tutorial bul
    tutorial = None
    if topic_path:
        parts = topic_path.split(".")
        if len(parts) >= 2:
            t = get_tutorial_for_concept(parts[1]) or get_tutorial_for_concept(parts[0])
            if t:
                tutorial = t

    # Template'i çağır
    template_fn = ERROR_TEMPLATES.get(f"error_{_map_category_to_rule(error_category)}")
    if not template_fn:
        return None
    email = template_fn(profile, count, tutorial)

    return {
        "rule": f"error_{_map_category_to_rule(error_category)}",
        "user": {
            "id": profile["id"],
            "username": profile.get("username"),
            "email": profile.get("email"),
        },
        "email": email,
        "data": {
            "category": error_category,
            "category_label": label,
            "topic_path": topic_path,
            "topic_name": topic_name,
            "count": count,
            "tutorial_slug": tutorial.get("slug") if tutorial else None,
        },
    }


def _map_category_to_rule(category: str) -> str:
    return {
        "index_error": "index_bounds",
        "type_error": "type_check",
        "recursion_error": "recursion_base",
        "name_error": "name",
        "attribute_error": "attribute",
        "key_error": "key",
    }.get(category, category)


def rule_error_index_bounds(act: UserActivity) -> Optional[Dict[str, Any]]:
    """Liste sınır hatası 3+ kez."""
    counts = _count_recent_errors(act.user_id)
    if counts.get("index_error", 0) >= ERROR_RULE_THRESHOLD:
        return _make_error_recommendation(act.user_id, "index_error")
    return None


def rule_error_type_check(act: UserActivity) -> Optional[Dict[str, Any]]:
    """Tip hatası 3+ kez."""
    counts = _count_recent_errors(act.user_id)
    if counts.get("type_error", 0) >= ERROR_RULE_THRESHOLD:
        return _make_error_recommendation(act.user_id, "type_error")
    return None


def rule_error_recursion_base(act: UserActivity) -> Optional[Dict[str, Any]]:
    """Recursion hatası 3+ kez."""
    counts = _count_recent_errors(act.user_id)
    if counts.get("recursion_error", 0) >= ERROR_RULE_THRESHOLD:
        return _make_error_recommendation(act.user_id, "recursion_error")
    return None


def rule_error_name(act: UserActivity) -> Optional[Dict[str, Any]]:
    """Tanımsız değişken 3+ kez."""
    counts = _count_recent_errors(act.user_id)
    if counts.get("name_error", 0) >= ERROR_RULE_THRESHOLD:
        return _make_error_recommendation(act.user_id, "name_error")
    return None


def rule_error_attribute(act: UserActivity) -> Optional[Dict[str, Any]]:
    """Yanlış metot 3+ kez."""
    counts = _count_recent_errors(act.user_id)
    if counts.get("attribute_error", 0) >= ERROR_RULE_THRESHOLD:
        return _make_error_recommendation(act.user_id, "attribute_error")
    return None


def rule_error_key(act: UserActivity) -> Optional[Dict[str, Any]]:
    """Dict key hatası 3+ kez."""
    counts = _count_recent_errors(act.user_id)
    if counts.get("key_error", 0) >= ERROR_RULE_THRESHOLD:
        return _make_error_recommendation(act.user_id, "key_error")
    return None


# ═══════════════════════════════════════════════════════════
# Orchestrator
# ═══════════════════════════════════════════════════════════

ALL_RULES = [
    ("first_solve", rule_first_solve),
    ("milestone", rule_milestone),
    ("streak", rule_streak),
    ("inactive", rule_inactive),
    ("difficulty_progression", rule_difficulty_progression),
    ("new_category", rule_new_category),
    ("category_struggle", rule_category_struggle),
    ("id_chain", rule_id_chain),
    ("concept_gap", rule_concept_gap),
    ("gentle_nudge", rule_gentle_nudge),
    ("error_index_bounds", rule_error_index_bounds),
    ("error_type_check", rule_error_type_check),
    ("error_recursion_base", rule_error_recursion_base),
    ("error_name", rule_error_name),
    ("error_attribute", rule_error_attribute),
    ("error_key", rule_error_key),
]


def recommend_for_user(user_id: str, dry_run: bool = True) -> List[Dict[str, Any]]:
    """Bir kullanıcı için tüm kuralları değerlendir, uygun mailleri döndür."""
    act = load_user_activity(user_id)
    if not act:
        return []
    results = []
    for rule_name, fn in ALL_RULES:
        try:
            if not dry_run and _user_recently_mailed(user_id, rule_name):
                continue
            r = fn(act)
            if r:
                results.append(r)
        except Exception as e:
            logger.exception("rule %s failed for user %s", rule_name, user_id)
    return results


def send_recommendation(rec: Dict[str, Any]) -> bool:
    """Bir öneriyi Resend ile gönder ve frequency cap güncelle."""
    import resend
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        logger.warning("RESEND_API_KEY not set, skipping send")
        return False
    resend.api_key = api_key
    try:
        user = rec["user"]
        email = rec["email"]
        params: Dict[str, Any] = {
            "from": BRAND["from_email"],
            "to": [user["email"]],
            "subject": email["subject"],
            "html": email["html"],
        }
        result = resend.Emails.send(params)
        logger.info("coach.email.sent rule=%s user=%s id=%s",
                    rec["rule"], user["id"], getattr(result, "id", "?"))
        _mark_mailed(user["id"], rec["rule"])
        return True
    except Exception as e:
        logger.exception("send_recommendation failed rule=%s", rec["rule"])
        return False