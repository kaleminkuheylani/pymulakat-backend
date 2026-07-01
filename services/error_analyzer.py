# services/error_analyzer.py
# Hata sınıflandırma + lint — kullanıcının yazdığı koddan ne tür hata yaptığını çıkarır.
# AI YOK — pattern matching + heuristic.

import re
from typing import Dict, List, Optional, Tuple

# ── Hata kategorileri (lint + kategorizasyon) ─────────────

class ErrorCategory:
    SYNTAX = "syntax"
    INDENTATION = "indentation"
    TYPE_ERROR = "type_error"
    NAME_ERROR = "name_error"
    INDEX_ERROR = "index_error"
    KEY_ERROR = "key_error"
    ATTRIBUTE_ERROR = "attribute_error"
    LOGIC = "logic"
    OFF_BY_ONE = "off_by_one"
    INFINITE_LOOP = "infinite_loop"
    NONE_RETURN = "none_return"
    OFF_BY_SIGN = "off_by_sign"
    COMPARISON = "comparison"
    CONFUSION = "confusion"  # anlaşılamayan / çok karmaşık
    MISSING_RETURN = "missing_return"
    WRONG_ALGORITHM = "wrong_algorithm"
    EMPTY_CODE = "empty_code"


CATEGORY_LABELS_TR: Dict[str, str] = {
    "syntax": "Yazım Hatası (Syntax)",
    "indentation": "Girinti Hatası",
    "type_error": "Tip Hatası",
    "name_error": "Tanımsız Değişken",
    "index_error": "Liste/Metin İndeks Hatası",
    "key_error": "Sözlük Anahtarı Yok",
    "attribute_error": "Nesne Özelliği Yok",
    "logic": "Mantık Hatası",
    "off_by_one": "Sınır Hatası (off-by-one)",
    "off_by_sign": "İşaret Hatası (+/- karışması)",
    "infinite_loop": "Sonsuz Döngü",
    "none_return": "None Dönmek",
    "missing_return": "Eksik Return",
    "comparison": "Karşılaştırma Hatası",
    "confusion": "Yaklaşım Karışıklığı",
    "wrong_algorithm": "Algoritma Yanlış",
    "empty_code": "Boş Kod",
}


# ── Syntax pattern'leri (Pyodide output) ────────────────

SYNTAX_PATTERNS = [
    (r"SyntaxError: invalid syntax", "syntax"),
    (r"SyntaxError:.*was never closed", "syntax"),
    (r"SyntaxError:.*never closed", "syntax"),
    (r"SyntaxError: EOF while parsing", "syntax"),
    (r"SyntaxError: unmatched", "syntax"),
    (r"IndentationError", "indentation"),
    (r"unexpected indent", "indentation"),
    (r"unindent does not match", "indentation"),
    (r"TabError", "indentation"),
]

RUNTIME_PATTERNS = [
    (r"NameError: name '(\w+)' is not defined", "name_error"),
    (r"TypeError: unsupported operand", "type_error"),
    (r"TypeError: can'?t convert", "type_error"),
    (r"TypeError: object is not callable", "type_error"),
    (r"TypeError: 'NoneType' object", "none_return"),
    (r"IndexError: list index out of range", "index_error"),
    (r"IndexError: string index out of range", "index_error"),
    (r"KeyError:\s*['\"]?(\w+)['\"]?", "key_error"),
    (r"AttributeError: '(\w+)' object has no attribute", "attribute_error"),
    (r"RecursionError", "infinite_loop"),
    (r"MemoryError", "infinite_loop"),
]


def classify_error(error_text: Optional[str], user_code: str = "") -> Tuple[str, str]:
    """
    Bir Pyodide hata metnini sınıflandır.
    Returns: (category, short_label)
    """
    if not user_code or user_code.strip() in ("", "pass", "# Buraya kodunu yaz"):
        return ("empty_code", CATEGORY_LABELS_TR["empty_code"])

    # Önce syntax/runtime pattern'leri — error_text varsa öncelikli
    if error_text:
        for pat, cat in SYNTAX_PATTERNS:
            if re.search(pat, error_text):
                return (cat, CATEGORY_LABELS_TR.get(cat, cat))
        for pat, cat in RUNTIME_PATTERNS:
            if re.search(pat, error_text):
                return (cat, CATEGORY_LABELS_TR.get(cat, cat))

    # error_text yoksa logic heuristikleri
    if "return" not in user_code and "print" not in user_code:
        return ("missing_return", CATEGORY_LABELS_TR["missing_return"])
    if re.search(r"\bif\s+\w+\s*=\s*\w+\s*:", user_code):
        return ("comparison", CATEGORY_LABELS_TR["comparison"])
    if re.search(r"range\(\s*len\([^)]+\)\s*\)\s*:", user_code):
        return ("off_by_one", CATEGORY_LABELS_TR["off_by_one"])

    return ("logic", CATEGORY_LABELS_TR["logic"])


def difficulty_of_error(category: str) -> int:
    """
    Hata zorluğu 1-5:
    1 = trivial (syntax, indentation)
    2 = beginner (type, name)
    3 = intermediate (index, key, logic)
    4 = advanced (algorithm, recursion)
    5 = expert (off-by-one subtle logic)
    """
    map_ = {
        "syntax": 1, "indentation": 1,
        "name_error": 2, "type_error": 2, "empty_code": 1,
        "index_error": 3, "key_error": 3, "attribute_error": 3,
        "missing_return": 2, "comparison": 2, "none_return": 3,
        "off_by_one": 4, "off_by_sign": 3,
        "logic": 3, "confusion": 4,
        "infinite_loop": 3, "wrong_algorithm": 5,
    }
    return map_.get(category, 3)


# ── Time-window korelasyonu (±5dk) ─────────────────────

def correlate_nearby_errors(reports: List[Dict], window_minutes: int = 5) -> List[List[Dict]]:
    """
    Birbirine ±window_minutes dakika içinde olan hataları grupla.
    Returns: cluster list — her cluster aynı anda çözülen hatalar.
    """
    if not reports:
        return []
    sorted_r = sorted(reports, key=lambda x: x.get("created_at", ""))
    clusters: List[List[Dict]] = []
    cur: List[Dict] = [sorted_r[0]]
    from datetime import datetime, timedelta
    for r in sorted_r[1:]:
        try:
            t1 = datetime.fromisoformat(cur[-1]["created_at"].replace("Z", "+00:00"))
            t2 = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
            if abs((t2 - t1).total_seconds()) <= window_minutes * 60:
                cur.append(r)
            else:
                if len(cur) >= 2:
                    clusters.append(cur)
                cur = [r]
        except Exception:
            cur = [r]
    if len(cur) >= 2:
        clusters.append(cur)
    return clusters