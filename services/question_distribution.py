# services/question_distribution.py
# QUESTIONS.py ve Supabase'den soru dağılımını analiz eder.
# Output type bazlı kategorizasyon: string / number / boolean / list / dict / tuple.
# Sadece input -> output ilişkisi olan sorular (algoritma / veri dönüşüm mantığı).

import os
import re
import logging
from collections import Counter
from typing import Dict, List, Tuple, Optional, Any

logger = logging.getLogger(__name__)


# ── Output type kategorileri ────────────────────────────

OUTPUT_TYPES = {
    "string": {
        "label": "String Çıktı",
        "description": "Fonksiyon str/dict[str]/formatted output döndürür",
        "examples": [
            "email validate -> bool",
            "sayıyı yazıya çevir -> 'yüz yirmi üç'",
            "şifre maskele -> 'a***@gmail.com'",
            "tarih formatla -> '2026-07-01'",
        ],
        "test_expected_types": ["str"],
    },
    "number": {
        "label": "Sayı Çıktı",
        "description": "Fonksiyon int/float döndürür (count, sum, index, math)",
        "examples": [
            "listedeki en büyük sayı -> 42",
            "OBEB hesapla -> 12",
            "binary search adım sayısı -> 3",
            "basamak sayısı -> 5",
        ],
        "test_expected_types": ["int", "float", "number"],
    },
    "boolean": {
        "label": "Boolean Çıktı",
        "description": "Fonksiyon True/False döndürür (check, validation)",
        "examples": [
            "palindrom mu? -> True",
            "sayı asal mı? -> False",
            "parantezler dengeli mi? -> True",
            "iki string anagram mı? -> False",
        ],
        "test_expected_types": ["bool", "boolean"],
    },
    "list": {
        "label": "Liste Çıktı",
        "description": "Fonksiyon list döndürür (transform, filter, sort)",
        "examples": [
            "string -> char list ['h','e','l','l','o']",
            "top 3 maaş [9000, 8000, 7500]",
            "factoriel listesi [1, 1, 2, 6, 24]",
            "benzersiz kelimeler sorted",
        ],
        "test_expected_types": ["list", "array"],
    },
    "dict": {
        "label": "Sözlük Çıktı",
        "description": "Fonksiyon dict/map döndürür (group, count, lookup)",
        "examples": [
            "harf sayacı {'a': 3, 'b': 1}",
            "kelime grupları {'short': [...], 'long': [...]}",
            "envanter {'elma': 5, 'armut': 2}",
        ],
        "test_expected_types": ["dict", "object"],
    },
    "tuple": {
        "label": "Tuple Çıktı",
        "description": "Fonksiyon tuple döndürür (pair, multi-return)",
        "examples": [
            "(min, max) -> (1, 100)",
            "(quotient, remainder) -> (3, 1)",
            "(rgb, hex) -> ((255,0,0), '#FF0000')",
        ],
        "test_expected_types": ["tuple"],
    },
}


def infer_output_type(test_cases: List[Dict], starter_code: str = "") -> str:
    """
    Test case'lerden output type çıkar.
    Döner: 'string' | 'number' | 'boolean' | 'list' | 'dict' | 'tuple' | 'mixed'
    """
    if not test_cases:
        return "string"  # default

    expected_values = [tc.get("expected") for tc in test_cases if "expected" in tc]
    if not expected_values:
        return "string"

    # Type counter
    type_counts = Counter()
    for val in expected_values:
        if isinstance(val, bool):
            type_counts["boolean"] += 1
        elif isinstance(val, (int, float)):
            type_counts["number"] += 1
        elif isinstance(val, str):
            type_counts["string"] += 1
        elif isinstance(val, list):
            type_counts["list"] += 1
        elif isinstance(val, dict):
            type_counts["dict"] += 1
        elif isinstance(val, tuple):
            type_counts["tuple"] += 1
        else:
            type_counts["mixed"] += 1

    # En çok olan tip
    if not type_counts:
        return "string"
    return type_counts.most_common(1)[0][0]


def analyze_questions_py(questions: List) -> Dict:
    """
    QUESTIONS listesinden output_type dağılımı çıkar.
    """
    by_type = Counter()
    by_type_level = Counter()
    existing_ids = []
    type_examples = {}

    for q in questions:
        out_type = infer_output_type(q.test_cases, getattr(q, "starter_code", ""))
        level = getattr(q, "level", "unknown")
        by_type[out_type] += 1
        by_type_level[(out_type, level)] += 1
        existing_ids.append(getattr(q, "id", 0))

        # Her tip için bir örnek başlık sakla
        if out_type not in type_examples:
            type_examples[out_type] = getattr(q, "title", "")

    return {
        "total": len(questions),
        "by_output_type": dict(by_type),
        "by_output_type_level": {f"{k[0]}|{k[1]}": v for k, v in by_type_level.items()},
        "type_examples": type_examples,
        "existing_ids": sorted(existing_ids),
    }


def identify_gaps(distribution: Dict, target_per_type: int = 12) -> List[Dict]:
    """
    Eksik output type'ları tespit et.
    Hedef: her tip için 12 soru (toplam ~72 soru, dengeli dağılım).
    """
    by_type = distribution["by_output_type"]

    gaps = []
    for out_type, info in OUTPUT_TYPES.items():
        current = by_type.get(out_type, 0)
        if current < target_per_type:
            needed = target_per_type - current
            gaps.append({
                "type": "output_type",
                "output_type": out_type,
                "label": info["label"],
                "current": current,
                "target": target_per_type,
                "needed": needed,
                "priority": "high" if needed >= 6 else "medium",
            })

    gaps.sort(key=lambda g: (-g["needed"], g["priority"] != "high"))
    return gaps


def select_questions_to_generate(gaps: List[Dict], n: int = 5) -> List[Dict]:
    """
    N adet soru üretim planı seç.
    Dengeli output type dağılımı, her seferde farklı tip.
    """
    plan = []
    used_types = set()
    by_type_index = {}  # Her tip için kaçıncı soruyu seçtik

    for gap in gaps:
        if len(plan) >= n:
            break
        out_type = gap["output_type"]
        if out_type in used_types and len(plan) < n - 1:
            continue  # Aynı tipte art arda alma (mümkünse)

        plan.append({
            "output_type": out_type,
            "level": "beginner" if gap["current"] < 4 else "intermediate",
            "reason": f"{gap['label']}: {gap['current']}/{gap['target']}",
            "guidance": OUTPUT_TYPES[out_type]["description"],
            "examples": OUTPUT_TYPES[out_type]["examples"][:2],
        })
        used_types.add(out_type)
        by_type_index[out_type] = by_type_index.get(out_type, 0) + 1

    # Eğer plan n'den az olduysa (yeterli gap yok), duplicate tip ekle
    if len(plan) < n:
        for gap in gaps:
            if len(plan) >= n:
                break
            out_type = gap["output_type"]
            plan.append({
                "output_type": out_type,
                "level": "intermediate",
                "reason": f"{gap['label']}: ek soru",
                "guidance": OUTPUT_TYPES[out_type]["description"],
                "examples": OUTPUT_TYPES[out_type]["examples"][:2],
            })

    return plan[:n]


def get_next_id(existing_ids: List[int]) -> int:
    """Bir sonraki ID."""
    return max(existing_ids) + 1 if existing_ids else 1


def build_distribution_prompt(plan: List[Dict], existing_questions_sample: str) -> str:
    """
    Gemini için prompt — input/output ilişkisi olan sorular.
    """
    plan_lines_parts = []
    for i, p in enumerate(plan):
        ex0 = p['examples'][0]
        ex1 = p['examples'][1] if len(p['examples']) > 1 else "—"
        plan_lines_parts.append(
            "{n}. OUTPUT TYPE: {ot} ({lvl}) — {r}\n   Kılavuz: {g}\n   Örnekler:\n     • {e0}\n     • {e1}".format(
                n=i+1, ot=p['output_type'], lvl=p['level'], r=p['reason'],
                g=p['guidance'], e0=ex0, e1=ex1
            )
        )
    plan_lines = "\n".join(plan_lines_parts)

    template = """Sen uzman bir Python eğitmenisin. Aşağıdaki output type planına göre TAM OLARAK __N__ adet yeni soru üreteceksin.

⚠️ **ÖNEMLİ KURAL**: Her soru **input → output** ilişkisi olan bir dönüşüm fonksiyonu olmalı.
- Fonksiyon SADECE bir değer döndürmeli (return x), print/yan etki yok
- Input ne olursa olsun, output tipi belirli bir Python tipi olmalı (str, int, float, bool, list, dict, tuple)
- Side-effect'siz (dosya yazma, network çağrısı yok)

**Plan (her satır bir soru, output type'a göre):**
__PLAN__

**Mevcut soru format örneği (takip et):**
```python
__SAMPLE__
```

**Genel kurallar:**
1. Her soru gerçek hayat senaryosu içermeli (günlük hayat, iş dünyası, oyun)
2. Starter code `def fn(param: tip) -> donus_tipi: # yorum\\n    pass` formatında
3. 2-4 test case (kolay → zor sırayla)
4. 3 ipucu (kademeli, "💡 İpucu N: ..." formatında)
5. Title'da emoji kullan
6. Türkçe description
7. test_cases.input TEK parametre ise direkt değer, çok parametre ise dict
8. test_cases.expected SADECE belirtilen output type'ta (string için str, list için list, vs.)
9. **Output tipi plan'a TAM UY** — string ise sadece str, number ise int/float

**Her output type için beklenen expected tipleri:**
- `string`: 'merhaba', 'kullanici@gmail.com' gibi tırnak içinde
- `number`: 42, 3.14 gibi tırnaksız sayı
- `boolean`: true veya false (küçük harf, JSON standardı)
- `list`: [1, 2, 3] köşeli parantez
- `dict`: %7B%22key%22%3A%20%22value%22%7D süslü parantez
- `tuple`: (1, 2) normal parantez

**Çıktı formatı (SADECE JSON array, başka metin yok):**
[
  %7B
    "title": "🛒 Sepet Toplamı",
    "output_type": "number",
    "category": "python-basics",
    "level": "beginner",
    "description": "...",
    "starter_code": "def fn(...) -> ...:\\n    pass",
    "test_cases": [
      %7B"input": "100", "expected": 150%7D,
      %7B"input": "200", "expected": 250%7D
    ],
    "hints": ["💡 İpucu 1: ...", "💡 İpucu 2: ...", "💡 İpucu 3: ..."],
    "complexity": "O(n)"
  %7D,
  ...
]
"""
    # Placeholder replace
    result = template.replace("__N__", str(len(plan)))
    result = result.replace("__PLAN__", plan_lines)
    result = result.replace("__SAMPLE__", existing_questions_sample)
    # URL-decode the JSON braces back to normal
    result = result.replace("%7B", "{").replace("%7D", "}")
    return result