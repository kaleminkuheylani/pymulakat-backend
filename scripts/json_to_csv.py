#!/usr/bin/env python3
"""scripts/json_to_csv.py — QUESTIONS-v3.json → QUESTIONS_FACTORY.csv dönüştürücü.

Kullanım:
    python3 scripts/json_to_csv.py                          # V3.json → FACTORY.csv
    python3 scripts/json_to_csv.py --input v3.json --output factory.csv

CSV format (RFC 4180):
    category,title,level,description,starter_code,test_cases,hints,id
    algorithms,İkili Arama,beginner,"...","def ..","[{...}]","[""💡 ...""]",1

Multi-line alanlar: description/starter_code \n içerebilir.
CSV standardı tırnak içinde \n kabul eder, ama bazı editörler
(Google Sheets, Excel) round-trip'te bozabilir. Manuel edit için
Google Sheets → "Download as CSV" veya direkt metin editörü önerilir.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "data" / "QUESTIONS-v3.json"
DEFAULT_OUTPUT = ROOT / "data" / "QUESTIONS_FACTORY.csv"

CSV_COLUMNS = [
    "category",
    "title",
    "level",
    "description",
    "starter_code",
    "test_cases",
    "hints",
    "id",
]


def json_to_csv(input_path: Path, output_path: Path) -> None:
    """JSON list → CSV (RFC 4180 quote escaping)."""
    with open(input_path, encoding="utf-8") as f:
        questions = json.load(f)

    # ID'ye göre sırala
    questions.sort(key=lambda q: q.get("id", 0))

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # newline="" csv modülü için kritik (Windows'ta boş satır issue'si önler)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=CSV_COLUMNS,
            quoting=csv.QUOTE_ALL,  # Tüm alanları quote içine al (güvenli)
            lineterminator="\n",
        )
        writer.writeheader()
        for q in questions:
            writer.writerow({
                "category": q.get("category", ""),
                "title": q.get("title", ""),
                "level": q.get("level", ""),
                "description": q.get("description", ""),
                "starter_code": q.get("starter_code", ""),
                # test_cases ve hints liste/dict — JSON string olarak serialize
                "test_cases": json.dumps(q.get("test_cases", []), ensure_ascii=False),
                "hints": json.dumps(q.get("hints", []), ensure_ascii=False),
                "id": q.get("id", ""),
            })

    print(f"✅ {input_path.name} → {output_path.name}: {len(questions)} soru yazıldı")


def main():
    parser = argparse.ArgumentParser(description="JSON → CSV (Questions)")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="JSON dosya yolu")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="CSV dosya yolu")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"❌ Girdi yok: {args.input}")
        sys.exit(1)

    json_to_csv(args.input, args.output)


if __name__ == "__main__":
    main()