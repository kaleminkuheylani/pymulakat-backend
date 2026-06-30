import os
import re
from dotenv import load_dotenv
from supabase import create_client
from typing import List, Dict, Any
from dataclasses import dataclass, field

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


@dataclass
class Question:
    id: int
    title: str
    category: str
    level: str
    description: str
    starter_code: str
    test_cases: List[Dict[str, Any]]
    hints: List[str] = field(default_factory=list)


# ════════════════════════════════════════════════════════════════
# QUESTIONS.py'yi güvenli şekilde parse et (SyntaxWarning'leri yut)
# ════════════════════════════════════════════════════════════════
import sys
import importlib.util
import warnings

warnings.filterwarnings("ignore")  # "\|" gibi geçersiz escape uyarılarını bastır

QUESTIONS_PATH = r"C:\projelerim\gozbebgim\backend\data\QUESTIONS.py"

spec = importlib.util.spec_from_file_location("questions_module", QUESTIONS_PATH)
module = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(module)
    QUESTIONS: List[Question] = module.QUESTIONS
    print(f"✅ {len(QUESTIONS)} soru QUESTIONS.py'den yüklendi.")
except SyntaxError as e:
    print(f"❌ QUESTIONS.py parse hatası: {e}")
    print("💡 Dosyadaki \\ karakterlerini escape et veya raw string yap.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Beklenmeyen hata: {e}")
    sys.exit(1)


if not supabase:
    print("Supabase bağlantısı yok!")
    sys.exit(1)

if not QUESTIONS:
    print("⚠️ QUESTIONS listesi boş.")
    sys.exit(1)


# ════════════════════════════════════════════════════════════════
# Payload hazırla — duplicate id'leri temizle (son olan kalsın)
# ════════════════════════════════════════════════════════════════
seen_ids = {}
for q in QUESTIONS:
    seen_ids[q.id] = q  # aynı id varsa üzerine yaz, son kalan kalsın

unique_questions = list(seen_ids.values())
unique_questions.sort(key=lambda x: x.id)  # id sırasına göre

print(f"🔍 Duplicate temizleme sonrası: {len(unique_questions)} benzersiz soru")


payload = []
for q in unique_questions:
    payload.append({
        "id": q.id,
        "title": q.title,
        "category": q.category,
        "level": q.level,
        "description": q.description,
        "starter_code": q.starter_code,
        "test_cases": q.test_cases,
        "hints": q.hints,
    })


# ════════════════════════════════════════════════════════════════
# Upsert — on_conflict ile çakışmaları güncelle
# ════════════════════════════════════════════════════════════════
print(f"📦 {len(payload)} soru yükleniyor...")

try:
    # 'id' kolonunda unique constraint var, on_conflict='id' ile güncelleme yap
    result = (
        supabase.table("interwiews")
        .upsert(payload, on_conflict="id")
        .execute()
    )
    print(f"✅ {len(payload)} soru başarıyla yüklendi/güncellendi.")
    if result.data:
        print(f"📊 İlk kayıt örneği: id={result.data[0].get('id')}, title={result.data[0].get('title')}")
except Exception as e:
    print(f"❌ Supabase hatası: {e}")
    print("\n💡 Olası çözümler:")
    print("   1. Service role key kullan (anon key RLS nedeniyle yetmez)")
    print("   2. Supabase dashboard > SQL Editor'da çalıştır:")
    print("      ALTER TABLE interwiews DISABLE ROW LEVEL SECURITY;")
    print("   3. Ya da unique constraint'i kaldır:")
    print("      ALTER TABLE interwiews DROP CONSTRAINT IF EXISTS interwiews_id_key;")