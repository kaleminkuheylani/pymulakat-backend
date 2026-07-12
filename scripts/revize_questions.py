#!/usr/bin/env python3
"""
CSV revize script — Excel raporundaki 37 ID'yi düzelt.
- Duplicate (10): birini sil
- Bozuk title (8): düzelt
- Kesik açıklama (14): düzelt
- Fonksiyon çakışma (4): rename
- Imza/test uyumsuz (4): düzelt
- Boş hints (6): ekle
"""
import csv
import shutil
from pathlib import Path

CSV_PATH = "data/QUESTIONS-v3.csv"
BAK_PATH = "data/QUESTIONS-v3.csv.pre-revize.bak"

# ─────────────────────────────────────────────────────────────────
# 1) DUPLICATE: Birini sil (daha düşük ID'li kalır)
# ─────────────────────────────────────────────────────────────────
DELETE_IDS = {
    "92",  # Bir 2D matris var (transpose dup of 14)
    "138", # Pivotlanmış Binary Search (search_rotated dup of 95)
    "155", # Top K Frequent Elements (top_k_frequent dup of 100)
    "146", # Longest Increasing Subsequence (lis dup of 33 — actually keep this)
    "168", # Sliding Window Maximum (sliding_window_max dup of 132)
}
# 146'yı tutmaya karar verdim, geri al
DELETE_IDS.discard("146")

# ─────────────────────────────────────────────────────────────────
# 2) BAŞLIK DÜZELTMESİ (bozuk/kesik title)
# ─────────────────────────────────────────────────────────────────
TITLE_FIXES = {
    "50": "En Kısa Yol (BFS)",
    "92": "Matris Transpozu 2",
    "96": "Tepe Elemanı Bul",
    "123": "Cümle Tokenize",
    "128": "En Uzun Artan Alt Dizi Uzunluğu",
    "133": "Liste Kesişimi (Sıralı)",
    "135": "Parantez Dengeleme",
    "136": "Linked List Döngü Tespiti",
}

# ─────────────────────────────────────────────────────────────────
# 3) AÇIKLAMA DÜZELTMESİ (kesik/bozuk)
# ─────────────────────────────────────────────────────────────────
DESCRIPTION_FIXES = {
    "37": (
        "fill_missing",
        "Bir sayı listesindeki None değerleri, listenin ortalamasıyla doldur. "
        "Ortalama hesaplanırken None değerler yoksayılır. "
        "Tüm liste None ise tüm elemanlar None kalır. "
        "Liste boşsa boş liste döndür.\n\n"
        "Örnek: [1, None, 3, None, 5] → [1, 3.0, 3, 3.0, 5] (ortalama = 3.0)\n\n"
        "pandas/NumPy kullanmadan, saf Python (sum, len, list comprehension) ile çöz.",
    ),
    "41": (
        "remove_duplicates_count",
        "Bir listedeki tekrar eden öğeleri kaldır ve kaç tane kaldırıldığını döndür. "
        "Sonuç: (temizlenmiş_liste, kaldırılan_sayısı) tuple'ı. "
        "Sıra korunur, ilk görülen kalır.\n\n"
        "Örnek: [1, 2, 2, 3, 3, 3, 4] → ([1, 2, 3, 4], 3) "
        "(3 adet tekrar kaldırıldı: bir 2 ve iki 3).\n\n"
        "dict.fromkeys veya set kullanmadan, manuel çözüm gerekli.",
    ),
    "71": (
        "longest_char_chain",
        "Bir string içinde art arda tekrar eden karakterlerden oluşan en uzun zinciri bul. "
        "Sonuç: (karakter, zincir_uzunluğu) tuple'ı. "
        "Birden fazla eşit uzunlukta zincir varsa alfabetik ilk karakteri döndür.\n\n"
        "Örnek: 'aabbbcccddde' → ('b', 3) veya 'aaabbb' → ('a', 3)\n\n"
        "itertools.groupby yasak, manuel sayaç mantığı gerekli.",
    ),
    "72": (
        "subarray_sum_exists",
        "Bir sayı listesi ve bir hedef sayı veriliyor. "
        "Listedeki herhangi bir alt dizinin (continuous subsequence) toplamı hedefe eşit mi? "
        "Varsa True, yoksa False döndür. "
        "Boş alt dizi toplamı 0 kabul edilir, hedef 0 ise True.\n\n"
        "Örnek: [1, 4, 2, 7], hedef=6 → True (4+2). "
        "Örnek: [1, 4, 2, 7], hedef=20 → False.\n\n"
        "O(n^2) brute force kabul, O(n) prefix sum ile optimal çözüm teşvik edilir.",
    ),
    "84": (
        "sum_even_squares",
        "Bir sayı listesi var. Listedeki SADECE çift sayıların karelerini al ve topla. "
        "Tek sayılar yok sayılır (sadece çiftler işlenir). "
        "Liste boşsa 0 döndür.\n\n"
        "Örnek: [1, 2, 3, 4, 5, 6] → 4² + 6² = 16 + 36 = 52.\n\n"
        "sum() ve filter() kullanmadan, manuel akümülatör gerekli (for döngüsü).",
    ),
    "88": (
        "two_sum_pairs",
        "Bir liste ve bir hedef sayı var. Listedeki hangi iki sayının toplamı hedefe eşit? "
        "Tüm benzersiz çiftleri (küçük, büyük) sırayla, hedef sırasına göre listele. "
        "Aynı değer iki kez kullanılamaz.\n\n"
        "Örnek: [1, 5, 3, 7, 2], hedef=8 → [(1, 7), (3, 5)]\n\n"
        "dict (hash map) ile O(n) çözüm; nested loop O(n²) kabul ama yavaş.",
    ),
    "92": (
        "transpose_matrix",
        "Verilen dikdörtgen bir matrisin transpozunu hesapla. "
        "Tüm satırlar aynı uzunlukta olmalı (input doğrulaması yapılır). "
        "Boş matris için boş liste döndür.\n\n"
        "Örnek: [[1,2,3], [4,5,6]] → [[1,4], [2,5], [3,6]]\n\n"
        "zip(*) yasak, manuel nested loop ile yeni matris oluştur.",
    ),
    "96": (
        "find_peak_element",
        "Bir dizide tepe elemanı bul: nums[i-1] < nums[i] > nums[i+1]. "
        "Sadece komşularına bakarak (O(log n)) bulunabilir. "
        "Birden fazla tepe varsa herhangi birinin indeksini döndür.\n\n"
        "Örnek: [1, 2, 3, 1] → 2 (nums[2]=3). "
        "Kenar elemanlar da tepe olabilir (sadece bir komşuya bakılır).\n\n"
        "Modified binary search: ortadan başla, tarafa göre daralt.",
    ),
    "97": (
        "is_palindrome_two_pointer",
        "Bir string'in palindrom olup olmadığını iki işaretçi ile kontrol et. "
        "Alfanümerik olmayan karakterler (boşluk, noktalama, büyük/küçük harf farkı) yoksayılır. "
        "Boş string palindrom kabul edilir.\n\n"
        "Örnek: 'A man, a plan, a canal: Panama' → True. "
        "Örnek: 'race a car' → False.\n\n"
        "str.replace/re.sub yasak, manuel karakter kontrolü gerekli.",
    ),
    "122": (
        "symmetric_difference",
        "İki listeyi parametre al. Yalnızca bir listede bulunan elemanları (simetrik fark) "
        "küçükten büyüğe sıralı liste olarak döndür. "
        "Tekrarlayan elemanlar tekilleştirilir.\n\n"
        "Örnek: [1, 2, 3], [2, 3, 4] → [1, 4]. "
        "Örnek: [1, 1, 2], [2, 3, 3] → [1, 3].\n\n"
        "set kullanmadan, manuel döngü ile çöz.",
    ),
    "124": (
        "majority_element",
        "Bir dizide n/2'den fazla geçen elemanı bul. "
        "Her zaman böyle bir eleman olduğu garanti edilir. "
        "Birden fazla varsa herhangi birini döndür.\n\n"
        "Örnek: [3, 2, 3] → 3. "
        "Örnek: [2, 2, 1, 1, 1, 2, 2] → 2.\n\n"
        "Boyer-Moore Voting Algorithm O(n) O(1) optimal çözüm.",
    ),
    "127": (
        "dataframe_row_normalize",
        "Bir DataFrame'in sayısal sütunlarını satır bazlı normalize et: "
        "her satırdaki değerler, o satırın toplamına bölünür (yüzde). "
        "Satır toplamı 0 olan satırlar aynen kalır (NaN yerine 0). "
        "Sayısal olmayan sütunlar dokunulmaz.\n\n"
        "Girdi/çıktı: DataFrame dict olarak verilir. "
        "Örnek giriş: {'a': [1, 2], 'b': [3, 4]} → "
        "çıkış: {'a': [0.25, 0.333], 'b': [0.75, 0.667]}.",
    ),
    "128": (
        "longest_increasing_subsequence",
        "Bir dizideki en uzun kesin artan altdizinin uzunluğunu bul. "
        "LIS — O(n log n) patience sorting veya O(n²) DP.\n\n"
        "Örnek: [10, 9, 2, 5, 3, 7, 101, 18] → 4 (2, 3, 7, 101). "
        "Altdizi sürekli olmak zorunda değil, sadece artan sırada olmalı.",
    ),
    "138": (
        "search_in_rotated_array",
        "Döndürülmüş sıralı dizide hedef değeri bul. Varsa index, yoksa -1. "
        "Dizi orijinalde sıralı, sonra herhangi bir pivot noktasında döndürülmüş "
        "(örn. [4,5,6,7,0,1,2]). Tüm elemanlar unique.\n\n"
        "Örnek: nums=[4,5,6,7,0,1,2], target=0 → 4. "
        "Modified binary search O(log n).",
    ),
}

# ─────────────────────────────────────────────────────────────────
# 4) FONKSİYON ADI ÇAKIŞMA DÜZELTMESİ
# ─────────────────────────────────────────────────────────────────
FUNCTION_NAME_FIXES = {
    # 27 merge_dicts (toplama) vs 137 merge_dicts (ikinci kazansın)
    "27": "merge_dicts_sum",
    "137": "merge_dicts_override",
    # 49 climb_stairs (grid) vs 142 climb_stairs (fibonacci merdiven)
    "49": "grid_unique_paths",
    "142": "stair_climb_steps",
}

# ─────────────────────────────────────────────────────────────────
# 5) STARTER_CODE / TEST FIXLERİ
# ─────────────────────────────────────────────────────────────────
IMZA_TEST_FIXES = {
    # id=41: starter test uyuşmazlığı (list[list[int]] ama test list[int])
    "41": {
        "starter_code": (
            "def remove_duplicates_count(nums: list[int]) -> tuple[list[int], int]:\n"
            "    # dict.fromkeys veya set yasak\n"
            "    # Manuel dedupe (sıra korunur, ilk görülen kalır)\n"
            "    pass"
        ),
    },
    # id=45: type hint hatası list[None] → list[float | None]
    "45": {
        "starter_code": (
            "def rolling_average(nums: list[float], k: int) -> list[float | None]:\n"
            "    # Manuel kayan pencere hesabı\n"
            "    pass"
        ),
    },
    # id=130: pandas test verisi düzelt (NaN doldurma, açıklayıcı text)
    "130": {
        "starter_code": (
            "def fill_missing_categorical(data: list[dict]) -> list[dict]:\n"
            "    # Her dict'teki 'category' alanı None ise en sık geçen değerle doldur\n"
            "    # data list of dicts (her dict: {'name': '...', 'category': 'X' veya None})\n"
            "    # en sık kategori tüm veriden hesaplanır\n"
            "    pass"
        ),
    },
    # id=139: pandas NaN sayımı, otomatik değerlendirilemez → saf Python
    "139": {
        "starter_code": (
            "def count_nans_per_column(data: list[dict]) -> dict:\n"
            "    # data: list of dicts, her dict bir satır\n"
            "    # Her sütun (key) için None/NaN sayısını döndür\n"
            "    # Sonuç: {'col1': 3, 'col2': 0, ...}\n"
            "    pass"
        ),
    },
}

# ─────────────────────────────────────────────────────────────────
# 6) BOŞ HINTS (medium bulgu) — 6 ID
# ─────────────────────────────────────────────────────────────────
HINTS_FIXES = {
    "9": [
        "İpucu 1: İlk iki eleman özel: [0] ve [0, 1].",
        "İpucu 2: Döngü ile: a, b = b, a+b her iterasyonda.",
        "İpucu 3: List append ile n eleman biriktir.",
    ],
    "40": [
        "İpucu 1: Pearson = cov(X, Y) / (std(X) * std(Y)).",
        "İpucu 2: Önce ortalama al, sonra sapma çarpımı topla.",
        "İpucu 3: |r| < 0.4 zayıf, 0.4-0.7 orta, ≥ 0.7 güçlü.",
    ],
    "45": [
        "İpucu 1: Pencere = liste dilimi data[i-k+1 : i+1].",
        "İpucu 2: İlk k-1 için None döndür (yetersiz veri).",
        "İpucu 3: Kısa yol: sum(window) / k.",
    ],
    "88": [
        "İpucu 1: Hash map: her sayının hedef-a eşini kontrol et.",
        "İpucu 2: dict[needed] = i, dict[number] = i.",
        "İpucu 3: Aynı çifti tekrar ekleme (set kullan).",
    ],
    "92": [
        "İpucu 1: Transpoz: result[j][i] = matrix[i][j].",
        "İpucu 2: zip(*) yasak, manuel nested loop gerekli.",
        "İpucu 3: Yeni matris: rows × cols → cols × rows.",
    ],
    "121": [
        "İpucu 1: sorted() key parametresi tuple alabilir.",
        "İpucu 2: sorted(data, key=lambda x: (x['age'], x['name']))",
        "İpucu 3: Çoklu anahtar: (k1, k2) soldan sağa öncelikli.",
    ],
    "130": [
        "İpucu 1: İlk geçişte her kategorinin frekansını say.",
        "İpucu 2: max(counts, key=counts.get) en sık olanı verir.",
        "İpucu 3: İkinci geçişte None'ları en sık ile değiştir.",
    ],
}


# ─────────────────────────────────────────────────────────────────
# UYGULA
# ─────────────────────────────────────────────────────────────────
shutil.copy(CSV_PATH, BAK_PATH)
print(f"✓ Yedek: {BAK_PATH}")

with open(CSV_PATH, encoding="utf-8", newline="") as f:
    rows = list(csv.reader(f))

header = rows[0]
id_idx = header.index("id")
title_idx = header.index("title")
fn_idx = header.index("function_name")
desc_idx = header.index("description")
sc_idx = header.index("starter_code")
hints_idx = header.index("hints")

stats = {"delete": 0, "title": 0, "desc": 0, "fn": 0, "imza": 0, "hints": 0}

new_rows = [header]
for row in rows[1:]:
    if len(row) <= id_idx:
        new_rows.append(row)
        continue
    sid = row[id_idx].strip()
    
    # 1) Sil
    if sid in DELETE_IDS:
        stats["delete"] += 1
        print(f"  ✗ SİL id={sid}: {row[title_idx]}")
        continue
    
    # 2) Title
    if sid in TITLE_FIXES:
        old = row[title_idx]
        row[title_idx] = TITLE_FIXES[sid]
        if old != row[title_idx]:
            stats["title"] += 1
            print(f"  ✓ TITLE id={sid}: '{old}' → '{row[title_idx]}'")
    
    # 3) Description (+ function_name birlikte gelirse)
    if sid in DESCRIPTION_FIXES:
        new_fn, new_desc = DESCRIPTION_FIXES[sid]
        old = row[desc_idx]
        # CSV escape
        new_desc_q = new_desc.replace('"', '""')
        if old != new_desc_q:
            row[desc_idx] = new_desc_q
            stats["desc"] += 1
            print(f"  ✓ DESC id={sid}: güncellendi")
        if new_fn and row[fn_idx] != new_fn:
            row[fn_idx] = new_fn
            print(f"    + fn: {new_fn}")
    
    # 4) Function name
    if sid in FUNCTION_NAME_FIXES:
        old = row[fn_idx]
        row[fn_idx] = FUNCTION_NAME_FIXES[sid]
        if old != row[fn_idx]:
            stats["fn"] += 1
            print(f"  ✓ FN id={sid}: '{old}' → '{row[fn_idx]}'")
    
    # 5) Starter code
    if sid in IMZA_TEST_FIXES:
        new_sc = IMZA_TEST_FIXES[sid]["starter_code"]
        new_sc_q = new_sc.replace('"', '""')
        old = row[sc_idx]
        if old != new_sc_q:
            row[sc_idx] = new_sc_q
            stats["imza"] += 1
            print(f"  ✓ SC id={sid}: starter_code düzeltildi")
    
    # 6) Hints
    if sid in HINTS_FIXES:
        import json
        hints_json = json.dumps(HINTS_FIXES[sid], ensure_ascii=False)
        # CSV escape
        hints_q = hints_json.replace('"', '""')
        if row[hints_idx] != hints_q:
            row[hints_idx] = hints_q
            stats["hints"] += 1
            print(f"  ✓ HINTS id={sid}: {len(HINTS_FIXES[sid])} ipucu eklendi")
    
    new_rows.append(row)

with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
    writer.writerows(new_rows)

print(f"\n── ÖZET ──")
print(f"  Silinen:        {stats['delete']}")
print(f"  Title düzeltme: {stats['title']}")
print(f"  Desc düzeltme:  {stats['desc']}")
print(f"  Fn rename:      {stats['fn']}")
print(f"  Starter fix:    {stats['imza']}")
print(f"  Hints ekleme:   {stats['hints']}")
print(f"\n  Önce: {len(rows)-1} → Sonra: {len(new_rows)-1}")
print(f"✓ CSV güncellendi: {CSV_PATH}")
