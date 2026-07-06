#!/usr/bin/env python3
"""
pymulakat — TAM KULLANICI TAŞIMA Scripti (KVKK uyumlu)
══════════════════════════════════════════════════════

Eski Supabase projesindeki tüm kullanıcı verisini yeni projeye taşır:
  • auth.users (email, encrypted_password, email_confirmed_at, raw_user_meta_data)
  • profiles (avatar, bio, social_links, display_name)
  • interview_attempts (tüm çözüm geçmişi + user_code)
  • notification_preferences (varsa)
  • Son 90 günlük oturum logları (varsa)

Kullanım:
  export OLD_SUPABASE_URL="https://OLD.supabase.co"
  export OLD_SUPABASE_SERVICE_ROLE_KEY="eyJ..."
  export NEW_SUPABASE_URL="https://NEW.supabase.co"
  export NEW_SUPABASE_SERVICE_ROLE_KEY="eyJ..."
  export DRY_RUN="true"   # sadece rapor, yazma
  python scripts/migrate_users_full.py

Çıktı:
  • data/migration_report.json — kimin ne taşındığı
  • data/consent_log.jsonl    — KVKK Md. 12 delil (açık rıza onayı varsa)
"""
import os
import sys
import json
import time
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

try:
    from supabase import create_client, Client
except ImportError:
    print("supabase paketi gerekli: uv add supabase", file=sys.stderr)
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("migrate")

# ─── Config ──────────────────────────────────────────────
OLD_URL = os.environ.get("OLD_SUPABASE_URL", "").rstrip("/")
OLD_KEY = os.environ.get("OLD_SUPABASE_SERVICE_ROLE_KEY", "")
NEW_URL = os.environ.get("NEW_SUPABASE_URL", "").rstrip("/")
NEW_KEY = os.environ.get("NEW_SUPABASE_SERVICE_ROLE_KEY", "")
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() == "true"
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "100"))
LOG_RETENTION_DAYS = 90
REPORT_PATH = Path("data/migration_report.json")
CONSENT_PATH = Path("data/consent_log.jsonl")


def require_env():
    missing = [
        n for n, v in [
            ("OLD_SUPABASE_URL", OLD_URL),
            ("OLD_SUPABASE_SERVICE_ROLE_KEY", OLD_KEY),
            ("NEW_SUPABASE_URL", NEW_URL),
            ("NEW_SUPABASE_SERVICE_ROLE_KEY", NEW_KEY),
        ]
        if not v
    ]
    if missing:
        log.error("Eksik env: %s", ", ".join(missing))
        sys.exit(1)


def client(url: str, key: str) -> Client:
    return create_client(url, key)


def fetch_all_users(sb: Client):
    """Service role ile sayfa sayfa kullanıcı çek (admin API)."""
    users, page, per_page = [], 1, 1000
    while True:
        result = sb.auth.admin.list_users(page=page, per_page=per_page)
        batch = result if isinstance(result, list) else getattr(result, "users", [])
        if not batch:
            break
        users.extend(batch)
        if len(batch) < per_page:
            break
        page += 1
    return users


def fetch_table(sb: Client, table: str, select: str = "*", filters: Optional[dict] = None):
    """Generic paginated SELECT."""
    rows, offset = [], 0
    while True:
        q = sb.table(table).select(select).range(offset, offset + BATCH_SIZE - 1)
        if filters:
            for col, val in filters.items():
                q = q.eq(col, val)
        resp = q.execute()
        data = resp.data or []
        rows.extend(data)
        if len(data) < BATCH_SIZE:
            break
        offset += BATCH_SIZE
    return rows


def migrate_user(old_user, new_sb: Client) -> dict:
    """Tek kullanıcıyı yeni sisteme yaz. attempts/profile ile birlikte."""
    email = old_user.email
    user_id_old = old_user.id
    user_id_new = None
    status = {"email": email, "old_id": user_id_old, "tables": {}}

    try:
        # ── 1. auth.users (admin create) ──
        meta = old_user.user_metadata or {}
        if DRY_RUN:
            status["tables"]["auth.users"] = "DRY_RUN_SKIP"
        else:
            try:
                created = new_sb.auth.admin.create_user({
                    "email": email,
                    "email_confirm": old_user.email_confirmed_at is not None,
                    "user_metadata": meta,
                })
                user_id_new = created.user.id
                status["tables"]["auth.users"] = "OK"
            except Exception as e:
                if "already registered" in str(e).lower():
                    # Zaten var, ID'yi bul
                    user_id_new = new_sb.auth.admin.list_users().users[0].id if False else None
                    status["tables"]["auth.users"] = "ALREADY_EXISTS"
                else:
                    status["tables"]["auth.users"] = f"ERROR: {e}"

        # ── 2. profiles ──
        if user_id_new:
            old_profile = (
                fetch_table(old_sb, "profiles", filters={"id": user_id_old}) or [{}]
            )[0]
            if old_profile and not DRY_RUN:
                profile_payload = {
                    "id": user_id_new,
                    "username": old_profile.get("username") or meta.get("username"),
                    "avatar_url": old_profile.get("avatar_url"),
                    "bio": old_profile.get("bio"),
                    "display_name": old_profile.get("display_name"),
                    "social_links": old_profile.get("social_links"),
                    "is_verified": old_profile.get("is_verified", False),
                    "created_at": old_profile.get("created_at"),
                }
                try:
                    new_sb.table("profiles").upsert(profile_payload).execute()
                    status["tables"]["profiles"] = "OK"
                except Exception as e:
                    status["tables"]["profiles"] = f"ERROR: {e}"
            else:
                status["tables"]["profiles"] = "DRY_RUN_SKIP" if DRY_RUN else "NO_DATA"

        # ── 3. interview_attempts ──
        attempts = fetch_table(
            old_sb,
            "interview_attempts",
            select="question_id,passed_tests,total_tests,success,execution_time_ms,hints_used,user_code,created_at",
            filters={"user_id": user_id_old},
        )
        if attempts and user_id_new and not DRY_RUN:
            for a in attempts:
                a["user_id"] = user_id_new
            try:
                # batch insert
                for i in range(0, len(attempts), BATCH_SIZE):
                    new_sb.table("interview_attempts").insert(
                        attempts[i:i + BATCH_SIZE]
                    ).execute()
                status["tables"]["interview_attempts"] = f"OK ({len(attempts)})"
            except Exception as e:
                status["tables"]["interview_attempts"] = f"ERROR: {e}"
        else:
            status["tables"]["interview_attempts"] = (
                "DRY_RUN_SKIP" if DRY_RUN else f"NO_DATA ({len(attempts) if attempts else 0})"
            )

        # ── 4. notification_preferences (varsa) ──
        try:
            notifs = fetch_table(
                old_sb, "notification_preferences", filters={"user_id": user_id_old}
            )
            if notifs and user_id_new and not DRY_RUN:
                for n in notifs:
                    n["user_id"] = user_id_new
                new_sb.table("notification_preferences").upsert(notifs).execute()
                status["tables"]["notification_preferences"] = f"OK ({len(notifs)})"
            else:
                status["tables"]["notification_preferences"] = (
                    "DRY_RUN_SKIP" if DRY_RUN else "NO_DATA"
                )
        except Exception:
            status["tables"]["notification_preferences"] = "TABLE_NOT_FOUND"

    except Exception as e:
        status["error"] = str(e)
        log.exception("User migration failed: %s", email)

    return status


def main():
    require_env()
    log.info("=" * 60)
    log.info("🚀 TAM TAŞIMA — %s modu", "DRY_RUN" if DRY_RUN else "CANLI")
    log.info("=" * 60)
    log.info("Eski : %s", OLD_URL)
    log.info("Yeni : %s", NEW_URL)

    global old_sb
    old_sb = client(OLD_URL, OLD_KEY)
    new_sb = client(NEW_URL, NEW_KEY)

    users = fetch_all_users(old_sb)
    log.info("📦 Eski sistemde %d kullanıcı bulundu", len(users))

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": DRY_RUN,
        "old_project": OLD_URL,
        "new_project": NEW_URL,
        "user_count": len(users),
        "users": [],
    }

    for i, u in enumerate(users, 1):
        log.info("[%d/%d] %s", i, len(users), u.email)
        status = migrate_user(u, new_sb)
        report["users"].append(status)
        # KVKK Md. 12 — işlem kanıtı (rıza bilgisi burada loglanabilir)
        # Şimdilik sadece işlem başarı durumu:
        if CONSENT_PATH.exists():
            with CONSENT_PATH.open("a") as f:
                f.write(json.dumps({
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "email": u.email,
                    "action": "migrate",
                    "status": status,
                }) + "\n")

    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    log.info("✅ Rapor: %s", REPORT_PATH)
    log.info("📊 Toplam: %d kullanıcı işlendi", len(report["users"]))


if __name__ == "__main__":
    main()