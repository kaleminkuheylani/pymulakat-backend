#!/usr/bin/env python3
"""scripts/csv_to_json.py — QUESTIONS_FACTORY.csv → QUESTIONS-v3.json dönüştürücü.

Kullanım:
    python3 scripts/csv_to_json.py                          # FACTORY.csv → V3.json
    python3 scripts/csv_to_json.py --input factory.csv --output v3.json
    python3 scripts/csv_to_json.py --dry-run                # sadece doğrula

CSV format (RFC 4180): her satır bir soru.
    category   : "python-basics" | "strings" | "list-dict" | "pandas" | "algorithms"
    title      : Soru başlığı
    level      : "beginner" | "intermediate" | "advanced"
    description: Çok satırlı açıklama (tırnak içinde \\n destekli)
    starter_code: def isminden başlayan Python fonksiyon şablonu
    test_cases : JSON array string: [{"input":..., "expected":...}]
    hints      : JSON array string: ["💡 ipucu 1", "💡 ipucu 2"]
    id         : Pozitif integer (unique)
"""
import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "data" / "QUESTIONS_FACTORY.csv"
DEFAULT_OUTPUT = ROOT / "data" / "QUESTIONS-v3.json"

REQUIRED_FIELDS = {
    "category", "title", "level", "description",
    "starter_code", "test_cases", "hints", "id",
}

VALID_CATEGORIES = {"python-basics", "strings", "list-dict", "pandas", "algorithms", "data-structures"}
VALID_LEVELS = {"beginner", "intermediate", "advanced"}


def parse_json_field(value: str, field_name: str, row_id: int) -> any:
    """CSV'deki JSON-encoded alanı parse et."""
    if not value or not value.strip():
        return [] if field_name in ("test_cases", "hints") else ""
    try:
        return json.loads(value)
    except json.JSONDecodeError as e:
        raise ValueError(f"id={row_id}: {field_name} alanı geçersiz JSON — {e}")


def validate_question(q: dict, idx: int) -> list[str]:
    """Soruyu validate et, hata listesi döndür (boş = OK)."""
    errors = []
    if not q.get("title"):
        errors.append(f"satır {idx}: title boş")
    if q.get("category") not in VALID_CATEGORIES:
        errors.append(
            f"satır {idx}: category='{q.get('category')}' geçersiz "
            f"(beklenen: {sorted(VALID_CATEGORIES)})"
        )
    if q.get("level") not in VALID_LEVELS:
        errors.append(
            f"satır {idx}: level='{q.get('level')}' geçersiz "
            f"(beklenen: {sorted(VALID_LEVELS)})"
        )
    if not isinstance(q.get("test_cases"), list):
        errors.append(f"satır {idx}: test_cases JSON array olmalı")
    if not isinstance(q.get("hints"), list):
        errors.append(f"satır {idx}: hints JSON array olmalı")
    try:
        qid = int(q.get("id", 0))
        if qid <= 0:
            errors.append(f"satır {idx}: id pozitif olmalı ({qid})")
    except (TypeError, ValueError):
        errors.append(f"satır {idx}: id integer değil ({q.get('id')})")
    return errors


def csv_to_json(input_path: Path, output_path: Path, dry_run: bool = False) -> int:
    """CSV → JSON dönüştür. Soru sayısını döndür."""
    if not input_path.exists():
        raise FileNotFoundError(f"CSV yok: {input_path}")

    questions = []
    seen_ids = set()
    all_errors = []

    # CSV oku — strict mode (eksik kolon hatası)
    with open(input_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("CSV başlık satırı yok")

        missing_cols = REQUIRED_FIELDS - set(reader.fieldnames)
        if missing_cols:
            raise ValueError(f"CSV eksik kolonlar: {missing_cols}")

        for idx, row in enumerate(reader, start=2):  # 2: başlık + 1-based
            qid = int(row.get("id", 0) or 0)
            if qid in seen_ids:
                all_errors.append(f"satır {idx}: duplicate id={qid}")
                continue
            seen_ids.add(qid)

            try:
                q = {
                    "id": qid,
                    "title": row.get("title", "").strip(),
                    "category": row.get("category", "").strip(),
                    "level": row.get("level", "").strip(),
                    "description": row.get("description", "").strip(),
                    "starter_code": row.get("starter_code", "").strip(),
                    "test_cases": parse_json_field(
                        row.get("test_cases", ""), "test_cases", qid
                    ),
                    "hints": parse_json_field(
                        row.get("hints", ""), "hints", qid
                    ),
                    # CSV'de olmayan alanlar None/default
                    "explanation": None,
                    "complexity": None,
                    "tags": [],
                    "related_concepts": [],
                    "related_question_ids": [],
                    "tutorial_slug": None,
                    "slug": None,  # loader'da üretilecek
                }
            except ValueError as e:
                all_errors.append(str(e))
                continue

            errors = validate_question(q, idx)
            if errors:
                all_errors.extend(errors)
                continue

            questions.append(q)

    # Hata varsa göster
    if all_errors:
        print(f"❌ {len(all_errors)} validasyon hatası:")
        for e in all_errors[:10]:  # İlk 10
            print(f"   {e}")
        if len(all_errors) > 10:
            print(f"   ... +{len(all_errors) - 10} hata daha")
        if not dry_run:
            sys.exit(1)

    # ID sıralı
    questions.sort(key=lambda q: q["id"])

    if dry_run:
        print(f"✅ Dry-run OK: {len(questions)} soru valide edildi")
        return len(questions)

    # JSON yaz (atomic write)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(".json.tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    tmp_path.replace(output_path)

    print(f"✅ {input_path.name} → {output_path.name}: {len(questions)} soru")
    return len(questions)


def main():
    parser = argparse.ArgumentParser(description="CSV → JSON (Questions)")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action="store_true", help="Sadece valide et, yazma")
    args = parser.parse_args()

    try:
        csv_to_json(args.input, args.output, args.dry_run)
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()