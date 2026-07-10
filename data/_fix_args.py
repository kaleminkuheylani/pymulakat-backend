"""
_fix_args.py — CSV function_name + placeholder argument düzeltme (regex-based, deterministic).

Ne yapar:
1) function_name boş ise starter_code'dan `def X(` regex'i ile extract eder
   ve CSV'nin function_name kolonuna yazar.
2) starter_code içindeki `arg0`, `arg1`, ... placeholder isimlerini tip
   bilgisinden tahmin edilen semantik isimlerle değiştirir.

Tip adı veritabanı (deterministic, kod-temizliği kuralına uygun):
  list[int]      -> arr / nums / lst   (positional: ilk nums, sonrakiler lst)
  list[float]    -> vals
  list[str]      -> tokens / texts
  list          -> arr / items
  str           -> s / text / line
  int           -> n / k / pos / threshold
  dict          -> mapping
  Any / Unknown -> input

Kural: aynı tip birden fazla parametre varsa sonrakileri `<tip><sayı>` ile
ayırır (örn. arr1, arr2). Tip grubu ayrımı yoksa tüm `list[int]` aynı
index'ten sayılır (arg0=nums, arg1=nums1, arg2=nums2 gibi).

Idempotent: ikinci kez çalıştırmak değişiklik yapmaz — önceden `arg0`
yoksa skip.
"""
import csv
import re
import shutil
from pathlib import Path
from collections import OrderedDict

CSV_PATH = Path(__file__).resolve().parent / "QUESTIONS-v3.csv"


# ─── Tip → isim mapping ─────────────────────────────────────
TYPE_NAME_POOL: dict[str, tuple[str, ...]] = {
    "list[float]": ("vals", "vals2", "vals3"),
    "list[list]":  ("matrix", "matrix2"),
    "list[int]":   ("nums", "lst", "arr2", "arr3"),
    "list[str]":   ("tokens", "texts", "strs"),
    "list":        ("arr", "items", "arr2", "arr3"),
    "dict":        ("mapping", "data"),
    "float":       ("val", "target", "ratio"),
    "int":         ("n", "k", "pos", "threshold", "count"),
    "str":         ("s", "text", "line", "input_str"),
    "bool":        ("flag", "strict"),
    "any":         ("value", "other"),
}


def type_pool(t: str) -> tuple[str, ...]:
    t = (t or "").strip().lower()
    if t in TYPE_NAME_POOL:
        return TYPE_NAME_POOL[t]
    return TYPE_NAME_POOL["any"]


def normalize_type(t: str) -> str:
    """Type annotation'ı normalize et, karmaşıksa fallback."""
    t = (t or "").strip().lower()
    if not t:
        return "any"
    if "," in t:
        return "any"
    if t.startswith("list[") and t.endswith("]"):
        return t
    if t in ("int", "float", "bool", "str", "dict", "any", "list"):
        return t
    return "any"


def first_unused(pool: tuple[str, ...], taken: set) -> str:
    """Pool'dan ilk kullanılmamış ismi döndür, yoksa suffix ekle."""
    for name in pool:
        if name not in taken:
            return name
    base = pool[0]
    n = 2
    while True:
        cand = f"{base}{n}"
        if cand not in taken:
            return cand
        n += 1


# ─── function_name extract ───────────────────────────────────
RE_DEF = re.compile(r"^\s*(?:async\s+)?def\s+(\w+)\s*\(", re.MULTILINE)
RE_CLASS = re.compile(r"^\s*class\s+(\w+)\s*[:\(]", re.MULTILINE)


def extract_function_name(starter_code: str) -> str | None:
    """starter_code'dan ilk fonksiyon/class adını çıkar. Hem def X hem class Y."""
    if not starter_code:
        return None
    m = RE_DEF.search(starter_code)
    if m:
        return m.group(1)
    m = RE_CLASS.search(starter_code)
    if m:
        return m.group(1)
    return None


# ─── arg0/arg1/arg2 → anlamlı isim ─────────────────────────────
RE_PARAM = re.compile(r"arg(\d+)\s*:\s*([^,)=]+)")


def rename_args(starter_code: str) -> tuple[str, dict[str, str]]:
    """starter_code içindeki arg0/arg1/arg2/... isimlerini tip-sırasına göre rename et.

    Returns: (new_code, rename_map)
    """
    if not starter_code or "arg0" not in starter_code and "arg1" not in starter_code:
        return starter_code, {}

    # groupby tip + index sırasına göre kullanılmış isimleri takip et
    used_names: dict[str, set] = {}  # tip -> kullanılan isimler
    rename: dict[str, str] = {}

    # Tüm parametreleri sırayla topla
    matches = list(RE_PARAM.finditer(starter_code))
    for m in matches:
        old = f"arg{m.group(1)}"
        if old in rename:
            continue  # aynı arg0 birden fazla geçiyorsa ilk eşleşmede kararla
        type_str = normalize_type(m.group(2))
        pool = type_pool(type_str)
        taken = used_names.setdefault(type_str, set())
        new_name = first_unused(pool, taken)
        taken.add(new_name)
        rename[old] = new_name

    if not rename:
        return starter_code, {}

    # Code içinde tüm eşleşmeleri replace et — kelime sınırı ile
    new_code = starter_code
    for old, new in rename.items():
        # \b regex word boundary: arg0 identifier olarak eşleşsin
        # ama arg01/arg012 gibi alt-string'leri yemesin
        # Python'da \b sol-sağ alphanumeric/underscore. arg0 + non-word char OK.
        new_code = re.sub(rf"\b{re.escape(old)}\b", new, new_code)

    return new_code, rename


# ─── Main ─────────────────────────────────────────────────────
def main():
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    updated_fn = 0
    updated_args = 0
    rename_log = []  # (id, before, after, rename_map)

    for row in rows:
        sc = row.get("starter_code", "") or ""

        # 1) function_name dolu değilse regex extract
        fn_now = (row.get("function_name") or "").strip()
        if not fn_now:
            extracted = extract_function_name(sc)
            if extracted:
                row["function_name"] = extracted
                updated_fn += 1

        # 2) starter_code içindeki arg0/arg1/arg2 placeholder'ları rename
        if sc and ("arg0" in sc or "arg1" in sc):
            new_sc, renames = rename_args(sc)
            if renames:
                row["starter_code"] = new_sc
                updated_args += 1
                rename_log.append((row["id"], sc.split("\n")[0], new_sc.split("\n")[0], renames))

    # Write back — quoting=QUOTE_ALL ve quotechar default
    # Önceki format QUOTE_ALL olduğu için koruyalım
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✔ {CSV_PATH}")
    print(f"  function_name doldurulan: {updated_fn}")
    print(f"  arg-rename uygulanan satır: {updated_args}")
    print(f"  Toplam düzeltme: {updated_fn + updated_args}")
    if rename_log:
        print(f"\n--- Örnek düzeltmeler ({min(len(rename_log), 5)}/{len(rename_log)}) ---")
        for rid, before, after, renames in rename_log[:5]:
            print(f"  id={rid}")
            print(f"    before: {before}")
            print(f"    after:  {after}")
            print(f"    renames: {renames}")


if __name__ == "__main__":
    main()
