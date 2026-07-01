"""Geçici admin endpointleri — migration ve bakım için.

⚠️ PRODUCTION'DA KULLANIRKEN DİKKATLİ OL!
Bu endpoint migration çalıştırır, DB'ye büyük INSERT/UPDATE yapar.
Sadece ilk kurulumda veya veri güncellemesinde kullanılmalı.

Kullanım:
    curl -X POST https://pymulakat-backend-production.up.railway.app/admin/migrate/questions
    curl -X POST https://pymulakat-backend-production.up.railway.app/admin/migrate/tutorials
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import os
import sys
import json
import re
import logging

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


class MigrationResponse(BaseModel):
    ok: bool
    message: str
    details: dict = {}


def _run_script(script_name: str) -> dict:
    """Bir Python script'i subprocess olarak çalıştır."""
    import subprocess
    script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", script_name)
    script_path = os.path.abspath(script_path)

    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Script bulunamadı: {script_path}")

    # Env'i forward et
    env = os.environ.copy()

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            env=env,
            timeout=300,  # 5 dakika timeout
        )
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout[-3000:],  # Son 3000 char
            "stderr": result.stderr[-1000:] if result.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {"exit_code": -1, "error": "Migration 300 saniyede tamamlanmadı"}
    except Exception as e:
        return {"exit_code": -1, "error": str(e)}


@router.post("/migrate/questions", response_model=MigrationResponse)
async def migrate_questions():
    """QUESTIONS.py + SEO_CONTENT'i Supabase 'interwiews' tablosuna migrate et."""
    result = _run_script("migrate_questions.py")
    return MigrationResponse(
        ok=result.get("exit_code") == 0,
        message="Migration tamamlandı" if result.get("exit_code") == 0 else "Migration başarısız",
        details=result,
    )


@router.post("/update/seo-fields", response_model=MigrationResponse)
async def update_seo_fields():
    """Mevcut 67 satırın SEO alanlarını title üzerinden güncelle."""
    result = _run_script("update_seo_fields.py")
    return MigrationResponse(
        ok=result.get("exit_code") == 0,
        message="SEO güncelleme tamamlandı" if result.get("exit_code") == 0 else "SEO güncelleme başarısız",
        details=result,
    )


@router.post("/migrate/tutorials", response_model=MigrationResponse)
async def migrate_tutorials():
    """7 fallback tutorial'ı 'tutorials' tablosuna migrate et."""
    result = _run_script("migrate_tutorials.py")
    return MigrationResponse(
        ok=result.get("exit_code") == 0,
        message="Migration tamamlandı" if result.get("exit_code") == 0 else "Migration başarısız",
        details=result,
    )


@router.post("/migrate/slugs", response_model=MigrationResponse)
async def migrate_slugs(force: bool = False):
    """interwiews tablosuna title'dan slug üretip yaz (canonical URL için)."""
    import re
    try:
        # 1. psycopg2 ile slug kolonu ekle (DATABASE_URL'den) — kolon zaten var muhtemelen
        sql_added = False
        sql_error = None
        try:
            import psycopg2
            db_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
            if db_url:
                try:
                    conn = psycopg2.connect(db_url)
                    conn.autocommit = True
                    cur = conn.cursor()
                    cur.execute("ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS slug TEXT")
                    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_interwiews_slug ON public.interwiews(slug) WHERE slug IS NOT NULL")
                    cur.execute("NOTIFY pgrst, 'reload schema'")
                    cur.close()
                    conn.close()
                    sql_added = True
                    print("✅ Slug kolonu + index eklendi (psycopg2)")
                except Exception as e:
                    sql_error = str(e)[:200]
                    print(f"⚠️ psycopg2 ALTER basarisiz: {e}")
            else:
                sql_error = "DATABASE_URL tanimli degil, SQL atlaniyor"
                print(f"⚠️ {sql_error}")
        except ImportError:
            sql_error = "psycopg2 yuklu degil"
            print(f"⚠️ {sql_error}")

        # 2. Supabase admin ile devam
        from supabase_client import get_supabase_admin
        sb = get_supabase_admin()

        try:
            result = sb.table("interwiews").select("id, title, slug").execute()
            rows = result.data or []
            print(f"📝 [SLUGS] {len(rows)} soru bulundu")
        except Exception as e:
            return MigrationResponse(
                ok=False,
                message=f"SELECT hatasi (slug kolonu hala yok?): {e}. SQL durumu: {'OK' if sql_added else sql_error}",
            )

        def slugify(text: str) -> str:
            tr = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
            text = text.lower().translate(tr)
            text = re.sub(r'[^a-z0-9\s-]', '', text)
            text = re.sub(r'\s+', '-', text).strip('-')
            return text[:80]

        updated = 0
        skipped = 0
        errors = []
        seen_slugs = set()
        for row in rows:
            title = row.get("title", "")
            existing = row.get("slug")
            if existing and not force:
                skipped += 1
                seen_slugs.add(existing)
                continue

            new_slug = slugify(title)
            final_slug = new_slug
            counter = 1
            while final_slug in seen_slugs:
                counter += 1
                final_slug = f"{new_slug}-{counter}"
            seen_slugs.add(final_slug)

            try:
                sb.table("interwiews").update({"slug": final_slug}).eq("id", row["id"]).execute()
                updated += 1
            except Exception as e:
                errors.append({"id": row["id"], "title": title, "error": str(e)})

        return MigrationResponse(
            ok=True,
            message=f"{updated} yeni slug, {skipped} zaten vardi (SQL: {'OK' if sql_added else sql_error})",
            details={
                "updated": updated,
                "skipped": skipped,
                "total": len(rows),
                "sql_added": sql_added,
                "sql_error": sql_error,
                "errors": errors[:5],
            },
        )
    except Exception as e:
        print(f"❌ [SLUGS] {type(e).__name__}: {e}")

@router.post("/migrate/related-questions")
async def migrate_related_questions():
    """Hardcoded mapping — frontend QuestionMeta ile senkronize."""
    try:
        RELATED_MAP = {
            1: [2, 3, 10, 11], 2: [53, 11, 1], 3: [1, 7, 17, 19],
            4: [30, 14, 10], 5: [9, 14, 16], 6: [11, 19, 29],
            7: [1, 3, 17], 8: [9, 11, 16], 9: [5, 7],
            10: [1, 3, 7, 17], 11: [12, 14, 16], 12: [26, 27, 28],
            13: [1, 17, 23], 14: [4, 30, 10], 15: [9, 11, 16],
            16: [17, 19, 23], 17: [23, 25, 27], 18: [1, 2, 3],
            19: [6, 18, 20], 20: [1, 2, 3], 21: [7, 22, 24],
            22: [1, 21, 25], 23: [11, 19, 25], 24: [19, 23, 25],
            25: [22, 24, 27], 26: [27, 28, 29], 27: [26, 28, 29],
            28: [26, 27, 29], 29: [26, 27, 28], 30: [14, 4, 27],
            31: [28, 29, 30], 32: [33, 35, 36], 33: [32, 35, 36],
            34: [28, 29, 30], 35: [8, 26, 27, 29], 36: [32, 33, 35],
            37: [38, 41, 43], 38: [32, 33, 41], 39: [32, 33, 35],
            40: [32, 33, 41], 41: [37, 42, 43], 42: [41, 43, 44],
            43: [38, 42, 44], 44: [32, 42, 43], 45: [38, 41, 43],
            46: [47, 48, 49], 47: [46, 48, 49], 48: [46, 47, 49],
            49: [46, 47, 48], 50: [16, 47, 48, 49], 51: [1, 3, 7],
            52: [1, 17, 23], 53: [1, 7, 17], 54: [1, 17, 19],
            55: [1, 7, 23], 56: [1, 17, 23], 57: [19, 38, 41],
            58: [1, 7, 17], 59: [19, 38, 41], 60: [1, 7, 17],
            61: [19, 23, 38], 62: [1, 17, 23], 63: [19, 38, 41],
            64: [19, 23, 38], 65: [38, 41, 42], 66: [38, 41, 43],
            67: [38, 41, 43],
        }
        print(f"Mapping: {len(RELATED_MAP)} entry")

        from supabase_client import get_supabase_admin
        sb = get_supabase_admin()

        updated = 0
        errors = []
        for qid, related_list in RELATED_MAP.items():
            try:
                sb.table("interwiews").update({"related_question_ids": related_list}).eq("id", qid).execute()
                updated += 1
            except Exception as e:
                errors.append({"id": qid, "error": str(e)[:100]})

        return {
            "ok": True,
            "message": f"{updated} soruya related_question_ids yazildi",
            "details": {"updated": updated, "total": len(RELATED_MAP), "errors": errors[:5]},
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"ok": False, "message": f"Hata: {e}"}

@router.post("/migrate/schema", response_model=MigrationResponse)
async def migrate_schema():
    """interwiews tablosuna yeni kolonları ekle (idempotent)."""
    import subprocess
    sql_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "migrate_schema.sql")
    sql_path = os.path.abspath(sql_path)

    if not os.path.exists(sql_path):
        raise HTTPException(404, f"SQL bulunamadı: {sql_path}")

    try:
        from supabase_client import get_supabase_admin
        sb = get_supabase_admin()

        with open(sql_path, "r") as f:
            sql_content = f.read()

        # SQL'i statement'lara böl ve her birini çalıştır
        statements = [s.strip() for s in sql_content.split(";") if s.strip() and not s.strip().startswith("--")]

        results = []
        for i, stmt in enumerate(statements):
            try:
                # rpc ile SQL çalıştır (PostgREST bunu desteklemiyor)
                # Alternatif: psycopg2 kullan
                results.append({"index": i, "stmt_preview": stmt[:80], "ok": True})
            except Exception as e:
                results.append({"index": i, "stmt_preview": stmt[:80], "ok": False, "error": str(e)})

        # psycopg2 ile direkt connection
        try:
            import psycopg2
            db_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
            if db_url:
                conn = psycopg2.connect(db_url)
                conn.autocommit = True
                cur = conn.cursor()
                cur.execute(sql_content)
                cur.close()
                conn.close()
                return MigrationResponse(
                    ok=True,
                    message="Schema migration tamamlandı (psycopg2)",
                    details={"method": "psycopg2", "statements": len(statements)},
                )
        except ImportError:
            pass
        except Exception as e:
            return MigrationResponse(
                ok=False,
                message=f"psycopg2 hatası: {e}",
                details={"hint": "DATABASE_URL tanımlı mı? psycopg2 yüklü mü?"},
            )

        # Fallback: supabase rpc (exec_sql fonksiyonu gerekli)
        return MigrationResponse(
            ok=False,
            message="Schema migration için DATABASE_URL veya Supabase exec_sql gerekli",
            details={
                "hint": "Supabase Dashboard → SQL Editor'da migrate_schema.sql'i manuel çalıştır",
                "sql_file_path": sql_path,
            },
        )
    except Exception as e:
        return MigrationResponse(
            ok=False,
            message=f"Schema migration hatası: {e}",
            details={},
        )


@router.get("/health")
async def admin_health():
    """Admin endpoint sağlık kontrolü."""
    return {
        "ok": True,
        "supabase_url": os.getenv("SUPABASE_URL", "NOT SET"),
        "has_service_key": bool(os.getenv("SUPABASE_SERVICE_ROLE_KEY")),
    }


# ═══════════════════════════════════════════════════════════
# Gemini ile Soru Üretimi (Dağılım Analizi)
# ═══════════════════════════════════════════════════════════

class GenerateQuestionsRequest(BaseModel):
    n: int = 5
    target_total: int = 90
    dry_run: bool = False
    categories: list[str] = []  # opsiyonel: belirli kategoriler


class GenerateQuestionsResponse(BaseModel):
    ok: bool
    message: str
    distribution: dict = {}
    gaps: list = []
    plan: list = []
    generated: list = []
    inserted_ids: list = []
    skipped: int = 0
    error: str = ""


@router.post("/generate/questions", response_model=GenerateQuestionsResponse)
async def generate_questions_endpoint(req: GenerateQuestionsRequest):
    """
    QUESTIONS.py + Supabase dağılımını analiz et, eksik yerlere
    Gemini ile yeni sorular üret, Supabase'e INSERT et.

    Kullanım:
        POST /admin/generate/questions
        Body: {"n": 5, "dry_run": false}

    Akış:
    1. QUESTIONS.py'i yükle
    2. Supabase'den mevcut soruları çek (DB üstün, fallback QUESTIONS.py)
    3. Dağılım analizi (kategori + level)
    4. Gap tespiti (eksik kategoriler/seviyeler)
    5. Gemini prompt hazırla
    6. Gemini'den soruları al
    7. dry_run=False ise Supabase'e INSERT
    """
    try:
        # 1. QUESTIONS.py'den örnek format al
        from data.QUESTIONS import QUESTIONS as FALLBACK_QS
        sample = FALLBACK_QS[:1]
        if sample:
            q = sample[0]
            existing_questions_sample = f'''Question(
    id={q.id},
    title={q.title!r},
    category={q.category!r},
    level={q.level!r},
    description="""{q.description[:300]}...""",
    starter_code="""{q.starter_code}""",
    test_cases=[{{'input': ..., 'expected': ...}}],
    hints=["💡 İpucu 1: ..."]
)'''
        else:
            existing_questions_sample = "(örnek bulunamadı)"

        # 2. DB'den mevcut soruları çek (DB öncelikli)
        from supabase_client import get_supabase_admin
        sb = get_supabase_admin()
        try:
            result = sb.table("interwiews").select("id, title, category, level").execute()
            db_questions = result.data or []
        except Exception as e:
            logger.warning("Supabase'den soru okunamadı, fallback kullanılıyor: %s", e)
            db_questions = []

        # 3. Dağılımı analiz et
        from services.question_distribution import (
            analyze_questions_py, identify_gaps,
            select_questions_to_generate, get_next_id,
            build_distribution_prompt,
        )

        if db_questions:
            # DB'den gelen minimal dict'leri normalize et
            class _Q:
                def __init__(self, d):
                    self.id = d.get("id", 0)
                    self.title = d.get("title", "")
                    self.category = d.get("category", "")
                    self.level = d.get("level", "")

            qs_objects = [_Q(d) for d in db_questions]
            distribution = analyze_questions_py(qs_objects)
        else:
            distribution = analyze_questions_py(FALLBACK_QS)

        # 4. Gap tespiti
        gaps = identify_gaps(distribution, target_total=req.target_total)

        # Kategori filtresi
        if req.categories:
            gaps = [g for g in gaps if g.get("category") in req.categories or g.get("type") == "level"]

        # 5. Plan seç
        plan = select_questions_to_generate(gaps, n=req.n)

        if not plan:
            return GenerateQuestionsResponse(
                ok=False,
                message="Eksik kategori bulunamadı (dağılım yeterli)",
                distribution=distribution,
                gaps=gaps,
            )

        # 6. Gemini prompt
        prompt = build_distribution_prompt(plan, existing_questions_sample)

        # 7. Gemini'den al
        from services.gemini import AIQuestionGenerator
        import google.generativeai as genai_mod
        gen = AIQuestionGenerator()

        try:
            response = gen.model.generate_content(
                prompt,
                generation_config=genai_mod.GenerationConfig(
                    response_mime_type="application/json"
                ),
            )
            raw_text = response.text.strip()
            # Markdown code block temizle
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                raw_text = re.sub(r"\s*```$", "", raw_text)
            generated = json.loads(raw_text)
        except Exception as e:
            return GenerateQuestionsResponse(
                ok=False,
                message=f"Gemini hatası: {e}",
                distribution=distribution,
                gaps=gaps,
                plan=plan,
                error=str(e),
            )

        # 8. Validate + ID ata
        existing_ids = distribution["existing_ids"]
        next_id = get_next_id(existing_ids)

        valid_questions = []
        skipped = 0
        for item in generated:
            try:
                # Zorunlu alanlar
                if not all(k in item for k in ("title", "category", "level", "description",
                                                "starter_code", "test_cases", "hints")):
                    skipped += 1
                    continue
                item["id"] = next_id
                next_id += 1
                # Default değerler
                item.setdefault("complexity", "O(n)")
                item.setdefault("tutorial_slug", None)
                item.setdefault("slug", None)
                valid_questions.append(item)
            except Exception:
                skipped += 1

        # 9. dry_run ise sadece göster
        if req.dry_run:
            return GenerateQuestionsResponse(
                ok=True,
                message=f"DRY RUN: {len(valid_questions)} soru üretildi (DB'ye yazılmadı)",
                distribution=distribution,
                gaps=gaps,
                plan=plan,
                generated=valid_questions,
                skipped=skipped,
            )

        # 10. Supabase'e INSERT
        inserted_ids = []
        for item in valid_questions:
            try:
                # day/week/theme/difficulty default
                item.setdefault("day", 1)
                item.setdefault("week", 1)
                item.setdefault("theme", item["category"])
                item.setdefault("difficulty", "medium")
                item.setdefault("related_concepts", [])
                item.setdefault("related_question_ids", [])

                # Slug üret (title'dan)
                if not item.get("slug"):
                    from services.slug_helper import slugify_tr
                    try:
                        item["slug"] = slugify_tr(item["title"])
                    except Exception:
                        import re as _re
                        item["slug"] = _re.sub(r"[^a-z0-9]+", "-", item["title"].lower()).strip("-")[:80]

                result = sb.table("interwiews").insert(item).execute()
                if result.data:
                    inserted_ids.append(item["id"])
            except Exception as e:
                logger.exception("Insert failed for q%d: %s", item.get("id"), e)
                skipped += 1

        return GenerateQuestionsResponse(
            ok=True,
            message=f"{len(inserted_ids)} soru eklendi ({skipped} atlandı)",
            distribution=distribution,
            gaps=gaps,
            plan=plan,
            generated=valid_questions,
            inserted_ids=inserted_ids,
            skipped=skipped,
        )

    except Exception as e:
        logger.exception("generate_questions_endpoint failed")
        return GenerateQuestionsResponse(
            ok=False,
            message=f"Beklenmeyen hata: {e}",
            error=str(e),
        )# 1782883061
# 1782885672
