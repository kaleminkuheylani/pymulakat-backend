# CSV → DB Seed Operasyonu

> **Endpoint:** `POST /admin/seed-questions`
> **Amaç:** `data/QUESTIONS-v3.csv` içeriğini Supabase `questions` tablosuna yazmak.
> **Tarih:** 2026-07-09

CSV'yi değiştirdikten sonra prod'a yansıtmak için tek endpoint. **Parametresiz, idempotent** — tekrar tekrar çağrılabilir, aynı sonucu verir.

## İstek

```http
POST /admin/seed-questions
X-Admin-Secret: <ADMIN_SECRET env değeri>
```

Body yok. Header yeter.

## Cevap

```json
{
  "ok": true,
  "rows_planned": 132,
  "upserted": 132,
  "failed": 0,
  "failed_detail": [],
  "csv_fields_written": [
    "description", "starter_code", "test_cases", "hints",
    "function_name", "title", "level", "category"
  ],
  "preserved_db_fields": [
    "slug", "complexity", "explanation", "meta_title",
    "meta_description", "meta_keywords", "related_concepts",
    "related_question_ids", "tags", "topic", "tutorial_slug"
  ],
  "next_step": "/admin/invalidate-cache çağırıp cache temizle, sonra /api/v2/questions/{id} ile doğrula"
}
```

## Ne yazar / ne yazmaz

CSV'deki `id` kolonu → DB `legacy_id` kolonuna yazılır (DB'nin auto-increment primary key değişmez). `on_conflict="legacy_id"` ile çalışır: aynı `legacy_id` varsa UPDATE, yoksa INSERT.

| CSV kolonu | DB kolonu | Davranış |
|---|---|---|
| `id` | `legacy_id` | Sorular orijinal id'lerini korur |
| `category`, `title`, `level` | aynı | Üzerine yazılır |
| `description`, `starter_code`, `test_cases`, `hints`, `function_name` | aynı | Üzerine yazılır |
| (yok) | `slug`, `complexity`, `explanation`, `meta_*`, `related_concepts`, `related_question_ids`, `tags`, `topic`, `tutorial_slug` | **Dokunulmaz** — DB-side managed |

`preserved_db_fields` listesinde gösterilen kolonlar CSV'de tanımlı değil, **DB-side ayrı yönetilen alanlar.** Bu yüzden endpoint bunları ezmez — production'daki `slug`, `related_question_ids`, `meta_description` gibi değerler korunur.

## Operasyon adımları

1. **CSV'yi push** et (github'a `data/QUESTIONS-v3.csv` değişikliği).
2. **Railway redeploy** bekle (CSV build artifact'e dahil olur).
3. **Seed çağrısı:**
   ```bash
   curl -X POST https://api.example.com/admin/seed-questions \
     -H "X-Admin-Secret: $ADMIN_SECRET"
   ```
4. **Cache invalidate:**
   ```bash
   curl -X POST https://api.example.com/admin/invalidate-cache \
     -H "X-Admin-Secret: $ADMIN_SECRET"
   ```
5. **Doğrulama:**
   ```bash
   curl https://api.example.com/api/v2/questions/14 | jq .data.description
   ```
   Bu komut yeni CSV'deki description'ı dönmeli.

## Güvenlik

| Konu | Davranış |
|---|---|
| Endpoint prefix | `/admin/*` — admin namespace |
| Koruma | `X-Admin-Secret` header = `ADMIN_SECRET` env |
| Header eksik/yanlış | `403 admin yetkisi gerekli` |
| Idempotent | Aynı çağrıyı tekrar tekrar yapabilirsin, sonuç değişmez |
| Destructive | Sadece CSV'de var olan alanlar yazılır, DB-managed alanlar korunur |
| Body parsing yok | Eski dry_run/limit/ids/fields parametreleri kaldırıldı, scope net |

## Hata durumları

| HTTP | Sebep |
|---|---|
| 403 | `X-Admin-Secret` eksik veya yanlış |
| 400 | `SUPABASE_URL` veya `SUPABASE_SERVICE_ROLE_KEY` env tanımlı değil |
| 500 | CSV dosyası eksik (`data/QUESTIONS-v3.csv`) |

İçerideki satır upsert hataları `failed_detail` listesinde döner (DB constraint, network timeout vs.); endpoint HTTP 200 döndürürse bile partial upsert olabilir.
