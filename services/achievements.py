# services/achievements.py
# Static achievement definitions + evaluation logic.
# Definitions are code-side; unlocked state lives in user_achievements table.

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

_LEVEL_ALIASES = {
    "başlangıç": "beginner",
    "beginner": "beginner",
    "easy": "beginner",
    "orta": "intermediate",
    "intermediate": "intermediate",
    "medium": "intermediate",
    "ileri": "advanced",
    "advanced": "advanced",
    "hard": "advanced",
}


@dataclass(frozen=True)
class AchievementDef:
    id: str
    title: str
    description: str
    icon: str
    points: int
    group: str
    condition: Callable[..., bool]


def _normalize_level(level: Any) -> str:
    if not level:
        return ""
    return _LEVEL_ALIASES.get(str(level).strip().lower(), str(level).strip().lower())


def _as_date(ts) -> Optional[datetime]:
    if not ts:
        return None
    if isinstance(ts, datetime):
        return ts
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00").replace("+00:00", ""))
    except Exception:
        return None


def _attempt_sort_key(a: Dict[str, Any]) -> tuple:
    dt = _as_date(a.get("created_at"))
    if dt is None:
        return (1, datetime.min)
    return (0, dt)


def _augment(attempts: List[Dict[str, Any]], questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    qmeta = {}
    for q in questions:
        qid = q.get("id")
        if qid is not None:
            qmeta[str(qid)] = q
        legacy = q.get("legacy_id")
        if legacy is not None:
            qmeta[str(legacy)] = q
    out = []
    for a in attempts:
        raw_qid = a.get("question_id")
        q = qmeta.get(str(raw_qid)) if raw_qid is not None else None
        qa = dict(a)
        qa["category"] = (q.get("category") or "") if q else ""
        qa["level"] = _normalize_level(q.get("level")) if q else ""
        qa["language"] = a.get("language") or "python"
        out.append(qa)
    return out


def _count_success(attempts: List[Dict[str, Any]], **filters) -> int:
    return sum(
        1 for a in attempts
        if a.get("success")
        and all(a.get(k) == v for k, v in filters.items())
    )


def _total_runs(attempts: List[Dict[str, Any]], **filters) -> int:
    return sum(
        1 for a in attempts
        if all(a.get(k) == v for k, v in filters.items())
    )


def _any_success(attempts: List[Dict[str, Any]], **filters) -> bool:
    return any(a.get("success") and all(a.get(k) == v for k, v in filters.items()) for a in attempts)


# ─────────────────────────────────────────────────────────────────
# Conditions
# ─────────────────────────────────────────────────────────────────

def _first_run(atts, *_):
    return len(atts) >= 1

def _first_success(atts, *_):
    return _any_success(atts)

def _first_perfect(atts, *_):
    first_by_q = {}
    for a in sorted(atts, key=_attempt_sort_key):
        qid = a.get("question_id")
        if qid is not None and qid not in first_by_q:
            first_by_q[qid] = a
    for a in first_by_q.values():
        if a.get("success") and a.get("passed_tests") == a.get("total_tests") and a.get("total_tests", 0) > 0:
            return True
    return False

def _first_fast(atts, *_):
    return any(a.get("success") and (a.get("execution_time_ms") or 0) <= 60000 for a in atts)

def _first_js_run(atts, *_):
    return _total_runs(atts, language="javascript") >= 1

def _first_js_success(atts, *_):
    return _count_success(atts, language="javascript") >= 1

def _hint_free_5(atts, *_):
    return _count_success([a for a in atts if a.get("hints_used", 0) == 0]) >= 5

def _share_first(atts, questions, context, *_):
    return bool(context.get("shared"))


def _make_count_success(n, **filters):
    def check(atts, *_):
        return _count_success(atts, **filters) >= n
    return check


def _make_count_runs(n, **filters):
    def check(atts, *_):
        return _total_runs(atts, **filters) >= n
    return check


def _tests_passed(n):
    def check(atts, *_):
        return sum(a.get("passed_tests", 0) for a in atts) >= n
    return check


def _perfect_n(n):
    def check(atts, questions, *_):
        total = len(questions)
        if total == 0:
            return False
        perfect = {
            a.get("question_id")
            for a in atts
            if a.get("success")
            and a.get("passed_tests") == a.get("total_tests")
            and a.get("total_tests", 0) > 0
        }
        target = min(n, total)
        return len(perfect) >= target
    return check


def _streak_success_n(n):
    def check(atts, *_):
        longest = 0
        cur = 0
        for a in sorted(atts, key=_attempt_sort_key):
            if a.get("success"):
                cur += 1
                longest = max(longest, cur)
            else:
                cur = 0
        return longest >= n
    return check


def _daily_n(n):
    def check(atts, *_):
        from collections import Counter
        by_day = Counter()
        for a in sorted(atts, key=_attempt_sort_key):
            if not a.get("success"):
                continue
            dt = _as_date(a.get("created_at"))
            if dt:
                by_day[dt.strftime("%Y-%m-%d")] += 1
        return any(c >= n for c in by_day.values())
    return check


def _speed_under_60(atts, *_):
    return any(a.get("success") and (a.get("execution_time_ms") or 0) <= 60000 for a in atts)


def _time_window(start, end):
    def check(atts, *_):
        for a in atts:
            if not a.get("success"):
                continue
            dt = _as_date(a.get("created_at"))
            if dt and start <= dt.hour < end:
                return True
        return False
    return check


def _weekend(atts, *_):
    for a in atts:
        if not a.get("success"):
            continue
        dt = _as_date(a.get("created_at"))
        if dt and dt.weekday() >= 5:
            return True
    return False


def _category_n(category, n):
    def check(atts, questions, *_):
        count = sum(1 for q in questions if q.get("category") == category)
        target = min(n, count) if count > 0 else float("inf")
        return _count_success(atts, category=category) >= target
    return check


def _cat_explorer(atts, questions, *_):
    excluded = {"pandas", "queue"}
    valid_cats = {q.get("category") for q in questions if q.get("category") not in excluded}
    if not valid_cats:
        return False
    solved_cats = {a.get("category") for a in atts if a.get("success") and a.get("category") in valid_cats}
    return len(solved_cats) >= min(6, len(valid_cats))


def _level_n(level, n):
    def check(atts, questions, *_):
        count = sum(1 for q in questions if _normalize_level(q.get("level")) == level)
        target = min(n, count) if count > 0 else float("inf")
        return _count_success(atts, level=level) >= target
    return check


def _level_all(atts, questions, *_):
    all_levels = {_normalize_level(q.get("level")) for q in questions if q.get("level")}
    if not all_levels:
        all_levels = {"beginner", "intermediate", "advanced"}
    solved_levels = {a.get("level") for a in atts if a.get("success") and a.get("level")}
    return all_levels.issubset(solved_levels)


def _level_advanced_first_try(atts, *_):
    first_by_q = {}
    for a in sorted(atts, key=_attempt_sort_key):
        qid = a.get("question_id")
        if qid is not None and qid not in first_by_q:
            first_by_q[qid] = a
    for a in first_by_q.values():
        if a.get("level") == "advanced" and a.get("success"):
            return True
    return False


def _attempt_distinct_n(n):
    def check(atts, questions, *_):
        total = len(questions)
        if total == 0:
            return False
        ids = {a.get("question_id") for a in atts if a.get("question_id")}
        target = min(n, total)
        return len(ids) >= target
    return check


def _solved_percent(percent):
    def check(atts, questions, *_):
        total = len(questions)
        solved = {a.get("question_id") for a in atts if a.get("success") and a.get("question_id")}
        if total == 0:
            return False
        return len(solved) >= math.ceil(total * percent / 100)
    return check


def _distinct_days_n(n):
    def check(atts, *_):
        days = set()
        for a in atts:
            dt = _as_date(a.get("created_at"))
            if dt:
                days.add(dt.strftime("%Y-%m-%d"))
        return len(days) >= n
    return check


def _consecutive_days(n):
    def check(atts, *_):
        days = sorted({
            _as_date(a.get("created_at")).strftime("%Y-%m-%d")
            for a in atts
            if _as_date(a.get("created_at"))
        })
        if not days:
            return False
        longest = 1
        cur = 1
        for i in range(1, len(days)):
            d1 = datetime.strptime(days[i-1], "%Y-%m-%d")
            d2 = datetime.strptime(days[i], "%Y-%m-%d")
            if (d2 - d1).days == 1:
                cur += 1
            else:
                cur = 1
            longest = max(longest, cur)
        return longest >= n
    return check


def _comeback(atts, *_):
    days = sorted({
        _as_date(a.get("created_at")).strftime("%Y-%m-%d")
        for a in atts
        if a.get("success") and _as_date(a.get("created_at"))
    })
    for i in range(1, len(days)):
        d1 = datetime.strptime(days[i-1], "%Y-%m-%d")
        d2 = datetime.strptime(days[i], "%Y-%m-%d")
        if (d2 - d1).days >= 7:
            return True
    return False


def _persistent(atts, *_):
    by_q = {}
    for a in atts:
        by_q.setdefault(a.get("question_id"), []).append(a)
    for _qid, qatts in by_q.items():
        sorted_q = sorted(qatts, key=_attempt_sort_key)
        for i, a in enumerate(sorted_q):
            if a.get("success"):
                failures_before = [x for x in sorted_q[:i] if not x.get("success")]
                if len(failures_before) >= 5:
                    return True
    return False


def _failure_10(atts, *_):
    return sum(1 for a in atts if not a.get("success")) >= 10


def _ai_feedback_5(atts, questions, context, *_):
    return context.get("ai_feedback_count", 0) >= 5


def _report_question(atts, questions, context, *_):
    return bool(context.get("reported"))


# ─────────────────────────────────────────────────────────────────
# Definitions
# ─────────────────────────────────────────────────────────────────

ACHIEVEMENTS: List[AchievementDef] = [
    AchievementDef("first_run", "İlk Adım", "İlk kod çalıştırma", "play", 10, "first", _first_run),
    AchievementDef("first_success", "Merhaba Dünya", "İlk başarılı çözüm", "smile", 20, "first", _first_success),
    AchievementDef("first_perfect", "İlk Onikilik", "İlk denemede tüm testleri geç", "star", 50, "first", _first_perfect),
    AchievementDef("first_fast", "Hızlı Başlangıç", "60 saniye içinde ilk başarı", "zap", 30, "first", _first_fast),
    AchievementDef("first_js", "JS Merhaba", "İlk JS çalıştırma", "globe", 30, "first", _first_js_run),
    AchievementDef("first_js_success", "JS Başarı", "İlk JS başarılı çözüm", "flag", 60, "first", _first_js_success),
    AchievementDef("hint_free_5", "İpucusuz", "İpucu kullanmadan 5 çözüm", "lock", 75, "first", _hint_free_5),
    AchievementDef("share_first", "Paylaşan", "İlk çözüm paylaşımı", "share-2", 25, "first", _share_first),

    AchievementDef("success_5", "Çaylak", "5 başarılı çözüm", "trophy", 50, "volume", _make_count_success(5)),
    AchievementDef("success_10", "Yetenekli", "10 başarılı çözüm", "award", 100, "volume", _make_count_success(10)),
    AchievementDef("success_25", "Usta", "25 başarılı çözüm", "medal", 200, "volume", _make_count_success(25)),
    AchievementDef("success_50", "Efsane", "50 başarılı çözüm", "crown", 500, "volume", _make_count_success(50)),
    AchievementDef("success_100", "Legendary", "100 başarılı çözüm", "flame", 1000, "volume", _make_count_success(100)),
    AchievementDef("tests_passed_100", "Test Savaşçısı", "100 test geç", "check-circle", 50, "volume", _tests_passed(100)),
    AchievementDef("tests_passed_500", "Test Ustası", "500 test geç", "shield-check", 250, "volume", _tests_passed(500)),
    AchievementDef("perfect_10", "Mükemmeliyetçi", "10 soruda tüm testleri geç", "sparkles", 100, "volume", _perfect_n(10)),
    AchievementDef("perfect_25", "Hatasız", "25 soruda tüm testleri geç", "gem", 300, "volume", _perfect_n(25)),
    AchievementDef("streak_success_5", "Peş Peşe", "5 ardışık başarılı deneme", "repeat", 75, "volume", _streak_success_n(5)),

    AchievementDef("py_run_10", "Python Dostu", "Python ile 10 çalıştırma", "terminal", 50, "language", _make_count_runs(10, language="python")),
    AchievementDef("py_success_10", "Python Çaylak", "Python ile 10 başarılı", "code-2", 100, "language", _make_count_success(10, language="python")),
    AchievementDef("py_success_25", "Python Usta", "Python ile 25 başarılı", "code", 250, "language", _make_count_success(25, language="python")),
    AchievementDef("js_run_10", "JS Dostu", "JS ile 10 çalıştırma", "activity", 50, "language", _make_count_runs(10, language="javascript")),
    AchievementDef("js_success_10", "JS Çaylak", "JS ile 10 başarılı", "hash", 150, "language", _make_count_success(10, language="javascript")),
    AchievementDef("polyglot", "Çokdilli", "Aynı soruyu hem Python hem JS ile çöz", "languages", 150, "language", lambda atts, *_: bool(
        {a.get("question_id") for a in atts if a.get("success") and a.get("language") == "python"}
        &
        {a.get("question_id") for a in atts if a.get("success") and a.get("language") == "javascript"}
    )),

    AchievementDef("cat_python_basics", "Programlama Temelleri", "programlama-temelleri'nde 10 başarılı", "book-open", 100, "category", _category_n("programlama-temelleri", 10)),
    AchievementDef("cat_list_dict", "Koleksiyoncu", "list-dict'te 4 başarılı", "list", 100, "category", _category_n("list-dict", 4)),
    AchievementDef("cat_data_structures", "Veri Yapıları Profu", "data-structures'ta 5 başarılı", "database", 100, "category", _category_n("data-structures", 5)),
    AchievementDef("cat_algorithms", "Algoritmacı", "algorithms'ta 5 başarılı", "cpu", 100, "category", _category_n("algorithms", 5)),
    AchievementDef("cat_dp", "DP Düşünürü", "dynamic-programming'de 3 başarılı", "layers", 150, "category", _category_n("dynamic-programming", 3)),
    AchievementDef("cat_heap", "Heap Kahramanı", "heap'te 2 başarılı", "triangle", 100, "category", _category_n("heap", 2)),
    AchievementDef("cat_stack", "Stack Ustası", "stack'te 2 başarılı", "stack-pusher", 100, "category", _category_n("stack", 2)),
    AchievementDef("cat_explorer", "Kategori Kaşifi", "6 farklı kategoride başarılı", "map", 200, "category", _cat_explorer),

    AchievementDef("level_beginner_10", "Başlangıç Ustası", "10 beginner başarılı", "sprout", 75, "level", _level_n("beginner", 10)),
    AchievementDef("level_intermediate_10", "Orta Seviye", "10 intermediate başarılı", "bar-chart-2", 100, "level", _level_n("intermediate", 10)),
    AchievementDef("level_advanced_5", "İleri Seviye", "5 advanced başarılı", "mountain", 200, "level", _level_n("advanced", 5)),
    AchievementDef("level_all", "Zirve", "Her seviyeden en az 1 başarılı", "sun", 150, "level", _level_all),
    AchievementDef("level_advanced_first_try", "Zorlu Başlangıç", "İlk denemede advanced çöz", "rocket", 250, "level", _level_advanced_first_try),

    AchievementDef("attempt_25", "Mozaik", "25 farklı soruda deneme", "grid", 50, "collection", _attempt_distinct_n(25)),
    AchievementDef("solved_25_percent", "Çeyrek", "Soruların %25'ini çöz", "pie-chart", 300, "collection", _solved_percent(25)),
    AchievementDef("solved_50_percent", "Yarım", "Soruların %50'sini çöz", "pie-chart", 600, "collection", _solved_percent(50)),
    AchievementDef("solved_75_percent", "Çoğunluk", "Soruların %75'ini çöz", "pie-chart", 900, "collection", _solved_percent(75)),
    AchievementDef("solved_all", "Tamamlayıcı", "Tüm soruları çöz", "check-square", 2000, "collection", _solved_percent(100)),

    AchievementDef("speed_under_60", "Süper Hızlı", "60 saniye altı başarılı", "clock", 75, "time", _speed_under_60),
    AchievementDef("daily_3", "Günlük Hedef", "Bir günde 3 başarılı", "calendar", 75, "time", _daily_n(3)),
    AchievementDef("streak_3", "3 Gün Seri", "3 gün üst üste deneme", "flame", 50, "time", _consecutive_days(3)),
    AchievementDef("streak_7", "Haftalık Seri", "7 gün üst üste deneme", "flame", 150, "time", _consecutive_days(7)),
    AchievementDef("streak_30", "Aylık Seri", "30 gün üst üste deneme", "flame", 500, "time", _consecutive_days(30)),
    AchievementDef("night_owl", "Gece Kuşu", "00:00-05:00 arası başarılı", "moon", 30, "time", _time_window(0, 5)),
    AchievementDef("weekend_warrior", "Hafta Sonu Savaşçısı", "Cumartesi/Pazar başarılı", "calendar-check", 30, "time", _weekend),

    AchievementDef("comeback_7", "Geri Dönüş", "7 gün ara verip tekrar çözüm", "refresh-cw", 50, "resilience", _comeback),
    AchievementDef("persistent", "Pes Etmemek", "Aynı soruda 5 başarısızdan sonra başarı", "anchor", 100, "resilience", _persistent),
    AchievementDef("failure_10", "Öğrenen", "10 başarısız deneme", "alert-circle", 30, "resilience", _failure_10),
    AchievementDef("ai_feedback_5", "AI Danışmanı", "5 kez AI feedback kullan", "message-square", 50, "resilience", _ai_feedback_5),
    AchievementDef("report_question", "Katkıcı", "Bir soru hatası bildir", "flag", 25, "resilience", _report_question),
]


def evaluate(
    attempts: List[Dict[str, Any]],
    questions: List[Dict[str, Any]],
    context: Optional[Dict[str, Any]] = None,
) -> List[str]:
    if context is None:
        context = {}
    atts = _augment(attempts, questions)
    return [a.id for a in ACHIEVEMENTS if a.condition(atts, questions, context)]


def get_achievements_with_state(unlocked_ids: Set[str]) -> List[Dict[str, Any]]:
    return [
        {
            "id": a.id,
            "title": a.title,
            "description": a.description,
            "icon": a.icon,
            "points": a.points,
            "group": a.group,
            "unlocked": a.id in unlocked_ids,
        }
        for a in ACHIEVEMENTS
    ]
