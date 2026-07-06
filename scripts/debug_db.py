"""
Debug script: backend'in gördüğü gerçek DB sayılarını döndürür.
Railway console'da: python3 /tmp/debug_db.py
"""
import os
from supabase import create_client

sb = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_ROLE_KEY"],
)

print(f"SUPABASE_URL = {os.environ['SUPABASE_URL']}")

# Total count
total = sb.table("questions").select("id", count="exact").execute()
print(f"Toplam soru: {total.count}")

# is_published=true count
active = sb.table("questions").select("id", count="exact").eq("is_published", True).execute()
print(f"is_published=true: {active.count}")

# Kategoriler
cats = sb.table("questions").select("category").eq("is_published", True).execute()
from collections import Counter
cat_counts = Counter(r["category"] for r in cats.data or [])
print(f"Kategori dağılımı: {dict(cat_counts)}")

# İlk 3 soru
sample = sb.table("questions").select("id, title, category, slug").eq("is_published", True).limit(3).execute()
print(f"Örnek 3 soru:")
for r in (sample.data or []):
    print(f"  #{r.get('id')} {r.get('category'):18s} | slug={r.get('slug')!r} | {r.get('title')[:50]}")
