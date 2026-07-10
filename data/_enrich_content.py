"""
_enrich_content.py — CSV'de thin description/hints zenginleştir + test case duplicate düzelt.

Mimari: CSV-only. Bu script idempotent: zenginse skip.
"""
import csv
import shutil
from pathlib import Path
from datetime import datetime

CSV = Path("data/QUESTIONS-v3.csv")
BACKUP = Path(f"data/QUESTIONS-v3.csv.bak-{datetime.now().strftime('%H%M%S')}-pre-enrich2")
shutil.copy(CSV, BACKUP)
print(f"✓ Yedek: {BACKUP}")

rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
header = list(rows[0].keys())
changes = 0

# ─── 49 (Kaplama Problemi) — Climbing Stairs ile AYNI test case vardı ──
# Gerçek "kaplama" senaryosu: n×m grid (sağ+aşağı), kaç farklı yol.
# Climbing Stairs (142) doğru olan.
for r in rows:
    if r["id"] == "49":
        old_desc = r["description"].strip()
        new_desc = (
            "n×m'lik bir grid var (ör: 3×3). Sol üstten (0,0) sağ alta (n-1,m-1) "
            "sadece SAĞ veya AŞAĞI hareket edebilirsin.\n"
            "Kaç farklı yol var? Bu klasik bir DP problemidir: "
            "dp[i][j] = dp[i-1][j] + dp[i][j-1]. n=1 veya m=1 için yol sayısı 1'dir.\n"
            "Örnek: 2×2 grid'de 2 yol (sağ-aşağı veya aşağı-sağ)."
        )
        if len(new_desc) > len(old_desc):
            r["description"] = new_desc
            changes += 1
        new_tc = '[{"input": {"n": 2, "m": 2}, "expected": 2}, {"input": {"n": 3, "m": 3}, "expected": 6}, {"input": {"n": 1, "m": 5}, "expected": 1}, {"input": {"n": 4, "m": 4}, "expected": 20}]'
        if new_tc != r.get("test_cases", ""):
            r["test_cases"] = new_tc
            changes += 1
        new_hints = '["💡 dp[i][j] = dp[i-1][j] + dp[i][j-1] — sol ve üst komşudan topla", "💡 Base case: dp[0][j] = dp[i][0] = 1 (sadece tek yön)", "💡 Pascal üçgeni ile simetrik: C(n+m-2, n-1)"]'
        if not r.get("hints", "").strip():
            r["hints"] = new_hints
            changes += 1

# ─── Kısa description'ları zenginleştir ──────────────────────
# Her (id, description) çifti. description 80 char'dan kısa ise zenginleştir.
ENRICH = {
    "12": (
        "Bir listedeki ikinci en büyük eşsiz sayıyı döndür.\n"
        "Eğer yeterli eşsiz eleman yoksa None döndür.\n"
        "Örnek: [3, 5, 2, 5, 6, 6, 1] → 5 (en büyük 6, ikinci en büyük 5).\n"
        "Sort yerine set ile O(n) çözüm yapabilirsin."
    ),
    "13": (
        "Metni n karakter kaydırarak şifrele (yalnızca İngilizce harfler, a-z).\n"
        "Örnek: n=3, 'abc' → 'def'. Harf dışı karakterler (boşluk, rakam, noktalama) "
        "dokunulmaz.\n"
        "Negatif n değeri sola kaydırır (decrypt). Büyük harf veya Türkçe karakter "
        "dokunulmaz, sadece a-z işlenir."
    ),
    "16": (
        "Verilen bir string'deki parantezlerin dengeli olup olmadığını kontrol et.\n"
        "Parantez tipleri: (), [], {}. Sadece bu 3 tip desteklenir.\n"
        "Örnek: '()[]{}' → True, '([)]' → False, '{[()]}' → True.\n"
        "Stack (LIFO) yapısı ile O(n) çözüm: açan parantez stack'e it, kapayan parantez "
        "stack'ten son elemanla eşleşmeli."
    ),
    "18": (
        "Bir string'i run-length encoding ile sıkıştır.\n"
        "Örnek: 'aaabbc' → '3a2bc'. TekrarlanMAYAN karakterler 1 ile yazılmaz.\n"
        "Sadece ardışık tekrarlar sıkıştırılır. Tüm karakterler (harf, rakam, özel) "
        "desteklenir.\n"
        "Edge case: boş string → boş string."
    ),
    "21": (
        "1-3999 arasındaki bir tam sayıyı Roma rakamlarına çevir.\n"
        "Roma rakamları: I=1, V=5, X=10, L=50, C=100, D=500, M=1000.\n"
        "Çıkarma kuralı: IV=4, IX=9, XL=40, XC=90, CD=400, CM=900.\n"
        "Örnek: 1994 → 'MCMXCIV' (1000 + 900 + 90 + 4)."
    ),
    "22": (
        "Bir cümle pangram mı? (İngiliz alfabesinin tüm harflerini içeriyor mu?)\n"
        "26 harfin hepsi en az 1 kez geçmeli. Case insensitive.\n"
        "Örnek: 'The quick brown fox jumps over the lazy dog' → True.\n"
        "Edge case: 'Hello' → False (sadece 4 farklı harf)."
    ),
    "26": (
        "İki sıralı listeyi birleştirerek yeni bir sıralı liste oluştur.\n"
        "Her iki liste zaten sıralı (ascending). Sonuç da sıralı olmalı.\n"
        "Örnek: [1,3,5] + [2,4,6] → [1,2,3,4,5,6]. Tek liste boşsa diğerini döndür.\n"
        "İki pointer (i, j) ile O(n+m) çözüm."
    ),
    "27": (
        "İki sözlüğü birleştir. Aynı anahtarlar varsa değerlerini topla.\n"
        "Örnek: {a:1, b:2} + {b:3, c:4} → {a:1, b:5, c:4}.\n"
        "dict.update veya **spread ile yapılabilir ama aynı key toplama özel "
        "mantık gerektirir."
    ),
    "33": (
        "Bir dizideki en uzun sürekli artan alt dizinin uzunluğunu bul.\n"
        "Sürekli = ardışık indisler (skip yok).\n"
        "Örnek: [10, 9, 2, 5, 3, 7, 101, 18] için 4 ([2,3,7,101] veya [3,5,7,18]).\n"
        "DP yaklaşımı: dp[i] = nums[i]'den biten en uzun artan alt dizi."
    ),
    "34": (
        "Ürün fiyatlarının bulunduğu bir sözlükten min, max ve ortalama fiyatı "
        "döndür.\n"
        "Örnek: {'ekmek': 5, 'süt': 12, 'peynir': 45} → (5, 45, 20.67).\n"
        "Boş dict ise None veya raise ValueError. Ortalama 2 ondalık yuvarlanabilir."
    ),
    "42": (
        "Yaş listesini gruplara ayır: 0-17 'Genç', 18-64 'Yetişkin', 65+ 'Yaşlı'.\n"
        "Her yaş için karşılık gelen etiketi döndür.\n"
        "Örnek: [15, 25, 70] → ['Genç', 'Yetişkin', 'Yaşlı']. Pandas ile pd.cut veya "
        "saf Python ile if-elif-else."
    ),
    "73": (
        "Bir string'deki tüm benzersiz alt dizgilerin (substring) sayısını bul.\n"
        "Örnek: 'abc' → 6 ('a', 'b', 'c', 'ab', 'bc', 'abc').\n"
        "Formül: n*(n+1)/2 benzersiz substring'ler için, ama tekrar varsa azalır.\n"
        "En etkili çözüm: tüm olası substring'leri set'e ekle, len(set) al."
    ),
    "93": (
        "Bir string veriliyor. İlk kez tekrarlanMAYAN (unique) karakteri ve "
        "indeksini döndür. Yoksa None veya -1.\n"
        "Örnek: 'leetcode' → ('l', 0). 'aabb' → None.\n"
        "collections.Counter ile O(n) çözüm."
    ),
    "99": (
        "Bir dizide, dizideki elemanların toplamı daha büyük olan (dominant) "
        "sayıyı bul.\n"
        "Örnek: [16, 6, 3, 2, 1] → 16 (toplam 6+3+2+1=12, 16>12).\n"
        "2x > sum(dizi) kontrolü, max() ile en büyük dominant eleman."
    ),
    "102": (
        "Bir dizideki en uzun ard arda gelen sayı dizisinin uzunluğunu bul.\n"
        "Örnek: [100, 4, 200, 1, 3, 2] → 4 ([1,2,3,4]).\n"
        "HashSet yaklaşımı: O(n) — her eleman için zincirin uzunluğunu bul "
        "(komsuya bakarak)."
    ),
    "103": (
        "İki string'in anagram olup olmadığını kontrol et (harfler aynı, sıra farklı).\n"
        "Case insensitive. Boşluk ve özel karakterler yok sayılır.\n"
        "Örnek: 'listen' ↔ 'silent' → True. 'hello' ↔ 'world' → False.\n"
        "collections.Counter veya sorted() ile çözüm: O(n)."
    ),
    "111": (
        "İki koleksiyondaki ortak elemanları bul.\n"
        "Örnek: [1,2,3,4,5] ∩ [3,4,5,6,7] → [3, 4, 5]. Tekrarlar tekilleştirilir.\n"
        "set(a) & set(b) veya set(a).intersection(b)."
    ),
    "117": (
        "Sıralı bir koleksiyonda belirli bir değeri hızlıca bul.\n"
        "O(n) linear yerine O(log n) binary search kullan.\n"
        "Örnek: [1,3,5,7,9,11] içinde 7 → indeks 3. Yoksa -1.\n"
        "bisect.bisect_left(arr, target) tek satırda."
    ),
    "118": (
        "Bir koleksiyondaki en küçük K elemanı döndür.\n"
        "Listeyi tam sıralama O(n log n) yerine heap ile O(n log k).\n"
        "Örnek: [3,1,4,1,5,9,2,6], k=3 → [1, 1, 2]. heapq.nsmallest(k, iterable)."
    ),
    "130": (
        "DataFrame'deki kategorik sütunlarda NaN değerleri en sık geçen değerle "
        "(mode) doldur. Sayısal sütunlara dokunma.\n"
        "Her kategorik sütun kendi mode'u ile doldurulur.\n"
        "Örnek: {'şehir': ['İst', NaN, 'Ank', 'İst']} → 'İst' ile doldurulur."
    ),
    "132": (
        "Bir dizide k boyutunda kayan pencere ile her pencerenin maksimumunu bul.\n"
        "Örnek: [1,3,-1,-3,5,3,6,7], k=3 → [3,3,5,5,6,7].\n"
        "Deque (monotonic queue) ile O(n) çözüm: önceki küçük elemanları at."
    ),
    "136": (
        "Bir linked list'te döngü var mı? Tortoise-Hare (Floyd's cycle detection).\n"
        "İki pointer: slow 1 adım, fast 2 adım. Döngüde ise buluşurlar.\n"
        "Ek: döngünün başlangıç noktasını da bulabilirsin."
    ),
    "140": (
        "İki string birbirinin permütasyonu mu? (aynı karakterler farklı sırada).\n"
        "Örnek: 'abc' ↔ 'bca' → True. 'abc' ↔ 'abd' → False.\n"
        "Case sensitive. sorted() ile O(n log n), Counter ile O(n)."
    ),
    "145": (
        "İki string'in en uzun ortak alt dizisinin uzunluğu.\n"
        "LCS — klasik 2D DP.\n"
        "Örnek: 'abcde' vs 'ace' → 3 ('ace'). 'abc' vs 'abc' → 3.\n"
        "Formül: dp[i][j] = dp[i-1][j-1] + 1 (eşitse), max(dp[i-1][j], dp[i][j-1])."
    ),
    "147": (
        "Bir dizide en büyük toplam alt diziyi bul.\n"
        "Kadane's algorithm: O(n) — şu ana kadarki max'i tut.\n"
        "Örnek: [-2,1,-3,4,-1,2,1,-5,4] → 6 ([4,-1,2,1]).\n"
        "Tüm elemanlar negatifse en büyük (en az negatif) elemanı döndür."
    ),
    "150": (
        "m×n grid'de (0,0)'dan (m-1,n-1)'e sadece sağ/aşağı.\n"
        "Kaç farklı yol var?\n"
        "Örnek: 3×7 grid → 28 yol. Formül: C(m+n-2, m-1).\n"
        "DP: dp[i][j] = dp[i-1][j] + dp[i][j-1]."
    ),
    "151": (
        "Bir dizi ev var. Yan yana iki ev soyamazsın (alarm bağlı).\n"
        "Maksimum para. Maks 2 durum: soy (i) veya soyma (i-1).\n"
        "Formül: dp[i] = max(dp[i-1], dp[i-2] + nums[i]).\n"
        "Örnek: [2,7,9,3,1] → 12 (ev 0, 2, 4 veya ev 1, 3)."
    ),
    "152": (
        "Sayı string'ini decode et. A=1, B=2, ..., Z=26.\n"
        "Kaç farklı decode yolu var?\n"
        "Örnek: '12' → 2 ('AB' veya 'L'). '226' → 3. '06' → 0 (leading zero).\n"
        "DP: dp[i] = dp[i-1] (1 harf) + dp[i-2] (2 harf, 10-26 arası)."
    ),
    "153": (
        "Dizi iki alt kümeye bölünebilir mi, eşit toplam?\n"
        "Subset sum problem. Toplam tek ise False.\n"
        "Örnek: [1,5,11,5] → True ([1,5,5] ve [11]). [1,2,3,5] → False.\n"
        "DP yaklaşımı: hedef = sum/2, set ile olası toplamları tut."
    ),
    "154": (
        "Bir dizideki k. en büyük elemanı bul.\n"
        "O(n log k) heap ile. heapq.nlargest(k, liste)[-1].\n"
        "Örnek: [3,2,1,5,6,4], k=2 → 5. Quickselect ortalama O(n) ile de yapılabilir."
    ),
    "158": (
        "Aynı task arasında en az n boşluk olmalı. Minimum süre?\n"
        "Örnek: tasks=['A','A','A','B','B','B'], n=2 → 8.\n"
        "En sık task sayısı max_count, frame = (max_count-1)*(n+1), "
        "toplam = max(frame, len(tasks))."
    ),
    "160": (
        "İki en ağır taşı çarpıştır, küçük olan kaybolur (eşitse ikisi de).\n"
        "Son kalan taşın ağırlığı?\n"
        "Örnek: [2,7,4,1,8,1] → 1. heapq ile max-heap simülasyonu (negatif push)."
    ),
    "161": (
        "K sıralı dizide hepsinden en az 1 eleman içeren en küçük aralık.\n"
        "Örnek: [[4,10,15,20,24], [0,9,12,20], [5,18,22,30]] → [20,24] (aralık 4).\n"
        "Heap ile: her dizinin ilk elemanını heap'e at, min/max takip et."
    ),
    "164": (
        "Her gün için, sonraki daha sıcak günü kaç gün sonra? Yoksa 0.\n"
        "Örnek: [73,74,75,71,69,72,76,73] → [1,1,4,2,1,1,0,0].\n"
        "Stack (monotonic decreasing) ile O(n) çözüm: indeksleri tut."
    ),
    "167": (
        "Sadece stack kullanarak queue implement et. Amortized O(1) enqueue/dequeue.\n"
        "push: input stack'e ekle. pop: output stack boşsa input'tan aktar, "
        "sonra output'tan pop. Amortized O(1) çünkü her eleman en fazla 2 transfer."
    ),
    "168": (
        "Her k-boyutlu pencerede maksimum.\n"
        "Deque (monotonic queue) — O(n).\n"
        "Örnek: [1,3,-1,-3,5,3,6,7], k=3 → [3,3,5,5,6,7].\n"
        "Deque'da sadece potansiyel maksimumlar tutulur."
    ),
    "169": (
        "Sabit boyutlu circular queue tasarla.\n"
        "FIFO, front/rear wrap around (modular). O(1) enqueue/dequeue.\n"
        "Dolu vs boş kontrolü: count veya bir slot boş bırak (capacity vs max_size)."
    ),
    "170": (
        "Son 3000 ms içindeki ping sayısı. Her ping() çağrısı için.\n"
        "Deque (queue) ile: eski pings'leri (t-3000'den küçük) öne at, "
        "yeni ping'i arkaya ekle, len(deque) döndür.\n"
        "Örnek: ping(1), ping(300), ping(3000) → 3; ping(3002) → 3 (300 düşer)."
    ),
}

# ─── Boş hints için default (mimariye uygun minimal patch) ───
HINTS = {
    "4": '["💡 Her satır, sütun ve köşegen toplamı eşit mi kontrol et", "💡 Magic constant = n*(n²+1)/2 formülü", "💡 3x3 kare için 1+2+...+9 = 15 olmalı"]',
    "9": '["💡 Recursive: fib(n) = fib(n-1) + fib(n-2)", "💡 Iterative: a, b = 0, 1; n kez kaydır", "💡 Memoization veya @lru_cache ile performans"]',
    "26": '["💡 İki pointer: i ve j, küçük olanu result ekle", "💡 Bir liste bitince diğerinin kalanını ekle", "💡 Heap kullanmaya gerek yok (zaten sıralı)"]',
    "45": '["💡 collections.deque(maxlen=k) ile otomatik pencere", "💡 Her yeni eleman geldiğinde toplam += yeni - çıkan", "💡 Veya her adımda sum(window) hesapla"]',
    "87": '["💡 Set ile kontrol: nums[i] < nums[i+1] ve nums[i+1] > nums[i+2] mi?", "💡 Veya nums[i] > nums[i-1] ve nums[i] > nums[i+1]", "💡 Edge için tek komşuya bak"]',
    "88": '["💡 HashMap: her sayı için hedef-sayı zaten görüldü mü?", "💡 İki for loop: O(n²) basit ama yavaş", "💡 Sort + two pointers: O(n log n)"]',
    "90": '["💡 split() ile kelimelere ayır, [::-1] ile ters çevir, join", "💡 Her kelimeyi ters çevirmek için [::-1]", "💡 Sondaki boşlukları strip() ile temizle"]',
    "92": '["💡 zip(*matrix) ile transpose (built-in)", "💡 Manuel: [row[i] for row in matrix] for i in range", "💡 NumPy: np.array(matrix).T"]',
    "121": '["💡 sorted(key=lambda x: x[1]) ile tek kritere göre sırala", "💡 Çoklu: sorted(key=lambda x: (x[1], x[2]))", "💡 itemgetter kullan: from operator import itemgetter"]',
    "123": '["💡 Sırala, tek-tek kontrol et, sonraki küçükse atla", "💡 HashSet: tüm elemanları tut, sonra sırayla ara", "💡 Listenin son elemanı +1 = n ise tamamdır"]',
    "129": '["💡 Reverse edip baştan birleştir, sort() ile sırala, tekrar et", "💡 Sum of digits: n % 10, n // 10", "💡 Memoization ile cache tut"]',
}

# Description zenginleştir
for r in rows:
    rid = r["id"]
    if rid in ENRICH:
        new_desc = ENRICH[rid]
        if len(new_desc) > len(r.get("description", "").strip()):
            r["description"] = new_desc
            changes += 1

# Boş hints ekle
for r in rows:
    rid = r["id"]
    if rid in HINTS and not r.get("hints", "").strip():
        r["hints"] = HINTS[rid]
        changes += 1

# Yaz
with open(CSV, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=header)
    w.writeheader()
    w.writerows(rows)

print(f"✓ {changes} alan güncellendi")
print(f"✓ CSV: {CSV}")
print(f"  Boyut: {CSV.stat().st_size} bytes")
