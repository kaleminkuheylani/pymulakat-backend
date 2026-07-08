# data/ — Soru seti mimarisi

## Mevcut CSV'ler

| Dosya | Kaynak | Soru | Kategori | Durum |
|---|---|---|---|---|
| `QUESTIONS_FACTORY.csv` | Manuel eklenen yeni set | 67 | 5 (python-basics, strings, list-dict, pandas, algorithms) | aktif runtime |
| `QUESTIONS-v3.csv` | Eski QUESTIONS-v3.py'den donusturuldu | 102 | 5 (python-basics, list-dict, pandas, algorithms, data-structures) | yedek / opsiyonel |

## CSV mimarisi

```
data/QUESTIONS_FACTORY.csv    ← İnsan kaynağı (edit-friendly)
        ↓ (scripts/csv_to_json.py)
data/QUESTIONS-v3.json        ← Runtime artifact (build output)
        ↓ (question_loader.py)
Backend API (fallback zinciri)
```

Fallback zinciri (question_loader.py):
1. DB (Supabase) — primary, DB dolu ise
2. data/QUESTIONS-v3.json — build artifact
3. data/QUESTIONS_FACTORY.csv — CSV runtime parse
4. data/QUESTIONS-v3.py — LEGACY (eski dataclass, syntax bozuk olabilir)

**Neden CSV?**
- Excel / Google Sheets / Numbers'ta açılır
- Multi-line description doğrudan hücre içinde
- Syntax hatası riski sıfır (JSON'da quote kaçışı gerekmez)
- Non-developer katkı yapabilir
- Diff/PR review kolay

## CSV format (RFC 4180)

**Kolon sırası** (kontrol kolon için):
```
category,title,level,description,starter_code,test_cases,hints,id
```

| Kolon | Tip | Zorunlu | Açıklama |
|---|---|---|---|
| `id` | int | ✅ | Unique pozitif integer (1, 2, 3...) |
| `category` | enum | ✅ | `python-basics` \| `strings` \| `list-dict` \| `pandas` \| `algorithms` |
| `level` | enum | ✅ | `beginner` \| `intermediate` \| `advanced` |
| `title` | str | ✅ | Kısa başlık (max 100 char) |
| `description` | str | ✅ | Çok satırlı açıklama (`\n` serbest) |
| `starter_code` | str | ❌ | `def fn_name(...)` başlayan Python şablonu |
| `test_cases` | JSON | ❌ | Array string: `[{"input":..., "expected":...}]` |
| `hints` | JSON | ❌ | Array string: `["💡 ipucu 1", ...]` |

## Pipeline kullanımı

### Soru eklemek / düzenlemek

1. `data/QUESTIONS_FACTORY.csv` dosyasını aç (mobile: Google Sheets veya metin editörü)
2. Yeni satır ekle veya mevcut satırı düzenle
3. (Önerilir) CSV'yi kaydet ve şu komutu çalıştır:
   ```bash
   python3 scripts/csv_to_json.py --dry-run    # sadece valide et
   python3 scripts/csv_to_json.py              # JSON üret
   ```
4. JSON → GitHub → otomatik Railway deploy

### JSON → CSV geri dönüş (QA / test)

```bash
python3 scripts/json_to_csv.py
```

## Mobile'da düzenleme

**En güvenli**: Google Sheets (iOS/Android/Web) — CSV import/export built-in
**En hızlı**: VSCode mobile (iPad) veya Textastic — düz metin edit
**Önerilmez**: Safari/Chrome text input — quote escape bozulabilir

### ⚠️ Dikkat edilecekler

- Virgül içeren alanlar otomatik tırnak içine alınır (`QUOTE_ALL`)
- Açılış quote varsa editör kapatmalı, aksi halde parse hatası
- Tüm alanlar UTF-8, Türkçe karakterler OK
- Çok satırlı description: tırnak içinde `\n` serbest
- test_cases/hints: JSON array string olarak yaz (validasyon gerekir)

## Validasyon

`scripts/csv_to_json.py` otomatik kontrol eder:
- Duplicate ID
- Geçersiz kategori/level
- Boş title
- Bozuk JSON (test_cases/hints)
- ID pozitif int olmalı

Hata varsa exit code 1, JSON üretilmez.

## Geçmiş

| Versiyon | Tarih | Not |
|---|---|---|
| QUESTIONS.py | 2025-07 | İlk legacy dataclass format |
| QUESTIONS-v3.py | 2025-07 | Genişletilmiş, syntax bozuk |
| QUESTIONS-v4.json | 2025-07 | JSON geçişi (165 soru, 13 kategori) — **devre dışı** |
| QUESTIONS_FACTORY.csv | 2025-07 | **Şu an aktif** — 67 soru, 5 kategori |

V4 dosyaları `.disabled` olarak yedekte — geri dönmek için `.disabled` suffix'i kaldır.