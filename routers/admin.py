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
import re
import json
from typing import Dict, List, Optional

router = APIRouter(prefix="/admin", tags=["admin"])


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


@router.post("/fix/duplicate-slugs", response_model=MigrationResponse)
@router.post("/fix/slug", response_model=MigrationResponse)
async def fix_slug_alias():
    """Alias for /fix/duplicate-slugs."""
    return await fix_duplicate_slugs()


@router.post("/fix/slug/tr-ascii", response_model=MigrationResponse)
async def fix_slug_tr_ascii():
    """Tüm slug'lardaki Türkçe karakterleri ASCII'ye çevir.

    Ornek:
      iki-maaş-bordrosunu-birleştir-68 → iki-maas-bordrosunu-birlestir-68
      liste-düzleştirme-8              → liste-duzlestirme-8
    """
    try:
        from supabase_client import get_supabase_admin
        sb = get_supabase_admin()

        # Tüm slug'ları oku
        result = sb.table("interwiews").select("id, slug, title").execute()
        rows = result.data or []

        tr_map = {
            'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c',
            'İ': 'i', 'Ğ': 'g', 'Ü': 'u', 'Ş': 's', 'Ö': 'o', 'Ç': 'c',
        }
        fixed = 0
        skipped = 0
        for r in rows:
            qid = r.get("id")
            slug = r.get("slug", "")
            if not qid or not slug:
                continue
            # ASCII'ye çevir
            new_slug = slug
            for tr, asc in tr_map.items():
                new_slug = new_slug.replace(tr, asc)
            if new_slug != slug:
                try:
                    sb.table("interwiews").update({"slug": new_slug}).eq("id", qid).execute()
                    fixed += 1
                except Exception as e:
                    logger.exception("Slug fix q%d: %s", qid, e)
                    skipped += 1

        return MigrationResponse(
            ok=True,
            message=f"{fixed} slug ASCII'ye çevrildi ({skipped} hata)",
            details={"total": len(rows), "fixed": fixed, "skipped": skipped},
        )
    except Exception as e:
        logger.exception("fix_slug_tr_ascii failed")
        return MigrationResponse(ok=False, message=f"Hata: {e}")


class CreateTutorialRequest(BaseModel):
    slug: str
    title: str
    content_md: str
    description: Optional[str] = None
    category: str = "python-basics"
    difficulty: str = "beginner"
    reading_time_minutes: int = 5
    related_question_ids: List[int] = []
    faq: List[dict] = []


@router.post("/create/tutorial", response_model=MigrationResponse)
async def create_tutorial(payload: CreateTutorialRequest):
    """Yeni tutorial oluştur ve 'tutorials' tablosuna INSERT et.

    Body:
      {
        "slug": "python-palindrome-rehberi",
        "title": "Python Palindrome Algoritma Rehberi",
        "content_md": "Markdown icerik...",
        "description": "Kisa ozet",
        "category": "python-basics",
        "difficulty": "beginner",
        "reading_time_minutes": 7,
        "related_question_ids": [1, 11],
        "faq": [{"q": "Soru", "a": "Cevap"}]
      }
    """
    try:
        from supabase_client import get_supabase_admin
        sb = get_supabase_admin()

        # Slug uniqueness kontrolü
        existing = sb.table("tutorials").select("id, slug").eq("slug", payload.slug).execute()
        if existing.data:
            return MigrationResponse(
                ok=False,
                message=f"Bu slug zaten var: {payload.slug}",
                details={"existing_id": existing.data[0].get("id") if existing.data else None},
            )

        # INSERT - DB semasina uygun
        tutorial = {
            "slug": payload.slug,
            "title": payload.title,
            "content_md": payload.content_md,
            "description": payload.description or payload.title[:150],
            "category": payload.category,
            "difficulty": payload.difficulty,
            "reading_time_minutes": payload.reading_time_minutes,
            "related_question_ids": payload.related_question_ids,
            "faq": payload.faq,
        }

        result = sb.table("tutorials").insert(tutorial).execute()
        if result.data:
            new_id = result.data[0].get("id")
            return MigrationResponse(
                ok=True,
                message=f"Tutorial olusturuldu: {payload.slug} (id={new_id})",
                details={"id": new_id, "slug": payload.slug},
            )
        return MigrationResponse(ok=False, message="INSERT basarisiz, data donmedi")
    except Exception as e:
        logger.exception("create_tutorial failed")
        return MigrationResponse(ok=False, message=f"Hata: {e}")
async def fix_duplicate_slugs():
    """interwiews tablosundaki duplicate slug'ları temizle.

    Mantık:
    - Her slug grubundan sadece 1 tane (en küçük id) korunur
    - Geri kalanların slug'ı 'q{id}' formatına çevrilir
    - Bu sayede unique constraint ihlal edilmez
    """
    try:
        from supabase_client import get_supabase_admin
        sb = get_supabase_admin()

        # 1. Tüm slug'ları çek
        result = sb.table("interwiews").select("id, slug, title").execute()
        rows = result.data or []

        # 2. Slug gruplarını bul
        slug_groups: Dict[str, List[int]] = {}
        for r in rows:
            s = r.get("slug")
            if s:  # boş string ve NULL atla
                slug_groups.setdefault(s, []).append(r["id"])

        # 3. Duplicate'leri tespit et
        duplicates = {s: ids for s, ids in slug_groups.items() if len(ids) > 1}
        if not duplicates:
            return MigrationResponse(
                ok=True,
                message="Duplicate slug yok",
                details={"total": len(rows), "duplicates": 0, "fixed": 0},
            )

        # 4. Her gruptan ilk (en küçük id) kalsın, diğerlerini q{id} yap
        fixed = 0
        for slug, ids in duplicates.items():
            ids_sorted = sorted(ids)
            keep_id = ids_sorted[0]
            for qid in ids_sorted[1:]:
                new_slug = f"q{qid}"
                try:
                    sb.table("interwiews").update({"slug": new_slug}).eq("id", qid).execute()
                    fixed += 1
                except Exception as e:
                    logger.exception("Slug fix failed for id=%s: %s", qid, e)

        return MigrationResponse(
            ok=True,
            message=f"{fixed} duplicate slug temizlendi ({len(duplicates)} grup)",
            details={"total": len(rows), "duplicates": len(duplicates), "fixed": fixed, "groups": duplicates},
        )

    except Exception as e:
        logger.exception("fix_duplicate_slugs failed")
        return MigrationResponse(
            ok=False,
            message=f"Hata: {e}",
        )


# ═══════════════════════════════════════════════════════════
# Gemini ile Soru Üretimi (Output Type Dağılımı)
# ═══════════════════════════════════════════════════════════

class GenerateQuestionsRequest(BaseModel):
    n: int = 5
    target_per_type: int = 12
    dry_run: bool = False
    output_types: list[str] = []  # opsiyonel: belirli tipler


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
    QUESTIONS.py + Supabase dağılımını analiz et, eksik output type'lara
    Gemini ile yeni sorular üret, Supabase'e INSERT et.

    Kategoriler output_type bazlı (string, number, boolean, list, dict, tuple).
    Sorular input → output ilişkisi olan fonksiyonlardır.

    Kullanım:
        POST /admin/generate/questions
        Body: {"n": 5, "dry_run": false}

    Akış:
    1. QUESTIONS.py'den format örneği al
    2. Supabase'den mevcut soruları çek (DB öncelikli)
    3. Output type dağılımı çıkar (test case'lerden)
    4. Eksik tip tespiti
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

        # 2. DB'den mevcut soruları çek
        from supabase_client import get_supabase_admin
        sb = get_supabase_admin()
        db_questions = []
        try:
            result = sb.table("interwiews").select("id, title, category, level, test_cases").execute()
            db_questions = result.data or []
        except Exception as e:
            logger.warning("Supabase'den soru okunamadı, fallback kullanılıyor: %s", e)

        # 3. Dağılımı analiz et
        from services.question_distribution import (
            analyze_questions_py, identify_gaps,
            select_questions_to_generate, get_next_id,
            build_distribution_prompt, infer_output_type,
        )

        if db_questions:
            # DB'den gelen dict'leri Question benzeri objeye çevir
            class _Q:
                def __init__(self, d):
                    self.id = d.get("id", 0)
                    self.title = d.get("title", "")
                    self.category = d.get("category", "")
                    self.level = d.get("level", "")
                    self.test_cases = d.get("test_cases") or []
                    self.starter_code = d.get("starter_code", "")

            qs_objects = [_Q(d) for d in db_questions]
            distribution = analyze_questions_py(qs_objects)
        else:
            distribution = analyze_questions_py(FALLBACK_QS)

        # 4. Gap tespiti
        gaps = identify_gaps(distribution, target_per_type=req.target_per_type)

        # Output type filtresi
        if req.output_types:
            gaps = [g for g in gaps if g.get("output_type") in req.output_types]

        # 5. Plan seç
        plan = select_questions_to_generate(gaps, n=req.n)

        if not plan:
            return GenerateQuestionsResponse(
                ok=False,
                message="Eksik output type bulunamadı (dağılım yeterli)",
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
            raw_text = re.sub(r"^```(?:json)?\s*\n?", "", raw_text, flags=re.IGNORECASE)
            raw_text = re.sub(r"\n?```\s*$", "", raw_text, flags=re.IGNORECASE)
            raw_text = raw_text.strip()

            try:
                generated = json.loads(raw_text)
            except json.JSONDecodeError:
                if raw_text.startswith("{") and raw_text.endswith("}"):
                    raw_text = "[" + raw_text + "]"
                generated = json.loads(raw_text)

            if isinstance(generated, dict):
                generated = [generated]
            # {"questions": [...]} wrapper
            if isinstance(generated, list) and len(generated) == 1 and isinstance(generated[0], dict):
                inner = generated[0]
                list_key = next((k for k, v in inner.items() if isinstance(v, list)), None)
                if list_key and len(inner[list_key]) > 0:
                    generated = inner[list_key]
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
                if not all(k in item for k in ("title", "category", "level", "description",
                                                "starter_code", "test_cases", "hints")):
                    skipped += 1
                    continue
                item["id"] = next_id
                next_id += 1
                item.setdefault("complexity", "O(n)")
                item.setdefault("tutorial_slug", None)
                item.setdefault("slug", None)
                # Output type'ı DB'ye yazma (sadece soru üretimi için kullanıldı)
                item.pop("output_type", None)
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
        # Mevcut slug'ları topla (unique kontrolü için)
        try:
            existing_slugs_res = sb.table("interwiews").select("slug").execute()
            existing_slugs = {r["slug"] for r in (existing_slugs_res.data or []) if r.get("slug")}
        except Exception:
            existing_slugs = set()

        for item in valid_questions:
            try:
                item.setdefault("day", 1)
                item.setdefault("week", 1)
                item.setdefault("theme", item["category"])
                item.setdefault("difficulty", "medium")
                item.setdefault("related_concepts", [])
                item.setdefault("related_question_ids", [])

                if not item.get("slug"):
                    base = re.sub(r"[^a-z0-9]+", "-", item["title"].lower()).strip("-")[:80]
                    slug_candidate = f"{base}-{item['id']}" if base else f"q{item['id']}"
                    counter = 1
                    final = slug_candidate
                    while final in existing_slugs:
                        final = f"{slug_candidate}-{counter}"
                        counter += 1
                    item["slug"] = final
                    existing_slugs.add(final)

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
        )


# ═══════════════════════════════════════════════════════════
# Schedule yönetimi — Gemini otomatik soru üretimi
# ═══════════════════════════════════════════════════════════

class ScheduleUpdate(BaseModel):
    enabled: bool = True
    interval_days: int = 7
    n_questions: int = 5
    target_per_type: int = 12
    dry_run: bool = False


class ScheduleResponse(BaseModel):
    ok: bool
    schedule: dict = {}
    last_result: dict = {}


@router.get("/schedule/generation", response_model=ScheduleResponse)
async def get_schedule_endpoint():
    """Aktif schedule'i getir."""
    from services.question_scheduler import get_schedule
    schedule = get_schedule()
    return ScheduleResponse(ok=True, schedule=schedule)


@router.post("/schedule/generation", response_model=ScheduleResponse)
async def update_schedule_endpoint(payload: ScheduleUpdate):
    """Schedule'i guncelle. interval_days / n_questions / target_per_type ayarlanabilir."""
    from services.question_scheduler import update_schedule, compute_next_run

    updates = {
        "enabled": payload.enabled,
        "interval_days": payload.interval_days,
        "n_questions": payload.n_questions,
        "target_per_type": payload.target_per_type,
        "dry_run": payload.dry_run,
        "next_run_at": compute_next_run(payload.interval_days),
    }
    schedule = update_schedule(updates)
    return ScheduleResponse(ok=True, schedule=schedule)


@router.post("/schedule/generation/run-now", response_model=ScheduleResponse)
async def run_schedule_now():
    """Schedule'i simdi calistir (next_run_at'i beklemeden)."""
    from services.question_scheduler import run_scheduled_generation, get_schedule
    result = run_scheduled_generation()
    return ScheduleResponse(ok=result.get("ok", True), schedule=get_schedule(), last_result=result)


# ═══════════════════════════════════════════════════════════
# Cron Endpoint — Railway / external cron icin
# Shared secret ile korunur (CRON_SECRET env variable)
# ═══════════════════════════════════════════════════════════

@router.post("/cron/run-question-generation")
async def cron_run_question_generation(request: Request):
    """Cron job tarafindan cagrilir. Shared secret ile korunur.

    Cron ornegi (her Pazartesi 09:00):
      curl -X POST https://api.com/admin/cron/run-question-generation \\
        -H "X-Cron-Secret: $CRON_SECRET"
    """
    # Shared secret kontrol
    expected = os.getenv("CRON_SECRET", "")
    provided = request.headers.get("X-Cron-Secret", "")
    if not expected or provided != expected:
        # Development'ta CRON_SECRET yoksa skip
        if not expected:
            logger.warning("CRON_SECRET env tanimli degil, endpoint korumasiz")
        else:
            raise HTTPException(401, "Unauthorized")

    from services.question_scheduler import run_scheduled_generation
    result = run_scheduled_generation()
    return result# 1782883061
# 1782885672
