#!/usr/bin/env bash
#
# PostgreSQL backup — pg_dump + gzip
# GitHub Actions'ta çalışır, artifact olarak yükler.
#
# Gerekli env:
#   DB_URL  — postgresql://user:pass@host:port/db (URL-encoded password OK)
#
# Çıktı:
#   pymulakat-YYYYMMDDTHHMMSSZ.sql.gz  (env: BACKUP_FILE)
#
set -euo pipefail

: "${DB_URL:?DB_URL env variable gerekli (örn. postgresql://user:pass@host:5432/db)}"

# Python ile URL parse (shell quote injection'a karşı güvenli)
eval "$(python3 <<PYEOF
from urllib.parse import urlparse
import shlex
import socket
u = urlparse("${DB_URL}")
hostname = u.hostname or ''
# GitHub Actions runner IPv6 unreachable → IPv4'e zorla
try:
    ipv4 = socket.gethostbyname(hostname)
    print(f"# Resolved {hostname} → {ipv4} (IPv4)", file=__import__('sys').stderr)
    hostname = ipv4
except socket.gaierror:
    print(f"# {hostname} IPv4 resolve failed, using as-is", file=__import__('sys').stderr)
print(f"export PGHOST={shlex.quote(hostname)}")
print(f"export PGPORT={u.port or 5432}")
print(f"export PGUSER={shlex.quote(u.username or '')}")
print(f"export PGPASSWORD={shlex.quote(u.password or '')}")
print(f"export PGDATABASE={shlex.quote((u.path or '/postgres').lstrip('/') or 'postgres')}")
PYEOF
)"

TS=$(date -u +%Y%m%dT%H%M%SZ)
BACKUP_FILE="${BACKUP_FILE:-pymulakat-${TS}.sql.gz}"

echo "===Backup başlatılıyor==="
echo "Host:     $PGHOST"
echo "Port:     $PGPORT"
echo "Database: $PGDATABASE"
echo "User:     $PGUSER"
echo "Output:   $BACKUP_FILE"
echo ""

# pg_dump — schema + data, owners/privileges hariç (clean restore)
pg_dump \
  --no-owner \
  --no-privileges \
  --clean \
  --if-exists \
  --quote-all-identifiers \
  --format=plain \
  --compress=9 \
  --file="$BACKUP_FILE" \
  2>&1 | tail -10

# Boyut + satır sayısı
ls -lh "$BACKUP_FILE"
echo "Tablolar: $(gunzip -c "$BACKUP_FILE" | grep -c '^CREATE TABLE ' || echo 0)"

echo ""
echo "===Backup tamamlandı → $BACKUP_FILE==="
