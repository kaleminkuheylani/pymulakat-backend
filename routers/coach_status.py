# routers/coach_status.py
# Kullanıcı coach durumunu görür — HANGI kurallar tetiklendi, NE ZAMAN mail gitti.
# Sadece bilgi amaçlı — puanlama, skill tree, dashboard yok.

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from services.coach import load_user_activity, _user_recently_mailed, _calc_streak_days
from services.coach_templates import BRAND
from supabase_client import get_supabase_admin
from dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/coach-status", tags=["coach-status"])


def _rule_meta():
    """Coach kuralları için kullanıcı-dostu açıklamalar."""
    return {
        "first_solve": {"label": "İlk Çözüm", "icon": "🎉", "desc": "İlk başarılı sorundan sonra tebrik maili"},
        "milestone_10": {"label": "10. Soru", "icon": "🏆", "desc": "10 soru çözdüğünde milestone"},
        "milestone_25": {"label": "25. Soru", "icon": "🏆", "desc": "25 soru çözdüğünde milestone"},
        "milestone_50": {"label": "50. Soru", "icon": "🏆", "desc": "50 soru çözdüğünde milestone"},
        "milestone_100": {"label": "100. Soru", "icon": "🏆", "desc": "100 soru çözdüğünde milestone"},
        "streak_7": {"label": "7 Gün Streak", "icon": "🔥", "desc": "7 gün üst üste pratik yaptığında"},
        "streak_14": {"label": "14 Gün Streak", "icon": "🔥", "desc": "14 gün üst üste pratik yaptığında"},
        "streak_30": {"label": "30 Gün Streak", "icon": "🔥", "desc": "30 gün üst üste pratik yaptığında"},
        "inactive_7d": {"label": "Re-engagement", "icon": "👋", "desc": "7+ gün gelmezsen geri çağırma maili"},
        "inactive_30d": {"label": "Re-engagement", "icon": "👋", "desc": "30+ gün gelmezsen 'özledik' maili"},
        "difficulty_progression": {"label": "Seviye Atlama", "icon": "📈", "desc": "Beginner bitince intermediate'a yönlendirme"},
        "new_category_python-basics": {"label": "Yeni Kategori", "icon": "🆕", "desc": "Denenmemiş kategorileri keşfetme"},
        "new_category_strings": {"label": "Yeni Kategori", "icon": "🆕", "desc": "Denenmemiş kategorileri keşfetme"},
        "new_category_list-dict": {"label": "Yeni Kategori", "icon": "🆕", "desc": "Denenmemiş kategorileri keşfetme"},
        "new_category_oop": {"label": "Yeni Kategori", "icon": "🆕", "desc": "Denenmemiş kategorileri keşfetme"},
        "new_category_algorithms": {"label": "Yeni Kategori", "icon": "🆕", "desc": "Denenmemiş kategorileri keşfetme"},
        "new_category_pandas": {"label": "Yeni Kategori", "icon": "🆕", "desc": "Denenmemiş kategorileri keşfetme"},
        "category_struggle_python-basics": {"label": "Zorlanma Tespiti", "icon": "😓", "desc": "Aynı kategoride 3+ başarısızlıkta rehber önerisi"},
        "category_struggle_strings": {"label": "Zorlanma Tespiti", "icon": "😓", "desc": "Aynı kategoride 3+ başarısızlıkta rehber önerisi"},
        "id_chain": {"label": "İlgili Soru", "icon": "🔗", "desc": "Çözülen soruya bağlı sonraki soru önerisi"},
        "concept_gap": {"label": "Konu Boşluğu", "icon": "🧩", "desc": "Benzer kavramların eksik olduğunu fark eder"},
        "gentle_nudge": {"label": "Günlük Hatırlatma", "icon": "🐍", "desc": "Aktif olduğun saatlerde hafif hatırlatma"},
        "error_index_bounds": {"label": "Liste Sınır Hatası", "icon": "📐", "desc": "3+ kez index out of range yaptıysan rehber"},
        "error_type_check": {"label": "Tip Kontrolü", "icon": "🎯", "desc": "3+ kez TypeError yaptıysan type hints rehberi"},
        "error_recursion_base": {"label": "Recursion Base Case", "icon": "🔁", "desc": "3+ kez recursion patladıysa base case rehberi"},
        "error_name": {"label": "Tanımsız Değişken", "icon": "🔤", "desc": "3+ kez NameError yaptıysan değişken rehberi"},
        "error_attribute": {"label": "Yanlış Metot", "icon": "🧩", "desc": "3+ kez AttributeError yaptıysan metot rehberi"},
        "error_key": {"label": "Sözlük Güvenli Erişim", "icon": "🔑", "desc": "3+ kez KeyError yaptıysan .get() rehberi"},
    }


@router.get("/me")
async def get_my_status(request: Request):
    """Auth'lı kullanıcının coach durumu — hangi kurallar tetiklenebilir, son mail ne zaman."""
    try:
        user = await get_current_user(request)
    except Exception:
        raise HTTPException(401, "Giriş gerekli")
    if not user:
        raise HTTPException(401, "Giriş gerekli")

    user_id = user["id"]
    act = load_user_activity(user_id)
    if not act:
        raise HTTPException(404, "Profil bulunamadı")

    # Hangi kurallar şu an tetiklenebilir durumda
    from services.coach import ALL_RULES
    available_rules = []
    for rule_name, fn in ALL_RULES:
        if _user_recently_mailed(user_id, rule_name):
            status = "rate_limited"
            note = "Son 7 gün içinde gönderildi"
        else:
            try:
                result = fn(act)
                status = "ready" if result else "not_triggered"
                note = "Tetiklenebilir" if result else "Koşul sağlanmadı"
            except Exception:
                status = "error"
                note = "Değerlendirme hatası"
        meta = _rule_meta().get(rule_name, {"label": rule_name, "icon": "📧", "desc": rule_name})
        available_rules.append({
            "rule": rule_name,
            "label": meta["label"],
            "icon": meta["icon"],
            "description": meta["desc"],
            "status": status,
            "note": note,
        })

    # Son mail gönderim zamanı
    sb = get_supabase_admin()
    last_mail_iso = None
    last_rule = None
    total_mails = 0
    try:
        prof = sb.table("profiles").select("coach_recent_sent").eq("id", user_id).execute()
        if prof.data:
            recent = prof.data[0].get("coach_recent_sent") or {}
            if recent:
                sorted_recent = sorted(recent.items(), key=lambda x: x[1], reverse=True)
                last_rule, last_mail_iso = sorted_recent[0]
                total_mails = len(recent)
    except Exception:
        pass

    last_mail_display = None
    if last_mail_iso:
        try:
            last_dt = datetime.fromisoformat(last_mail_iso.replace("Z", "+00:00"))
            delta = datetime.now(timezone.utc) - last_dt
            days = delta.days
            hours = delta.seconds // 3600
            last_mail_display = {
                "rule": last_rule,
                "label": _rule_meta().get(last_rule, {}).get("label", last_rule),
                "iso": last_mail_iso,
                "days_ago": days,
                "hours_ago": hours,
                "ago_text": f"{days}g {hours}s önce" if days > 0 else f"{hours} saat önce",
            }
        except Exception:
            pass

    return {
        "user": {
            "username": act.username,
            "total_solved": act.total_solved,
            "total_attempted": act.total_attempted,
            "streak_days": _calc_streak_days(act.attempts),
            "days_since_active": act.days_since_active,
        },
        "coach": {
            "enabled": True,
            "from_email": BRAND["from_email"],
            "total_mails_sent": total_mails,
            "last_mail": last_mail_display,
            "frequency_cap_days": 7,
            "available_rules": available_rules,
        },
    }