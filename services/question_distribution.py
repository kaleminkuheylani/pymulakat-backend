# services/question_distribution.py
# QUESTIONS.py ve Supabase'den soru dağılımını analiz eder.
# Eksik kategori/level tespit edip Gemini prompt hazırlar.

import os
import re
import logging
from collections import Counter
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


def analyze_questions_py(questions: List) -> Dict:
    """
    QUESTIONS listesinden dağılım çıkar.
    Döner: {
        "total": int,
        "by_category": {"python-basics": 5, "strings": 3, ...},
        "by_level": {"beginner": 30, "intermediate": 25, ...},
        "by_category_level": {("python-basics", "beginner"): 4, ...},
        "existing_ids": [1, 2, ...]
    }
    """
    by_category = Counter()
    by_level = Counter()
    by_cat_level = Counter()
    existing_ids = []

    for q in questions:
        cat = getattr(q, "category", "unknown")
        lvl = getattr(q, "level", "unknown")
        qid = getattr(q, "id", 0)
        by_category[cat] += 1
        by_level[lvl] += 1
        by_cat_level[(cat, lvl)] += 1
        existing_ids.append(qid)

    return {
        "total": len(questions),
        "by_category": dict(by_category),
        "by_level": dict(by_level),
        "by_category_level": {f"{k[0]}|{k[1]}": v for k, v in by_cat_level.items()},
        "existing_ids": sorted(existing_ids),
    }


def identify_gaps(distribution: Dict, target_total: int = 90) -> List[Dict]:
    """
    Eksik kategori/level tespit et.
    Hedef: 90 soru (beginner: 45, intermediate: 35, advanced: 10)
    Kategori başına minimum: 5 soru
    """
    # Hedef dağılım (gerçekçi bir Python mülakat seti)
    TARGET_BY_CATEGORY = {
        "python-basics": 12,
        "strings": 8,
        "list-dict": 10,
        "oop": 8,
        "algorithms": 12,
        "data-types": 5,
        "pandas": 6,
        "numpy": 4,
        "sqlite3": 4,
        "sklearn": 3,
        "matplotlib": 3,
        "beyin-firtinasi": 5,
        "simple-apps": 4,
        "web": 3,
        "async": 3,
    }

    TARGET_BY_LEVEL = {
        "beginner": 45,
        "intermediate": 35,
        "advanced": 10,
    }

    gaps = []
    by_cat = distribution["by_category"]
    by_lvl = distribution["by_level"]

    # Kategori eksikleri
    for cat, target in TARGET_BY_CATEGORY.items():
        current = by_cat.get(cat, 0)
        if current < target:
            needed = target - current
            gaps.append({
                "type": "category",
                "category": cat,
                "current": current,
                "target": target,
                "needed": needed,
                "priority": "high" if needed >= 4 else "medium",
            })

    # Level eksikleri
    for lvl, target in TARGET_BY_LEVEL.items():
        current = by_lvl.get(lvl, 0)
        if current < target:
            needed = target - current
            gaps.append({
                "type": "level",
                "level": lvl,
                "current": current,
                "target": target,
                "needed": needed,
                "priority": "high" if needed >= 5 else "medium",
            })

    # Öncelik sırala
    gaps.sort(key=lambda g: (-g["needed"], g["priority"] != "high"))
    return gaps


def select_questions_to_generate(
    gaps: List[Dict], n: int = 5
) -> List[Dict]:
    """
    Gap listesinden N adet soru üretim planı seç.
    Öncelik: yüksek gap + dengeli kategori/level dağılımı.
    """
    plan = []
    used_cats = set()
    used_levels = set()

    for gap in gaps[:n * 2]:  # Daha fazla aday seç, sonra filtrele
        if len(plan) >= n:
            break

        if gap["type"] == "category":
            cat = gap["category"]
            # Beginner tercih et (daha çok eksik)
            level = "beginner" if cat not in used_levels else "intermediate"
            plan.append({
                "category": cat,
                "level": level,
                "reason": f"{cat}: {gap['current']}/{gap['target']}",
            })
            used_cats.add(cat)
            used_levels.add(level)
        elif gap["type"] == "level":
            level = gap["level"]
            # Çeşitli kategori
            cats = [g["category"] for g in gaps if g["type"] == "category"]
            cat = cats[0] if cats else "python-basics"
            if cat in used_cats and len(cats) > 1:
                cat = cats[1]
            plan.append({
                "category": cat,
                "level": level,
                "reason": f"{level}: {gap['current']}/{gap['target']}",
            })
            used_cats.add(cat)
            used_levels.add(level)

    return plan[:n]


def get_next_id(existing_ids: List[int]) -> int:
    """Bir sonraki ID (max + 1)."""
    return max(existing_ids) + 1 if existing_ids else 1


def build_distribution_prompt(plan: List[Dict], existing_questions_sample: str) -> str:
    """
    Gemini için prompt hazırla.
    Plan: [{"category": "oop", "level": "intermediate", ...}]
    existing_questions_sample: QUESTIONS.py'den 3 örnek (format göstermek için)
    """
    plan_lines = "\n".join(
        f"{i+1}. {p['category']} ({p['level']}) — gerekçe: {p['reason']}"
        for i, p in enumerate(plan)
    )

    return f"""Sen uzman bir Python eğitmenisin. Aşağıdaki dağılım planına göre TAM OLARAK {len(plan)} adet yeni soru üreteceksin.

**Dağılım planı (her satır bir soru için):**
{plan_lines}

**Mevcut soru formatı örneği (bunu takip et):**
```python
{existing_questions_sample}
```

**Kurallar:**
1. Her soru gerçek hayat senaryosu içermeli (oyun, günlük hayat, iş dünyası)
2. Starter code fonksiyon imzası + yorum + pass içermeli
3. 2-4 test case (kolaydan zora)
4. 3 ipucu (kademeli, 💡 İpucu N: ... formatında)
5. Difficulty beginner için "easy", intermediate için "medium", advanced için "hard"
6. Title'da emoji kullan
7. Türkçe description (öğrenci kitlesi Türk)
8. test_cases.input dict DEĞİL — direkt tek parametre (veya fonksiyon dict alıyorsa dict)

**Çıktı formatı (SADECE JSON array, başka metin yok):**
[
  {{
    "title": "...",
    "category": "...",
    "level": "...",
    "description": "...",
    "starter_code": "def fn(...) -> ...:\\n    pass",
    "test_cases": [{{"input": ..., "expected": ...}}],
    "hints": ["💡 İpucu 1: ...", "💡 İpucu 2: ...", "💡 İpucu 3: ..."],
    "complexity": "O(n) — ..."
  }},
  ...
]
"""