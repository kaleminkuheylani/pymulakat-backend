"""Shared helper for test case generation."""


def tcs(*cases):
    """Test case listesi oluştur.

    Her case dict'inin "input" key'i zorunlu, "expected" opsiyonel.
    expected yoksa tüm dict (input dahil) test case olarak saklanır.

    Kullanım:
        tcs(
            {"input": {...}, "expected": ...},  # normal
            {"input": {...}},                  # manual check (no expected)
            {"input": {...}, "_manual_check": "..."},  # annotated
        )
    """
    result = []
    for c in cases:
        if "input" not in c:
            raise ValueError(f"Test case missing 'input': {c}")
        tc = {"input": c["input"]}
        if "expected" in c:
            tc["expected"] = c["expected"]
        elif "_manual_check" in c:
            tc["_manual_check"] = c["_manual_check"]
        elif "expected_count" in c:
            tc["expected_count"] = c["expected_count"]
        elif "expected_len" in c:
            tc["expected_len"] = c["expected_len"]
        else:
            # No expected → manual check (whole dict as semantic marker)
            tc["_manual_check"] = repr(c)
        result.append(tc)
    return result