# Railway Deployment Guide

## Quick Start

### 1. Connect Repository

- https://railway.app/new
- Select "Deploy from GitHub repo"
- Choose `kaleminkuheylani/pymulakat-backend`
- Railway detects Python via Nixpacks

### 2. Set Environment Variables

In Railway Dashboard → Variables, add:

```
SUPABASE_URL=https://wetzphluxsamlttszdzw.supabase.co
SUPABASE_ANON_KEY=<your-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
ALLOWED_ORIGINS=https://www.pythonmulakat.com,https://pythonmulakat.com
LOG_LEVEL=WARNING
LOG_FORMAT=json
```

### 3. Deploy

Railway auto-deploys on git push to `main`. First deploy takes 2-3 min.

### 4. Verify

```bash
# Health check (DB connectivity)
curl https://pymulakat-backend-production.up.railway.app/health
# Expected: {"status":"ok","db":{"ok":true},...}

# Categories
curl https://pymulakat-backend-production.up.railway.app/api/v2/categories
# Expected: 5 categories (python-basics, data-structures, list-dict, pandas, algorithms)
```

### 5. Migrate Questions to DB

Run once after first deploy (or when QUESTIONS-v3.py changes):

```bash
# SSH into Railway shell or use 'railway run'
railway run python3 scripts/migrate_to_db.py --audit
```

## Monitoring

Railway provides:
- **Metrics**: CPU, RAM, network (Dashboard → Metrics tab)
- **Logs**: JSON line output (LOG_FORMAT=json)
- **Health checks**: /health endpoint polled every 60s
- **Restart policy**: ON_FAILURE with 10 retries

## Migration Commands

```bash
# Apply migration after QUESTIONS-v3.py change
python3 scripts/migrate_to_db.py --audit

# Dry-run (no DB write)
python3 scripts/migrate_to_db.py --dry-run

# With backup
python3 scripts/migrate_to_db.py --backup --audit
```

## Broken Link Testing

Test URL health periodically:

```bash
python3 scripts/test_broken_links.py \
    --base https://pythonmulakat.com \
    --backend https://pymulakat-backend-production.up.railway.app
```

Exits 0 if all URLs return 200; non-zero otherwise.

## Architecture

```
GitHub push → Railway auto-deploy → uvicorn main:app (2 workers)
                                          ↓
                                       Supabase (DB + Auth)
                                          ↑
                                       Frontend (Vercel)
```

## Cost

Railway free tier: $5/month credit, sufficient for MVP.
After free tier: ~$5-10/month for single instance.

## Rollback

In Railway Dashboard → Deployments → click previous deployment → "Redeploy".

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| 503 on /health | DB unreachable | Check SUPABASE_URL + service_role key |
| 500 on /api | Bug in code | Check Railway logs (JSON formatted) |
| CORS error | Wrong ALLOWED_ORIGINS | Update env var, redeploy |
| Slow responses | Single worker | Increase --workers in railway.json |
