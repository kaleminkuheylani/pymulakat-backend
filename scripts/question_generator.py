#!/usr/bin/env python3
"""
pymulakat — Mavis (MiniMax) API ile otomatik soru üretici (v3 +)
════════════════════════════════════════════════════════════════════

QUESTIONS-v3.py'yi okur → son ID'yi bulur → dağılımlı yeni sorular üretir
→ aynı dosyaya append eder. ESKİ generate_questions.py'nin halefidir.

Davranış sözleşmesi (uyumluluk):
  • input/expected/output formatı korunur (test_cases listesi)
  • dosya formatı korunur (dataclass Question(...) literal)
  • genel akış bozulmaz (DRY_RUN, idempotent insert, aynı env değişkenleri)
  • DRY_RUN=true ile dosya değiştirilmez, sadece önizleme yapılır

Kullanım:
  export MINIMAX_API_KEY="xxx"
  export MINIMAX_BASE_URL="https://api.minimax.chat/v1"   # opsiyonel
  export MINIMAX_MODEL="MiniMax-M3"                         # opsiyonel
  export GENERATE_COUNT=20                                  # opsiyonel (default 20)
  export DRY_RUN=true                                       # sadece yazdır, dosyaya yazma
  export GENERATE_SEED_ONLY=false                           # salt okunur mod (append yapma)
  python scripts/question_generator.py

Dağılım (eşit):
  • python-basics     → 25%
  • data-structures   → 25%
  • algorithms        → 25%
  • pandas            → 25% (+ ek olarak mevcutsa list-dict dahil)
"""

from __future__ import annotations

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
log = logging.getLogger("question_generator")

# ─── Config ──────────────────────────────────────────────
API_KEY = os.environ.get("MINIMAX_API_KEY", "")
BASE_URL = os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.chat/v1")
MODEL = os.environ.get("MINIMAX_MODEL", "MiniMax-M3")
GENERATE_COUNT = int(os.environ.get("GENERATE_COUNT", "20"))
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() == "true"
GENERATE_SEED_ONLY = os.environ.get("GENERATE_SEED_ONLY", "false").lower() == "true"

# Eşit dağılım — yeni sorular bu kategorilere dağıtılır
CATEGORIES = ["python-basics", "data-structures", "algorithms", "pandas"]

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

FORMAT (her obje — input/expected/output formatı bu):
{{
  "title": "Kısa Türkçe başlık (≤50 karakter)",
  "description": "2-3 cümle açıklama, günlük dil, emoji yok",
  "starter_code": "def fn_name(param1, param2):\\n    \\\"\\\"\\\"Docstring.\\\"\\\"\\\"\\n    pass",
  "test_cases": [
    {{"input": <arg>, "expected": <sonuç>, "description": "kısa test açıklaması"}}
  ],
  "hints": [
    "💡 İpucu 1: ...",
    "💡 İpucu 2: ...",
    "💡 İpucu 3: ..."
  ],
  "explanation": "EN AZ 200 KELİME Markdown açıklama. Problem tanımı, 3 farklı yaklaşım, time/space karmaşıklığı, edge case'ler.",
  "complexity": "O(?) — kısa açıklama",
  "related_concepts": ["kavram1", "kavram2", "kavram3"],
  "related_question_ids": [<mevcut ID'lerden 3-5 tane>],
  "tags": ["{category}", "{level}", "interview"],
  "slug": "url-friendly-kebab-case"
}}

KURALLAR:
1. test_cases içindeki "input"/"expected" JSON-serializable (string, int, float, list, dict, bool, None)
2. test_cases 3-5 arası, her biri description içermeli
3. explanation 200+ kelime Markdown
4. related_question_ids sadece mevcut ID'lerden olsun
5. slug benzersiz, küçük harf, tire ile
6. Mevcut başlıklardan farklı ol — ezber değil, farklı bir açı
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
        existing_ids=existing_ids[-30:],
        existing_titles=existing_titles[-20:],
    )


def parse_questions(raw: str) -> List[Dict[str, Any]]:
    """API yanıtından JSON array'i çıkar, parse et."""
    raw = raw.strip()
    fence_match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", raw, re.DOTALL)
    if fence_match:
        raw = fence_match.group(1)
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

    def fmt_inline_list(items: List[Any]) -> str:
        return "[" + ", ".join(repr(x) for x in items) + "]" if items else "[]"

    def fmt_dict_list(items: List[Dict[str, Any]]) -> str:
        return "[" + ", ".join(repr(x) for x in items) + "]" if items else "[]"

    return f"""    Question(
        id={next_id},
        title={q["title"]!r},
        category={q.get("category", "python-basics")!r},
        level={q.get("level", "intermediate")!r},
        description={q.get("description", "")!r},
        starter_code={q.get("starter_code", "")!r},
        test_cases={fmt_dict_list(q.get("test_cases", []))},
        hints={fmt_inline_list(q.get("hints", []))},
        explanation={q.get("explanation", "")!r},
        complexity={q.get("complexity", "O(n)")!r},
        related_concepts={fmt_inline_list(q.get("related_concepts", []))},
        related_question_ids={fmt_inline_list(q.get("related_question_ids", []))},
        tags={fmt_inline_list(q.get("tags", []))},
        tutorial_slug={q.get("tutorial_slug")!r},
        slug={q.get("slug")!r},
    ),"""


def append_questions(new_questions: List[Dict[str, Any]], start_id: int):
    """QUESTIONS-v3.py'ye yeni soruları ekle. DRY_RUN uyumlu."""
    if GENERATE_SEED_ONLY:
        log.info("GENERATE_SEED_ONLY=true — append atlandı")
        for q in new_questions:
            log.info("  • %s — %s", q.get("slug") or "—", q.get("title", "")[:60])
        return

    with open(QUESTIONS_FILE) as f:
        content = f.read()
    last_bracket = content.rfind("]")
    if last_bracket == -1:
        raise ValueError("QUESTIONS-v3.py'de QUESTIONS listesi bulunamadı")

    new_blocks = []
    for i, q in enumerate(new_questions):
        q.setdefault("category", "python-basics")
        q.setdefault("level", "intermediate")
        new_blocks.append(q_to_python_literal(q, start_id + i))

    before = content[:last_bracket].rstrip()
    if not before.endswith(","):
        before += ","

    new_content = before + "\n\n" + "\n\n".join(new_blocks) + "\n]\n"
    if DRY_RUN:
        log.info(f"[DRY_RUN] {len(new_questions)} soru eklenecek (ID {start_id}..{start_id + len(new_questions) - 1})")
        for i, q in enumerate(new_questions):
            log.info(f"  • #{start_id + i} {q.get('category')} :: {q.get('title', '')[:60]}")
        return

    with open(QUESTIONS_FILE, "w") as f:
        f.write(new_content)
    log.info(f"✅ {len(new_questions)} soru eklendi (ID {start_id}..{start_id + len(new_questions) - 1})")


# ═══════════════════════════════════════════════════════════════
# ─── Main ─────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════

def main():
    log.info("=" * 60)
    log.info("Mavis API ile soru üretimi (question_generator.py)")
    per_cat = GENERATE_COUNT // len(CATEGORIES)
    log.info(f"Toplam: {GENERATE_COUNT} (her kategoriden {per_cat})")
    log.info(f"DRY_RUN: {DRY_RUN} | SEED_ONLY: {GENERATE_SEED_ONLY}")
    log.info(f"Model: {MODEL}")
    log.info("=" * 60)

    existing = get_existing_questions()
    max_id = max(q.id for q in existing)
    log.info(f"Mevcut: {len(existing)} soru, max ID: {max_id}")

    all_new = []
    next_id = max_id + 1

    for cat in CATEGORIES:
        level = "beginner" if cat in ("python-basics", "pandas") else "intermediate"
        log.info(f"\n→ {cat} ({level}) × {per_cat}")
        prompt = build_prompt(cat, level, existing, per_cat)

        try:
            raw = call_minimax(
                prompt,
                system="Sen kıdemli bir Python mülakat soru tasarımcısısın. Sadece JSON çıktı ver.",
            )
            questions = parse_questions(raw)
            log.info(f"  ✓ {len(questions)} soru parse edildi")
            all_new.extend(questions)
            time.sleep(1)
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
