# data/QUESTIONS-v4.py
# ══════════════════════════════════════════════════════════════
# Backend QUESTION kaynağı V4 — JSON-on-disk + Python loader.
# ══════════════════════════════════════════════════════════════
#
# NEDEN .json + .py loader?
#   - JSON dosyası syntax-clean (data/QUESTIONS-v3.py syntax hataları içerir).
#   - .py sadece bir facade — json dosyasını runtime'da yükler.
#   - migrate_to_db.py önce .json dosyasını yüklemeyi dener; yoksa .py loader.
#
# TOPLAM SORU: 165
# KATEGORİLER (13 adet):
#   - algorithms: 19
#   - algorithms-dp: 12
#   - algorithms-graph: 14
#   - algorithms-recursion: 12
#   - concurrency: 12
#   - design-patterns: 12
#   - functional: 12
#   - oop-advanced: 12
#   - performance: 12
#   - python-3-12: 12
#   - real-world: 12
#   - standard-library: 12
#   - testing: 12
#
# FORMAT: Her öğe dataclass DEĞİL — plain dict.
#   {id, title, category, level, description, starter_code,
#    test_cases, hints, explanation, complexity, related_concepts,
#    related_question_ids, tags, tutorial_slug, slug}
#
# migrate_to_db.py kullanımı:
#   python3 scripts/migrate_to_db.py --v4-only

import json
from pathlib import Path
from typing import List, Dict, Any


def load_questions_v4() -> List[Dict[str, Any]]:
    """QUESTIONS-v4.json dosyasından dict list yükle.

    Returns:
        List[Dict[str, Any]]: 165 soru (dict formatında, dataclass değil).
    """
    p = Path(__file__).parent / "QUESTIONS-v4.json"
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return json.load(f)


# Script olarak çalıştırılırsa özet bas
if __name__ == "__main__":
    qs = load_questions_v4()
    print(f"📚 QUESTIONS-v4 yüklendi: {len(qs)} soru")
    cats = {}
    for q in qs:
        cats[q.get("category", "?")] = cats.get(q.get("category", "?"), 0) + 1
    print("\n📊 Kategori dağılımı:")
    for cat in sorted(cats.keys()):
        print(f"  {cat:25s} {cats[cat]:3d}")
