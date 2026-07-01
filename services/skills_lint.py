# services/skills_lint.py
# Topic graph lint — SADECE admin/cron tarafından çağrılır.
# Kullanıcıya asla dönmez. Hatalar sadece server log'a yazılır.

import logging
from typing import Dict, List, Tuple

from .skills import SKILL_GRAPH, is_valid_topic, all_topics, all_subskills

logger = logging.getLogger(__name__)


def lint_question_topics(qid: int, topics: List[str]) -> List[str]:
    """Bir sorunun topics listesini validate et. Hata varsa logla, kullanıcıya dönme."""
    issues = []
    if not topics:
        issues.append(f"q{qid}: topics boş")
        logger.warning("skills.lint.q_empty qid=%s", qid)
        return issues

    for t in topics:
        if not is_valid_topic(t):
            issues.append(f"q{qid}: tanımsız topic '{t}'")
            logger.warning("skills.lint.unknown_topic qid=%s topic=%s", qid, t)

    if len(topics) != len(set(topics)):
        issues.append(f"q{qid}: duplicate topic")
        logger.warning("skills.lint.duplicate qid=%s", qid)

    return issues


def lint_all_questions() -> Dict[str, List[str]]:
    """Tüm soruları Supabase'den çekip lint et. Admin-only / cron."""
    from supabase_client import get_supabase_admin
    sb = get_supabase_admin()
    try:
        result = sb.table("interwiews").select("id, topics").execute()
        rows = result.data or []
    except Exception as e:
        logger.exception("skills.lint.fetch_failed: %s", e)
        return {"error": ["Supabase erişim hatası"]}

    all_issues: List[str] = []
    used_topics: set = set()
    orphan_questions: List[int] = []

    for row in rows:
        qid = row.get("id")
        topics = row.get("topics") or []
        all_issues.extend(lint_question_topics(qid, topics))
        if not topics:
            orphan_questions.append(qid)
        else:
            used_topics.update(topics)

    # Orphan topics: hiçbir soruda kullanılmayan topic'ler
    all_defined = set(all_topics())
    orphan_topics = all_defined - used_topics
    for t in sorted(orphan_topics):
        msg = f"orphan topic '{t}' — hiçbir soruda kullanılmıyor"
        all_issues.append(msg)
        logger.info("skills.lint.orphan_topic topic=%s", t)

    if not all_issues:
        logger.info("skills.lint.ok questions=%d topics_used=%d", len(rows), len(used_topics))
    else:
        logger.warning("skills.lint.issues count=%d orphan_qs=%d", len(all_issues), len(orphan_questions))

    return {
        "summary": {
            "total_questions": len(rows),
            "topics_used": len(used_topics),
            "topics_defined": len(all_defined),
            "orphan_topics_count": len(orphan_topics),
            "issues_count": len(all_issues),
        },
        "issues": all_issues,
        "orphan_questions": orphan_questions,
        "orphan_topics": sorted(orphan_topics),
    }


def lint_quick() -> Tuple[bool, List[str]]:
    """Hızlı lint — sadece kullanılmayan topic'leri raporla."""
    from supabase_client import get_supabase_admin
    sb = get_supabase_admin()
    try:
        result = sb.table("interwiews").select("topics").execute()
    except Exception:
        return True, []  # sessizce fail

    used: set = set()
    for row in (result.data or []):
        used.update(row.get("topics") or [])

    defined = set(all_topics())
    orphans = defined - used
    if orphans:
        logger.info("skills.lint.quick orphans=%d", len(orphans))
        return False, sorted(orphans)
    return True, []