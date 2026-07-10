"""
_generate_questions.py — Mavis API ile CSV-uyumlu yeni sorular üret.

Mimari: CSV-only, deterministik. Mevcut kategorilerin dağılımına göre
eksik kategorilere öncelik verir. 10 yeni soru ekler.

API key: MAVIS_API_KEY (Railway env)
API URL: MAVIS_API_URL (default OpenAI uyumlu)

Kullanım:
    MAVIS_API_KEY=sk-... python3 data/_generate_questions.py
    MAVIS_API_KEY=sk-... python3 data/_generate_questions.py --count 20

Davranış:
- dry_run YOK — direkt çalışır (mimari: minimal patch, otomasyon)
- Mevcut 142 satır korunur, yeni 10 eklenir (id 182-191)
- Üretilen sorular CSV'deki başlık/function_name ile çakışmaz
- LLM JSON array döner; parse hatası varsa script exit
- İdempotent: aynı çalıştırma 2 kez → 2 kez ekler (manuel kontrol)
"""
import csv
import os
import sys
import json
import re
import shutil
from pathlib import Path
from datetime import datetime
from collections import Counter

CSV = Path("data/QUESTIONS-v3.csv")
BACKUP = Path(f"data/QUESTIONS-v3.csv.bak-{datetime.now().strftime('%H%M%S')}-pre-mavis")
API_KEY = os.environ.get("MAVIS_API_KEY", "")
API_URL = os.environ.get("MAVIS_API_URL", "https://api.openai.com/v1")
MODEL = os.environ.get("MAVIS_MODEL", "gpt-4o-mini")

# ─── CLI ─────────────────────────────────────────────────────
count = 10
if "--count" in sys.argv:
    idx = sys.argv.index("--count")
    count = int(sys.argv[idx + 1])

if not API_KEY:
    print("❌ MAVIS_API_KEY environment variable gerekli")
    print("   export MAVIS_API_KEY=sk-...")
    print("   (Railway'de MAVIS_API_KEY env variable olarak set edilecek)")
    sys.exit(1)

# ─── 1) Yedek ───────────────────────────────────────────────
shutil.copy(CSV, BACKUP)
print(f"✓ Yedek: {BACKUP}")

# ─── 2) Mevcut CSV analizi ──────────────────────────────────
rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
header = list(rows[0].keys())
existing_titles = {r["title"].lower().strip() for r in rows}
existing_fns = {r["function_name"].lower().strip() for r in rows}
existing_ids = {int(r["id"]) for r in rows}

# Kategori dağılımı
cat_count = Counter(r["category"] for r in rows)
print(f"✓ Mevcut: {len(rows)} soru, {len(cat_count)} kategori")
for cat, n in sorted(cat_count.items(), key=lambda x: x[1]):
    print(f"    {cat:<25} {n:>3}")

# ─── 3) Eksik kategorilere öncelik ─────────────────────────
# En az sorulu 5 kategori × 2 = 10 (dengeli dağılım)
sorted_cats = sorted(cat_count.items(), key=lambda x: x[1])
target_distribution = []
remaining = count
for cat, n in sorted_cats:
    if remaining <= 0:
        break
    take = min(2, remaining)
    target_distribution.append((cat, take))
    remaining -= take
# Hâlâ kaldıysa en büyük kategorilere ekle
if remaining > 0:
    for cat, n in reversed(sorted_cats):
        if remaining <= 0:
            break
        take = min(2, remaining)
        target_distribution.append((cat, take))
        remaining -= take

print(f"\n✓ Hedef dağılım:")
for cat, n in target_distribution:
    print(f"    {cat:<25} +{n} soru")

# ─── 4) Mavis API prompt ────────────────────────────────────
system_prompt = """Sen bir Python mülakat soru yazarısın. JSON array döndür.

Kurallar:
- Her soru için TAM 9 alan (CSV sırası): category, title, level, description, starter_code, test_cases, hints, id (string), function_name
- title: 3-6 kelime, Türkçe (veya İngilizce standart algoritma adı)
- level: beginner | intermediate | advanced
- description: 80-300 karakter, soruyu açıkça ifade et, örnek input/output ver
- starter_code: Python def fonksiyon imzası + 'pass', tip annotation'lı
- test_cases: JSON string array, 2-4 örnek, input/expected alanları
- hints: JSON string array, 2-3 ipucu (💡 ile başlayan)
- id: "0" placeholder (script otomatik atar)
- function_name: snake_case, mevcut fonksiyonlarla çakışmasın
- Klasik algoritma soruları (interview standard)
- Türkçe description + İngilizce fonksiyon adı (örn: 'LIS', 'fibonacci')

Sadece JSON array döndür, başka metin yok. Sadece JSON."""

# Kategori için örnekler
example_per_cat = ""
for cat, n in target_distribution:
    example_per_cat += f"\n- {cat}: {n} soru (mevcut: {cat_count[cat]})"

# Mevcut başlıklar (çakışma kontrolü)
existing_list = sorted(existing_titles)[:50]
user_prompt = f"""Şu mevcut 142 soruya EK OLARAK {count} yeni soru üret.

Mevcut kategoriler (azdan çoğa):
{chr(10).join(f'  {cat}: {n}' for cat, n in sorted_cats)}

İSTENEN DAĞILIM:{example_per_cat}

Mevcut soru başlıklarından (ilk 50): {existing_list}

ÖNEMLİ:
- Başlıklar ve function_name'ler mevcut 142 sorudan farklı olmalı
- Çakışma kontrolü: ürettiğin her başlık benzersiz olmalı
- Sadece JSON array döndür
- Her soruda 'id' alanı "0" olsun (otomatik atanır)

JSON:"""

# ─── 5) Mavis API çağrısı (OpenAI uyumlu) ──────────────────
print(f"\n→ Mavis API çağrısı: {API_URL} (model: {MODEL})")

try:
    from openai import OpenAI
    client = OpenAI(api_key=API_KEY, base_url=API_URL)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=4000,
    )
    content = response.choices[0].message.content.strip()
except ImportError:
    print("❌ openai SDK gerekli: pip install openai")
    sys.exit(1)
except Exception as e:
    print(f"❌ API hatası: {e}")
    sys.exit(1)

# ─── 6) JSON parse ─────────────────────────────────────────
# LLM bazen ```json ... ``` bloğu içinde döner, temizle
content = re.sub(r"^```json\s*", "", content)
content = re.sub(r"\s*```$", "", content)

try:
    new_questions = json.loads(content)
except json.JSONDecodeError as e:
    print(f"❌ JSON parse hatası: {e}")
    print(f"İlk 500 char: {content[:500]}")
    sys.exit(1)

if not isinstance(new_questions, list):
    print(f"❌ JSON array bekleniyor, alınan: {type(new_questions)}")
    sys.exit(1)

print(f"✓ {len(new_questions)} soru üretildi (ham)")

# ─── 7) Validasyon + id atama + çakışma kontrolü ──────────
next_id = max(existing_ids) + 1
added = []
skipped = []
seen_title = set()
seen_fn = set()

for q in new_questions:
    # Required alanlar
    required = ["category", "title", "level", "description", "starter_code",
                "test_cases", "hints", "id", "function_name"]
    if not all(k in q for k in required):
        skipped.append(("missing_field", q.get("title", "?")))
        continue

    # Çakışma kontrolü
    title_lower = q["title"].lower().strip()
    fn_lower = q["function_name"].lower().strip()
    if title_lower in existing_titles or title_lower in seen_title:
        skipped.append(("title_dup", q["title"]))
        continue
    if fn_lower in existing_fns or fn_lower in seen_fn:
        skipped.append(("fn_dup", q["title"]))
        continue

    # Category dağılım kontrolü
    target_count = dict(target_distribution).get(q["category"], 0)
    cat_added = sum(1 for r in added if r["category"] == q["category"])
    if cat_added >= target_count:
        skipped.append(("category_full", q["title"]))
        continue

    # id atama
    q["id"] = str(next_id)
    next_id += 1
    seen_title.add(title_lower)
    seen_fn.add(fn_lower)
    added.append(q)

# ─── 8) CSV'ye yaz ─────────────────────────────────────────
for q in added:
    rows.append(q)

# Deterministic sıralama: id'ye göre
rows.sort(key=lambda r: int(r["id"]))

with open(CSV, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=header)
    w.writeheader()
    w.writerows(rows)

# ─── 9) Rapor ──────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"✓ {len(added)} yeni soru eklendi")
if skipped:
    print(f"⚠ {len(skipped)} atlandı:")
    for reason, title in skipped:
        print(f"    [{reason}] {title}")

print(f"\nYeni sorular:")
for q in added:
    print(f"  id={q['id']:>3} [{q['category']:<22}] {q['title']}")

print(f"\n✓ CSV: {CSV} ({CSV.stat().st_size} bytes)")
print(f"  Toplam: {len(rows)} soru")
