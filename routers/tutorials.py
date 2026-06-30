"""Tutorials endpoint — uzun form rehber yazıları.

DB-first, fallback Python dict.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from supabase_client import get_supabase

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
        print(f"[WARN] tutorials DB fetch failed: {e}")
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
        print(f"[WARN] tutorial DB fetch: {e}")

    # Fallback
    fallback = _fallback_tutorial(slug)
    if not fallback:
        raise HTTPException(404, f"Tutorial bulunamadı: {slug}")
    return {"data": fallback, "source": "fallback"}