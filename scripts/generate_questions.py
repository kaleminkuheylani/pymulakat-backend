#!/usr/bin/env python3
"""
pymulakat — Mavis (MiniMax) API ile otomatik soru üretici
════════════════════════════════════════════════════════════

Mevcut QUESTIONS-v3.py'yi okur → son ID'yi bulur → dağılımlı yeni sorular üretir
→ aynı dosyaya append eder.

Kullanım:
  export MINIMAX_API_KEY="xxx"
  export MINIMAX_BASE_URL="https://api.minimax.chat/v1"   # opsiyonel
  export MINIMAX_MODEL="MiniMax-M3"                         # opsiyonel
  export GENERATE_COUNT=20                                  # opsiyonel (default 20)
  export DRY_RUN=true                                       # sadece yazdır, dosyaya yazma
  python scripts/generate_questions.py

Dağılım (4 kategori eşit):
  • python-basics     → 5
  • data-structures   → 5
  • algorithms        → 5
  • pandas            → 5
"""

import os
import sys
import json
import time
import re
import logging
import importlib.util
from pathlib import Path
from typing import List, Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("generate")

# ─── Config ──────────────────────────────────────────────
API_KEY = os.environ.get("MINIMAX_API_KEY", "")
BASE_URL = os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.chat/v1")
MODEL = os.environ.get("MINIMAX_MODEL", "MiniMax-M3")
GENERATE_COUNT = int(os.environ.get("GENERATE_COUNT", "20"))
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() == "true"

# Eşit dağılım
CATEGORIES = ["python-basics", "data-structures", "algorithms", "pandas"]
PER_CATEGORY = GENERATE_COUNT // len(CATEGORIES)

# Kaynak dosya
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
QUESTIONS_FILE = DATA_DIR / "QUESTIONS-v3.py"


# ═══════════════════════════════════════════════════════════════
# ─── API Client (OpenAI uyumlu) ───────────────────────────
# ═══════════════════════════════════════════════════════════════

def call_minimax(prompt: str, system: str = "") -> str:
    """Mavis/MiniMax API'ye sohbet isteği gönder, içerik döndür."""
    import urllib.request
    import urllib.error

    if not API_KEY:
        log.error("MINIMAX_API_KEY env tanımlı değil")
        sys.exit(1)

    url = f"{BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        log.error(f"API HTTP {e.code}: {e.read().decode('utf-8')[:500]}")
        raise
    except Exception as e:
        log.error(f"API call failed: {e}")
        raise


# ═══════════════════════════════════════════════════════════════
# ─── Prompt üretici ───────────────────────────────────────
# ═══════════════════════════════════════════════════════════════

PROMPT_TEMPLATE = """Sen bir Python mülakat sorusu tasarımcısısın. Aşağıdaki spesifikasyona uygun
TAM {count} ADET yeni soru üret. Çıktıyı JSON array olarak ver, başka açıklama ekleme.

KATEGORİ: {category}
SEVİYE: {level}

Mevcut soru ID'leri (çakışma): {existing_ids}
Mevcut başlıklar (çakışma): {existing_titles}

FORMAT (her obje):
{{
  "title": "Kısa Türkçe başlık (≤50 karakter)",
  "description": "2-3 cümle açıklama, günlük dil, emoji yok",
  "starter_code": "def fn_name(param1, param2):\\n    \\\"\\\"\\\"Docstring.\\\"\\\"\\\"\\n    pass",
  "test_cases": [
    {{"input": <arg>, "expected": <sonuç>, "description": "kısa test açıklaması"}},
    {{"input": <arg>, "expected": <sonuç>, "description": "..."}},
    {{"input": <arg>, "expected": <sonuç>, "description": "..."}}
  ],
  "hints": [
    "💡 İpucu 1: ...",
    "💡 İpucu 2: ...",
    "💡 İpucu 3: ..."
  ],
  "explanation": "EN AZ 200 KELİME Markdown açıklama. Problem tanımı, 3 farklı yaklaşım (naif, optimize, Pythonic), neden o yaklaşım, time/space karmaşıklığı, edge case'ler, gerçek hayattan örnek. Kod blokları içerebilir.",
  "complexity": "O(?) — kısa açıklama",
  "related_concepts": ["kavram1", "kavram2", "kavram3", "kavram4"],
  "related_question_ids": [<mevcut ID'lerden 3-5 tane>],
  "tags": ["{category}", "{level}", "interview"],
  "slug": "url-friendly-kebab-case"
}}

KURALLAR:
1. Girdi/çıktı her zaman JSON-serializable olsun (string, int, float, list, dict, bool, None)
2. test_cases 3-5 arası
3. explanation 200+ kelime, markdown başlıklar kullanabilir (## gibi)
4. related_question_ids sadece mevcut ID'lerden olsun
5. slug benzersiz, küçük harf, tire ile
6. Mevcut başlıklardan farklı ol — pattern'ın bir tık üstü, ezber değil
7. starter_code imza + docstring + pass yeterli
8. Çıktı: SADECE JSON array, başka hiçbir şey yazma
"""


def get_existing_questions() -> List[Any]:
    """QUESTIONS-v3.py'yi import edip mevcut soruları döndür."""
    spec = importlib.util.spec_from_file_location("q3", QUESTIONS_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.QUESTIONS


def build_prompt(category: str, level: str, existing: List[Any], count: int) -> str:
    existing_ids = sorted({q.id for q in existing})
    existing_titles = [q.title for q in existing if q.category == category]
    return PROMPT_TEMPLATE.format(
        count=count,
        category=category,
        level=level,
        existing_ids=existing_ids,
        existing_titles=existing_titles,
    )


def parse_questions(raw: str) -> List[Dict[str, Any]]:
    """API yanıtından JSON array'i çıkar, parse et."""
    raw = raw.strip()
    # ```json ... ``` bloğu olabilir
    fence_match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", raw, re.DOTALL)
    if fence_match:
        raw = fence_match.group(1)
    # Bazen öncesinde/sonrasında metin olur, ilk [ ile son ] arasını al
    if not raw.startswith("["):
        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end != -1:
            raw = raw[start:end + 1]
    return json.loads(raw)


# ═══════════════════════════════════════════════════════════════
# ─── Append to QUESTIONS-v3.py ────────────────────────────
# ═══════════════════════════════════════════════════════════════

def q_to_python_literal(q: Dict[str, Any], next_id: int) -> str:
    """Dict → Python Question(...) dataclass literal string."""
    def fmt_list(items, indent=8):
        if not items:
            return "[]"
        prefix = " " * indent
        inner = [f"{prefix}    {repr(item)}" for item in items]
        return "[\n" + ",\n".join(inner) + f",\n{prefix}]"

    def fmt_dicts(items, indent=8):
        if not items:
            return "[]"
        prefix = " " * indent
        inner = []
        for it in items:
            inner.append(f"{prefix}    {repr(it)}")
        return "[\n" + ",\n".join(inner) + f",\n{prefix}]"

    return f"""    Question(
        id={next_id},
        title={q["title"]!r},
        category={q.get("category", "python-basics")!r},
        level={q.get("level", "intermediate")!r},
        description={q.get("description", "")!r},
        starter_code={q.get("starter_code", "")!r},
        test_cases={fmt_dicts(q.get("test_cases", []))},
        hints={fmt_list(q.get("hints", []))},
        explanation={q.get("explanation", "")!r},
        complexity={q.get("complexity", "O(n)")!r},
        related_concepts={fmt_list(q.get("related_concepts", []))},
        related_question_ids={fmt_list(q.get("related_question_ids", []))},
        tags={fmt_list(q.get("tags", []))},
        tutorial_slug={q.get("tutorial_slug")!r},
        slug={q.get("slug")!r},
    ),"""


def append_questions(new_questions: List[Dict[str, Any]], start_id: int):
    """QUESTIONS-v3.py'ye yeni soruları ekle."""
    with open(QUESTIONS_FILE) as f:
        content = f.read()
    # Son ] bul ve öncesine ekle
    last_bracket = content.rfind("]")
    if last_bracket == -1:
        raise ValueError("QUESTIONS-v3.py'de QUESTIONS listesi bulunamadı")

    new_blocks = []
    for i, q in enumerate(new_questions):
        # category/level ekle (prompt'ta yoktu)
        q.setdefault("category", "python-basics")
        q.setdefault("level", "intermediate")
        new_blocks.append(q_to_python_literal(q, start_id + i))

    # Mevcut son virgülü kontrol et
    before = content[:last_bracket].rstrip()
    if not before.endswith(","):
        before += ","

    new_content = before + "\n\n" + "\n\n".join(new_blocks) + "\n]\n"
    if DRY_RUN:
        log.info(f"[DRY_RUN] {len(new_questions)} soru eklenecek (ID {start_id}..{start_id + len(new_questions) - 1})")
        return

    with open(QUESTIONS_FILE, "w") as f:
        f.write(new_content)
    log.info(f"✅ {len(new_questions)} soru eklendi (ID {start_id}..{start_id + len(new_questions) - 1})")


# ═══════════════════════════════════════════════════════════════
# ─── Main ─────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════

def main():
    log.info("=" * 60)
    log.info("Mavis API ile soru üretimi")
    log.info(f"Toplam: {GENERATE_COUNT} (her kategoriden {PER_CATEGORY})")
    log.info(f"DRY_RUN: {DRY_RUN}")
    log.info("=" * 60)

    existing = get_existing_questions()
    max_id = max(q.id for q in existing)
    log.info(f"Mevcut: {len(existing)} soru, max ID: {max_id}")
    log.info(f"Kategori dağılımı: {dict((c, sum(1 for q in existing if q.category == c)) for c in CATEGORIES)}")

    all_new = []
    next_id = max_id + 1

    for cat in CATEGORIES:
        # Seviye: her kategoride beginner + intermediate karışık
        level = "beginner" if cat in ("python-basics", "pandas") else "intermediate"

        log.info(f"\n→ {cat} ({level}) × {PER_CATEGORY}")
        prompt = build_prompt(cat, level, existing, PER_CATEGORY)

        try:
            raw = call_minimax(
                prompt,
                system="Sen kıdemli bir Python mülakat soru tasarımcısısın. Sadece JSON çıktı ver.",
            )
            questions = parse_questions(raw)
            log.info(f"  ✓ {len(questions)} soru parse edildi")
            all_new.extend(questions)
            time.sleep(1)  # rate limit koruması
        except Exception as e:
            log.error(f"  ✗ {cat} başarısız: {e}")
            continue

    if not all_new:
        log.error("Hiç soru üretilemedi")
        sys.exit(1)

    log.info(f"\nToplam üretilen: {len(all_new)} soru")
    append_questions(all_new, next_id)


if __name__ == "__main__":
    main()