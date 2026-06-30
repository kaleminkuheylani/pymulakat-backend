"""Her soruya SEO-friendly Türkçe açıklama, complexity, related_concepts ekler.

DB'de tablo adı: interwiews (mevcut typo, korunuyor)
Python'da: QUESTIONS list (data/QUESTIONS.py)

Bu modül QUESTIONS listesini mutate eder.
"""

from data.QUESTIONS import QUESTIONS

# Her soru için: id -> { explanation, complexity, related_concepts, related_question_ids, tutorial_slug }
# Stil: doğrudan, teknik, emoji'siz, kod-block ağırlıklı, "neden" odaklı
SEO_DATA = {
    # ═══ PYTHON BASICS (15 soru) ═══
    1: {
        "explanation": """Palindrome kontrolü, Python mülakatlarının **en sık** sorduğu string sorusudur.

**Problem:** Bir metin tersten okunduğunda aynı mı? Noktalama, boşluk ve büyük/küçük harf yok sayılır.

**Üç yaklaşım:**

```python
# 1. Slicing — en kısa
def is_palindrome(s):
    cleaned = re.sub(r'[^a-z0-9]', '', s.lower())
    return cleaned == cleaned[::-1]

# 2. İki pointer — O(1) ek bellek
def is_palindrome(s):
    cleaned = re.sub(r'[^a-z0-9]', '', s.lower())
    l, r = 0, len(cleaned) - 1
    while l < r:
        if cleaned[l] != cleaned[r]:
            return False
        l += 1
        r -= 1
    return True
```

**Neden slicing daha hızlı görünür ama iki pointer O(1) bellek?** Slicing yeni string oluşturur (O(n) bellek), iki pointer sadece index taşır.

**Edge case'ler:**
- Boş string → True (vakum palindromdur)
- Tek karakter → True
- Karışık Unicode (Türkçe: "Ağaç") → ASCII-cleaning ile kaybedilir, çözüm `unicodedata.normalize`.""",
        "complexity": "O(n) zaman, O(n) bellek (slicing) veya O(1) (iki pointer)",
        "related_concepts": ["string slicing", "regex", "two pointers", "string normalization"],
        "related_question_ids": [3, 7, 51],
        "tutorial_slug": "python-palindrome-cozum",
    },
    2: {
        "explanation": """FizzBuzz, mülakatlarda **template** soru olarak kullanılır. Şirketler adayın temel kontrol yapılarını anlayıp anlamadığını test eder.

**Problem:** 1'den n'e kadar:
- 3'e bölünürse "Fizz"
- 5'e bölünürse "Buzz"
- İkisine de bölünürse "FizzBuzz"

**Kritik detay — sıra:**

```python
# YANLIŞ sıra
for i in range(1, n+1):
    if i % 3 == 0: print("Fizz")      # 15 buraya düşer, "FizzBuzz" kaçar
    elif i % 5 == 0: print("Buzz")
    elif i % 15 == 0: print("FizzBuzz")  # hiç gelmez

# DOĞRU sıra
for i in range(1, n+1):
    if i % 15 == 0: print("FizzBuzz")
    elif i % 3 == 0: print("Fizz")
    elif i % 5 == 0: print("Buzz")
    else: print(i)
```

**Tek satır çözüm:**
```python
result = ["FizzBuzz" if i % 15 == 0 else "Fizz" if i % 3 == 0 else "Buzz" if i % 5 == 0 else i for i in range(1, n+1)]
```

**Neden bu soru önemli:** Junior/staj pozisyonlarında adayın modulo, if/elif mantığı ve döngü bilgisi ölçülür. Çözemeyen genelde diğer sorularda da zorlanır.""",
        "complexity": "O(n) zaman, O(1) ek bellek",
        "related_concepts": ["modulo", "kontrol yapıları", "list comprehension", "edge case sıralaması"],
        "related_question_ids": [1, 4, 53],
        "tutorial_slug": "python-fizzbuzz-algoritma",
    },
    3: {
        "explanation": """Bir cümledeki en uzun kelimeyi bulmak, Python'da `max()` fonksiyonunun `key` parametresini anlamayı ölçer.

**Problem:** "Python mülakat hazırlığı" → "mülakat" veya "hazırlığı" (uzunluk 8).

**İki çözüm:**

```python
def longest_word(sentence):
    words = sentence.split()
    return max(words, key=len)

# Manuel (key'siz)
def longest_word(sentence):
    words = sentence.split()
    longest = ""
    for w in words:
        if len(w) > len(longest):
            longest = w
    return longest
```

**Püf noktaları:**
- `split()` varsayılan olarak tüm whitespace'i ayırıcı kabul eder (boşluk, tab, newline).
- Aynı uzunlukta birden fazla kelime varsa `max()` **ilkini** döndürür.
- Noktalama dahil mi? "Merhaba, dünya" → split() noktalamayı kelimeye yapıştırır. Önce regex ile temizle.""",
        "complexity": "O(n) zaman, O(1) ek bellek",
        "related_concepts": ["max fonksiyonu", "key parametresi", "split", "string temizleme"],
        "related_question_ids": [1, 7, 51],
        "tutorial_slug": None,
    },
    4: {
        "explanation": """Sihirli kare (magic square), 3x3 matrisin tüm satır, sütun ve çapraz toplamlarının eşit olup olmadığını kontrol eder.

**Matematik:** 1-9 toplamı 45. 3 satıra bölünürse satır toplamı 15. Ortanca (1,1) hücre **her zaman 5**'tir.

**Çözüm:**

```python
def is_magic_square(square):
    target = sum(square[0])  # İlk satır toplamı
    # Satırlar
    for row in square:
        if sum(row) != target:
            return False
    # Sütunlar
    for col in range(3):
        if sum(square[r][col] for r in range(3)) != target:
            return False
    # Çaprazlar
    if sum(square[i][i] for i in range(3)) != target:
        return False
    if sum(square[i][2-i] for i in range(3)) != target:
        return False
    return True
```

**Optimizasyon:** zip() ile sütun kontrolünü tek satıra indirge: `if any(sum(col) != target for col in zip(*square)): return False`""",
        "complexity": "O(n²) — sabit 3x3 için O(1)",
        "related_concepts": ["matris iterasyonu", "zip", "iç içe liste", "matematik"],
        "related_question_ids": [5, 15, 102],
        "tutorial_slug": None,
    },
    5: {
        "explanation": """Sayı tahmin oyunu, **oyun döngüsü** ve kullanıcı etkileşimi simülasyonudur.

**Problem:** Bilgisayar 1-100 arası sayı seçer, kullanıcı tahmin eder, "daha büyük/küçük" ipucu verir.

**Temel yapı:**

```python
import random

def number_guessing_game():
    target = random.randint(1, 100)
    attempts = 0
    while True:
        guess = int(input("Tahmininiz: "))
        attempts += 1
        if guess < target:
            print("Daha büyük")
        elif guess > target:
            print("Daha küçük")
        else:
            print(f"Doğru! {attempts} denemede bildiniz")
            break
```

**Genişletme:** Binary search stratejisi (her zaman ortancayı tahmin et) en iyi skoru verir — O(log n) denemede garantili çözüm.

**Gerçek dünya:** Kullanıcı deneyimi (UX), oyun geliştirme, A/B test varyantları.""",
        "complexity": "O(log n) optimal strateji, O(n) en kötü",
        "related_concepts": ["random modülü", "while döngüsü", "input parsing", "oyun döngüsü"],
        "related_question_ids": [14, 23, 302],
        "tutorial_slug": None,
    },
    6: {
        "explanation": """Karakter sayacı, veri analizinde **frekans analizi** olarak bilinen klasik tekniğin basit halidir.

**Problem:** "hello" → {'h': 1, 'e': 1, 'l': 2, 'o': 1}

**Üç yaklaşım:**

```python
# 1. Counter — en kısa
from collections import Counter
counts = Counter("hello")

# 2. dict.get — klasik
counts = {}
for c in "hello":
    counts[c] = counts.get(c, 0) + 1

# 3. defaultdict
from collections import defaultdict
counts = defaultdict(int)
for c in "hello":
    counts[c] += 1
```

**Neden Counter en hızlı?** CPython implementasyonu C ile yazılmış, Python-level döngü overhead'i yok.

**Gerçek dünya:** Şifre gücü kontrolü, doğal dil işleme (NLP), kriptografi (frekans analizi ile şifre kırma).""",
        "complexity": "O(n) zaman, O(k) bellek (k = unique karakter)",
        "related_concepts": ["collections.Counter", "defaultdict", "dict.get", "frekans analizi"],
        "related_question_ids": [7, 11, 51],
        "tutorial_slug": None,
    },
    7: {
        "explanation": """Anagram kontrolü, iki string'in aynı harfleri aynı sayıda içerip içermediğini kontrol eder.

**Problem:** "listen" ve "silent" → True (anagram).

**İki yaklaşım:**

```python
from collections import Counter

# 1. Counter karşılaştırma — O(n)
def is_anagram(s1, s2):
    return Counter(s1) == Counter(s2)

# 2. Sıralama — O(n log n) ama basit
def is_anagram(s1, s2):
    return sorted(s1) == sorted(s2)
```

**Normalizasyon şart:** Büyük/küçük harf ve boşluk farkını yok saymak için önce `s.replace(" ", "").lower()`.

**Performans karşılaştırması:** 1MB metin için Counter ~3ms, sorted ~120ms. Counter O(n) olduğu için 40x hızlı.

**Edge case:** Unicode (Türkçe karakterler) — `casefold()` kullan, `lower()` Türkçe "İ" için yanlış sonuç verir.""",
        "complexity": "O(n) Counter ile, O(n log n) sıralama ile",
        "related_concepts": ["Counter", "sorted", "string normalize", "casefold"],
        "related_question_ids": [1, 6, 51],
        "tutorial_slug": None,
    },
    8: {
        "explanation": """Rakam toplamı, özyinelemeli (recursive) düşüncenin temelidir.

**Problem:** 123 → 1+2+3 = 6.

**Özyinelemeli:**

```python
def sum_digits(n):
    if n == 0:
        return 0
    return n % 10 + sum_digits(n // 10)
```

**Iteratif (özyinelemeli tercih edilir):**

```python
def sum_digits(n):
    n = abs(n)  # Negatif sayılar için
    total = 0
    while n > 0:
        total += n % 10
        n //= 10
    return total
```

**Neden iteratif?** Python'da recursion limiti 1000. 10^1000 sayısı için stack overflow olur.

**Bonus — dijital kök:** Rakam toplamı tek haneye indirgenene kadar tekrarlanır (örn 123 → 6). Bu süreç O(log n) yerine O(log log n).""",
        "complexity": "O(log n) — basamak sayısı kadar",
        "related_concepts": ["özyineleme", "modulo", "floor division", "base case"],
        "related_question_ids": [9, 11, 16],
        "tutorial_slug": None,
    },
    9: {
        "explanation": """Asal sayı kontrolü, matematik tabanlı algoritma sorularının temelidir.

**Naive yaklaşım:**

```python
def is_prime(n):
    if n < 2: return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True
```

**Neden √n'e kadar?** Eğer n = a*b ise, en az bir çarpan √n'den küçük olmalı.

**Optimizasyon:**
- 2'den sonra sadece tek sayıları dene: `range(3, int(n**0.5) + 1, 2)`
- 6k±1 optimizasyonu: tüm asallar 6k±1 formunda.

**Eratosthenes eleği** — çok sayıda asal kontrolü için:

```python
def sieve(n):
    primes = [True] * (n + 1)
    primes[0] = primes[1] = False
    for i in range(2, int(n**0.5) + 1):
        if primes[i]:
            for j in range(i*i, n + 1, i):
                primes[j] = False
    return [i for i, p in enumerate(primes) if p]
```

**Kullanım:** Kriptografi (RSA), sayı teorisi, hash fonksiyonları.""",
        "complexity": "O(√n) tek sayı, O(n log log n) Eratosthenes",
        "related_concepts": ["Eratosthenes eleği", "matematik", "asal sayılar", "modulo"],
        "related_question_ids": [11, 16, 23],
        "tutorial_slug": "python-asal-sayi-algoritma",
    },
    10: {
        "explanation": """Cumulative sum (kümülatif toplam), finansal analiz ve sinyal işlemede çok kullanılır.

**Problem:** [1, 2, 3, 4] → [1, 3, 6, 10].

**Üç yaklaşım:**

```python
import itertools

# 1. itertools.accumulate — en hızlı (C implementasyonu)
def cumsum(arr):
    return list(itertools.accumulate(arr))

# 2. Manuel döngü
def cumsum(arr):
    result = []
    total = 0
    for x in arr:
        total += x
        result.append(total)
    return result

# 3. List comprehension (O(n²) — yavaş)
def cumsum(arr):
    return [sum(arr[:i+1]) for i in range(len(arr))]
```

**Neden itertools en hızlı?** C-level implementasyonu, Python interpreter overhead'i yok.

**Pandas ile:** `df['cumulative'] = df['value'].cumsum()`

**Gerçek dünya:** Kümülatif satış, portföy değeri, eğri altı alan (AUC).""",
        "complexity": "O(n) tüm yaklaşımlar için",
        "related_concepts": ["itertools.accumulate", "kümülatif toplam", "running sum"],
        "related_question_ids": [4, 13, 102],
        "tutorial_slug": None,
    },
    11: {
        "explanation": """OBEB (EBOB/GCD), Öklid algoritmasının klasik uygulamasıdır.

**Öklid teoremi:** gcd(a, b) = gcd(b, a mod b). Base case: gcd(a, 0) = a.

**Özyinelemeli:**

```python
def gcd(a, b):
    return a if b == 0 else gcd(b, a % b)
```

**Iteratif:**

```python
def gcd(a, b):
    while b:
        a, b = b, a % b
    return a
```

**Python builtin:** `math.gcd(a, b)` — C implementasyonu, daha hızlı.

**OKEK (LCM) hesabı:** `lcm(a, b) = a * b / gcd(a, b)`. Python 3.9+: `math.lcm(a, b)`.

**Kullanım:** Kesir sadeleştirme, RSA kriptografi, periyodik olaylar (müzik teorisi, saat hesabı).""",
        "complexity": "O(log(min(a, b))) — Öklid'in garanti alt sınırı",
        "related_concepts": ["Öklid algoritması", "özyineleme", "modulo", "matematik"],
        "related_question_ids": [8, 9, 16],
        "tutorial_slug": "python-obeb-oklid",
    },
    12: {
        "explanation": """Üçgen tipi kontrolü, **üçgen eşitsizliği** kuralının uygulamasıdır.

**Üçgen eşitsizliği:** Her kenar, diğer iki kenarın toplamından küçük olmalı. a + b > c ∧ a + c > b ∧ b + c > a.

**Çözüm:**

```python
def triangle_type(a, b, c):
    if not (a + b > c and a + c > b and b + c > a):
        return "Geçersiz"
    if a == b == c:
        return "Eşkenar"
    elif a == b or a == c or b == c:
        return "İkizkenar"
    else:
        return "Çeşitkenar"
```

**Edge case'ler:**
- Negatif kenarlar → geçersiz
- Sıfır kenar → geçersiz (üçgen oluşmaz)
- Float precision: 0.1 + 0.2 != 0.3 sorunu için `math.isclose()`

**Genişletme:** Alan hesabı (Heron formülü), dik üçgen kontrolü (Pisagor).""",
        "complexity": "O(1)",
        "related_concepts": ["üçgen eşitsizliği", "koşullu ifadeler", "Pisagor"],
        "related_question_ids": [4, 13, 15],
        "tutorial_slug": None,
    },
    13: {
        "explanation": """String/liste ters çevirme, **en temel** algoritma sorularındandır.

**Problem:** "hello" → "olleh".

**Yaklaşımlar:**

```python
# 1. Slicing — en kısa
reversed_str = s[::-1]

# 2. reversed() + join
reversed_str = ''.join(reversed(s))

# 3. Manuel (in-place, O(1) bellek)
def reverse_string(s):
    s = list(s)  # string immutable
    l, r = 0, len(s) - 1
    while l < r:
        s[l], s[r] = s[r], s[l]
        l += 1
        r -= 1
    return ''.join(s)
```

**Liste için:** `lst.reverse()` (in-place) veya `lst[::-1]` (yeni liste).

**Bellek:** Slicing O(n) yeni nesne oluşturur. In-place swap O(1).""",
        "complexity": "O(n) zaman, O(1) veya O(n) bellek",
        "related_concepts": ["slicing", "in-place swap", "reversed", "two pointers"],
        "related_question_ids": [1, 3, 14],
        "tutorial_slug": None,
    },
    14: {
        "explanation": """İkili arama (binary search), **sıralı** dizide hedef bulmanın en hızlı yoludur.

**Problem:** Sıralı [2, 5, 8, 12, 16, 23, 38, 56, 72, 91]'da 23'ü bul.

**Algoritma:**

```python
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
```

**Dikkat:** `(left + right) // 2` overflow riski (C/C++). Python'da sorun yok ama genel kültür: `left + (right - left) // 2`.

**Neden log n?** Her adımda arama alanı yarıya iner. 1 milyar eleman için max 30 karşılaştırma.

**Recursion limiti:** Python'da 1000. Çok derin arama için iterative tercih edilir.""",
        "complexity": "O(log n) zaman, O(1) bellek",
        "related_concepts": ["binary search", "sıralı dizi", "divide and conquer"],
        "related_question_ids": [5, 23, 302],
        "tutorial_slug": "python-binary-search",
    },
    15: {
        "explanation": """Matris çarpımı, **lineer cebirin** temelidir ve makine öğrenmesinin kalbidir.

**Problem:** (2,3) × (3,2) matrislerin çarpımı (2,2) sonuç verir.

**Naive — O(n³):**

```python
def matmul(A, B):
    n = len(A)
    result = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            for k in range(n):
                result[i][j] += A[i][k] * B[k][j]
    return result
```

**NumPy ile — O(n^2.81) veya BLAS optimize:**

```python
import numpy as np
result = A @ B  # veya np.dot(A, B)
```

**Neden NumPy 100x hızlı?** C/Fortran implementasyonu, SIMD vektörizasyonu, multi-threading.

**İleri:** Strassen algoritması (O(n^2.807)) teoride hızlı ama pratikte cache misses nedeniyle küçük matrislerde yavaş.""",
        "complexity": "O(n³) naive, O(n^2.807) Strassen, NumPy ile donanıma bağlı",
        "related_concepts": ["iç içe döngü", "NumPy", "BLAS", "lineer cebir"],
        "related_question_ids": [4, 10, 301],
        "tutorial_slug": None,
    },
    # ═══ STRINGS (24 soru) ═══
    51: {
        "explanation": """Türkçe metinlerde emoji/normal karakter duygu analizi, basit **NLP** sorusudur.

**Problem:** "Ürün harika 😍 ama kargo yavaş 🐌" → pozitif ağırlıklı.

**Çözüm:**

```python
import re

POSITIVE = {"harika": 1, "mükemmel": 1, "süper": 1, "beğendim": 1, "😍": 2, "❤️": 2, "🔥": 1}
NEGATIVE = {"kötü": -1, "berbat": -2, "yavaş": -1, "🐌": -2, "😡": -2, "👎": -1}

def analyze(text):
    words = re.findall(r'\\w+|[\\U0001F600-\\U0001F64F]', text, re.UNICODE)
    score = sum(POSITIVE.get(w, 0) + NEGATIVE.get(w, 0) for w in words)
    return "pozitif" if score > 0 else "negatif" if score < 0 else "nötr"
```

**Gerçek dünya:** Sosyal medya monitoring, müşteri geri bildirim analizi, marka algısı.""",
        "complexity": "O(n) metin uzunluğu, O(1) lookup",
        "related_concepts": ["regex", "Unicode", "sözlük lookup", "NLP"],
        "related_question_ids": [52, 53, 54],
        "tutorial_slug": None,
    },
    52: {
        "explanation": """**Steganografi** — veriyi görünmez karakterlere gizleme sanatı.

**Yaklaşım: zero-width characters:**

```python
ZWC = {'00': '\\u200b', '01': '\\u200c', '10': '\\u200d', '11': '\\ufeff'}

def hide(secret, cover):
    bits = ''.join(format(ord(c), '08b') for c in secret)
    zwc_map = {bits[i:i+2]: ZWC[bits[i:i+2]] for i in range(0, len(bits), 2)}
    return ''.join(zwc_map[bits[i:i+2]] if bits[i:i+2] in zwc_map else bits[i] for i in range(0, len(bits), 2))
```

**Neden çalışır:** U+200B, U+200C, U+200D gibi karakterler görünmez ama render edilebilir metin olarak sayılır.

**Kullanım:** Watermarking, güvenli mesajlaşma, dijital imza.""",
        "complexity": "O(n) encode/decode",
        "related_concepts": ["steganografi", "Unicode", "binary encoding", "güvenlik"],
        "related_question_ids": [51, 53],
        "tutorial_slug": None,
    },
    53: {
        "explanation": """FizzBuzz'ın emoji versiyonu, **junior mülakatların klasik sorusu**. Sıra önemli (15 için FizzBuzz önce kontrol edilmeli).""",
        "complexity": "O(n)",
        "related_concepts": ["modulo", "kontrol yapıları", "emoji string"],
        "related_question_ids": [2, 51],
        "tutorial_slug": "python-fizzbuzz-algoritma",
    },
    54: {
        "explanation": """Türkçe karakter normalizasyonu kritik çünkü `lower()` Türkçe "İ" için yanlış sonuç verir ("İ" → "i̇" noktalı, "I" → "ı" noktasız).

**Doğru yöntem — `casefold()`:**

```python
"ISTANBUL".casefold()  # "istanbul" (doğru)
"İSTANBUL".casefold()  # "istanbul" (doğru)

# lower() ile karşılaştır
"ISTANBUL".lower()  # "istanbul"
"İSTANBUL".lower()  # "i̇stanbul" (noktalı i — yanlış)
```

**Veri temizleme fonksiyonu:**

```python
def normalize_turkish(text):
    return text.casefold().replace('i̇', 'i')
```

**Kullanım:** Arama motoru, kullanıcı kayıt, ETL süreçleri.""",
        "complexity": "O(n) string uzunluğu",
        "related_concepts": ["casefold", "Unicode normalization", "Türkçe locale"],
        "related_question_ids": [1, 51, 56],
        "tutorial_slug": None,
    },
    55: {
        "explanation": """String şifreleme temel güvenlik sorusudur.

**Caesar cipher (ROT-N):**

```python
def caesar(text, shift):
    result = []
    for c in text:
        if c.isalpha():
            base = ord('A') if c.isupper() else ord('a')
            result.append(chr((ord(c) - base + shift) % 26 + base))
        else:
            result.append(c)
    return ''.join(result)

def decrypt(cipher, shift):
    return caesar(cipher, -shift)
```

**Modern:** AES (cryptography kütüphanesi). Mülakatlarda asla Caesar kullanmayın (kırılması 26 deneme).

**Kullanım:** Klasik kriptografi eğitimi, CTF yarışmaları.""",
        "complexity": "O(n)",
        "related_concepts": ["Caesar cipher", "modulo", "karakter encoding", "kriptografi"],
        "related_question_ids": [52, 56],
        "tutorial_slug": None,
    },
    56: {
        "explanation": """URL slug üretimi, SEO için kritik. "Python Mülakat Hazırlığı" → "python-mulakat-hazirligi".

**ASCII-only versiyon:**

```python
import re

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\\s-]', '', text)
    text = re.sub(r'[\\s-]+', '-', text).strip('-')
    return text
```

**Unicode desteği için:** `python-slugify` veya `django.utils.text.slugify` kütüphanesi.

**İpuçları:** Maksimum uzunluk koy (50 char), trailing dash temizle, stopwords kaldır.""",
        "complexity": "O(n)",
        "related_concepts": ["regex", "URL encoding", "SEO", "string normalization"],
        "related_question_ids": [1, 54, 51],
        "tutorial_slug": None,
    },
    # ═══ LIST-DICT (13 soru) ═══
    101: {
        "explanation": """Liste döndürme, en temel veri yapısı sorularındandır.

**Yaklaşımlar:**

```python
# 1. Slicing — yeni liste döner
lst[::-1]

# 2. reversed() — iterator döner
list(reversed(lst))

# 3. in-place — orijinali değiştirir
lst.reverse()
```

**Fark:** Slicing ve reversed() yeni liste oluşturur (orijinal korunur). `.reverse()` orijinali değiştirir.

**Performans:** Tüm yaklaşımlar O(n). Slicing en hızlı çünkü C-level implementasyon.""",
        "complexity": "O(n)",
        "related_concepts": ["slicing", "reversed", "in-place", "immutable vs mutable"],
        "related_question_ids": [13, 102, 105],
        "tutorial_slug": None,
    },
    102: {
        "explanation": """Sözlük birleştirme (merge), veri işlemede sık yapılan işlem.

**Yaklaşımlar:**

```python
d1 = {'a': 1, 'b': 2}
d2 = {'b': 3, 'c': 4}

# 1. Dict unpacking (Python 3.5+)
merged = {**d1, **d2}  # {'a': 1, 'b': 3, 'c': 4}

# 2. Union operatörü (Python 3.9+)
merged = d1 | d2  # {'a': 1, 'b': 3, 'c': 4}

# 3. update() — in-place
d1.update(d2)  # d1 değişir
```

**Çakışma:** Aynı key'de **sağdaki** kazanır (d2 değeri kullanılır).

**Çakışma kontrolü:**

```python
def merge_conflict(d1, d2):
    conflicts = {k for k in d1 if k in d2 and d1[k] != d2[k]}
    return conflicts
```""",
        "complexity": "O(n + m)",
        "related_concepts": ["dict unpacking", "union operatörü", "merge", "key collision"],
        "related_question_ids": [103, 110, 113],
        "tutorial_slug": None,
    },
    103: {
        "explanation": """Sözlük erişim güvenliği, Python'da **en sık yapılan hatanın** (KeyError) çözümüdür.

**Yaklaşımlar:**

```python
d = {'a': 1, 'b': 2}

# 1. get() — default değer döner
d.get('c', 0)  # 0

# 2. setdefault() — yoksa ekler
d.setdefault('c', 0)  # d artık {'a': 1, 'b': 2, 'c': 0}

# 3. defaultdict — otomatik default
from collections import defaultdict
dd = defaultdict(int)
dd['x'] += 1  # KeyError yok, otomatik 0

# 4. try/except — açık hata yönetimi
try:
    val = d['c']
except KeyError:
    val = 0
```

**Performans:** `get()` en hızlı tek seferlik erişim için. defaultdict constructor overhead'i var ama toplu işlemlerde (Counter, groupby) hızlı.""",
        "complexity": "O(1) ortalama",
        "related_concepts": ["dict.get", "defaultdict", "KeyError", "try/except"],
        "related_question_ids": [102, 104, 111],
        "tutorial_slug": None,
    },
    104: {
        "explanation": """Sözlük sıralama, veri sunumu için önemli.

**Anahtara göre:**

```python
sorted(d.items())  # [(key1, val1), (key2, val2), ...]
```

**Değere göre:**

```python
sorted(d.items(), key=lambda x: x[1], reverse=True)
```

**Çoklu anahtar** (önce değer, sonra anahtar):

```python
sorted(d.items(), key=lambda x: (x[1], x[0]))
```

**Sıralı sözlük:** Python 3.7+ normal dict ekleme sırasını korur. Strict ordering için `collections.OrderedDict` (artık gereksiz).""",
        "complexity": "O(n log n)",
        "related_concepts": ["sorted", "lambda", "tuple sorting", "OrderedDict"],
        "related_question_ids": [102, 103, 110],
        "tutorial_slug": None,
    },
    105: {
        "explanation": """Sıralı iki listeyi birleştirme, klasik **iki pointer** algoritmasıdır.

**Algoritma:**

```python
def merge_sorted(l1, l2):
    result = []
    i = j = 0
    while i < len(l1) and j < len(l2):
        if l1[i] <= l2[j]:
            result.append(l1[i]); i += 1
        else:
            result.append(l2[j]); j += 1
    result.extend(l1[i:])
    result.extend(l2[j:])
    return result
```

**heapq.merge:**

```python
import heapq
list(heapq.merge([1, 3, 5], [2, 4, 6]))  # [1, 2, 3, 4, 5, 6]
```

**Karmaşıklık:** O(n + m). heapq C-level implementasyonu, lazy evaluation (iterator).""",
        "complexity": "O(n + m)",
        "related_concepts": ["two pointers", "heapq.merge", "merge sort alt adımı"],
        "related_question_ids": [106, 107, 112],
        "tutorial_slug": None,
    },
    106: {
        "explanation": """İç içe listeyi düzleştirme (flatten).

**Yaklaşımlar:**

```python
# 1. Tek seviye — chain
import itertools
list(itertools.chain.from_iterable([[1, 2], [3, 4]]))  # [1, 2, 3, 4]

# 2. Özyinelemeli — derin flatten
def flatten(lst):
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result

# 3. Generator (lazy, memory-efficient)
def flatten_gen(lst):
    for item in lst:
        if isinstance(item, list):
            yield from flatten_gen(item)
        else:
            yield item
```

**Neden `sum(lst, [])` kullanma?** O(n²) — Python liste concat'i yeni liste oluşturur.""",
        "complexity": "O(n) toplam eleman",
        "related_concepts": ["özyineleme", "itertools.chain", "isinstance", "generator"],
        "related_question_ids": [105, 107, 110],
        "tutorial_slug": None,
    },
    107: {
        "explanation": """Liste parçalama (chunking), büyük veriyi batch'lere bölmek için kullanılır.

**Yaklaşımlar:**

```python
# 1. List comprehension
def chunk(lst, n):
    return [lst[i:i+n] for i in range(0, len(lst), n)]

# 2. itertools.batched (Python 3.12+)
import itertools
list(itertools.batched([1, 2, 3, 4, 5], 2))  # [(1, 2), (3, 4), (5,)]

# 3. Generator — lazy, büyük veri için
def chunk_gen(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]
```

**Kullanım:** API pagination, batch processing, CSV chunked okuma.""",
        "complexity": "O(n)",
        "related_concepts": ["list slicing", "itertools.batched", "generator", "batch"],
        "related_question_ids": [105, 106, 108],
        "tutorial_slug": None,
    },
    108: {
        "explanation": """Liste tekilleştirme (unique), koruma sırasıyla veya sırasız yapılabilir.

**Yaklaşımlar:**

```python
# 1. dict.fromkeys — sırayı korur (Python 3.7+)
list(dict.fromkeys([3, 1, 2, 1, 3]))  # [3, 1, 2]

# 2. set — sıra garantisi yok, en hızlı
list(set([3, 1, 2, 1, 3]))  # sıra farklı olabilir

# 3. Manuel — sırayı korur, anlaşılır
seen = set()
result = []
for x in lst:
    if x not in seen:
        seen.add(x)
        result.append(x)
```

**Ne zaman?** Sıra önemliyse dict.fromkeys, hız önemliyse set.""",
        "complexity": "O(n) ortalama",
        "related_concepts": ["set", "dict.fromkeys", "unique", "veri temizleme"],
        "related_question_ids": [102, 109, 111],
        "tutorial_slug": None,
    },
    109: {
        "explanation": """Liste karşılaştırma (kesişim, fark, simetrik fark).

**Set operasyonları:**

```python
a = {1, 2, 3, 4}
b = {3, 4, 5, 6}

a & b   # {3, 4}     — kesişim
a - b   # {1, 2}     — fark (a'da olup b'de olmayan)
a ^ b   # {1, 2, 5, 6} — simetrik fark (ikisinde de olmayanlar)
a | b   # {1, 2, 3, 4, 5, 6} — birleşim
```

**Sıra korumak için** (list comprehension):

```python
[x for x in lst1 if x in set(lst2)]  # kesişim, lst1 sırası
```

**Performans:** Set operasyonları O(n+m), sıra koruyan O(n*m).""",
        "complexity": "O(n + m) set, O(n*m) list",
        "related_concepts": ["set operations", "kesişim", "fark", "birleşim"],
        "related_question_ids": [102, 108, 111],
        "tutorial_slug": None,
    },
    110: {
        "explanation": """Sözlük gruplama, bir listeyi key'e göre gruplara ayırır.

**Çözümler:**

```python
from collections import defaultdict

# defaultdict ile
def group_by(items, key_fn):
    groups = defaultdict(list)
    for item in items:
        groups[key_fn(item)].append(item)
    return dict(groups)

# itertools.groupby (sıralı veri için)
from itertools import groupby
sorted_items = sorted(items, key=key_fn)
groups = {k: list(g) for k, g in groupby(sorted_items, key=key_fn)}
```

**Fark:** defaultdict tüm veri ile çalışır (sırasız). groupby sadece ardışık aynı key'leri gruplar — **önce sort gerekli**.""",
        "complexity": "O(n) defaultdict, O(n log n) groupby",
        "related_concepts": ["defaultdict", "itertools.groupby", "groupby aggregation"],
        "related_question_ids": [102, 111, 113],
        "tutorial_slug": None,
    },
    111: {
        "explanation": """Liste frekans sayımı, en sık kullanılan veri analizi işlemi.

**Counter ile:**

```python
from collections import Counter

# En sık 3 eleman
Counter(['a', 'b', 'a', 'c', 'a', 'b']).most_common(3)  # [('a', 3), ('b', 2), ('c', 1)]

# Çoklu liste frekansı
Counter(a=4, b=2) + Counter(a=1, b=3)  # Counter({'a': 5, 'b': 5})
```

**Pandas:** `df['column'].value_counts()` — Series olarak döner.""",
        "complexity": "O(n)",
        "related_concepts": ["collections.Counter", "most_common", "value_counts"],
        "related_question_ids": [6, 110, 207],
        "tutorial_slug": None,
    },
    112: {
        "explanation": """Liste sıralama, custom key ile ileri seviye konu.

**Yaklaşımlar:**

```python
# sorted — yeni liste döner
sorted(lst, key=lambda x: x['age'], reverse=True)

# list.sort — in-place
lst.sort(key=lambda x: x['age'])

# Çoklu key
sorted(students, key=lambda s: (-s['gpa'], s['name']))
```

**TimSort:** Python'un sort algoritması C implementasyonu, stabil (eşit elemanların sırası korunur), pratikte O(n) — neredeyse sıralı diziler için.""",
        "complexity": "O(n log n) ortalama, O(n) en iyi (sıralı)",
        "related_concepts": ["sorted", "list.sort", "TimSort", "stable sort"],
        "related_question_ids": [104, 105, 110],
        "tutorial_slug": None,
    },
    113: {
        "explanation": """Sözlüğü ters çevirme (key-value yer değiştirme). Aynı value'da birden fazla key varsa value liste olur.

**Çözümler:**

```python
# Basit — unique value varsa
inv = {v: k for k, v in d.items()}

# Çakışma varsa
inv = {}
for k, v in d.items():
    inv.setdefault(v, []).append(k)

# defaultdict
from collections import defaultdict
inv = defaultdict(list)
for k, v in d.items():
    inv[v].append(k)
```

**Kullanım:** Lookup index tersine çevirme, inverted search.""",
        "complexity": "O(n)",
        "related_concepts": ["dict comprehension", "setdefault", "inversion"],
        "related_question_ids": [102, 110],
        "tutorial_slug": None,
    },
    # ═══ PANDAS (10 soru) ═══
    201: {
        "explanation": """Pandas filtreleme, veri analizinin temelidir.

**Yaklaşımlar:**

```python
# Boolean indexing — en yaygın
df[df['age'] > 25]
df[df['name'].str.startswith('A')]

# Çoklu koşul (parantez ŞART)
df[(df['age'] > 25) & (df['city'] == 'İstanbul')]

# query — SQL benzeri
df.query('age > 25 and city == "İstanbul"')

# loc/iloc — label/position
df.loc[df['age'] > 25, ['name', 'age']]
```

**Performans:** Çok büyük DataFrame'lerde (10M+ satır) `query()` veya numpy backend'li pandas.""",
        "complexity": "O(n)",
        "related_concepts": ["boolean indexing", "query", "loc/iloc", "mask"],
        "related_question_ids": [202, 206, 207],
        "tutorial_slug": None,
    },
    202: {
        "explanation": """Pandas groupby, SQL'deki GROUP BY'a eşdeğer.

**Split-Apply-Combine:**

```python
# Basit
df.groupby('category')['value'].mean()

# Çoklu aggregation
df.groupby('category').agg({'price': 'mean', 'quantity': 'sum', 'id': 'count'})

# Named aggregation (Pandas 0.25+)
df.groupby('category').agg(
    avg_price=('price', 'mean'),
    total_qty=('quantity', 'sum')
)
```

**Çoklu key:** `df.groupby(['cat1', 'cat2']).sum()` — MultiIndex sonuç.

**Transform vs aggregate:** Transform orijinal shape'i korur (her satıra group değeri yazılır).""",
        "complexity": "O(n)",
        "related_concepts": ["groupby", "agg", "transform", "split-apply-combine"],
        "related_question_ids": [201, 203, 205],
        "tutorial_slug": "pandas-groupby-rehberi",
    },
    203: {
        "explanation": """Pandas merge/join, iki DataFrame'i key üzerinden birleştirir.

**Yaklaşımlar:**

```python
# merge — SQL benzeri
pd.merge(df1, df2, on='user_id')

# Farklı key isimleri
pd.merge(df1, df2, left_on='id', right_on='user_id')

# Suffix (çakışan kolon adları için)
pd.merge(df1, df2, on='id', suffixes=('_left', '_right'))

# how: 'inner' (default), 'left', 'right', 'outer'
pd.merge(df1, df2, on='id', how='left')
```

**Performans:** `key`i sırala, `sort=False` (merge sort yapmasın), 100M+ satır için Dask veya Polars.""",
        "complexity": "O(n + m) hash join",
        "related_concepts": ["merge", "join", "SQL JOIN", "suffixes"],
        "related_question_ids": [201, 202, 204],
        "tutorial_slug": None,
    },
    204: {
        "explanation": """Pandas apply, satır/sütun bazlı özel fonksiyon uygular. **Esnek ama yavaş**.

**Yaklaşımlar:**

```python
# Satır bazlı
df.apply(lambda row: row['price'] * row['qty'], axis=1)

# Sütun bazlı (varsayılan)
df.apply(lambda col: col.max() - col.min())

# map — Series, daha hızlı
df['category'].map({'A': 'Alpha', 'B': 'Beta'})

# applymap — tüm hücrelere (deprecated, use .map)
```

**Vectorized alternatifler** (50-100x hızlı):

```python
# ❌ Yavaş
df['total'] = df.apply(lambda r: r['p'] * r['q'], axis=1)

# ✅ Hızlı
df['total'] = df['p'] * df['q']
```

**Kural:** Önce vectorized dene, yoksa apply, en son map.""",
        "complexity": "O(n) Python overhead ile",
        "related_concepts": ["apply", "map", "vectorization", "lambda"],
        "related_question_ids": [201, 205, 207],
        "tutorial_slug": None,
    },
    205: {
        "explanation": """Pivot table, long → wide format dönüşümüdür. Excel'deki pivot tabloya eşdeğer.

**Çözüm:**

```python
# Basit
df.pivot_table(values='sales', index='region', columns='product', aggfunc='sum')

# Çoklu aggregation
df.pivot_table(
    values='sales',
    index='region',
    columns='product',
    aggfunc={'sales': ['sum', 'mean'], 'quantity': 'count'}
)

# margins=True — toplam satırı/sütunu ekler
df.pivot_table(values='sales', index='region', columns='product', aggfunc='sum', margins=True)
```

**fill_value:** NaN yerine değer koy (`fill_value=0`).""",
        "complexity": "O(n)",
        "related_concepts": ["pivot_table", "melt", "wide/long format", "margins"],
        "related_question_ids": [202, 203, 206],
        "tutorial_slug": None,
    },
    206: {
        "explanation": """Missing data (NaN) yönetimi, gerçek dünya veri temizleme için **zorunlu**.

**Tespit:**

```python
df.isnull()           # DataFrame (True/False)
df.isnull().sum()     # kolon bazlı NaN sayısı
df.isnull().any()     # herhangi bir NaN var mı
```

**Doldurma:**

```python
df.fillna(0)                    # sabit değer
df.fillna(df.mean())            # kolon ortalaması
df.fillna(method='ffill')       # önceki değer (forward fill)
df.fillna(method='bfill')       # sonraki değer (backward fill)
```

**Silme:**

```python
df.dropna()                     # herhangi bir NaN varsa satırı sil
df.dropna(subset=['col1'])      # sadece col1 NaN ise sil
df.dropna(thresh=3)             # en az 3 non-NaN değer olan satırları tut
```

**Strateji:** %5'ten az missing → dropna, %5-30 → fillna, %30+ → kolonu çıkar veya ML imputation.""",
        "complexity": "O(n)",
        "related_concepts": ["isnull", "fillna", "dropna", "missing data imputation"],
        "related_question_ids": [201, 207, 209],
        "tutorial_slug": None,
    },
    207: {
        "explanation": """Pandas string metotları, `.str` accessor ile vectorized string işlemleri yapar. **apply()'den 50-100x hızlı**.

**Yaygın operasyonlar:**

```python
df['name'].str.lower()                    # küçük harf
df['email'].str.contains('@gmail.com')   # regex eşleşme
df['text'].str.replace('\\d+', '')        # değiştirme
df['text'].str.extract('(\\d+)')          # grup yakalama
df['name'].str[:3]                        # ilk 3 karakter
df['tags'].str.split(',')                 # virgülle ayır
```

**Performans:** 1M satır için `.str.contains()` ~50ms, `apply(lambda x: '@' in x)` ~3000ms.

**Erişim:** `.str` accessor sadece string kolonlarda çalışır. Diğer tipler için `.astype(str)` önce.""",
        "complexity": "O(n)",
        "related_concepts": ["str accessor", "regex", "vectorization"],
        "related_question_ids": [201, 204, 208],
        "tutorial_slug": None,
    },
    208: {
        "explanation": """Pandas datetime işlemleri, zaman serisi analizinin temelidir.

**Parse:**

```python
df['date'] = pd.to_datetime(df['date_str'], format='%Y-%m-%d')
df['date'] = pd.to_datetime(df['date_str'], infer_datetime_format=True)  # otomatik algılama
```

**Extract:**

```python
df['date'].dt.year
df['date'].dt.month
df['date'].dt.day_name()  # 'Monday', 'Tuesday'...
df['date'].dt.quarter
```

**Filter:**

```python
df[df['date'] > '2024-01-01']
df[df['date'].dt.month == 12]  # Aralık ayları
```

**Resample:**

```python
df.set_index('date').resample('M').sum()  # aylık toplam
df.resample('W', on='date').mean()        # haftalık ortalama
```

**Timezone:** `df['date'].dt.tz_localize('UTC').dt.tz_convert('Europe/Istanbul')`.""",
        "complexity": "O(n)",
        "related_concepts": ["to_datetime", "dt accessor", "resample", "time series"],
        "related_question_ids": [201, 209, 210],
        "tutorial_slug": None,
    },
    209: {
        "explanation": """Pandas çıktı alma (export).

**Formatlar:**

```python
# CSV
df.to_csv('file.csv', index=False, encoding='utf-8')

# Excel — sheet desteği
df.to_excel('file.xlsx', sheet_name='Sheet1', index=False)

# JSON
df.to_json('file.json', orient='records', force_ascii=False)

# Parquet — sıkıştırılmış, hızlı (büyük veri için)
df.to_parquet('file.parquet', index=False)
```

**Performans karşılaştırması (100MB veri):**
- CSV: 100MB boyut, 5s yazma
- Parquet: 30MB boyut, 0.5s yazma (sütun bazlı sıkıştırma)

**Encoding:** Türkçe için `encoding='utf-8'` veya `utf-8-sig` (Excel uyumu).""",
        "complexity": "O(n)",
        "related_concepts": ["to_csv", "to_excel", "to_parquet", "encoding"],
        "related_question_ids": [201, 208, 210],
        "tutorial_slug": None,
    },
    210: {
        "explanation": """Pandas read_csv, veri yükleme fonksiyonu.

**Yaklaşımlar:**

```python
# Basit
df = pd.read_csv('file.csv')

# Büyük dosya — chunked okuma
chunks = pd.read_csv('big.csv', chunksize=10000)
for chunk in chunks:
    process(chunk)

# Bellek optimizasyonu
df = pd.read_csv('file.csv', dtype={'id': 'int32', 'price': 'float32'})

# Sadece belirli kolonlar
df = pd.read_csv('file.csv', usecols=['id', 'name', 'price'])

# Tarih kolonları
df = pd.read_csv('file.csv', parse_dates=['created_at'])
```

**Alternatifler (büyük veri):** `pyarrow` engine (read_csv'te), `read_parquet` (10x hızlı).""",
        "complexity": "O(n)",
        "related_concepts": ["read_csv", "chunksize", "dtype", "parse_dates"],
        "related_question_ids": [201, 208, 209],
        "tutorial_slug": None,
    },
    # ═══ ALGORITHMS (5 soru) ═══
    301: {
        "explanation": """**Two Sum** — en klasik mülakat sorusu.

**Problem:** [2, 7, 11, 15], target=9 → [0, 1] (2+7).

**Çözümler:**

```python
# Brute force — O(n²)
def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]

# Hash map — O(n)
def two_sum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        complement = target - n
        if complement in seen:
            return [seen[complement], i]
        seen[n] = i
```

**Neden hash map O(n)?** Her eleman için bir kere lookup, ortalama O(1).

**Varyant:** Three Sum, Four Sum — hash map yerine two pointers tercih edilir (sıralı dizi için).""",
        "complexity": "O(n) hash, O(n²) brute",
        "related_concepts": ["hash map", "enumerate", "two pointers", "complement"],
        "related_question_ids": [302, 303, 305],
        "tutorial_slug": "python-two-sum",
    },
    302: {
        "explanation": """Sıralı dizide hedef arama (binary search). O(log n) garantili performans.

Bkz. Soru #14 (Binary Search) detaylı açıklama için.""",
        "complexity": "O(log n)",
        "related_concepts": ["binary search", "sıralı dizi", "divide and conquer"],
        "related_question_ids": [14, 301, 303],
        "tutorial_slug": "python-binary-search",
    },
    303: {
        "explanation": """Dizi döndürme (array rotation). In-place, O(1) bellek.

**Problem:** [1,2,3,4,5,6,7], k=3 → [5,6,7,1,2,3,4].

**Üç ters çevirme algoritması:**

```python
def rotate(nums, k):
    n = len(nums)
    k %= n  # k > n için
    nums[:] = nums[::-1]          # [7,6,5,4,3,2,1]
    nums[:k] = nums[:k][::-1]     # [5,6,7,4,3,2,1]
    nums[k:] = nums[k:][::-1]     # [5,6,7,1,2,3,4]
```

**Alternatif:** `collections.deque.rotate(k)` — O(k).""",
        "complexity": "O(n) zaman, O(1) bellek",
        "related_concepts": ["in-place reversal", "array rotation", "three reversals"],
        "related_question_ids": [13, 301, 304],
        "tutorial_slug": None,
    },
    304: {
        "explanation": """Linked List reverse, klasik pointer manipülasyonu sorusudur.

**Çözüm:**

```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def reverse(head):
    prev, curr = None, head
    while curr:
        nxt = curr.next
        curr.next = prev
        prev = curr
        curr = nxt
    return prev
```

**Üç pointer:** prev (önceki düğüm), curr (şu anki), nxt (sonraki — curr.next kaybolmasın diye sakla).

**Karmaşıklık:** O(n) zaman, O(1) bellek.

**Kullanım:** OS kernel (process list), tarayıcı history, undo/redo.""",
        "complexity": "O(n) zaman, O(1) bellek",
        "related_concepts": ["linked list", "pointer manipulation", "in-place"],
        "related_question_ids": [303, 305, 306],
        "tutorial_slug": None,
    },
    305: {
        "explanation": """Stack (LIFO) veri yapısı, **DFS, parantez eşleştirme, expression evaluation** için temel.

**Python'da stack:**

```python
# list (append/pop) — en yaygın
stack = []
stack.append(1)   # push
top = stack.pop()  # pop

# collections.deque — O(1) guaranteed
from collections import deque
stack = deque()
stack.append(1)
top = stack.pop()
```

**List vs deque:** `list.pop()` amortized O(1) ama bazen O(n) (reallocation). deque garantili O(1).

**Kullanım:** Fonksiyon çağrı yığını, parantez eşleştirme, syntax parser, undo/redo, DFS.""",
        "complexity": "O(1) amortized",
        "related_concepts": ["stack", "deque", "LIFO", "DFS"],
        "related_question_ids": [304, 306, 301],
        "tutorial_slug": None,
    },
}


def apply_seo_content():
    """Tüm sorulara SEO içeriklerini uygula."""
    applied = 0
    for q in QUESTIONS:
        seo = SEO_DATA.get(q.id)
        if seo:
            q.explanation = seo.get("explanation", "")
            q.complexity = seo.get("complexity", "O(n)")
            q.related_concepts = seo.get("related_concepts", [])
            q.related_question_ids = seo.get("related_question_ids", [])
            q.tutorial_slug = seo.get("tutorial_slug")
            applied += 1

    # Default değer ata (eksik sorular için)
    for q in QUESTIONS:
        if not q.explanation:
            q.explanation = f"{q.title} sorusu, {q.category} kategorisinde Python mülakat pratiği içindir."
        if not q.complexity:
            q.complexity = "O(n)"
        if not q.related_concepts:
            q.related_concepts = [q.category]
        if not q.related_question_ids:
            same_cat = [o.id for o in QUESTIONS if o.category == q.category and o.id != q.id][:3]
            q.related_question_ids = same_cat

    print(f"[OK] SEO content uygulandi: {applied}/{len(QUESTIONS)} soruya detayli icerik")
    return applied


if __name__ == "__main__":
    apply_seo_content()
    for q in QUESTIONS[:2]:
        print(f"\n#{q.id} {q.title}")
        print(f"  complexity: {q.complexity}")
        print(f"  related_concepts: {q.related_concepts}")
        print(f"  tutorial_slug: {q.tutorial_slug}")
        print(f"  explanation (ilk 80): {q.explanation[:80]}...")