"""Tutorials endpoint — uzun form rehber yazıları.

DB-first, fallback Python dict.
"""

import logging
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from supabase_client import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/tutorials", tags=["tutorials-v2"])


class TutorialOut(BaseModel):
    id: int
    slug: str
    title: str
    description: str
    content_md: str
    category: Optional[str] = None
    difficulty: Optional[str] = None
    reading_time_minutes: int = 10
    related_question_ids: List[int] = []
    faq: List[Dict[str, str]] = []
    cover_image: Optional[str] = None
    view_count: int = 0
    published_at: str
    updated_at: str


# ═══════════════════════════════════════════════════════════
# FALLBACK: Hard-coded tutorials (DB'den çekilemezse)
# Bu fallback'ler SEO_CONTENT.py'deki tutorial_slug'ları destekler
# ═══════════════════════════════════════════════════════════

FALLBACK_TUTORIALS: Dict[str, Dict[str, Any]] = {
    "python-palindrome-cozum": {
        "id": 1,
        "slug": "python-palindrome-cozum",
        "title": "Python'da Palindrome Kontrolü — 3 Farklı Yaklaşım",
        "description": "String slicing, iki pointer ve regex yaklaşımlarıyla palindrome kontrolü. Python mülakatlarının en sık sorulan sorusudur.",
        "category": "python-basics",
        "difficulty": "beginner",
        "reading_time_minutes": 8,
        "related_question_ids": [1, 3, 51],
        "content_md": """# Python'da Palindrome Kontrolü

Palindrome, tersten okunduğunda aynı olan kelime/cümledir. "radar", "level" veya "A man a plan a canal Panama" gibi.

## Problem Tanımı

Bir string'in palindrome olup olmadığını kontrol et. Büyük/küçük harf, boşluk ve noktalama fark etmemeli.

## Yaklaşım 1: String Slicing

En kısa ve en Pythonic yol.

```python
import re

def is_palindrome(text):
    cleaned = re.sub(r'[^a-z0-9]', '', text.lower())
    return cleaned == cleaned[::-1]
```

**Avantajlar:**
- Tek satır çözüm
- Okunabilir
- Performanslı

**Dezavantaj:** O(n) ek bellek (yeni string oluşturur)

## Yaklaşım 2: İki Pointer

O(1) ek bellek ile çalışır.

```python
def is_palindrome(text):
    cleaned = re.sub(r'[^a-z0-9]', '', text.lower())
    left, right = 0, len(cleaned) - 1
    while left < right:
        if cleaned[left] != cleaned[right]:
            return False
        left += 1
        right -= 1
    return True
```

**Avantaj:** Bellek dostu, büyük string'lerde avantajlı.

## Yaklaşım 3: Recursive

Öğretici ama pratikte yavaş.

```python
def is_palindrome(s):
    if len(s) <= 1:
        return True
    if s[0] != s[-1]:
        return False
    return is_palindrome(s[1:-1])
```

## Edge Case'ler

- Boş string → True
- Tek karakter → True
- Karışık Unicode → `unicodedata.normalize` kullan

## Performans Karşılaştırması

| Yaklaşım | Zaman | Bellek |
|---------|-------|--------|
| Slicing | O(n) | O(n) |
| İki pointer | O(n) | O(1) |
| Recursive | O(n) | O(n) (stack) |

## Sonuç

Mülakatlarda **iki pointer yaklaşımını** gösterin — hem teknik hem bellek açısından en iyisi.
""",
        "faq": [
            {"question": "Türkçe karakterlerle palindrome nasıl kontrol edilir?", "answer": "Türkçe 'Ağaç' gibi kelimeler için unicodedata.normalize('NFKD', text) kullanın. ASCII-cleaning ile 'Ağaç' kaybolur."},
            {"question": "Hangi yaklaşım production'da tercih edilir?", "answer": "Büyük veri setleri için iki pointer (O(1) bellek). Küçük string'ler için slicing (daha okunabilir)."},
        ],
    },
    "python-fizzbuzz-algoritma": {
        "id": 2,
        "slug": "python-fizzbuzz-algoritma",
        "title": "FizzBuzz Algoritması — Python'da Junior Mülakat Sorusu",
        "description": "FizzBuzz, programlama dünyasının 'Hello World'üdür. Sıralama önemi, tek satır çözüm ve edge case'ler.",
        "category": "python-basics",
        "difficulty": "beginner",
        "reading_time_minutes": 6,
        "related_question_ids": [2, 53],
        "content_md": """# FizzBuzz Algoritması

1'den n'e kadar:
- 3'e bölünürse "Fizz"
- 5'e bölünürse "Buzz"
- İkisine de bölünürse "FizzBuzz"

## Temel Çözüm

```python
def fizzbuzz(n):
    for i in range(1, n + 1):
        if i % 15 == 0:
            print("FizzBuzz")
        elif i % 3 == 0:
            print("Fizz")
        elif i % 5 == 0:
            print("Buzz")
        else:
            print(i)
```

## Tek Satır Versiyon

```python
result = ["FizzBuzz" if i % 15 == 0 else "Fizz" if i % 3 == 0 else "Buzz" if i % 5 == 0 else i for i in range(1, n + 1)]
```

## Neden Sıra Önemli?

```python
# YANLIŞ
if i % 3 == 0: print("Fizz")
elif i % 5 == 0: print("Buzz")
elif i % 15 == 0: print("FizzBuzz")  # Hiç gelmez!

# DOĞRU
if i % 15 == 0: print("FizzBuzz")  # Önce en spesifik
elif i % 3 == 0: print("Fizz")
elif i % 5 == 0: print("Buzz")
```

## Genişletmeler

- FizzBuzzJazz (3, 5, 7 için)
- Gerçek hayatta: Worker scheduling, batch processing
""",
        "faq": [
            {"question": "Bu soru neden bu kadar popüler?", "answer": "Junior/staj pozisyonlarında adayın temel kontrol yapılarını anlayıp anlamadığını ölçer. Çözemeyen genelde diğer sorularda da zorlanır."},
        ],
    },
    "python-binary-search": {
        "id": 3,
        "slug": "python-binary-search",
        "title": "İkili Arama (Binary Search) — O(log n) Performans",
        "description": "Sıralı dizide hedef bulmanın en hızlı yolu. Algoritma mantığı, recursion vs iteration, gerçek dünya kullanımı.",
        "category": "algorithms",
        "difficulty": "intermediate",
        "reading_time_minutes": 10,
        "related_question_ids": [14, 302],
        "content_md": """# İkili Arama (Binary Search)

Sıralı dizide hedef bulmanın en hızlı yoludur: O(log n).

## Algoritma

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

## Neden O(log n)?

Her adımda arama alanı yarıya iner:
- 1 milyar eleman → max 30 karşılaştırma
- 1 trilyon → max 40 karşılaştırma

## Recursive Versiyon

```python
def binary_search_recursive(arr, target, left=0, right=None):
    if right is None:
        right = len(arr) - 1
    if left > right:
        return -1
    mid = (left + right) // 2
    if arr[mid] == target:
        return mid
    elif arr[mid] < target:
        return binary_search_recursive(arr, target, mid + 1, right)
    else:
        return binary_search_recursive(arr, target, left, mid - 1)
```

## Python'da Hazır: bisect

```python
import bisect
arr = [1, 3, 5, 7, 9]
idx = bisect.bisect_left(arr, 5)  # 2 (insert position)
```

## Gerçek Dünya Kullanımı

- Veritabanı indeksleri (B-tree)
- Sözlükler (aslen BST)
- Versiyon kontrol sistemleri (git bisect)
- Oyun motorları (state lookup)
""",
        "faq": [
            {"question": "Sıralı olmayan dizide binary search kullanılır mı?", "answer": "Hayır. Önce sıralama gerek (O(n log n)), sonra arama (O(log n)). Toplam O(n log n), brute force'tan yavaş."},
            {"question": "Floating point sayılarda çalışır mı?", "answer": "Evet, ama epsilon karşılaştırması gerekir: `abs(arr[mid] - target) < 1e-9`."},
        ],
    },
    "python-asal-sayi-algoritma": {
        "id": 4,
        "slug": "python-asal-sayi-algoritma",
        "title": "Asal Sayı Algoritmaları — Naive'den Eratosthenes'e",
        "description": "Asal sayı kontrolü, Eratosthenes eleği ve performans optimizasyonu. Kriptografi temeli.",
        "category": "algorithms",
        "difficulty": "intermediate",
        "reading_time_minutes": 12,
        "related_question_ids": [9, 11],
        "content_md": """# Asal Sayı Algoritmaları

## Naive: O(√n)

```python
def is_prime(n):
    if n < 2: return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True
```

**Neden √n?** Eğer n = a*b ise, en az bir çarpan √n'den küçük olmalı.

## Optimizasyon: 6k ± 1

Tüm asallar 6k±1 formundadır (2 ve 3 hariç):

```python
def is_prime(n):
    if n < 2: return False
    if n < 4: return True
    if n % 2 == 0 or n % 3 == 0: return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True
```

## Eratosthenes Eleği: O(n log log n)

Çok sayıda asal kontrolü için:

```python
def sieve(n):
    primes = [True] * (n + 1)
    primes[0] = primes[1] = False
    for i in range(2, int(n**0.5) + 1):
        if primes[i]:
            for j in range(i * i, n + 1, i):
                primes[j] = False
    return [i for i, p in enumerate(primes) if p]
```

## Performans Karşılaştırması

| n | Naive | 6k±1 | Sieve (10 tekrar için) |
|---|-------|------|------------------------|
| 10⁶ | 1ms | 0.5ms | 50ms (10× kontrol için) |
| 10⁹ | 30ms | 15ms | 800ms |

## Kullanım Alanları

- **Kriptografi:** RSA, Diffie-Hellman
- **Hash fonksiyonları:** Hashing
- **Sayı teorisi:** Araştırma
""",
        "faq": [
            {"question": "Eratosthenes neden i*i'den başlıyor?", "answer": "Daha küçük katlar zaten 2,3,...,i-1 tarafından elenmiş olur. i*i zaten elenmemiş bir sayının en küçük katı."},
        ],
    },
    "python-obeb-oklid": {
        "id": 5,
        "slug": "python-obeb-oklid",
        "title": "Öklid Algoritması — OBEB (EBOB) Hesaplama",
        "description": "İki sayının en büyük ortak bölenini O(log n) sürede hesaplayın.",
        "category": "algorithms",
        "difficulty": "intermediate",
        "reading_time_minutes": 8,
        "related_question_ids": [11],
        "content_md": """# Öklid Algoritması

İki sayının en büyük ortak bölenini (OBEB/EBOB) hesaplar.

## Algoritma

gcd(a, b) = gcd(b, a mod b). Base case: gcd(a, 0) = a.

## Recursive

```python
def gcd(a, b):
    return a if b == 0 else gcd(b, a % b)
```

## Iterative

```python
def gcd(a, b):
    while b:
        a, b = b, a % b
    return a
```

## Python Builtin

```python
import math
math.gcd(12, 18)  # 6
```

## OKEK (LCM) Hesaplama

lcm(a, b) = a × b / gcd(a, b):

```python
from math import gcd
def lcm(a, b):
    return a * b // gcd(a, b)

# Python 3.9+:
import math
math.lcm(12, 18)  # 36
```

## Performans

O(log(min(a, b))) — iki sayının küçüğünün logaritması kadar adım.

## Kullanım Alanları

- **Kriptografi:** RSA
- **Kesir sadeleştirme:** 8/12 → 2/3
- **Periyodik olaylar:** Müzik, saat
""",
        "faq": [
            {"question": "Üç sayının OBEB'i nasıl hesaplanır?", "answer": "Associative: gcd(a, b, c) = gcd(gcd(a, b), c). Python'da: `math.gcd(math.gcd(a, b), c)` veya `math.gcd(a, b, c)` (Python 3.9+)."},
        ],
    },
    "python-two-sum": {
        "id": 6,
        "slug": "python-two-sum",
        "title": "Two Sum — En Klasik Mülakat Sorusu",
        "description": "Brute force'dan hash map'e. O(n²)'den O(n)'ye nasıl düşürülür?",
        "category": "algorithms",
        "difficulty": "beginner",
        "reading_time_minutes": 7,
        "related_question_ids": [301],
        "content_md": """# Two Sum

**Problem:** [2, 7, 11, 15], target=9 → [0, 1] (2+7=9).

## Brute Force: O(n²)

```python
def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
```

## Hash Map: O(n)

```python
def two_sum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        complement = target - n
        if complement in seen:
            return [seen[complement], i]
        seen[n] = i
```

## Neden Hash Map O(n)?

Her eleman için:
1. complement hesapla — O(1)
2. seen'de var mı — O(1) ortalama
3. Ekle — O(1)

n eleman için toplam O(n).

## Varyantlar

**Three Sum:** [a, b, c] öyle ki a+b+c=0.
```python
def three_sum(nums):
    nums.sort()
    result = []
    for i in range(len(nums) - 2):
        if i > 0 and nums[i] == nums[i-1]: continue
        left, right = i + 1, len(nums) - 1
        while left < right:
            s = nums[i] + nums[left] + nums[right]
            if s < 0: left += 1
            elif s > 0: right -= 1
            else:
                result.append([nums[i], nums[left], nums[right]])
                while left < right and nums[left] == nums[left+1]: left += 1
                while left < right and nums[right] == nums[right-1]: right -= 1
                left += 1; right -= 1
    return result
```
""",
        "faq": [
            {"question": "Aynı eleman iki kez kullanılabilir mi?", "answer": "Hayır. Two Sum'da her index bir kez kullanılır. 'Two Sum II' (sıralı input) varyasyonunda aynı eleman bir kez kullanılabilir."},
        ],
    },
    "pandas-groupby-rehberi": {
        "id": 7,
        "slug": "pandas-groupby-rehberi",
        "title": "Pandas GroupBy — Split-Apply-Combine Deseni",
        "description": "Pandas'ın en güçlü fonksiyonu. SQL GROUP BY karşılığı, çoklu aggregation, transform vs aggregate.",
        "category": "pandas",
        "difficulty": "intermediate",
        "reading_time_minutes": 15,
        "related_question_ids": [202, 205],
        "content_md": """# Pandas GroupBy

SQL'deki GROUP BY'ın Pandas karşılığı. **Split-Apply-Combine** deseni.

## Temel Kullanım

```python
import pandas as pd

df = pd.DataFrame({
    'category': ['A', 'B', 'A', 'B', 'A'],
    'value': [10, 20, 30, 40, 50]
})

df.groupby('category')['value'].mean()
# category
# A    30
# B    30
```

## Çoklu Aggregation

```python
df.groupby('category').agg({
    'value': ['mean', 'sum', 'count'],
    'price': ['min', 'max']
})
```

## Named Aggregation (Pandas 0.25+)

```python
df.groupby('category').agg(
    avg_value=('value', 'mean'),
    total_value=('value', 'sum'),
    count_records=('value', 'count')
)
```

## Transform vs Aggregate

**Aggregate:** Her grup için tek değer.
**Transform:** Orijinal shape'i korur, her satıra grup değeri yazılır.

```python
# Aggregate
df.groupby('cat')['value'].mean()  # Her kategori için 1 değer

# Transform
df['group_mean'] = df.groupby('cat')['value'].transform('mean')
# Her satıra kendi kategorisinin ortalaması yazılır
```

## Filter

```python
# 5'ten fazla kayıt olan kategorileri tut
df.groupby('cat').filter(lambda g: len(g) > 5)
```

## Apply (Custom Fonksiyon)

```python
df.groupby('cat').apply(lambda g: pd.Series({
    'range': g['value'].max() - g['value'].min(),
    'cv': g['value'].std() / g['value'].mean()  # coefficient of variation
}))
```

## Performans İpuçları

1. **Çok büyük veri:** `groupby('cat', sort=False)` — sort'u devre dışı bırak
2. **Çoklu kolon:** `groupby(['c1', 'c2'])` — MultiIndex döner
3. **Bellek:** `observed=True` (categorical kolonlar için)

## Gerçek Dünya

- A/B test analizi
- Müşteri segmentasyonu
- ETL pipeline
- Rapor oluşturma
""",
        "faq": [
            {"question": "GroupBy neden yavaş?", "answer": "Çok büyük DataFrame'lerde (10M+ satır) `sort=False` ekleyin veya `pyarrow` backend kullanın. Dask/Polars da seçenek."},
            {"question": "groupby.shift ne işe yarar?", "answer": "Zaman serisi analizinde lag/lead değerleri hesaplar. Örn: bir önceki güne göre değişim."},
        ],
    },

    # ═══ 8: Python Değişken Rehberi (2026-07-03) ═══
    "python-degisken-nedir": {
        "id": 8,
        "slug": "python-degisken-nedir",
        "title": "Python Değişken Nedir? Nasıl Oluşturulur? — Başlangıç Rehberi",
        "description": "Python'da değişken kavramı, atama operatörü, veri tipleri (int, float, str, bool) ve isimlendirme kuralları. Yeni başlayanlar için eksiksiz rehber.",
        "category": "python-basics",
        "difficulty": "beginner",
        "reading_time_minutes": 10,
        "related_question_ids": [74, 76, 77, 78],
        "content_md": """# Python Değişken Nedir?

Değişken, bir değeri sakladığın **isimlendirilmiş kutu**dur. Python'da her şey bir nesnedir ve değişken o nesneye referans (işaretçi) tutar.

## Değişken Tanımlama

Python'da değişken tanımlamak için `=` (atama operatörü) kullanılır. `let` veya `var` gibi anahtar kelimeye gerek yoktur.

```python
# Temel atamalar
isim = "Ali"
yas = 25
boy = 1.75
ogrenci = True
```

**Okunuşu:** "isim değişkenine 'Ali' ata" veya "isim 'Ali'ye eşittir" (teknik olarak eşitlik değil atamadır).

## Değişken İsimlendirme Kuralları

### Zorunlu kurallar (hata verir)
- **Harf veya `_` ile başlamalı**: `sayi1`, `_gizli`, `isim2` ✅
- **Sayı ile başlayamaz**: `1sayi` ❌
- **Sadece harf, rakam, `_` içerebilir**: `isim-soyad` ❌ (tire olmaz)
- **Python anahtar kelimesi olamaz**: `if`, `for`, `class`, `return` ❌

### Tavsiye edilen kurallar (PEP 8)
- **snake_case**: `kullanici_adi`, `toplam_fiyat`
- **Türkçe karakter kullanma**: `isim` yerine `ad` veya `name`
- **Anlamlı isim**: `x` yerine `toplam`, `s` yerine `cumle`
- **Sabitler BÜYÜK_HARF**: `PI = 3.14`, `MAX_DENEME = 3`

```python
# ❌ Kötü
x = 25
s = "Ali"
PI = 3.14

# ✅ İyi
kullanici_yasi = 25
kullanici_adi = "Ali"
pi_sabiti = 3.14
```

## Veri Tipleri

Python'da her değişkenin bir tipi vardır. `type()` fonksiyonu ile öğrenebilirsin:

```python
sayi = 42
print(type(sayi))        # <class 'int'> — tam sayı

ondalik = 3.14
print(type(ondalik))     # <class 'float'> — ondalıklı sayı

metin = "merhaba"
print(type(metin))       # <class 'str'> — string (metin)

dogru_mu = True
print(type(dogru_mu))    # <class 'bool'> — boolean (mantıksal)

liste = [1, 2, 3]
print(type(liste))       # <class 'list'> — liste
```

### Tip Dönüşümü

```python
# str → int
sayi = int("42")              # 42

# int → str
metin = str(42)               # "42"

# int → float
ondalik = float(5)            # 5.0

# str → float
pi = float("3.14")            # 3.14
```

## Dinamik Tip (Dynamic Typing)

Python'da değişkenin tipini **sen belirtmezsin**, Python yorumlar. Aynı değişkene farklı tipler atayabilirsin:

```python
x = 10        # x artık int
x = "merhaba" # x artık str
x = [1, 2, 3] # x artık list
```

Bu esneklik güçlüdür ama büyük projelerde karışıklığa yol açabilir. Çözüm: **type hints** (Python 3.5+):

```python
isim: str = "Ali"
yas: int = 25
```

## Çoklu Atama

```python
# Aynı değer
a = b = c = 0

# Farklı değerler (tuple unpacking)
x, y, z = 1, 2, 3
# x=1, y=2, z=3

# Takas
a, b = b, a
```

## Pratik Örnekler

**Örnek 1: Kullanıcı bilgileri**
```python
ad = "Zeynep"
soyad = "Yılmaz"
tam_ad = ad + " " + soyad  # "Zeynep Yılmaz"
yas = 22
dogum_yili = 2026 - yas    # 2004
```

**Örnek 2: Daire alanı**
```python
pi = 3.14159
yaricap = 5
alan = pi * yaricap ** 2    # 78.53975
```

**Örnek 3: Basit sayaç**
```python
sayac = 0
sayac = sayac + 1   # 1
sayac += 1          # 2 (kısa yazımı)
```

## Sık Yapılan Hatalar

1. **Değişken tanımsız**: `print(isim)` hata verir eğer `isim` daha önce tanımlanmadıysa.
2. **Tire kullanımı**: `kullanici-adi = "Ali"` SyntaxError.
3. **Büyük-küçük harf duyarlılığı**: `Isim` ile `isim` farklı değişkenlerdir.
4. **Rezerve kelimeler**: `class = "9-A"` hata verir, `sinif = "9-A"` çalışır.

## Özet

| Kavram | Örnek |
|--------|-------|
| Tanımlama | `isim = "Ali"` |
| Tip öğrenme | `type(isim)` → `str` |
| Çoklu atama | `a, b = 1, 2` |
| Tip dönüşümü | `int("42")` → `42` |
| Type hint | `yas: int = 25` |

Değişken, programlamanın **temel yapı taşı**dır. İyi isimlendirme alışkanlığı edinmek, junior'dan senior'a geçişin en önemli adımıdır.
""",
        "faq": [
            {"question": "Python'da değişken tanımlamak için 'let' veya 'var' gerekir mi?", "answer": "Hayır. Python dinamik tipli bir dil olduğu için sadece `=` ile atama yapılır: `isim = 'Ali'`."},
            {"question": "Bir değişkenin tipini nasıl öğrenirim?", "answer": "`type(degisken)` fonksiyonunu kullan. Örn: `type(42)` → `<class 'int'>`."},
            {"question": "Aynı isimde iki değişken tanımlayabilir miyim?", "answer": "Evet, ama ikincisi birincisinin üzerine yazar (rebind). `x = 5; x = 'a'` sonra `x` artık 'a' string'idir."},
            {"question": "Türkçe karakterli değişken ismi kullanabilir miyim?", "answer": "Python 3 evet, ama PEP 8 rehberi İngilizce ASCII karakter önerir. `yaş` yerine `yas` yazmak daha yaygın."},
            {"question": "Değişken ile sabit arasındaki fark nedir?", "answer": "Python'da sabit kavramı yoktur (constant), sadece convention vardır: BÜYÜK_HARF ile yazılan değişkenler dokunulmamalıdır (örn: `PI = 3.14`)."},
        ],
    },

    # ═══ 9: Python If-Else Rehberi (2026-07-03) ═══
    "python-if-else-kosullar": {
        "id": 9,
        "slug": "python-if-else-kosullar",
        "title": "Python If-Else Koşulları — Nerede ve Nasıl Kullanılır?",
        "description": "Python'da koşullu ifadeler (if, elif, else), karşılaştırma operatörleri, mantıksal operatörler (and, or, not) ve iç içe koşullar. Örneklerle başlangıç rehberi.",
        "category": "python-basics",
        "difficulty": "beginner",
        "reading_time_minutes": 12,
        "related_question_ids": [75, 76, 74],
        "content_md": """# Python If-Else Koşulları

Programlamada **karar verme** yapısıdır. "Eğer X doğruysa şunu yap, değilse bunu yap" mantığını kurar.

## Temel Yapı

```python
if kosul:
    # kosul True ise çalışır
    yapilacak_islem()
else:
    # kosul False ise çalışır
    alternatif_islem()
```

**Kritik kural:** `:` (iki nokta üst üste) ve **4 boşluk girinti** (indent) zorunludur. Girinti Python'da kod bloğunu tanımlar.

## Karşılaştırma Operatörleri

| Operatör | Anlam | Örnek | Sonuç |
|----------|-------|-------|-------|
| `==` | Eşit mi | `5 == 5` | `True` |
| `!=` | Eşit değil mi | `5 != 3` | `True` |
| `>` | Büyük mü | `5 > 3` | `True` |
| `<` | Küçük mü | `5 < 3` | `False` |
| `>=` | Büyük eşit mi | `5 >= 5` | `True` |
| `<=` | Küçük eşit mi | `3 <= 5` | `True` |

⚠️ **Yaygın hata:** `=` (atama) ile `==` (karşılaştırma) karıştırılır.
```python
# ❌ YANLIŞ — atama yapar, her zaman True döner
if x = 5:

# ✅ DOĞRU — karşılaştırma yapar
if x == 5:
```

## if-elif-else Zinciri

Birden fazla koşulu sırayla kontrol etmek için `elif` (else if) kullanılır:

```python
puan = 85

if puan >= 90:
    harf_notu = "AA"
elif puan >= 80:
    harf_notu = "BA"
elif puan >= 70:
    harf_notu = "BB"
elif puan >= 60:
    harf_notu = "CC"
else:
    harf_notu = "FF"

print(harf_notu)  # "BA"
```

**Kritik:** `elif` sırası önemlidir. İlk doğru koşulda durur, aşağıya geçmez.

## Mantıksal Operatörler

Birden fazla koşulu birleştirmek için:

```python
# AND — her iki koşul da doğru olmalı
if yas >= 18 and ehliyet_var:
    araba_kullanabilir()

# OR — en az biri doğru olmalı
if hava_yagmurlu or kar_yagli:
    semsiye_al()

# NOT — koşulu tersine çevirir
if not kullanici_giris_yapmis:
    login_sayfasina_yonlendir()
```

### Truthy / Falsy

Python'da koşul ifadesi sadece True/False değil, **herhangi bir değer** olabilir:

```python
# Falsy değerler (False sayılır)
if 0:           # False
if "":          # False (boş string)
if []:          # False (boş liste)
if None:        # False

# Truthy değerler (True sayılır)
if 1:           # True
if "merhaba":   # True
if [1, 2]:      # True (dolu liste)
if "0":         # True (string "0", int 0'dan farklı!)
```

## İç İçe Koşullar (Nested If)

```python
yas = 20
ehliyet_var = True
saglikli = True

if yas >= 18:
    if ehliyet_var:
        if saglikli:
            print("Araba kullanabilirsin")
        else:
            print("Sağlık raporu gerekli")
    else:
        print("Ehliyetin yok")
else:
    print("Yaşın yetmiyor")
```

**Daha okunabilir versiyon (`and` ile):**

```python
if yas >= 18 and ehliyet_var and saglikli:
    print("Araba kullanabilirsin")
elif yas < 18:
    print("Yaşın yetmiyor")
elif not ehliyet_var:
    print("Ehliyetin yok")
else:
    print("Sağlık raporu gerekli")
```

## Tek Satırlık If (Ternary)

Basit koşullar için kısa yazım:

```python
# Normal
if yas >= 18:
    durum = "yetiskin"
else:
    durum = "cocuk"

# Ternary (tek satır)
durum = "yetiskin" if yas >= 18 else "cocuk"
```

## Pratik Örnekler

**Örnek 1: Sayı tek/çift**
```python
sayi = 7
if sayi % 2 == 0:
    print("Çift sayı")
else:
    print("Tek sayı")
```

**Örnek 2: En büyük sayıyı bul**
```python
a, b, c = 5, 12, 8

if a >= b and a >= c:
    en_buyuk = a
elif b >= a and b >= c:
    en_buyuk = b
else:
    en_buyuk = c
```

**Örnek 3: Şifre doğrulama**
```python
kullanici_sifre = input("Şifre: ")
dogru_sifre = "python123"

if kullanici_sifre == dogru_sifre:
    print("Giriş başarılı")
elif kullanici_sifre == "":
    print("Şifre boş olamaz")
else:
    print("Yanlış şifre")
```

**Örnek 4: Hipotenüs hesabı (koşullu validasyon)**
```python
def hipotenus(a, b):
    a, b = abs(a), abs(b)
    
    if a == 0 and b == 0:
        return 0  # Üçgen oluşmaz
    
    import math
    return math.sqrt(a * a + b * b)
```

**Örnek 5: Not sistemi**
```python
notu = 75

if notu >= 90:
    derece = "A"
elif notu >= 80:
    derece = "B"
elif notu >= 70:
    derece = "C"
elif notu >= 60:
    derece = "D"
else:
    derece = "F"
```

## Sık Yapılan Hatalar

1. **`=` ile `==` karıştırmak**: `if x = 5` SyntaxError.
2. **Girinti unutmak**: `if kosul:` altındaki kod aynı seviyede olmalı.
3. **elif yerine if**: `if` yeni bir kontrol başlatır, `elif` zincirin parçasıdır.
4. **Truthy karışıklığı**: `if liste:` ile listenin **dolu** olup olmadığını kontrol edersin, `if len(liste) > 0:` değil.
5. **Negatif öncelik**: `not (a and b)` ile `not a and b` farklıdır!

```python
# Farklı anlamlar
not (a and b)   # a AND b'nin değili
not a and b     # (a değil) AND b
```

## Özet Tablo

| Yapı | Kullanım |
|------|----------|
| `if` | Tek koşul |
| `if-else` | İki durum (doğru/yanlış) |
| `if-elif-else` | Çoklu koşul |
| `and`, `or`, `not` | Koşulları birleştir |
| Ternary | Tek satır atama |
| Nested if | Koşul içinde koşul |

If-else, programlamanın **kalbi**dir. Algoritma tasarımının %80'i doğru koşul yazmaya dayanır.
""",
        "faq": [
            {"question": "Python'da 'else if' yerine 'elif' mi yazılır?", "answer": "Evet. Python'da 'else if' kısaltması olarak `elif` kullanılır: `if ... elif ... else ...`."},
            {"question": "if ile tek satırda yazılabilir mi?", "answer": "Evet, ternary (üçlü) operatör ile: `sonuc = 'yetiskin' if yas >= 18 else 'cocuk'`."},
            {"question": "Birden fazla koşulu nasıl birleştiririm?", "answer": "`and` (her ikisi de doğru), `or` (en az biri doğru), `not` (tersi) operatörleriyle. Örn: `if yas >= 18 and ehliyet:`."},
            {"question": "Boş liste if bloğuna girer mi?", "answer": "Hayır. Boş liste `[]`, boş string `\"\"`, `0`, `None` Falsy değerlerdir ve `if` bloğuna girmez. `if liste:` liste doluysa çalışır."},
            {"question": "Switch-case var mı Python'da?", "answer": "Klasik switch-case yoktur. Python 3.10+ ile `match-case` yapısı geldi. Daha eski sürümlerde if-elif-else zinciri kullanılır."},
        ],
    },
}


# ═══════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════

async def _get_from_db():
    """DB'den tutorial'ları çek (hata durumunda None)."""
    try:
        supabase = get_supabase()
        if not supabase:
            return None
        # service role ile bypass RLS
        from supabase_client import get_service_role
        sb = get_service_role()
        res = sb.table("tutorials").select("*").execute()
        return res.data if res.data else None
    except Exception as e:
        logger.warning("tutorials.list.db_failed: %s", e)
        return None


def _fallback_tutorial(slug: str) -> Optional[Dict[str, Any]]:
    """Fallback'ten tek tutorial getir."""
    return FALLBACK_TUTORIALS.get(slug)


def _all_fallback_tutorials() -> List[Dict[str, Any]]:
    """Fallback'ten tüm tutorial'lar (görüntülenme sırası korunur)."""
    return list(FALLBACK_TUTORIALS.values())


@router.get("", response_model=dict)
async def list_tutorials():
    """Tüm tutorial'ları listele. DB-first, fallback Python."""
    db_tutorials = await _get_from_db()
    if db_tutorials:
        return {"data": db_tutorials, "total": len(db_tutorials), "source": "db"}

    fallback = _all_fallback_tutorials()
    return {"data": fallback, "total": len(fallback), "source": "fallback"}


@router.get("/{slug}", response_model=dict)
async def get_tutorial(slug: str):
    """Slug ile tek tutorial getir."""
    # Önce DB
    try:
        supabase = get_service_role()
        res = supabase.table("tutorials").select("*").eq("slug", slug).execute()
        if res.data and len(res.data) > 0:
            return {"data": res.data[0], "source": "db"}
    except Exception as e:
        logger.warning("tutorials.detail.db_failed slug=%s: %s", slug, e)

    # Fallback
    fallback = _fallback_tutorial(slug)
    if not fallback:
        raise HTTPException(404, f"Tutorial bulunamadı: {slug}")
    return {"data": fallback, "source": "fallback"}