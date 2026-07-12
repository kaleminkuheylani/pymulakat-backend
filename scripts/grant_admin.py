"""
scripts/grant_admin.py
Verilen email'i Supabase admin yap.

KULLANIM:
  python scripts/grant_admin.py kaleminkuheylani@gmail.com

Backend service_role key (.env) ile calisir.
Supabase Dashboard SQL Editor yerine CLI uzerinden admin atamak icin.
"""

import sys
import os
from pathlib import Path

# .env yukle
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().split("\n"):
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

from supabase_client import get_supabase_admin

def grant_admin(email: str, role: str = "admin"):
    sb = get_supabase_admin()
    print(f"Aranıyor: {email}")
    
    # Tum user'lar (200 max)
    result = sb.auth.admin.list_users(page=1, per_page=200)
    target = None
    for u in result:
        if u.email and u.email.lower() == email.lower():
            target = u
            break
    
    if not target:
        print(f"❌ User bulunamadi: {email}")
        sys.exit(1)
    
    current_meta = dict(target.app_metadata or {})
    current_meta["role"] = role
    
    sb.auth.admin.update_user_by_id(
        target.id,
        {"app_metadata": current_meta}
    )
    print(f"✓ {email} → role='{role}' (id: {target.id})")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanim: python scripts/grant_admin.py <email> [role]")
        sys.exit(1)
    email = sys.argv[1]
    role = sys.argv[2] if len(sys.argv) > 2 else "admin"
    grant_admin(email, role)
