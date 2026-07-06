# DB Backup & Recovery Runbook

> **Son güncelleme:** 2026-07-06
> **Backup sıklığı:** Haftalık (Pazartesi 03:00 UTC)
> **Retention:** GitHub Artifact 90 gün + (opsiyonel) S3 cold storage

---

## 📥 Backup'tan geri yükleme (disaster recovery)

### Senaryo: DB bozuldu, production restore gerekli

**1. En son backup'ı al**
- GitHub → https://github.com/kaleminkuheylani/pymulakat-backend/actions/workflows/backup.yml
- Son başarılı run → Artifacts → `pymulakat-db-backup-<id>` indir
- Veya GitHub CLI: `gh run download <run-id> -n pymulakat-db-backup-<run-id>`

**2. Backup'ı doğrula (önizleme)**
```bash
# İçeriği gör
gunzip -c pymulakat-*.sql.gz | head -100

# Tablo sayısı
gunzip -c pymulakat-*.sql.gz | grep -c "^CREATE TABLE"

# Kritik tabloları kontrol et
gunzip -c pymulakat-*.sql.gz | grep -E "CREATE TABLE (profiles|interview_attempts|questions|tutorials)" | head
```

**3. Local'de restore testi (production'a dokunmadan)**
```bash
# Yeni local DB oluştur
createdb pymulakat_restore_test

# Restore
gunzip -c pymulakat-*.sql.gz | psql pymulakat_restore_test

# Doğrula
psql pymulakat_restore_test -c "SELECT COUNT(*) FROM questions;"
psql pymulakat_restore_test -c "SELECT COUNT(*) FROM profiles;"
```

**4. Production'a restore (DİKKATLİ!)**
```bash
# Önce yedek al (mevcut durumu)
pg_dump "$DB_URL" --no-owner --no-privileges --clean --if-exists | gzip > "pre-restore-$(date +%s).sql.gz"

# Restore
gunzip -c pymulakat-*.sql.gz | psql "$DB_URL"

# Doğrula
psql "$DB_URL" -c "SELECT version(); SELECT COUNT(*) FROM questions;"
```

---

## 🔄 Otomatik backup durumu

- ✅ **GitHub Actions** her Pazartesi 03:00 UTC backup alır
- ✅ Artifact 90 gün saklanır (download link Actions UI'da)
- ⏳ **S3 cold storage** — opsiyonel, sınırsız retention

---

## 🔐 Secrets

- `DB_URL` — Supabase direct connection string
- (opsiyonel) `S3_*` — Cloudflare R2 / AWS S3 / Backblaze B2

**Secret tanımlama:** GitHub → Settings → Secrets and variables → Actions → New repository secret

---

## 📋 Checklist (recovery drill için)

[ ] 6 ayda bir "restore test" yap:
  1. Son artifact indir
  2. Local DB'de restore et
  3. 5 kritik tabloyu say (questions, profiles, interview_attempts, tutorials, ...)
  4. Sonuç raporla

[ ] Yıl başında backup stratejisini gözden geçir:
  1. Retention yeterli mi? (90 gün → S3 ekle)
  2. Supabase PITR açık mı? (Pro plan gerekli)
  3. DB büyümesi öngörülebilir mi?
