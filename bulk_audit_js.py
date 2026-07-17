#!/usr/bin/env python3
"""
bulk_audit_js.py — 2026-07-16

JS bulk audit: mevcut sorulari (CSV) DeepSeek'e cozdurur, 3 tur dener,
test case'leri Node.js'de calistirarak dogrular. Gecemeyenleri sil
Supabase bulk delete icin SQL dosyasi uretir.

Kullanim:
    export DEEPSEEK_API_KEY=sk-xxx
    python bulk_audit_js.py [--dry-run] [--max-tours 3] [--delete]

Cikti:
    audit_results.csv     — her soru icin pass/fail + raw DeepSeek output
    audit_to_delete.sql   — basarisiz sorular icin DELETE SQL
    audit_stats.json      — istatistik (pass/fail orani, sure, maliyet)
"""

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import requests

# ─── Config ─────────────────────────────────────────────────────────
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"  # DeepSeek V3
MAX_TOKENS = 800
TEMPERATURE = 0.2  # dusuk = deterministik, kod icin ideal
TIMEOUT_S = 30
CSV_PATH = Path(__file__).parent / "data" / "QUESTIONS-v3.csv"
NODE_TIMEOUT_S = 3  # JS test runner subprocess timeout

SYSTEM_PROMPT = """Sen deneyimli bir JavaScript teknik mulakat asistanisin.
Kullanici sana bir JavaScript problemi, fonksiyon imzasi ve test case'leri verecek.
Sen sadece ve sadece SAF JavaScript kodu yaz. Aciklama YAPMA. Yorum SATIRI EKLEME.
Sadece fonksiyon implementasyonunu yaz, baska bir sey yazma.

Kurallar:
- Sadece function declaration/arrow function yaz
- console.log KULLANMA (sadece return)
- Test case'lerdeki expected degerleri birebir dondurmeli (case-sensitive)
- true/false (lowercase) — Python True/False DEGIL
- null (lowercase) — Python None DEGIL
- Bos array [] icin [] dondur, "[]" string DEGIL
- String icin tirnak kullan: "racecar" veya 'racecar' (tutarli ol)
- NaN, Infinity gibi ozel degerler dogru kullan
- Array/object dondureceksen JSON formatinda (tirnak icinde) yazma, native JS literal yaz

Cikti formatin:
- Sadece kod. Basinda/sonda ```javascript veya ``` isareti OLMASIN.
- Sadece saf JS, hicbir aciklama yok."""


def call_deepseek(user_prompt: str, api_key: str) -> tuple[str, dict]:
    """DeepSeek V3 chat completion. (content, usage) doner."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "stream": False,
    }
    try:
        r = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=TIMEOUT_S)
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"].strip()
        # Kod blok isaretlerini temizle
        content = re.sub(r"^```(?:javascript|js)?\s*\n?", "", content)
        content = re.sub(r"\n?```\s*$", "", content)
        return content, data.get("usage", {})
    except Exception as e:
        return f"// DEEPSEEK_ERROR: {e}", {}


def python_to_js_starter(python_code: str, function_name: str = "") -> str:
    """starters.ts'deki Python→JS transform. Basit versiyon (soru starter'lari icin)."""
    if not python_code:
        return ""
    js = python_code

    # Docstring → block comment
    js = re.sub(r'^(\s*)"""([\s\S]*?)"""', r"\1/*\2*/", js, flags=re.MULTILINE)

    # Tek satir yorum # → //
    js = re.sub(r"(^|\s)#(.*)$", r"\1//\2", js, flags=re.MULTILINE)

    # True/False/None → true/false/null
    js = re.sub(r"\bTrue\b", "true", js)
    js = re.sub(r"\bFalse\b", "false", js)
    js = re.sub(r"\bNone\b", "null", js)

    # Python operatorler
    js = re.sub(r"\bnot in\b", "!==", js)  # not in (ayri, sonra bak)
    js = re.sub(r"\bin\b", " in ", js)  # in operatoru ayni
    js = re.sub(r"\bnot\b", "!", js)
    js = re.sub(r"\band\b", "&&", js)
    js = re.sub(r"\bor\b", "||", js)

    # def fn_name(args): → function fnName(args) {
    # elif → else if
    js = re.sub(r"\bdef\s+(\w+)\s*\(([^)]*)\)\s*:", r"function \1(\2) {", js)
    js = re.sub(r"\belif\b", "else if", js)

    # print(x) → console.log(x)
    js = re.sub(r"\bprint\(", "console.log(", js)

    # return ... → ayni, noktali virgul eklenebilir (JS opsiyonel)
    return js


def run_js_test(solution_code: str, function_name: str, test_input: str) -> tuple[bool, str]:
    """Node.js subprocess ile JS kodu calistir, output'u al."""
    # Test wrapper: solution + test call
    # input JSON ise parsed, degilse raw string
    test_input_json = json.dumps(test_input)
    wrapper = f"""
const _input = {test_input_json};
let _parsed;
try {{ _parsed = JSON.parse(_input); }} catch {{ _parsed = _input; }}

{solution_code}

const _result = {function_name}(_parsed);
if (_result === undefined) {{
  console.log("UNDEFINED");
}} else if (typeof _result === "string") {{
  console.log(_result);
}} else {{
  console.log(JSON.stringify(_result));
}}
"""
    try:
        result = subprocess.run(
            ["node", "-e", wrapper],
            capture_output=True,
            text=True,
            timeout=NODE_TIMEOUT_S,
        )
        if result.returncode != 0:
            return False, f"RUNTIME_ERROR: {result.stderr.strip()[:200]}"
        actual = result.stdout.strip()
        return True, actual
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    except Exception as e:
        return False, f"SUBPROCESS_ERROR: {e}"


def normalize_expected(expected: str) -> str:
    """Python boolean → JS lowercase (palindrome True/False sorununun onlemi)."""
    s = str(expected).strip()
    if s == "True":
        return "true"
    if s == "False":
        return "false"
    if s == "None":
        return "null"
    return s


def normalize_actual(actual: str) -> str:
    """JS boolean print normalization: 'true' → 'true' (lowercase)."""
    return actual.strip()


def audit_question(q: dict, api_key: str, max_tours: int = 3) -> dict:
    """Bir soruyu 3 tur DeepSeek'e sor, test case'lerle dogrula."""
    qid = q.get("id", "?")
    title = q.get("title", "")
    fn = q.get("function_name", "")
    starter_py = q.get("starter_code", "")
    description = q.get("description", "")
    test_cases_raw = q.get("test_cases", [])

    # Test case parse
    test_cases = []
    if isinstance(test_cases_raw, str):
        # Python list string representation
        try:
            test_cases_raw = eval(test_cases_raw)
        except Exception:
            test_cases = []

    for tc in test_cases_raw if isinstance(test_cases_raw, list) else []:
        if isinstance(tc, dict):
            test_cases.append({
                "input": str(tc.get("input", "")),
                "expected": str(tc.get("expected", "")),
            })

    if not fn:
        return {
            "id": qid,
            "title": title,
            "status": "SKIP",
            "reason": "no_function_name",
            "tours": 0,
            "pass_count": 0,
            "total_tests": len(test_cases),
        }

    if not test_cases:
        return {
            "id": qid,
            "title": title,
            "status": "SKIP",
            "reason": "no_test_cases",
            "tours": 0,
            "pass_count": 0,
            "total_tests": 0,
        }

    # User prompt: soru + imza + test case'ler
    user_prompt = f"""Problem: {title}

{description}

Function signature: function {fn}(input)

Test cases (input → expected):
"""
    for i, tc in enumerate(test_cases[:5], 1):  # max 5 test
        user_prompt += f"  {i}) input: {tc['input']!r} → expected: {tc['expected']!r}\n"

    user_prompt += "\nSadece JavaScript fonksiyon implementasyonunu yaz."

    tours_log = []
    pass_count = 0

    for tour in range(1, max_tours + 1):
        t0 = time.time()
        solution, usage = call_deepseek(user_prompt, api_key)
        duration_ms = int((time.time() - t0) * 1000)

        if solution.startswith("// DEEPSEEK_ERROR"):
            tours_log.append({"tour": tour, "error": solution, "duration_ms": duration_ms})
            continue

        # Her test case'i calistir
        test_results = []
        tour_pass = 0
        for tc in test_cases:
            ok, actual = run_js_test(solution, fn, tc["input"])
            expected_norm = normalize_expected(tc["expected"])
            actual_norm = normalize_actual(actual)
            test_ok = ok and actual_norm == expected_norm
            if test_ok:
                tour_pass += 1
            test_results.append({
                "input": tc["input"],
                "expected": expected_norm,
                "actual": actual_norm,
                "passed": test_ok,
            })

        tours_log.append({
            "tour": tour,
            "solution": solution[:200],
            "tests": test_results,
            "pass_count": tour_pass,
            "total": len(test_cases),
            "duration_ms": duration_ms,
            "tokens": usage.get("total_tokens", 0),
        })

        if tour_pass == len(test_cases):
            pass_count = tour_pass
            break  # Tum testler gecti

    # Sonuc: pass_count >= total_tests / 2 (majority) veya 3/3 zorunlu
    final_status = "PASS" if pass_count == len(test_cases) else "FAIL"
    return {
        "id": qid,
        "title": title,
        "function_name": fn,
        "status": final_status,
        "tours": len(tours_log),
        "tours_log": tours_log,
        "pass_count": pass_count,
        "total_tests": len(test_cases),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Sadece CSV oku, audit etme")
    parser.add_argument("--max-tours", type=int, default=3)
    parser.add_argument("--limit", type=int, default=None, help="Ilk N soruyu audit et")
    parser.add_argument("--delete", action="store_true", help="Basarisizlari SQL DELETE dosyasi uret")
    args = parser.parse_args()

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key and not args.dry_run:
        print("HATA: DEEPSEEK_API_KEY env degiskeni tanimli degil")
        print("Ornek: export DEEPSEEK_API_KEY=sk-xxx")
        sys.exit(1)

    if not CSV_PATH.exists():
        print(f"HATA: CSV bulunamadi: {CSV_PATH}")
        sys.exit(1)

    # CSV oku
    with open(CSV_PATH, encoding="utf-8") as f:
        questions = list(csv.DictReader(f))

    if args.limit:
        questions = questions[:args.limit]

    print(f"Auditing {len(questions)} soru (max_tours={args.max_tours})...")
    print(f"DeepSeek model: {DEEPSEEK_MODEL}")
    print()

    results = []
    total_tokens = 0
    start_time = time.time()

    for i, q in enumerate(questions, 1):
        qid = q.get("id", "?")
        title = q.get("title", "")
        print(f"[{i}/{len(questions)}] id={qid} {title[:50]}...", end=" ", flush=True)

        if args.dry_run:
            result = {"id": qid, "title": title, "status": "DRY_RUN"}
        else:
            result = audit_question(q, api_key, args.max_tours)
            for t in result.get("tours_log", []):
                total_tokens += t.get("tokens", 0)

        status = result.get("status", "?")
        print(f"{status} ({result.get('pass_count', 0)}/{result.get('total_tests', 0)} tests, {result.get('tours', 0)} tours)")

        results.append(result)

    elapsed = time.time() - start_time

    # Istatistik
    passed = sum(1 for r in results if r.get("status") == "PASS")
    failed = sum(1 for r in results if r.get("status") == "FAIL")
    skipped = sum(1 for r in results if r.get("status") == "SKIP")
    dry_runs = sum(1 for r in results if r.get("status") == "DRY_RUN")

    # CSV sonuc
    with open("audit_results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "title", "status", "pass_count", "total_tests", "tours", "function_name"])
        for r in results:
            w.writerow([
                r.get("id", ""),
                r.get("title", "")[:80],
                r.get("status", ""),
                r.get("pass_count", 0),
                r.get("total_tests", 0),
                r.get("tours", 0),
                r.get("function_name", ""),
            ])

    # JSON stats
    stats = {
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "dry_runs": dry_runs,
        "pass_rate": round(passed / max(len(results), 1) * 100, 2),
        "elapsed_seconds": round(elapsed, 1),
        "total_tokens": total_tokens,
        "estimated_cost_usd": round(total_tokens * 0.00000014, 4),  # DeepSeek V3 input $0.14/M
    }
    with open("audit_stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    # SQL delete (basarisiz olanlar icin)
    if args.delete and failed > 0:
        with open("audit_to_delete.sql", "w", encoding="utf-8") as f:
            f.write("-- Basarisiz sorular (audit basarisiz, 3 tur gecemedi)\n")
            f.write("-- Calistirmadan once review edin!\n\n")
            for r in results:
                if r.get("status") == "FAIL":
                    f.write(f"DELETE FROM questions WHERE id = {r['id']};  -- {r.get('title', '')[:60]}\n")
        print(f"\nSQL delete dosyasi: audit_to_delete.sql ({failed} soru)")

    print()
    print("=" * 50)
    print(f"PASS:  {passed}")
    print(f"FAIL:  {failed}")
    print(f"SKIP:  {skipped}")
    if not args.dry_run:
        print(f"Sure:  {elapsed:.1f}s")
        print(f"Tokens: {total_tokens}")
        print(f"Tahmini maliyet: ${stats['estimated_cost_usd']}")
    print("=" * 50)
    print("Sonuclar: audit_results.csv, audit_stats.json")


if __name__ == "__main__":
    main()
