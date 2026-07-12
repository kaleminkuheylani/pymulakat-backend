"""
routers/admin_setup.py
Schema kurulum endpoint'i — service_role ile.

Bu endpoint admin panelden çağrılır:
  POST /api/v2/admin/setup-schema
  Headers: Authorization: Bearer <SUPABASE_SERVICE_ROLE_KEY>

Tablolar idempotent olarak kurulur (CREATE TABLE IF NOT EXISTS).
Production'da service_role key Railway env'de, supabase_admin
client zaten service_role kullanıyor.

GUARD:
  Bu endpoint service_role key gerektirir (admin user degil).
  Backend service_role_key env Supabase dashboard'tan alinir.
"""

import os
import logging
from fastapi import APIRouter, Header, HTTPException

log = logging.getLogger("pymulakat.admin_setup")

router = APIRouter(prefix="/api/v2/admin/setup", tags=["admin-setup"])

SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


@router.post("/schema")
def setup_schema(authorization: str = Header(default="")):
    """Idempotent schema kurulumu. service_role key ile çağrılır.

    Body: yok
    Headers: Authorization: Bearer <service_role_key>

    4 admin tablosu + 2 page_views tablosu + 1 RPC + RLS policy'ler.
    """
    # Service role key kontrol
    expected_key = f"Bearer {SUPABASE_SERVICE_KEY}"
    if not SUPABASE_SERVICE_KEY or authorization != expected_key:
        raise HTTPException(status_code=401, detail="service_role key gerekli")

    # SQL komutları (idempotent, IF NOT EXISTS)
    sql_statements = [
        # 1) admin_mfa
        """CREATE TABLE IF NOT EXISTS admin_mfa (
  user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  secret TEXT NOT NULL,
  enabled BOOLEAN NOT NULL DEFAULT FALSE,
  backup_codes TEXT[] DEFAULT ARRAY[]::TEXT[],
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  enabled_at TIMESTAMPTZ
);""",
        "CREATE INDEX IF NOT EXISTS idx_admin_mfa_enabled ON admin_mfa(enabled);",
        # 2) admin_sessions
        """CREATE TABLE IF NOT EXISTS admin_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  ip INET,
  user_agent TEXT,
  issued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL,
  revoked BOOLEAN NOT NULL DEFAULT FALSE,
  revoked_at TIMESTAMPTZ,
  revoke_reason TEXT
);""",
        "CREATE INDEX IF NOT EXISTS idx_admin_sessions_user ON admin_sessions(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_admin_sessions_expires ON admin_sessions(expires_at);",
        "CREATE INDEX IF NOT EXISTS idx_admin_sessions_revoked ON admin_sessions(revoked) WHERE revoked = FALSE;",
        # 3) admin_audit_log
        """CREATE TABLE IF NOT EXISTS admin_audit_log (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  user_email TEXT,
  action TEXT NOT NULL,
  ip INET,
  user_agent TEXT,
  success BOOLEAN NOT NULL,
  detail JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);""",
        "CREATE INDEX IF NOT EXISTS idx_admin_audit_user ON admin_audit_log(user_id, created_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_admin_audit_action ON admin_audit_log(action, created_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_admin_audit_failed ON admin_audit_log(success, created_at DESC) WHERE success = FALSE;",
        # 4) admin_lockout
        """CREATE TABLE IF NOT EXISTS admin_lockout (
  user_email TEXT PRIMARY KEY,
  failed_count INT NOT NULL DEFAULT 0,
  last_attempt_at TIMESTAMPTZ,
  locked_until TIMESTAMPTZ
);""",
        "CREATE INDEX IF NOT EXISTS idx_admin_lockout_until ON admin_lockout(locked_until);",
        # 5) page_views
        """CREATE TABLE IF NOT EXISTS page_views (
  id BIGSERIAL PRIMARY KEY,
  path TEXT NOT NULL,
  category TEXT,
  user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  ip INET,
  user_agent TEXT,
  referrer TEXT,
  session_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);""",
        "CREATE INDEX IF NOT EXISTS idx_page_views_path ON page_views(path, created_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_page_views_category ON page_views(category, created_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_page_views_user ON page_views(user_id, created_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_page_views_created ON page_views(created_at DESC);",
        # 6) page_views_daily
        """CREATE TABLE IF NOT EXISTS page_views_daily (
  path TEXT NOT NULL,
  category TEXT,
  view_date DATE NOT NULL,
  view_count INT NOT NULL DEFAULT 0,
  unique_sessions INT NOT NULL DEFAULT 0,
  PRIMARY KEY (path, view_date)
);""",
        "CREATE INDEX IF NOT EXISTS idx_pvd_date ON page_views_daily(view_date DESC);",
        "CREATE INDEX IF NOT EXISTS idx_pvd_category_date ON page_views_daily(category, view_date DESC);",
        # RLS
        "ALTER TABLE admin_mfa ENABLE ROW LEVEL SECURITY;",
        "ALTER TABLE admin_sessions ENABLE ROW LEVEL SECURITY;",
        "ALTER TABLE admin_audit_log ENABLE ROW LEVEL SECURITY;",
        "ALTER TABLE admin_lockout ENABLE ROW LEVEL SECURITY;",
        "ALTER TABLE page_views ENABLE ROW LEVEL SECURITY;",
        "ALTER TABLE page_views_daily ENABLE ROW LEVEL SECURITY;",
        # RLS policies
        'DROP POLICY IF EXISTS "service_role_all_admin_mfa" ON admin_mfa;',
        'CREATE POLICY "service_role_all_admin_mfa" ON admin_mfa FOR ALL TO service_role USING (TRUE) WITH CHECK (TRUE);',
        'DROP POLICY IF EXISTS "service_role_all_admin_sessions" ON admin_sessions;',
        'CREATE POLICY "service_role_all_admin_sessions" ON admin_sessions FOR ALL TO service_role USING (TRUE) WITH CHECK (TRUE);',
        'DROP POLICY IF EXISTS "service_role_all_admin_audit_log" ON admin_audit_log;',
        'CREATE POLICY "service_role_all_admin_audit_log" ON admin_audit_log FOR ALL TO service_role USING (TRUE) WITH CHECK (TRUE);',
        'DROP POLICY IF EXISTS "service_role_all_admin_lockout" ON admin_lockout;',
        'CREATE POLICY "service_role_all_admin_lockout" ON admin_lockout FOR ALL TO service_role USING (TRUE) WITH CHECK (TRUE);',
        'DROP POLICY IF EXISTS "service_role_all_pv" ON page_views;',
        'CREATE POLICY "service_role_all_pv" ON page_views FOR ALL TO service_role USING (TRUE) WITH CHECK (TRUE);',
        'DROP POLICY IF EXISTS "service_role_all_pvd" ON page_views_daily;',
        'CREATE POLICY "service_role_all_pvd" ON page_views_daily FOR ALL TO service_role USING (TRUE) WITH CHECK (TRUE);',
        # 7) RPC
        """CREATE OR REPLACE FUNCTION increment_page_view_daily(
  p_path TEXT,
  p_category TEXT,
  p_date DATE
)
RETURNS void AS $$
BEGIN
  INSERT INTO page_views_daily (path, category, view_date, view_count, unique_sessions)
  VALUES (p_path, p_category, p_date, 1, 1)
  ON CONFLICT (path, view_date)
  DO UPDATE SET view_count = page_views_daily.view_count + 1;
END;
$$ LANGUAGE plpgsql;""",
    ]

    from supabase_client import get_supabase_admin

    sb = get_supabase_admin()
    results = {"success": [], "errors": []}

    # SQL'i tek tek calistir (rpc ile)
    # supabase-py direct SQL calistirmiyor, psycopg2 kullanalim
    import os
    import psycopg2
    from urllib.parse import urlparse

    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        raise HTTPException(500, "DATABASE_URL env tanimsiz")

    try:
        conn = psycopg2.connect(database_url, connect_timeout=10)
        conn.autocommit = True
        cur = conn.cursor()

        for i, sql in enumerate(sql_statements):
            try:
                cur.execute(sql)
                results["success"].append(i)
            except Exception as e:
                results["errors"].append({"index": i, "error": str(e)[:200]})

        cur.close()
        conn.close()
    except Exception as e:
        log.error(f"[admin/setup] DB connection hatasi: {e}")
        raise HTTPException(500, f"DB baglanti hatasi: {e}")

    return {
        "ok": len(results["errors"]) == 0,
        "success_count": len(results["success"]),
        "error_count": len(results["errors"]),
        "errors": results["errors"][:5] if results["errors"] else [],
    }
