"""
routers/admin_v2.py
═══════════════════════════════════════════════════════════════
Tüm admin router'lar için TEK import noktası.

MİMARİ KARAR (revize):
  - 4 router dosyası korundu: admin.py, admin_auth.py, audit.py, analytics.py
  - admin_v2.py: FACADE - sub_routers listesi döndürür
  - main.py: sub_routers'ı app.include_router ile bağlar

URL prefix'leri korundu (backward compat):
  /api/v2/admin/...        → admin.py + admin_auth.py
  /api/v2/admin/audit/...  → audit.py
  /api/v2/analytics/...    → analytics.py

Toplam 32 endpoint, 4 router dosyası + 1 facade.
"""

import logging

log = logging.getLogger("pymulakat.admin_v2")

# Tüm sub-router'ları import et
sub_routers = []

for name in ("admin", "admin_auth", "audit", "analytics"):
    try:
        mod = __import__(f"routers.{name}", fromlist=["router"])
        sub_routers.append((name, mod.router))
        log.info(f"[admin_v2] ✓ {name} sub-router")
    except Exception as e:
        log.error(f"[admin_v2] ✗ {name}: {e}")
