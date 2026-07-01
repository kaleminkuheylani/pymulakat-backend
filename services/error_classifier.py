# services/error_classifier.py
# user_code + success bilgisinden hata tipi çıkar (heuristic, AI yok).
# Sadece coach kuralları için kullanılır — production'da hafif.

import re
from typing import Optional, Tuple


# ── Hata kategorileri (sadece 6 tane — coach için yeterli) ──

ERR_INDEX = "index_error"          # liste/metin sınır dışı
ERR_TYPE = "type_error"            # None + str, int + str
ERR_RECURSION = "recursion_error"  # RecursionError, MemoryError
ERR_NAME = "name_error"            # tanımsız değişken
ERR_ATTRIBUTE = "attribute_error"  # obj.method yok
ERR_KEY = "key_error"              # dict['yok']


CATEGORY_TO_TOPIC = {
    ERR_INDEX: ("list-dict.lists", "Liste/Metin Sınırları"),
    ERR_TYPE: ("python-basics.data_types.type_hints", "Tip Kontrolü"),
    ERR_RECURSION: ("algorithms.recursion.base_case", "Base Case (Özyineleme)"),
    ERR_NAME: ("python-basics.variables.naming", "Değişken Tanımı"),
    ERR_ATTRIBUTE: ("oop.classes.attributes_methods", "Nesne Metotları"),
    ERR_KEY: ("list-dict.dicts.get_setdefault", "Sözlük Güvenli Erişim"),
}


CATEGORY_LABELS = {
    ERR_INDEX: "Liste/Metin Sınır Hatası",
    ERR_TYPE: "Tip Hatası",
    ERR_RECURSION: "Özyineleme Hatası",
    ERR_NAME: "Tanımsız Değişken",
    ERR_ATTRIBUTE: "Nesne Özelliği Yok",
    ERR_KEY: "Sözlük Anahtarı Yok",
}


def classify_attempt(user_code: str, success: bool, passed: int = 0, total: int = 0) -> Optional[str]:
    """
    Bir attempt'ten hata kategorisi çıkar.
    success=True ise None döner (hata yok).
    Sadece user_code + test sonucu yeterli — gerçek Pyodide output'u gerekmez.

    Strateji:
    1. user_code boşsa → muhtemelen syntax (ama bunu 'logic' olarak sınıflandırmıyoruz)
    2. Recursion varsa → ERR_RECURSION
    3. Yaygın pattern'ler → heuristic eşleşme
    4. Bulunamazsa → None (kural tetiklenmez, generic feedback zaten var)
    """
    if success:
        return None
    if not user_code or user_code.strip() in ("", "pass"):
        return None  # boş kod → zaten başka kurallar bunu yakalar

    code = user_code

    # 1. Recursion açıkça kendini çağırıyorsa
    m = re.match(r"def\s+(\w+)\s*\([^)]*\)\s*:", code)
    if m:
        fn_name = m.group(1)
        if re.search(rf"\b{re.escape(fn_name)}\s*\(", code[m.end():]):
            return ERR_RECURSION

    # 2. Yaygın pattern'ler
    # IndexError: for + range(len(...)) veya manuel x[len(x)]
    if re.search(r"range\s*\(\s*len\s*\([^)]+\)\s*\)", code):
        # for i in range(len(arr)) pattern — tipik off-by-one
        return ERR_INDEX
    if re.search(r"\w+\s*\[\s*(?:len\s*\(\s*\w+\s*\)|-\s*1\s*)\s*\]", code):
        # x[len(x)] veya x[-1]
        return ERR_INDEX
    if re.search(r"\w+\s*\[\s*\w+\s*\+\s*1\s*\]", code) and re.search(r"range\s*\(\s*len\s*\(", code):
        return ERR_INDEX
    if re.search(r"for\s+\w+\s+in\s+range\s*\(\s*len", code):
        return ERR_INDEX

    # TypeError: None ile işlem
    if re.search(r"\bNone\b\s*[+\-*/]", code) or re.search(r"[+\-*/]\s*\bNone\b", code):
        return ERR_TYPE
    if re.search(r"return\s+\w+\s*[+\-*/]\s*1\b", code) and re.search(r"\bNone\b", code):
        return ERR_TYPE
    # str + int veya int + str
    if re.search(r"['\"]\s*\+\s*\d|\d\s*\+\s*['\"]", code):
        return ERR_TYPE
    if re.search(r"['\"][^'\"]*['\"]\s*\+\s*\w+\(", code) and not re.search(r"str\s*\(", code):
        return ERR_TYPE
    # str(x) + ' done' OK ama 'done' + x değil
    if re.search(r"\w+\s*\+\s*['\"][^'\"]*['\"]", code) and re.search(r"\bint\s*\(", code):
        return ERR_TYPE

    # NameError: for döngüsü değişkeni scope dışı kullanım
    # Basit heuristic: fonksiyon içinde değişken tanımlanıp dışarıda kullanılmış gibi
    # Daha karmaşık, geç

    # AttributeError: dict.method() veya set.append() gibi yanlış metot
    if re.search(r"dict\.\w+\s*\(", code):
        return ERR_ATTRIBUTE
    if re.search(r"set\.\w+\s*\(", code):
        return ERR_ATTRIBUTE
    if re.search(r"tuple\.\w+\s*\(", code):
        return ERR_ATTRIBUTE
    # .push() (Java/C# alışkanlığı)
    if re.search(r"\.\s*push\s*\(", code):
        return ERR_ATTRIBUTE
    # .length (JS alışkanlığı)
    if re.search(r"\.\s*length\b", code):
        return ERR_ATTRIBUTE

    # KeyError: d[key] doğrudan erişim + key_exists kontrolü yok
    if re.search(r"\w+\s*\[\s*['\"]\w+['\"]\s*\]", code) and not re.search(r"\w+\.get\s*\(", code):
        return ERR_KEY

    # Yaygın NameError pattern'i: değişken adı typo
    # for i in range(3): print(I)  (büyük I)
    # Bu tespit zor, geç

    # Hiçbir şey eşleşmedi
    return None


def get_recent_error_counts(user_id: str, days: int = 7, sb=None) -> dict:
    """
    Son `days` günde kullanıcının her hata kategorisinden kaç tane yaptığını say.
    Döner: {ERR_INDEX: 3, ERR_TYPE: 1, ...}
    """
    if sb is None:
        from supabase_client import get_supabase_admin
        sb = get_supabase_admin()

    from datetime import datetime, timezone, timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    try:
        result = (
            sb.table("interview_attempts")
            .select("user_code, success, passed_tests, total_tests")
            .eq("user_id", user_id)
            .gte("created_at", cutoff)
            .execute()
        )
        attempts = result.data or []
    except Exception:
        return {}

    counts = {cat: 0 for cat in CATEGORY_TO_TOPIC.keys()}
    for a in attempts:
        cat = classify_attempt(
            a.get("user_code") or "",
            a.get("success", False),
            a.get("passed_tests", 0),
            a.get("total_tests", 0),
        )
        if cat:
            counts[cat] += 1
    return counts