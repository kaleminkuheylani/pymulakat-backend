"""scripts/fix_questions_schema.sql dosyasını Railway shell'den uygula.

Kullanım (Railway shell):
    python3 scripts/apply_schema_fix.py

Bu script:
  1. scripts/fix_questions_schema.sql'i okur
  2. .sql'i supabase postgrest endpoint üzerinden parça parça uygular
  3. Sonra migrate_to_db.py --v4-only ile soruları insert eder
"""
import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SQL_PATH = ROOT / "scripts" / "fix_questions_schema.sql"


def main():
    if not SQL_PATH.exists():
        print(f"❌ SQL bulunamadı: {SQL_PATH}")
        sys.exit(1)

    sql = SQL_PATH.read_text(encoding="utf-8")

    # Öncelik: DATABASE_URL (postgres://...) — direct connection
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL env gerekli")
        sys.exit(1)

    # Yöntem 1: psql varsa kullan
    print("🔧 Schema fix uygulanıyor...")
    try:
        result = subprocess.run(
            ["psql", db_url, "-v", "ON_ERROR_STOP=1", "-f", str(SQL_PATH)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            print("✅ psql ile başarılı")
            print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
            return
        else:
            print(f"⚠️  psql hatası (returncode={result.returncode}):")
            print(result.stderr[:1000])
            print("→ psycopg2 ile denenecek")
    except FileNotFoundError:
        print("⚠️  psql bulunamadı → psycopg2 ile denenecek")
    except Exception as e:
        print(f"⚠️  psql exception: {e}")

    # Yöntem 2: psycopg2 (Railway genelde yüklü)
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 yüklü değil: pip install psycopg2-binary")
        sys.exit(1)

    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()
    try:
        cur.execute(sql)
        print("✅ psycopg2 ile başarılı")
    except Exception as e:
        print(f"❌ SQL hatası: {e}")
        sys.exit(1)
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
