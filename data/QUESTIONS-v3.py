# data/QUESTIONS-v3.py
# 82 yaratıcı soru: 70 (eski) + 12 (yeni data-structures)
# "Kullanıcı karar versin" mülakat prensibi — veri yapısı zorlaması yok.
# DB ile paralel kaynak (fallback). DB-first mimari.

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class Question:
    id: int
    title: str
    category: str
    level: str
    description: str
    starter_code: str
    test_cases: List[Dict[str, Any]]
    hints: List[str] = field(default_factory=list)
    # SEO alanlari
    explanation: str = ""
    complexity: str = "O(n)"
    related_concepts: List[str] = field(default_factory=list)
    related_question_ids: List[int] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    tutorial_slug: Optional[str] = None
    slug: Optional[str] = None


QUESTIONS: List[Question] = [
    Question(
        id=1,
        title='Palindrome Checker',
        category='python-basics',
        level='beginner',
        description="""Bir kelimenin veya cümlenin palindrome olup olmadığını kontrol et.
Büyük/küçük harf fark etmesin, boşluk ve noktalama işaretlerini yok say.
Örnek: 'A man a plan a canal Panama' → True""",
        starter_code='''def is_palindrome(text: str) -> bool:
    # Buraya kodunu yaz
    pass''',
        test_cases=[{'input': 'radar', 'expected': True}, {'input': 'Python', 'expected': False}, {'input': 'A man a plan a canal Panama', 'expected': True}, {'input': 'hello', 'expected': False}],
        hints=["💡 İpucu 1: Önce metnin yalnızca harf ve rakamlardan oluşan temiz halini oluştur. ''.join(...) ve str.isalnum() kullanabilirsin.", '💡 İpucu 2: Büyük/küçük harf farkını ortadan kaldırmak için .lower() metodunu kullan.', "💡 İpucu 3: Temizlenmiş string'i tersiyle karşılaştır: cleaned == cleaned[::-1]"],
        explanation='Palindrome kontrolü, Python mülakatlarının **en sık** sorduğu string sorusudur.\n\n**Problem:** Bir metin tersten okunduğunda aynı mı? Noktalama, boşluk ve büyük/küçük harf yok sayılır.\n\n**Üç yaklaşım:**\n\n```python\n# 1. Slicing — en kısa\ndef is_palindrome(s):\n    cleaned = re.sub(r\'[^a-z0-9]\', \'\', s.lower())\n    return cleaned == cleaned[::-1]\n\n# 2. İki pointer — O(1) ek bellek\ndef is_palindrome(s):\n    cleaned = re.sub(r\'[^a-z0-9]\', \'\', s.lower())\n    l, r = 0, len(cleaned) - 1\n    while l < r:\n        if cleaned[l] != cleaned[r]:\n            return False\n        l += 1\n        r -= 1\n    return True\n```\n\n**Neden slicing daha hızlı görünür ama iki pointer O(1) bellek?** Slicing yeni string oluşturur (O(n) bellek), iki pointer sadece index taşır.\n\n**Edge case\'ler:**\n- Boş string → True (vakum palindromdur)\n- Tek karakter → True\n- Karışık Unicode (Türkçe: "Ağaç") → ASCII-cleaning ile kaybedilir, çözüm `unicodedata.normalize`.',
        complexity='O(n) zaman, O(n) bellek (slicing) veya O(1) (iki pointer)',
        related_concepts=['string slicing', 'regex', 'two pointers', 'string normalization'],
        related_question_ids=[3, 7],
        tags=['beginner', 'python_basics'],
        tutorial_slug='python-palindrome-cozum',
    ),
    Question(
        id=2,
        title='Emoji FizzBuzz',
        category='python-basics',
        level='beginner',
        description="""1'den n'e kadar say.
3'e bölünüyorsa 'Fizz🎉', 5'e bölünüyorsa 'Buzz🚀',
her ikisine de bölünüyorsa 'FizzBuzz🎊' yaz.
Diğer sayıları string olarak ekle.""",
        starter_code='''def emoji_fizzbuzz(n: int) -> list:
    result = []
    for i in range(1, n+1):
        # Kodunu buraya yaz
        pass
    return result''',
        test_cases=[{'input': 5, 'expected': ['1', '2', 'Fizz🎉', '4', 'Buzz🚀']}, {'input': 15, 'expected': ['1', '2', 'Fizz🎉', '4', 'Buzz🚀', 'Fizz🎉', '7', '8', 'Fizz🎉', 'Buzz🚀', '11', 'Fizz🎉', '13', '14', 'FizzBuzz🎊']}],
        hints=["💡 İpucu 1: Önce hem 3 hem 5'e bölünme durumunu kontrol et (FizzBuzz🎊). Sıra önemli!", '💡 İpucu 2: Bölünebilirlik için % (modulo) operatörünü kullan: i % 3 == 0', "💡 İpucu 3: Hiçbir koşula uymuyorsa sayıyı string'e çevir: str(i)"],
        explanation='FizzBuzz, mülakatlarda **template** soru olarak kullanılır. Şirketler adayın temel kontrol yapılarını anlayıp anlamadığını test eder.\n\n**Problem:** 1\'den n\'e kadar:\n- 3\'e bölünürse "Fizz"\n- 5\'e bölünürse "Buzz"\n- İkisine de bölünürse "FizzBuzz"\n\n**Kritik detay — sıra:**\n\n```python\n# YANLIŞ sıra\nfor i in range(1, n+1):\n    if i % 3 == 0: print("Fizz")      # 15 buraya düşer, "FizzBuzz" kaçar\n    elif i % 5 == 0: print("Buzz")\n    elif i % 15 == 0: print("FizzBuzz")  # hiç gelmez\n\n# DOĞRU sıra\nfor i in range(1, n+1):\n    if i % 15 == 0: print("FizzBuzz")\n    elif i % 3 == 0: print("Fizz")\n    elif i % 5 == 0: print("Buzz")\n    else: print(i)\n```\n\n**Tek satır çözüm:**\n```python\nresult = ["FizzBuzz" if i % 15 == 0 else "Fizz" if i % 3 == 0 else "Buzz" if i % 5 == 0 else i for i in range(1, n+1)]\n```\n\n**Neden bu soru önemli:** Junior/staj pozisyonlarında adayın modulo, if/elif mantığı ve döngü bilgisi ölçülür. Çözemeyen genelde diğer sorularda da zorlanır.',
        complexity='O(n) zaman, O(1) ek bellek',
        related_concepts=['modulo', 'kontrol yapıları', 'list comprehension', 'edge case sıralaması'],
        related_question_ids=[1, 4],
        tags=['beginner', 'python_basics'],
        tutorial_slug='python-fizzbuzz-algoritma',
    ),
    Question(
        id=3,
        title='Kelimelerin En Uzunu',
        category='python-basics',
        level='beginner',
        description='''Bir cümledeki en uzun kelimeyi ve uzunluğunu döndür.
Birden fazla aynı uzunlukta kelime varsa ilkini döndür.
Not: Sonuç [kelime, uzunluk] şeklinde liste olmalı.''',
        starter_code='''def longest_word(sentence: str) -> list:
    # Düşün: split() ile kelimeleri ayır, max ile bul
    # Döndür: [en_uzun_kelime, uzunlugu]
    pass''',
        test_cases=[{'input': 'Python çok eğlenceli bir dil', 'expected': ['eğlenceli', 9]}, {'input': 'Merhaba dünya', 'expected': ['Merhaba', 7]}, {'input': 'a bb ccc', 'expected': ['ccc', 3]}],
        hints=['💡 İpucu 1: sentence.split() ile cümleyi kelimelere ayır.', '💡 İpucu 2: max(words, key=len) ile en uzun kelimeyi bul.', '💡 İpucu 3: Sonucu liste olarak döndür: [word, len(word)]'],
        explanation='Bir cümledeki en uzun kelimeyi bulmak, Python\'da `max()` fonksiyonunun `key` parametresini anlamayı ölçer.\n\n**Problem:** "Python mülakat hazırlığı" → "mülakat" veya "hazırlığı" (uzunluk 8).\n\n**İki çözüm:**\n\n```python\ndef longest_word(sentence):\n    words = sentence.split()\n    return max(words, key=len)\n\n# Manuel (key\'siz)\ndef longest_word(sentence):\n    words = sentence.split()\n    longest = ""\n    for w in words:\n        if len(w) > len(longest):\n            longest = w\n    return longest\n```\n\n**Püf noktaları:**\n- `split()` varsayılan olarak tüm whitespace\'i ayırıcı kabul eder (boşluk, tab, newline).\n- Aynı uzunlukta birden fazla kelime varsa `max()` **ilkini** döndürür.\n- Noktalama dahil mi? "Merhaba, dünya" → split() noktalamayı kelimeye yapıştırır. Önce regex ile temizle.',
        complexity='O(n) zaman, O(1) ek bellek',
        related_concepts=['max fonksiyonu', 'key parametresi', 'split', 'string temizleme'],
        related_question_ids=[1, 7],
        tags=['beginner', 'python_basics'],
    ),
    Question(
        id=4,
        title='Sihirli Kare Kontrolü',
        category='python-basics',
        level='beginner',
        description='''Verilen 3x3 liste bir sihirli kare mi?
Satır, sütun ve iki çapraz toplamların hepsi eşit olmalı.''',
        starter_code='''def is_magic_square(grid: list) -> bool:
    # Her satır, sütun ve çaprazın toplamını karşılaştır
    pass''',
        test_cases=[{'input': [[2, 7, 6], [9, 5, 1], [4, 3, 8]], 'expected': True}, {'input': [[1, 2, 3], [4, 5, 6], [7, 8, 9]], 'expected': False}],
        hints=['💡 İpucu 1: Hedef toplamı belirle: target = sum(grid[0])', '💡 İpucu 2: Sütunlar için: sum(grid[r][c] for r in range(3)) şeklinde döngü kur.', '💡 İpucu 3: Çaprazlar: grid[0][0]+grid[1][1]+grid[2][2] ve grid[0][2]+grid[1][1]+grid[2][0]'],
        explanation="""Sihirli kare (magic square), 3x3 matrisin tüm satır, sütun ve çapraz toplamlarının eşit olup olmadığını kontrol eder.

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
        complexity='O(n²) — sabit 3x3 için O(1)',
        related_concepts=['matris iterasyonu', 'zip', 'iç içe liste', 'matematik'],
        related_question_ids=[5, 102],
        tags=['beginner', 'python_basics'],
    ),
    Question(
        id=5,
        title='Sayı Tahmin Skoru',
        category='python-basics',
        level='beginner',
        description='''Kullanıcının tahminleri ve gerçek sayı verildiğinde,
kaç tahminin tam doğru, kaç tahminin ±5 içinde, kaç tahminin uzak olduğunu döndür.''',
        starter_code="""def score_guesses(guesses: list, secret: int) -> dict:
    # {'exact': x, 'close': y, 'far': z} döndür
    pass""",
        test_cases=[{'input': {'guesses': [10, 12, 50, 11], 'secret': 10}, 'expected': {'exact': 1, 'close': 2, 'far': 1}}, {'input': {'guesses': [1, 2, 3], 'secret': 100}, 'expected': {'exact': 0, 'close': 0, 'far': 3}}],
        hints=['💡 İpucu 1: abs(guess - secret) ile farkın mutlak değerini al.', "💡 İpucu 2: diff == 0 ise 'exact', diff <= 5 ise 'close', değilse 'far'.", '💡 İpucu 3: Sonuçları sayacak bir dict oluştur ve döngüde güncelle.'],
        explanation='''Sayı tahmin oyunu, **oyun döngüsü** ve kullanıcı etkileşimi simülasyonudur.

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

**Gerçek dünya:** Kullanıcı deneyimi (UX), oyun geliştirme, A/B test varyantları.''',
        complexity='O(log n) optimal strateji, O(n) en kötü',
        related_concepts=['random modülü', 'while döngüsü', 'input parsing', 'oyun döngüsü'],
        related_question_ids=[14],
        tags=['beginner', 'python_basics'],
    ),
    Question(
        id=7,
        title='Asal Sayı Kontrolü',
        category='python-basics',
        level='beginner',
        description='''Verilen sayının asal olup olmadığını kontrol et.
1 ve altındaki sayılar asal değildir.''',
        starter_code='''def is_prime(n: int) -> bool:
    # Asal sayı: yalnızca 1 ve kendisine bölünür
    pass''',
        test_cases=[{'input': 2, 'expected': True}, {'input': 17, 'expected': True}, {'input': 1, 'expected': False}, {'input': 9, 'expected': False}],
        hints=['💡 İpucu 1: n <= 1 ise direkt False döndür.', "💡 İpucu 2: 2'den √n'e kadar bölenleri kontrol et: range(2, int(n**0.5)+1)", '💡 İpucu 3: Herhangi bir bölen bulursan False, döngü biterse True döndür.'],
        explanation='Anagram kontrolü, iki string\'in aynı harfleri aynı sayıda içerip içermediğini kontrol eder.\n\n**Problem:** "listen" ve "silent" → True (anagram).\n\n**İki yaklaşım:**\n\n```python\nfrom collections import Counter\n\n# 1. Counter karşılaştırma — O(n)\ndef is_anagram(s1, s2):\n    return Counter(s1) == Counter(s2)\n\n# 2. Sıralama — O(n log n) ama basit\ndef is_anagram(s1, s2):\n    return sorted(s1) == sorted(s2)\n```\n\n**Normalizasyon şart:** Büyük/küçük harf ve boşluk farkını yok saymak için önce `s.replace(" ", "").lower()`.\n\n**Performans karşılaştırması:** 1MB metin için Counter ~3ms, sorted ~120ms. Counter O(n) olduğu için 40x hızlı.\n\n**Edge case:** Unicode (Türkçe karakterler) — `casefold()` kullan, `lower()` Türkçe "İ" için yanlış sonuç verir.',
        complexity='O(n) Counter ile, O(n log n) sıralama ile',
        related_concepts=['Counter', 'sorted', 'string normalize', 'casefold'],
        related_question_ids=[1],
        tags=['beginner', 'python_basics'],
    ),
    Question(
        id=8,
        title='Liste Düzleştirme',
        category='python-basics',
        level='beginner',
        description='''İç içe geçmiş listeyi tek seviyeli listeye dönüştür.
Yalnızca bir seviye derinlik garantilidir.''',
        starter_code='''def flatten(nested: list) -> list:
    # [[1,2],[3,4],[5]] -> [1,2,3,4,5]
    pass''',
        test_cases=[{'input': [[1, 2], [3, 4], [5]], 'expected': [1, 2, 3, 4, 5]}, {'input': [[10], [20, 30], [40, 50, 60]], 'expected': [10, 20, 30, 40, 50, 60]}],
        hints=['💡 İpucu 1: Boş bir liste oluştur ve her alt listeyi üzerine extend() et.', '💡 İpucu 2: List comprehension ile: [item for sublist in nested for item in sublist]', '💡 İpucu 3: itertools.chain.from_iterable(nested) de çalışır.'],
        explanation="""Rakam toplamı, özyinelemeli (recursive) düşüncenin temelidir.

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
        complexity='O(log n) — basamak sayısı kadar',
        related_concepts=['özyineleme', 'modulo', 'floor division', 'base case'],
        related_question_ids=[9, 11, 16],
        tags=['beginner', 'python_basics'],
    ),
    Question(
        id=9,
        title='Fibonacci Dizisi',
        category='python-basics',
        level='beginner',
        description='''İlk n Fibonacci sayısını liste olarak döndür.
F(0)=0, F(1)=1, F(n)=F(n-1)+F(n-2)''',
        starter_code='''def fibonacci(n: int) -> list:
    # İlk n elemanı hesapla
    pass''',
        test_cases=[{'input': 7, 'expected': [0, 1, 1, 2, 3, 5, 8]}, {'input': 1, 'expected': [0]}, {'input': 2, 'expected': [0, 1]}],
        hints=['💡 İpucu 1: Özel durumlar: n==1 → [0], n==2 → [0,1]', '💡 İpucu 2: [0, 1] ile başla, döngüde fib[-1]+fib[-2] ekle.', '💡 İpucu 3: while len(fib) < n: fib.append(fib[-1]+fib[-2])'],
        explanation="""Asal sayı kontrolü, matematik tabanlı algoritma sorularının temelidir.

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
        complexity='O(√n) tek sayı, O(n log log n) Eratosthenes',
        related_concepts=['Eratosthenes eleği', 'matematik', 'asal sayılar', 'modulo'],
        related_question_ids=[11, 16],
        tags=['beginner', 'python_basics'],
        tutorial_slug='python-asal-sayi-algoritma',
    ),
    Question(
        id=10,
        title='Anagram Kontrolü',
        category='python-basics',
        level='beginner',
        description='''İki kelimenin anagram olup olmadığını kontrol et.
Büyük/küçük harf ve boşluk fark etmesin.''',
        starter_code='''def is_anagram(word1: str, word2: str) -> bool:
    # Anagram: aynı harfleri farklı sırada kullanan kelimeler
    pass''',
        test_cases=[{'input': {'word1': 'listen', 'word2': 'silent'}, 'expected': True}, {'input': {'word1': 'hello', 'word2': 'world'}, 'expected': False}, {'input': {'word1': 'Astronomer', 'word2': 'Moon starer'}, 'expected': True}],
        hints=["💡 İpucu 1: Her iki string'i .lower() yap ve boşlukları kaldır.", '💡 İpucu 2: sorted() ile harfleri sırala ve karşılaştır: sorted(a) == sorted(b)', '💡 İpucu 3: Ya da Counter(a) == Counter(b) ile frekans karşılaştır.'],
        explanation="""Cumulative sum (kümülatif toplam), finansal analiz ve sinyal işlemede çok kullanılır.

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
        complexity='O(n) tüm yaklaşımlar için',
        related_concepts=['itertools.accumulate', 'kümülatif toplam', 'running sum'],
        related_question_ids=[4, 13, 102],
        tags=['beginner', 'python_basics'],
    ),
    Question(
        id=11,
        title='Kelime Tersleyici',
        category='python-basics',
        level='beginner',
        description='''Cümledeki kelimelerin sırasını tersine çevir,
fakat kelimelerin kendisini tersine çevirme.''',
        starter_code='''def reverse_words(sentence: str) -> str:
    # "Merhaba Dünya" -> "Dünya Merhaba"
    pass''',
        test_cases=[{'input': 'Merhaba Dünya', 'expected': 'Dünya Merhaba'}, {'input': 'Python çok güzel', 'expected': 'güzel çok Python'}],
        hints=['💡 İpucu 1: sentence.split() ile kelimelere ayır.', '💡 İpucu 2: words[::-1] veya reversed(words) ile sırayı tersine çevir.', "💡 İpucu 3: ' '.join(...) ile tekrar birleştir."],
        explanation='''OBEB (EBOB/GCD), Öklid algoritmasının klasik uygulamasıdır.

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

**Kullanım:** Kesir sadeleştirme, RSA kriptografi, periyodik olaylar (müzik teorisi, saat hesabı).''',
        complexity="O(log(min(a, b))) — Öklid'in garanti alt sınırı",
        related_concepts=['Öklid algoritması', 'özyineleme', 'modulo', 'matematik'],
        related_question_ids=[8, 9, 16],
        tags=['beginner', 'python_basics'],
        tutorial_slug='python-obeb-oklid',
    ),
    Question(
        id=12,
        title='İkinci En Büyük',
        category='python-basics',
        level='beginner',
        description='''Bir listedeki ikinci en büyük eşsiz sayıyı döndür.
Eğer yoksa None döndür.''',
        starter_code='''def second_largest(numbers: list):
    # Tekrar eden sayıları dikkate alma
    pass''',
        test_cases=[{'input': [3, 1, 4, 1, 5, 9, 2, 6], 'expected': 6}, {'input': [5, 5, 5], 'expected': None}, {'input': [10, 20], 'expected': 10}],
        hints=['💡 İpucu 1: Önce set() ile tekrarları kaldır.', '💡 İpucu 2: sorted() veya max() kullanarak en büyükleri bul.', '💡 İpucu 3: len(unique) < 2 ise None döndür, yoksa sorted(unique)[-2]'],
        explanation='Üçgen tipi kontrolü, **üçgen eşitsizliği** kuralının uygulamasıdır.\n\n**Üçgen eşitsizliği:** Her kenar, diğer iki kenarın toplamından küçük olmalı. a + b > c ∧ a + c > b ∧ b + c > a.\n\n**Çözüm:**\n\n```python\ndef triangle_type(a, b, c):\n    if not (a + b > c and a + c > b and b + c > a):\n        return "Geçersiz"\n    if a == b == c:\n        return "Eşkenar"\n    elif a == b or a == c or b == c:\n        return "İkizkenar"\n    else:\n        return "Çeşitkenar"\n```\n\n**Edge case\'ler:**\n- Negatif kenarlar → geçersiz\n- Sıfır kenar → geçersiz (üçgen oluşmaz)\n- Float precision: 0.1 + 0.2 != 0.3 sorunu için `math.isclose()`\n\n**Genişletme:** Alan hesabı (Heron formülü), dik üçgen kontrolü (Pisagor).',
        complexity='O(1)',
        related_concepts=['üçgen eşitsizliği', 'koşullu ifadeler', 'Pisagor'],
        related_question_ids=[4, 13],
        tags=['beginner', 'python_basics'],
    ),
    Question(
        id=13,
        title='Sezar Şifresi',
        category='python-basics',
        level='beginner',
        description='''Metni n karakter kaydırarak şifrele (yalnızca İngilizce harfler).
Büyük/küçük harf korunmalı, diğer karakterler değişmemeli.''',
        starter_code='''def caesar_cipher(text: str, shift: int) -> str:
    # Her harfi alfabede shift kadar ilerlet
    pass''',
        test_cases=[{'input': {'text': 'Hello', 'shift': 3}, 'expected': 'Khoor'}, {'input': {'text': 'xyz', 'shift': 3}, 'expected': 'abc'}, {'input': {'text': 'Hello, World!', 'shift': 13}, 'expected': 'Uryyb, Jbeyq!'}],
        hints=['💡 İpucu 1: ord() ile karakterin ASCII kodunu al, chr() ile geri dönüştür.', "💡 İpucu 2: Büyük harf için: chr((ord(c) - ord('A') + shift) % 26 + ord('A'))", '💡 İpucu 3: Harf olmayanları (noktalama vb.) olduğu gibi bırak.'],
        explanation='String/liste ters çevirme, **en temel** algoritma sorularındandır.\n\n**Problem:** "hello" → "olleh".\n\n**Yaklaşımlar:**\n\n```python\n# 1. Slicing — en kısa\nreversed_str = s[::-1]\n\n# 2. reversed() + join\nreversed_str = \'\'.join(reversed(s))\n\n# 3. Manuel (in-place, O(1) bellek)\ndef reverse_string(s):\n    s = list(s)  # string immutable\n    l, r = 0, len(s) - 1\n    while l < r:\n        s[l], s[r] = s[r], s[l]\n        l += 1\n        r -= 1\n    return \'\'.join(s)\n```\n\n**Liste için:** `lst.reverse()` (in-place) veya `lst[::-1]` (yeni liste).\n\n**Bellek:** Slicing O(n) yeni nesne oluşturur. In-place swap O(1).',
        complexity='O(n) zaman, O(1) veya O(n) bellek',
        related_concepts=['slicing', 'in-place swap', 'reversed', 'two pointers'],
        related_question_ids=[1, 3, 14],
        tags=['beginner', 'python_basics'],
    ),
    Question(
        id=14,
        title='Matris Transpozu',
        category='python-basics',
        level='beginner',
        description='Bir matrisin transpozunu al (satırları sütun, sütunları satır yap).',
        starter_code='''def transpose(matrix: list) -> list:
    # [[1,2,3],[4,5,6]] -> [[1,4],[2,5],[3,6]]
    pass''',
        test_cases=[{'input': [[1, 2, 3], [4, 5, 6]], 'expected': [[1, 4], [2, 5], [3, 6]]}, {'input': [[1, 2], [3, 4], [5, 6]], 'expected': [[1, 3, 5], [2, 4, 6]]}],
        hints=['💡 İpucu 1: zip(*matrix) sihirli bir araçtır — satırları transpose eder.', '💡 İpucu 2: [list(row) for row in zip(*matrix)] ile sonucu listele.', '💡 İpucu 3: Manuel yol: result[j][i] = matrix[i][j] ile iç içe döngü.'],
        explanation="""İkili arama (binary search), **sıralı** dizide hedef bulmanın en hızlı yoludur.

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
        complexity='O(log n) zaman, O(1) bellek',
        related_concepts=['binary search', 'sıralı dizi', 'divide and conquer'],
        related_question_ids=[5],
        tags=['beginner', 'python_basics'],
        tutorial_slug='python-binary-search',
    ),
    Question(
        id=16,
        title='Parantez Dengesi',
        category='python-basics',
        level='beginner',
        description="""Verilen bir string'deki parantezlerin dengeli olup olmadığını kontrol et.
( ) [ ] { } desteklenir.""",
        starter_code='''def is_balanced(s: str) -> bool:
    # Stack (yığın) veri yapısını kullan
    pass''',
        test_cases=[{'input': '([]{})', 'expected': True}, {'input': '([)]', 'expected': False}, {'input': '', 'expected': True}, {'input': '(((', 'expected': False}],
        hints=['💡 İpucu 1: Bir yığın (stack = []) kullan.', '💡 İpucu 2: Açık parantez görünce yığına ekle (push). Kapalı görünce yığından çıkar (pop) ve eşleş mi kontrol et.', '💡 İpucu 3: Sonunda yığın boşsa True, doluysa False döndür.'],
        explanation="""**Parantez Dengesi** sorusu, **String Islemleri** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** Verilen bir string'deki parantezlerin dengeli olup olmadığını kontrol et.

**Yaklaşım:**

```python
def is_balanced(s: str) -> bool:
    # ...implementasyon...
```

**Kategori ipuçları (String Islemleri):**
- string method bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Beginner seviye mülakatlarda string islemleri bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['strings', 'beginner', 'interview'],
        related_question_ids=[2, 3],
        tags=['strings', 'string_methods', 'manipulation', 'beginner'],
    ),
    Question(
        id=18,
        title='Run-Length Encoding',
        category='python-basics',
        level='beginner',
        description="""Bir string'i run-length encoding ile sıkıştır.
'aaabbc' → '3a2b1c'""",
        starter_code='''def rle_encode(s: str) -> str:
    # Ardışık aynı karakterleri say ve sıkıştır
    pass''',
        test_cases=[{'input': 'aaabbc', 'expected': '3a2b1c'}, {'input': 'aabbccdd', 'expected': '2a2b2c2d'}, {'input': 'abc', 'expected': '1a1b1c'}],
        hints=['💡 İpucu 1: Mevcut karakteri ve sayısını tut: current_char, count.', '💡 İpucu 2: Karakter değişince sonucu ekle: result += str(count) + current_char', '💡 İpucu 3: Döngü bittikten sonra son grubu da eklemeyi unutma.'],
        explanation="""**Run-Length Encoding** sorusu, **String Islemleri** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** Bir string'i run-length encoding ile sıkıştır.

**Yaklaşım:**

```python
def rle_encode(s: str) -> str:
    # ...implementasyon...
```

**Kategori ipuçları (String Islemleri):**
- string method bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Beginner seviye mülakatlarda string islemleri bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['strings', 'beginner', 'interview'],
        related_question_ids=[1, 2],
        tags=['strings', 'string_methods', 'manipulation', 'beginner'],
    ),
    Question(
        id=19,
        title='Kelime Sıklığı',
        category='python-basics',
        level='beginner',
        description='''Bir metindeki en sık geçen k kelimeyi döndür.
Büyük/küçük harf duyarlı olmasın, noktalama işaretlerini yok say.''',
        starter_code='''def top_k_words(text: str, k: int) -> list:
    # En sık geçen k kelimeyi liste olarak döndür
    pass''',
        test_cases=[{'input': {'text': 'bir iki bir üç iki bir', 'k': 2}, 'expected': ['bir', 'iki']}, {'input': {'text': 'the cat sat on the mat the', 'k': 1}, 'expected': ['the']}],
        hints=['💡 İpucu 1: .lower() ve .split() ile kelimeleri ayır.', '💡 İpucu 2: collections.Counter(words) ile frekans sözlüğü oluştur.', '💡 İpucu 3: counter.most_common(k) ile en sık k kelimeyi al.'],
        explanation="""**Kelime Sıklığı** sorusu, **String Islemleri** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** Bir metindeki en sık geçen k kelimeyi döndür.

**Yaklaşım:**

```python
def top_k_words(text: str, k: int) -> list:
    # ...implementasyon...
```

**Kategori ipuçları (String Islemleri):**
- string method bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Beginner seviye mülakatlarda string islemleri bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['strings', 'beginner', 'interview'],
        related_question_ids=[1, 2],
        tags=['strings', 'string_methods', 'manipulation', 'beginner'],
    ),
    Question(
        id=20,
        title='String Sıkıştırma',
        category='python-basics',
        level='beginner',
        description="""Bir string'i sıkıştır: art arda tekrar eden karakterleri tek karaktere indir.
'aabbcc' → 'abc', 'aabba' → 'aba'""",
        starter_code='''def compress(s: str) -> str:
    # Art arda tekrarları kaldır
    pass''',
        test_cases=[{'input': 'aabbcc', 'expected': 'abc'}, {'input': 'aabba', 'expected': 'aba'}, {'input': 'abcdef', 'expected': 'abcdef'}],
        hints=['💡 İpucu 1: Boş string durumunu kontrol et.', '💡 İpucu 2: result = s[0] ile başla, sonraki karakter öncekinden farklıysa ekle.', '💡 İpucu 3: itertools.groupby(s) ile de çözebilirsin.'],
        explanation="""**String Sıkıştırma** sorusu, **String Islemleri** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** Bir string'i sıkıştır: art arda tekrar eden karakterleri tek karaktere indir.

**Yaklaşım:**

```python
def compress(s: str) -> str:
    # ...implementasyon...
```

**Kategori ipuçları (String Islemleri):**
- string method bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Beginner seviye mülakatlarda string islemleri bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['strings', 'beginner', 'interview'],
        related_question_ids=[1, 2],
        tags=['strings', 'string_methods', 'manipulation', 'beginner'],
    ),
    Question(
        id=21,
        title='Roman Numerals',
        category='python-basics',
        level='intermediate',
        description='1-3999 arasındaki bir tam sayıyı Roma rakamlarına çevir.',
        starter_code="""def to_roman(num: int) -> str:
    values = [1000,900,500,400,100,90,50,40,10,9,5,4,1]
    symbols = ['M','CM','D','CD','C','XC','L','XL','X','IX','V','IV','I']
    # Buraya kodunu yaz
    pass""",
        test_cases=[{'input': 3, 'expected': 'III'}, {'input': 58, 'expected': 'LVIII'}, {'input': 1994, 'expected': 'MCMXCIV'}],
        hints=['💡 İpucu 1: values ve symbols listesi zaten verilmiş, sırayla karşılaştır.', '💡 İpucu 2: num >= value iken: result += symbol, num -= value', '💡 İpucu 3: CM=900, CD=400 gibi özel durumlar listeye dahil edilmiş, endişelenme.'],
        explanation="""**Roman Numerals** sorusu, **String Islemleri** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** 1-3999 arasındaki bir tam sayıyı Roma rakamlarına çevir.

**Yaklaşım:**

```python
def to_roman(num: int) -> str:
    # ...implementasyon...
```

**Kategori ipuçları (String Islemleri):**
- string method bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Intermediate seviye mülakatlarda string islemleri bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['strings', 'intermediate', 'interview'],
        related_question_ids=[1, 2],
        tags=['strings', 'string_methods', 'manipulation', 'intermediate'],
    ),
    Question(
        id=22,
        title='Pangram Kontrolü',
        category='python-basics',
        level='beginner',
        description='''Bir cümle pangram mı? (İngiliz alfabesinin tüm harflerini içeriyor mu?)
Büyük/küçük harf duyarlı olmasın.''',
        starter_code='''def is_pangram(sentence: str) -> bool:
    # 26 İngilizce harfin hepsi var mı?
    pass''',
        test_cases=[{'input': 'The quick brown fox jumps over the lazy dog', 'expected': True}, {'input': 'Hello World', 'expected': False}],
        hints=['💡 İpucu 1: sentence.lower() ile küçük harfe çevir.', '💡 İpucu 2: set() ile unique harfleri bul.', "💡 İpucu 3: set('abcdefghijklmnopqrstuvwxyz').issubset(set(sentence.lower()))"],
        explanation="""**Pangram Kontrolü** sorusu, **String Islemleri** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** Bir cümle pangram mı? (İngiliz alfabesinin tüm harflerini içeriyor mu?)

**Yaklaşım:**

```python
def is_pangram(sentence: str) -> bool:
    # ...implementasyon...
```

**Kategori ipuçları (String Islemleri):**
- string method bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Beginner seviye mülakatlarda string islemleri bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['strings', 'beginner', 'interview'],
        related_question_ids=[1, 2, 3],
        tags=['strings', 'string_methods', 'manipulation', 'beginner'],
        tutorial_slug='python-strings-pangram-kontrolu',
    ),
    Question(
        id=25,
        title='DNA Tamamlayıcısı',
        category='python-basics',
        level='beginner',
        description='''Bir DNA zincirinin tamamlayıcısını bul.
A↔T, C↔G  kuralını uygula ve sonucu tersine çevir.''',
        starter_code='''def dna_complement(strand: str) -> str:
    # ATCG -> CGAT (önce tamamlayıcı sonra ters)
    pass''',
        test_cases=[{'input': 'ATCG', 'expected': 'CGAT'}, {'input': 'TTAA', 'expected': 'TTAA'}],
        hints=["💡 İpucu 1: Bir eşleşme dict'i oluştur: {'A':'T','T':'A','C':'G','G':'C'}", "💡 İpucu 2: Her karakteri eşleşme dict'inden bul: comp[c]", '💡 İpucu 3: Tamamlayıcıyı oluşturduktan sonra [::-1] ile tersine çevir.'],
        explanation="""**DNA Tamamlayıcısı** sorusu, **String Islemleri** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** Bir DNA zincirinin tamamlayıcısını bul.

**Yaklaşım:**

```python
def dna_complement(strand: str) -> str:
    # ...implementasyon...
```

**Kategori ipuçları (String Islemleri):**
- string method bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Beginner seviye mülakatlarda string islemleri bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['strings', 'beginner', 'interview'],
        related_question_ids=[1, 2, 3],
        tags=['strings', 'string_methods', 'manipulation', 'beginner'],
        tutorial_slug='python-strings-dna-tamamlayicisi',
    ),
    Question(
        id=26,
        title='İki Listeyi Birleştir',
        category='data-structures',
        level='beginner',
        description='''İki sıralı listeyi birleştirerek yeni bir sıralı liste oluştur.
sort() kullanmadan yap.''',
        starter_code='''def merge_sorted(a: list, b: list) -> list:
    # İki işaretçi (pointer) tekniği kullan
    pass''',
        test_cases=[{'input': {'a': [1, 3, 5], 'b': [2, 4, 6]}, 'expected': [1, 2, 3, 4, 5, 6]}, {'input': {'a': [1, 2], 'b': [3, 4, 5, 6]}, 'expected': [1, 2, 3, 4, 5, 6]}, {'input': {'a': [], 'b': [1, 2, 3]}, 'expected': [1, 2, 3]}],
        hints=['💡 İpucu 1: İki işaretçi: i=0 (a için), j=0 (b için)', "💡 İpucu 2: Her adımda küçük olanı result'a ekle ve o işaretçiyi ilerlet.", '💡 İpucu 3: Döngü bitince kalan elemanları result.extend(a[i:]) ile ekle.'],
        explanation="""**İki Listeyi Birleştir** sorusu, **Veri Yapilari** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** İki sıralı listeyi birleştirerek yeni bir sıralı liste oluştur.

**Yaklaşım:**

```python
def merge_sorted(a: list, b: list) -> list:
    # ...implementasyon...
```

**Kategori ipuçları (Veri Yapilari):**
- list bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Beginner seviye mülakatlarda veri yapilari bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['list-dict', 'beginner', 'interview'],
        related_question_ids=[1, 2],
        tags=['collections', 'list_dict', 'beginner', 'loops'],
        tutorial_slug='python-list-dict-iki-listeyi-birlestir',
    ),
    Question(
        id=27,
        title='Sözlük Birleştirme',
        category='list-dict',
        level='beginner',
        description='İki sözlüğü birleştir. Aynı anahtarlar varsa değerlerini topla.',
        starter_code='''def merge_dicts(d1: dict, d2: dict) -> dict:
    # {"a":1,"b":2} + {"b":3,"c":4} -> {"a":1,"b":5,"c":4}
    pass''',
        test_cases=[{'input': {'d1': {'a': 1, 'b': 2}, 'd2': {'b': 3, 'c': 4}}, 'expected': {'a': 1, 'b': 5, 'c': 4}}, {'input': {'d1': {}, 'd2': {'x': 10}}, 'expected': {'x': 10}}],
        hints=["💡 İpucu 1: d1.copy() ile başla, d2'nin öğelerini üzerine ekle.", '💡 İpucu 2: result.get(key, 0) + value ile birleştirme yap.', '💡 İpucu 3: collections.Counter da bu iş için kullanılabilir.'],
        explanation="""**Sözlük Birleştirme** sorusu, **Veri Yapilari** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** İki sözlüğü birleştir. Aynı anahtarlar varsa değerlerini topla.

**Yaklaşım:**

```python
def merge_dicts(d1: dict, d2: dict) -> dict:
    # ...implementasyon...
```

**Kategori ipuçları (Veri Yapilari):**
- list bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Beginner seviye mülakatlarda veri yapilari bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['list-dict', 'beginner', 'interview'],
        related_question_ids=[1, 2],
        tags=['collections', 'list_dict', 'beginner', 'loops'],
        tutorial_slug='python-list-dict-sozluk-birlestirme',
    ),
    Question(
        id=28,
        title='Gruplama',
        category='list-dict',
        level='beginner',
        description="""Bir sayı listesini 'tek' ve 'çift' olarak grupla.
Sonuç: {'tek': [...], 'çift': [...]}""",
        starter_code='''def group_by_parity(items: list) -> dict:
    # Sayıları tek ve çift olarak grupla
    pass''',
        test_cases=[{'input': [1, 2, 3, 4, 5, 6], 'expected': {'tek': [1, 3, 5], 'çift': [2, 4, 6]}}, {'input': [10, 15, 20, 25], 'expected': {'tek': [15, 25], 'çift': [10, 20]}}],
        hints=["💡 İpucu 1: Boş bir dict oluştur: result = {'tek': [], 'çift': []}", "💡 İpucu 2: Her öğe için: if n % 2 == 0 → 'çift', else → 'tek'", "💡 İpucu 3: result['tek'].append(n) veya result['çift'].append(n)"],
        explanation="""**Gruplama** sorusu, **Veri Yapilari** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** Bir sayı listesini 'tek' ve 'çift' olarak grupla.

**Yaklaşım:**

```python
def group_by_parity(items: list) -> dict:
    # ...implementasyon...
```

**Kategori ipuçları (Veri Yapilari):**
- list bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Beginner seviye mülakatlarda veri yapilari bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['list-dict', 'beginner', 'interview'],
        related_question_ids=[1, 2],
        tags=['collections', 'list_dict', 'beginner', 'loops'],
        tutorial_slug='python-list-dict-gruplama',
    ),
    Question(
        id=29,
        title='Fark Listesi',
        category='list-dict',
        level='beginner',
        description="İki liste arasındaki farkları bul: yalnızca A'da, yalnızca B'de ve ikisinde birden olan elemanlar.",
        starter_code="""def list_diff(a: list, b: list) -> dict:
    # {'only_a': [...], 'only_b': [...], 'common': [...]} döndür
    pass""",
        test_cases=[{'input': {'a': [1, 2, 3, 4], 'b': [3, 4, 5, 6]}, 'expected': {'only_a': [1, 2], 'only_b': [5, 6], 'common': [3, 4]}}],
        hints=['💡 İpucu 1: set() dönüşümü yap: sa=set(a), sb=set(b)', '💡 İpucu 2: only_a = sorted(sa - sb), only_b = sorted(sb - sa)', '💡 İpucu 3: common = sorted(sa & sb)  (kesişim)'],
        explanation="""**Fark Listesi** sorusu, **Veri Yapilari** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** İki liste arasındaki farkları bul: yalnızca A'da, yalnızca B'de ve ikisinde birden olan elemanlar.

**Yaklaşım:**

```python
def list_diff(a: list, b: list) -> dict:
    # ...implementasyon...
```

**Kategori ipuçları (Veri Yapilari):**
- list bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Beginner seviye mülakatlarda veri yapilari bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['list-dict', 'beginner', 'interview'],
        related_question_ids=[1, 2],
        tags=['collections', 'list_dict', 'beginner', 'loops'],
    ),
    Question(
        id=30,
        title='Matris Çarpımı',
        category='data-structures',
        level='intermediate',
        description='İki matrisi çarp (nokta çarpımı). numpy kullanma.',
        starter_code='''def matrix_multiply(a: list, b: list) -> list:
    # C[i][j] = sum(A[i][k] * B[k][j] for k in range(...))
    pass''',
        test_cases=[{'input': {'a': [[1, 2], [3, 4]], 'b': [[5, 6], [7, 8]]}, 'expected': [[19, 22], [43, 50]]}],
        hints=['💡 İpucu 1: Boyutlar: a = m×n, b = n×p → sonuç m×p', '💡 İpucu 2: Üç iç içe döngü: i (satır a), j (sütun b), k (ortak boyut)', '💡 İpucu 3: C[i][j] += A[i][k] * B[k][j]'],
        explanation="""**Matris Çarpımı** sorusu, **Veri Yapilari** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** İki matrisi çarp (nokta çarpımı). numpy kullanma.

**Yaklaşım:**

```python
def matrix_multiply(a: list, b: list) -> list:
    # ...implementasyon...
```

**Kategori ipuçları (Veri Yapilari):**
- list bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Intermediate seviye mülakatlarda veri yapilari bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['list-dict', 'intermediate', 'interview'],
        related_question_ids=[1, 2],
        tags=['collections', 'list_dict', 'loops', 'intermediate'],
    ),
    Question(
        id=31,
        title='Stok Takibi',
        category='list-dict',
        level='beginner',
        description="""Bir mağazanın stok hareketlerini takip et.
Her hareket '+ürün:miktar' veya '-ürün:miktar' şeklinde.""",
        starter_code="""def track_inventory(movements: list) -> dict:
    # ['+elma:10', '-elma:3', '+armut:5'] -> {'elma':7,'armut':5}
    pass""",
        test_cases=[{'input': ['+elma:10', '-elma:3', '+armut:5'], 'expected': {'elma': 7, 'armut': 5}}, {'input': ['+kalem:100', '+kalem:50', '-kalem:30'], 'expected': {'kalem': 120}}],
        hints=["💡 İpucu 1: Her harekette sign = m[0], geri kalanını ':' ile böl.", "💡 İpucu 2: item, qty = m[1:].split(':'); qty = int(qty)", "💡 İpucu 3: sign=='+' ise ekle, '-' ise çıkar."],
        explanation="""**Stok Takibi** sorusu, **Veri Yapilari** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** Bir mağazanın stok hareketlerini takip et.

**Yaklaşım:**

```python
def track_inventory(movements: list) -> dict:
    # ...implementasyon...
```

**Kategori ipuçları (Veri Yapilari):**
- list bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Beginner seviye mülakatlarda veri yapilari bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['list-dict', 'beginner', 'interview'],
        related_question_ids=[1, 2],
        tags=['collections', 'list_dict', 'beginner', 'loops'],
    ),
    Question(
        id=32,
        title='Hareketli Ortalama',
        category='list-dict',
        level='beginner',
        description='''k elemanlı hareketli ortalama hesapla.
Yeterli eleman olmayan başlangıç pencerelerini atla.''',
        starter_code="""def moving_average(nums: list, k: int) -> list:
    # Her k'lı pencere için ortalamayı hesapla
    pass""",
        test_cases=[{'input': {'nums': [1, 2, 3, 4, 5], 'k': 3}, 'expected': [2.0, 3.0, 4.0]}, {'input': {'nums': [10, 20, 30, 40], 'k': 2}, 'expected': [15.0, 25.0, 35.0]}],
        hints=['💡 İpucu 1: range(k-1, len(nums)) ile kayan pencere için döngü kur.', '💡 İpucu 2: Her adımda dilim: nums[i-k+1:i+1]', "💡 İpucu 3: sum(window)/k ile ortalmayı hesapla ve result'a ekle."],
        explanation="""**Hareketli Ortalama** sorusu, **Veri Yapilari** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** k elemanlı hareketli ortalama hesapla.

**Yaklaşım:**

```python
def moving_average(nums: list, k: int) -> list:
    # ...implementasyon...
```

**Kategori ipuçları (Veri Yapilari):**
- list bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Beginner seviye mülakatlarda veri yapilari bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['list-dict', 'beginner', 'interview'],
        related_question_ids=[1, 2],
        tags=['collections', 'list_dict', 'beginner', 'loops'],
    ),
    Question(
        id=33,
        title='En Uzun Artan Alt Dizi',
        category='data-structures',
        level='intermediate',
        description='Bir dizideki en uzun sürekli artan alt dizinin uzunluğunu bul.',
        starter_code='''def longest_increasing_subsequence(nums: list) -> int:
    # Sürekli artan: her eleman bir öncekinden büyük
    pass''',
        test_cases=[{'input': [1, 3, 5, 4, 7], 'expected': 3}, {'input': [2, 2, 2, 2, 2], 'expected': 1}, {'input': [1, 2, 3, 4, 5], 'expected': 5}],
        hints=['💡 İpucu 1: current ve max_len sayaçları tut.', '💡 İpucu 2: nums[i] > nums[i-1] ise current += 1, değilse current = 1', '💡 İpucu 3: Her adımda max_len = max(max_len, current) güncelle.'],
        explanation="""**En Uzun Artan Alt Dizi** sorusu, **Veri Yapilari** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** Bir dizideki en uzun sürekli artan alt dizinin uzunluğunu bul.

**Yaklaşım:**

```python
def longest_increasing_subsequence(nums: list) -> int:
    # ...implementasyon...
```

**Kategori ipuçları (Veri Yapilari):**
- list bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Intermediate seviye mülakatlarda veri yapilari bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['list-dict', 'intermediate', 'interview'],
        related_question_ids=[1, 2],
        tags=['collections', 'list_dict', 'loops', 'intermediate'],
    ),
    Question(
        id=34,
        title='Fiyat Analizi',
        category='data-structures',
        level='beginner',
        description='''Ürün fiyatlarının bulunduğu bir sözlükten
min, max ve ortalama fiyatı döndür.''',
        starter_code="""def price_analysis(prices: dict) -> dict:
    # {'elma':5,'armut':8,'muz':3} -> {'min':3,'max':8,'avg':5.33}
    pass""",
        test_cases=[{'input': {'elma': 5, 'armut': 8, 'muz': 3}, 'expected': {'min': 3, 'max': 8, 'avg': 5.33}}],
        hints=['💡 İpucu 1: values = list(prices.values()) ile değerleri al.', '💡 İpucu 2: min(), max() ve sum()/len() ile istatistikleri hesapla.', '💡 İpucu 3: round(avg, 2) ile yuvarla.'],
        explanation="""**Fiyat Analizi** sorusu, **Veri Yapilari** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** Ürün fiyatlarının bulunduğu bir sözlükten

**Yaklaşım:**

```python
def price_analysis(prices: dict) -> dict:
    # ...implementasyon...
```

**Kategori ipuçları (Veri Yapilari):**
- list bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Beginner seviye mülakatlarda veri yapilari bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['list-dict', 'beginner', 'interview'],
        related_question_ids=[1, 2],
        tags=['collections', 'list_dict', 'beginner', 'loops'],
    ),
    Question(
        id=35,
        title='Kümülatif Toplam',
        category='data-structures',
        level='beginner',
        description='''Bir listenin kümülatif (birikimli) toplamını döndür.
[1,2,3,4] → [1,3,6,10]''',
        starter_code='''def cumulative_sum(nums: list) -> list:
    # Her eleman, o noktaya kadar olan toplam olmalı
    pass''',
        test_cases=[{'input': [1, 2, 3, 4], 'expected': [1, 3, 6, 10]}, {'input': [5, 5, 5, 5, 5], 'expected': [5, 10, 15, 20, 25]}],
        hints=['💡 İpucu 1: Döngü başında running_total = 0 tut.', "💡 İpucu 2: Her elemanda running_total += n, ardından result'a ekle.", '💡 İpucu 3: itertools.accumulate(nums) de aynı sonucu verir.'],
        explanation="""**Kümülatif Toplam** sorusu, **Veri Yapilari** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** Bir listenin kümülatif (birikimli) toplamını döndür.

**Yaklaşım:**

```python
def cumulative_sum(nums: list) -> list:
    # ...implementasyon...
```

**Kategori ipuçları (Veri Yapilari):**
- list bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Beginner seviye mülakatlarda veri yapilari bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['list-dict', 'beginner', 'interview'],
        related_question_ids=[1, 2],
        tags=['collections', 'list_dict', 'beginner', 'loops'],
    ),
    Question(
        id=36,
        title='Favori Renk Anketi',
        category='pandas',
        level='beginner',
        description='''Bir anket sonucu sözlüğü veriliyor. En popüler rengi bul.
(pandas kullanmadan, saf Python ile yap)''',
        starter_code='''def favorite_color(poll_data: dict) -> str:
    # poll_data = {"Ahmet": "Mavi", "Ayşe": "Kırmızı", ...}
    # En çok tekrar eden rengi döndür
    pass''',
        test_cases=[{'input': {'A': 'Mavi', 'B': 'Kırmızı', 'C': 'Mavi', 'D': 'Yeşil', 'E': 'Mavi'}, 'expected': 'Mavi'}, {'input': {'X': 'Siyah', 'Y': 'Siyah'}, 'expected': 'Siyah'}],
        hints=['💡 İpucu 1: Boş bir dict oluştur: counts = {}', '💡 İpucu 2: Her değer için counts[color] = counts.get(color, 0) + 1', '💡 İpucu 3: max(counts, key=counts.get) ile en yüksek frekanslıyı bul.'],
        explanation="""**Favori Renk Anketi** sorusu, **Veri Analizi** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** Bir anket sonucu sözlüğü veriliyor. En popüler rengi bul.

**Yaklaşım:**

```python
def favorite_color(poll_data: dict) -> str:
    # ...implementasyon...
```

**Kategori ipuçları (Veri Analizi):**
- DataFrame bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Beginner seviye mülakatlarda veri analizi bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['pandas', 'beginner', 'interview'],
        related_question_ids=[1, 2],
        tags=['dataframe', 'data_analysis', 'beginner', 'pandas'],
    ),
    Question(
        id=37,
        title='Eksik Değer Doldurma',
        category='pandas',
        level='beginner',
        description='''Bir sayı listesindeki None değerleri, listenin ortalamasıyla doldur.
(pandas kullanmadan, saf Python ile)''',
        starter_code='''def fill_missing(numbers: list) -> list:
    # [1, None, 3, None, 5] -> [1, 3.0, 3, 3.0, 5]
    pass''',
        test_cases=[{'input': [1, None, 3, None, 5], 'expected': [1, 3.0, 3, 3.0, 5]}, {'input': [10, None, 20], 'expected': [10, 15.0, 20]}],
        hints=['💡 İpucu 1: Önce sadece sayısal değerlerin ortalamasını hesapla.', '💡 İpucu 2: nums = [x for x in numbers if x is not None]', "💡 İpucu 3: Ortalama = sum(nums) / len(nums); sonra None'ları bu değerle değiştir."],
        explanation="""**Eksik Değer Doldurma** sorusu, **Veri Analizi** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** Bir sayı listesindeki None değerleri, listenin ortalamasıyla doldur.

**Yaklaşım:**

```python
def fill_missing(numbers: list) -> list:
    # ...implementasyon...
```

**Kategori ipuçları (Veri Analizi):**
- DataFrame bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Beginner seviye mülakatlarda veri analizi bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['pandas', 'beginner', 'interview'],
        related_question_ids=[1, 2],
        tags=['dataframe', 'data_analysis', 'beginner', 'pandas'],
    ),
    Question(
        id=38,
        title='Satış Raporu',
        category='pandas',
        level='beginner',
        description='Satış verisini ürün bazında grupla, toplam satışı hesapla ve en çok satan ürünü döndür.',
        starter_code="""def top_selling_product(sales_data: list) -> str:
    # [{'product':'A','amount':100}, ...] -> en çok satan ürün adı
    pass""",
        test_cases=[{'input': [{'product': 'A', 'amount': 100}, {'product': 'B', 'amount': 200}, {'product': 'A', 'amount': 150}], 'expected': 'A'}],
        hints=['💡 İpucu 1: Bir dict ile ürün → toplam satış tut: totals = {}', '💡 İpucu 2: Her kayıt için totals[product] = totals.get(product, 0) + amount', '💡 İpucu 3: max(totals, key=totals.get) ile en yüksek satışlı ürünü bul.'],
        explanation="""**Satış Raporu** sorusu, **Veri Analizi** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** Satış verisini ürün bazında grupla, toplam satışı hesapla ve en çok satan ürünü döndür.

**Yaklaşım:**

```python
def top_selling_product(sales_data: list) -> str:
    # ...implementasyon...
```

**Kategori ipuçları (Veri Analizi):**
- DataFrame bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Beginner seviye mülakatlarda veri analizi bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['pandas', 'beginner', 'interview'],
        related_question_ids=[1, 2],
        tags=['dataframe', 'data_analysis', 'beginner', 'pandas'],
    ),
    Question(
        id=39,
        title='Günlük Ortalama',
        category='pandas',
        level='intermediate',
        description='''Günlük veri sözlüğünden haftalık ortalama hesapla.
Her hafta 7 günlük gruplara böl ve ortalamasını al.''',
        starter_code="""def weekly_average(daily_data: dict) -> list:
    # {'2024-01-01': 10, '2024-01-02': 20, ...} -> [hafta1_ort, hafta2_ort, ...]
    pass""",
        test_cases=[{'input': {'d1': 10, 'd2': 20, 'd3': 30, 'd4': 40, 'd5': 50, 'd6': 60, 'd7': 70, 'd8': 80}, 'expected': [40.0, 80.0]}],
        hints=['💡 İpucu 1: Değerleri listeye al: values = list(daily_data.values())', "💡 İpucu 2: 7'şerlik gruplara böl: [values[i:i+7] for i in range(0, len(values), 7)]", '💡 İpucu 3: Her grubun ortalamasını al: sum(group)/len(group)'],
        explanation="""**Günlük Ortalama** sorusu, **Veri Analizi** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** Günlük veri sözlüğünden haftalık ortalama hesapla.

**Yaklaşım:**

```python
def weekly_average(daily_data: dict) -> list:
    # ...implementasyon...
```

**Kategori ipuçları (Veri Analizi):**
- DataFrame bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Intermediate seviye mülakatlarda veri analizi bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['pandas', 'intermediate', 'interview'],
        related_question_ids=[1, 2],
        tags=['dataframe', 'data_analysis', 'pandas', 'intermediate'],
    ),
    Question(
        id=40,
        title='Korelasyon Analizi',
        category='pandas',
        level='intermediate',
        description='''İki sayı listesi arasındaki Pearson korelasyonunu hesapla ve yorumla.
0.7+ güçlü, 0.4-0.7 orta, <0.4 zayıf.''',
        starter_code="""def correlation_analysis(x: list, y: list) -> dict:
    # {'correlation': float, 'strength': str} döndür
    pass""",
        test_cases=[{'input': {'x': [1, 2, 3, 4, 5], 'y': [2, 4, 6, 8, 10]}, 'expected': {'correlation': 1.0, 'strength': 'güçlü'}}, {'input': {'x': [1, 2, 3, 4, 5], 'y': [5, 4, 3, 2, 1]}, 'expected': {'correlation': -1.0, 'strength': 'güçlü'}}],
        hints=['💡 İpucu 1: Pearson formülü: r = Σ((xi-x̄)(yi-ȳ)) / √(Σ(xi-x̄)² · Σ(yi-ȳ)²)', '💡 İpucu 2: Önce x_bar = sum(x)/len(x), y_bar = sum(y)/len(y) hesapla.', "💡 İpucu 3: abs(r) >= 0.7 → 'güçlü', >= 0.4 → 'orta', else → 'zayıf'"],
        explanation="""**Korelasyon Analizi** sorusu, **Veri Analizi** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** İki sayı listesi arasındaki Pearson korelasyonunu hesapla ve yorumla.

**Yaklaşım:**

```python
def correlation_analysis(x: list, y: list) -> dict:
    # ...implementasyon...
```

**Kategori ipuçları (Veri Analizi):**
- DataFrame bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Intermediate seviye mülakatlarda veri analizi bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['pandas', 'intermediate', 'interview'],
        related_question_ids=[1, 2],
        tags=['dataframe', 'data_analysis', 'pandas', 'intermediate'],
    ),
    Question(
        id=41,
        title='Tekrar Eden Satırlar',
        category='pandas',
        level='beginner',
        description='''Bir listedeki tekrar eden öğeleri kaldır ve kaç tane kaldırıldığını döndür.
Sonuç: (temizlenmiş_liste, kaldırılan_sayısı)''',
        starter_code='''def remove_duplicates(items: list) -> list:
    # (temizlenmiş_liste, kaldırılan_sayısı) döndür
    pass''',
        test_cases=[{'input': [1, 2, 2, 3, 3, 3, 4], 'expected': [[1, 2, 3, 4], 3]}, {'input': ['a', 'b', 'a', 'c'], 'expected': [['a', 'b', 'c'], 1]}],
        hints=['💡 İpucu 1: seen = set() ile görülen öğeleri takip et.', '💡 İpucu 2: Her öğe için: if item not in seen → ekle, else → sayacı artır.', '💡 İpucu 3: Sonuç: [clean_list, removed_count]'],
        explanation="""**Tekrar Eden Satırlar** sorusu, **Veri Analizi** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** Bir listedeki tekrar eden öğeleri kaldır ve kaç tane kaldırıldığını döndür.

**Yaklaşım:**

```python
def remove_duplicates(items: list) -> list:
    # ...implementasyon...
```

**Kategori ipuçları (Veri Analizi):**
- DataFrame bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Beginner seviye mülakatlarda veri analizi bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['pandas', 'beginner', 'interview'],
        related_question_ids=[1, 2],
        tags=['dataframe', 'data_analysis', 'beginner', 'pandas'],
        tutorial_slug='python-pandas-tekrar-eden-satirlar',
    ),
    Question(
        id=42,
        title='Yaş Grubu Segmentasyonu',
        category='pandas',
        level='beginner',
        description="Yaş listesini gruplara ayır: 0-17 'Genç', 18-64 'Yetişkin', 65+ 'Yaşlı'.",
        starter_code="""def age_segment(ages: list) -> list:
    # [15, 25, 70, 5] -> ['Genç', 'Yetişkin', 'Yaşlı', 'Genç']
    pass""",
        test_cases=[{'input': [15, 25, 70, 5, 45], 'expected': ['Genç', 'Yetişkin', 'Yaşlı', 'Genç', 'Yetişkin']}],
        hints=['💡 İpucu 1: Her yaş için koşullu kontrol yap.', "💡 İpucu 2: if age <= 17: 'Genç', elif age <= 64: 'Yetişkin', else: 'Yaşlı'", '💡 İpucu 3: List comprehension kullan: [segment(a) for a in ages]'],
        explanation="""**Yaş Grubu Segmentasyonu** sorusu, **Veri Analizi** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** Yaş listesini gruplara ayır: 0-17 'Genç', 18-64 'Yetişkin', 65+ 'Yaşlı'.

**Yaklaşım:**

```python
def age_segment(ages: list) -> list:
    # ...implementasyon...
```

**Kategori ipuçları (Veri Analizi):**
- DataFrame bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Beginner seviye mülakatlarda veri analizi bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['pandas', 'beginner', 'interview'],
        related_question_ids=[1, 2],
        tags=['dataframe', 'data_analysis', 'beginner', 'pandas'],
    ),
    Question(
        id=43,
        title='Grup Toplamı',
        category='pandas',
        level='intermediate',
        description='''Satış verisinden bölge bazında toplam satışı hesapla.
Sonuç: {bölge: toplam_satış} sözlüğü''',
        starter_code="""def region_totals(sales: list) -> dict:
    # [{'region':'A','sales':100}, ...] -> {'A': 250, 'B': 150}
    pass""",
        test_cases=[{'input': [{'region': 'A', 'sales': 100}, {'region': 'B', 'sales': 50}, {'region': 'A', 'sales': 150}, {'region': 'B', 'sales': 100}], 'expected': {'A': 250, 'B': 150}}],
        hints=['💡 İpucu 1: Boş bir dict: totals = {}', '💡 İpucu 2: Her kayıt için totals[region] = totals.get(region, 0) + sales', "💡 İpucu 3: totals dict'ini döndür."],
        explanation="""**Grup Toplamı** sorusu, **Veri Analizi** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** Satış verisinden bölge bazında toplam satışı hesapla.

**Yaklaşım:**

```python
def region_totals(sales: list) -> dict:
    # ...implementasyon...
```

**Kategori ipuçları (Veri Analizi):**
- DataFrame bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Intermediate seviye mülakatlarda veri analizi bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['pandas', 'intermediate', 'interview'],
        related_question_ids=[1, 2],
        tags=['dataframe', 'data_analysis', 'pandas', 'intermediate'],
        tutorial_slug='python-pandas-grup-toplami',
    ),
    Question(
        id=44,
        title='Aykırı Değer Tespiti',
        category='pandas',
        level='intermediate',
        description='''IQR yöntemiyle aykırı değerleri tespit et.
Q1-1.5*IQR altındakiler veya Q3+1.5*IQR üstündekiler aykırıdır.
Sonuç: aykırı değerlerin indeks listesi.''',
        starter_code='''def detect_outliers(data: list) -> list:
    # Aykırı değerlerin indekslerini döndür
    pass''',
        test_cases=[{'input': [1, 2, 2, 3, 3, 3, 100], 'expected': [6]}, {'input': [10, 11, 12, 13, 14, 15], 'expected': []}],
        hints=['💡 İpucu 1: Sıralı listeden Q1 (25. yüzdelik) ve Q3 (75. yüzdelik) hesapla.', '💡 İpucu 2: IQR = Q3 - Q1; alt sınır = Q1 - 1.5*IQR, üst sınır = Q3 + 1.5*IQR', '💡 İpucu 3: [i for i, x in enumerate(data) if x < lower or x > upper]'],
        explanation="""**Aykırı Değer Tespiti** sorusu, **Veri Analizi** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** IQR yöntemiyle aykırı değerleri tespit et.

**Yaklaşım:**

```python
def detect_outliers(data: list) -> list:
    # ...implementasyon...
```

**Kategori ipuçları (Veri Analizi):**
- DataFrame bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Intermediate seviye mülakatlarda veri analizi bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['pandas', 'intermediate', 'interview'],
        related_question_ids=[1, 2],
        tags=['dataframe', 'data_analysis', 'pandas', 'intermediate'],
        tutorial_slug='python-pandas-aykiri-deger-tespiti',
    ),
    Question(
        id=45,
        title='Rolling Ortalama',
        category='pandas',
        level='intermediate',
        description='''k pencereli rolling (kayan) ortalama hesapla.
İlk k-1 değer için sonuç None olsun.''',
        starter_code='''def rolling_average(data: list, k: int) -> list:
    # k pencereli kayan ortalama
    pass''',
        test_cases=[{'input': {'data': [1, 2, 3, 4, 5], 'k': 3}, 'expected': [None, None, 2.0, 3.0, 4.0]}, {'input': {'data': [10, 20, 30, 40], 'k': 2}, 'expected': [None, 15.0, 25.0, 35.0]}],
        hints=['💡 İpucu 1: İlk k-1 değer için None döndür.', '💡 İpucu 2: i >= k-1 için: sum(data[i-k+1:i+1]) / k', '💡 İpucu 3: Sonuç listesi oluştur ve her adımda ekle.'],
        explanation="""**Rolling Ortalama** sorusu, **Veri Analizi** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** k pencereli rolling (kayan) ortalama hesapla.

**Yaklaşım:**

```python
def rolling_average(data: list, k: int) -> list:
    # ...implementasyon...
```

**Kategori ipuçları (Veri Analizi):**
- DataFrame bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Intermediate seviye mülakatlarda veri analizi bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['pandas', 'intermediate', 'interview'],
        related_question_ids=[1, 2],
        tags=['dataframe', 'data_analysis', 'pandas', 'intermediate'],
    ),
    Question(
        id=46,
        title='İkili Arama',
        category='algorithms',
        level='beginner',
        description='''Sıralı bir listede binary search ile hedef sayının indeksini döndür.
Bulunamazsa -1 döndür.''',
        starter_code='''def binary_search(arr: list, target: int) -> int:
    # O(log n) zaman karmaşıklığı hedefle
    pass''',
        test_cases=[{'input': {'arr': [1, 3, 5, 7, 9, 11], 'target': 7}, 'expected': 3}, {'input': {'arr': [1, 3, 5, 7, 9, 11], 'target': 6}, 'expected': -1}, {'input': {'arr': [1], 'target': 1}, 'expected': 0}],
        hints=['💡 İpucu 1: left=0, right=len(arr)-1 ile başla.', '💡 İpucu 2: mid = (left+right)//2; arr[mid]>target ise right=mid-1, küçükse left=mid+1', "💡 İpucu 3: arr[mid]==target ise mid'i döndür. Döngü biterse -1."],
        explanation="""**İkili Arama** sorusu, **Algoritmalar** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** Sıralı bir listede binary search ile hedef sayının indeksini döndür.

**Yaklaşım:**

```python
def binary_search(arr: list, target: int) -> int:
    # ...implementasyon...
```

**Kategori ipuçları (Algoritmalar):**
- arama bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Beginner seviye mülakatlarda algoritmalar bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['algorithms', 'beginner', 'interview'],
        related_question_ids=[1, 2],
        tags=['binary_search', 'algorithms', 'beginner'],
        tutorial_slug='python-algorithms-ikili-arama',
    ),
    Question(
        id=47,
        title='Bubble Sort',
        category='algorithms',
        level='beginner',
        description='''Bubble sort algoritmasıyla bir listeyi küçükten büyüğe sırala.
Orijinal listeyi değiştirme, kopyasını döndür.''',
        starter_code='''def bubble_sort(arr: list) -> list:
    # Her geçişte büyük elemanları sona taşı
    pass''',
        test_cases=[{'input': [64, 34, 25, 12, 22, 11, 90], 'expected': [11, 12, 22, 25, 34, 64, 90]}, {'input': [5, 1, 4, 2, 8], 'expected': [1, 2, 4, 5, 8]}],
        hints=['💡 İpucu 1: arr = arr[:] ile kopya al.', '💡 İpucu 2: İki iç içe döngü: dış n kez, iç komşuları karşılaştırır.', '💡 İpucu 3: arr[j] > arr[j+1] ise swap yap: arr[j], arr[j+1] = arr[j+1], arr[j]'],
        explanation="""**Bubble Sort** sorusu, **Algoritmalar** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** Bubble sort algoritmasıyla bir listeyi küçükten büyüğe sırala.

**Yaklaşım:**

```python
def bubble_sort(arr: list) -> list:
    # ...implementasyon...
```

**Kategori ipuçları (Algoritmalar):**
- arama bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Beginner seviye mülakatlarda algoritmalar bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['algorithms', 'beginner', 'interview'],
        related_question_ids=[1, 2],
        tags=['sorting', 'algorithms', 'beginner'],
    ),
    Question(
        id=68,
        title='İki Maaş Bordrosunu Birleştir',
        category='algorithms',
        level='intermediate',
        description='İK ekibindesin. Elinde iki bölümün maaş listesi var:\n  - mühendislik (azalan sırada, en yüksek maaş başta)\n  - pazarlama (artan sırada, en düşük maaş başta)\n\nİki listeyi **birleştirip tek maaş listesi** oluşturman lazım.\nSonuç azalan sırada olmalı (en yüksek maaş başta).\n\n📌 Önemli: Her iki girdi listesi de kendi içinde sıralı.\n   Bu sana avantaj sağlıyor — sıfırdan sıralama yapma.\n\n⚠️ sorted()/sort() KULLANMA. Mülakat sorusu olarak\n   O(n+m) yerine O(n log n) yazarsan eleniyorsun.\n\n💡 İpucu (gizli): İki sıralı listeyi tek sıralı liste yapmak için\n   klasik bir algoritma var — ismi "merge". İnternette\n   \'merge two sorted lists\' diye aratabilirsin ama önce kendin dene.',
        starter_code='''def merge_salaries(engineering: list, marketing: list) -> list:
    # İki sıralı listeyi birleştir, sonuç azalan sırada
    # engineering: azalan sırada (örn [12000, 9000, 8000])
    # marketing:  artan sırada  (örn [4000, 5000, 6500])
    # Sonuç: azalan sırada, tüm maaşlar
    pass''',
        test_cases=[{'input': ([12000, 9000, 8000], [4000, 5000, 6500]), 'expected': [12000, 9000, 8000, 6500, 5000, 4000]}, {'input': ([], [3000, 5000]), 'expected': [5000, 3000]}, {'input': ([10000, 5000], []), 'expected': [10000, 5000]}, {'input': ([], []), 'expected': []}, {'input': ([15000, 11000, 7000], [8500, 6000, 4000]), 'expected': [15000, 11000, 8500, 7000, 6000, 4000]}],
        hints=['💡 İpucu 1: İki pointer kullan — biri engineering, biri marketing için. İlk elemanları karşılaştır.', '💡 İpucu 2: Engineering azalan (büyük → küçük), marketing artan (küçük → büyük). Yani engineering[0] en büyük, marketing[0] en küçük.', '💡 İpucu 3: Hangisinin maaşı daha büyükse onu sonuca ekle, o pointer’ı ilerlet. Biri bitince diğerini olduğu gibi ekle.'],
        explanation='**Çözüm: Two-Pointer Merge (Klasik Merge Adımı)**\n\nBu soru merge sort algoritmasının temel parçasıdır:\n**"İki sıralı listeyi tek sıralı liste yap"**.\n\n```python\ndef merge_salaries(engineering, marketing):\n    result = []\n    i, j = 0, 0\n    while i < len(engineering) and j < len(marketing):\n        # engineering azalan (büyük başta), marketing artan (küçük başta)\n        # En büyük maaşı engineering[0] veya marketing[-1] tutar\n        if engineering[i] >= marketing[len(marketing) - 1 - j]:\n            result.append(engineering[i])\n            i += 1\n        else:\n            result.append(marketing[len(marketing) - 1 - j])\n            j += 1\n    # Kalanları olduğu gibi ekle\n    result.extend(engineering[i:])\n    result.extend(reversed(marketing[:len(marketing) - j]))\n    return result\n```\n\n**Daha temiz yaklaşım (iki listeyi aynı yöne çevir):**\n\n```python\ndef merge_salaries(engineering, marketing):\n    # engineering azalan, marketing artan → ikisini azalana çevir\n    m = sorted(marketing, reverse=True)  # sadece marketing için\n    # Artık ikisi de azalan sırada\n    result, i, j = [], 0, 0\n    while i < len(engineering) and j < len(m):\n        if engineering[i] >= m[j]:\n            result.append(engineering[i])\n            i += 1\n        else:\n            result.append(m[j])\n            j += 1\n    result.extend(engineering[i:])\n    result.extend(m[j:])\n    return result\n```\n\n**Karmaşıklık:**\n- Zaman: **O(n + m)** — her eleman bir kez ziyaret edilir\n- Alan: **O(n + m)** — sonuç listesi\n\n**Neden bu önemli?**\nBu "merge" adımı merge sort\'un (O(n log n)) temel taşıdır.\nEğer bu adımı sorted() ile yaparsan → O((n+m) log(n+m)) olur, mülakatta elenme sebebi.\n\n**Mülakat metaforu:**\n"İki klasörün sıralı sayfalarını tek masada birleştiriyorsun" — bu da aynı şey.',
        complexity='O(n+m) — iki sıralı listenin tek geçişte birleştirilmesi',
        related_concepts=['algorithms', 'intermediate', 'interview'],
        related_question_ids=[2, 3, 4],
        tags=['algorithms', 'intermediate'],
    ),
    Question(
        id=48,
        title='Bozuk Para Hesabı (Greedy)',
        category='algorithms',
        level='beginner',
        description='''Verilen miktarı en az sayıda bozuk para ile öde.
Kullanılabilir bozukluklar: [100,50,25,10,5,1] kuruş.''',
        starter_code='''def make_change(amount: int) -> dict:
    # {100:x, 50:y, ...} kaç tane hangi bozukluktan
    coins = [100, 50, 25, 10, 5, 1]
    pass''',
        test_cases=[{'input': 187, 'expected': {100: 1, 50: 1, 25: 1, 10: 1, 5: 0, 1: 2}}, {'input': 75, 'expected': {100: 0, 50: 1, 25: 1, 10: 0, 5: 0, 1: 0}}],
        hints=['💡 İpucu 1: Her bozukluk için: count = amount // coin', '💡 İpucu 2: amount = amount % coin ile kalanı güncelle.', '💡 İpucu 3: Sonuçları result[coin] = count olarak sakla.'],
        explanation="""**Bozuk Para Hesabı (Greedy)** sorusu, **Algoritmalar** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** Verilen miktarı en az sayıda bozuk para ile öde.

**Yaklaşım:**

```python
def make_change(amount: int) -> dict:
    # ...implementasyon...
```

**Kategori ipuçları (Algoritmalar):**
- arama bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Beginner seviye mülakatlarda algoritmalar bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['algorithms', 'beginner', 'interview'],
        related_question_ids=[1, 2],
        tags=['algorithms', 'beginner'],
    ),
    Question(
        id=49,
        title='Kaplama Problemi',
        category='algorithms',
        level='intermediate',
        description='''n merdiven basamağı var. Her adımda 1 veya 2 basamak çıkabilirsin.
Kaç farklı yol var? (Dinamik programlama)''',
        starter_code='''def climb_stairs(n: int) -> int:
    # DP ile çöz: dp[i] = dp[i-1] + dp[i-2]
    pass''',
        test_cases=[{'input': 2, 'expected': 2}, {'input': 3, 'expected': 3}, {'input': 5, 'expected': 8}],
        hints=['💡 İpucu 1: Bu aslında Fibonacci dizisi! dp[1]=1, dp[2]=2', '💡 İpucu 2: dp[i] = dp[i-1] + dp[i-2] (bir önceki veya iki önceki basamaktan gelir)', '💡 İpucu 3: Hafıza optimizasyonu için yalnızca son iki değeri tut.'],
        explanation="""**Kaplama Problemi** sorusu, **Algoritmalar** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** n merdiven basamağı var. Her adımda 1 veya 2 basamak çıkabilirsin.

**Yaklaşım:**

```python
def climb_stairs(n: int) -> int:
    # ...implementasyon...
```

**Kategori ipuçları (Algoritmalar):**
- arama bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Intermediate seviye mülakatlarda algoritmalar bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['algorithms', 'intermediate', 'interview'],
        related_question_ids=[1, 2],
        tags=['algorithms', 'intermediate'],
    ),
    Question(
        id=50,
        title='En Kısa Yol (BFS)',
        category='algorithms',
        level='intermediate',
        description="""Bir 2D grid'de (0=geçit, 1=duvar) baştan (0,0) hedefe (n-1,m-1) en kısa yol kaç adım?
Yol yoksa -1 döndür.""",
        starter_code='''def shortest_path(grid: list) -> int:
    # BFS ile en kısa yol
    pass''',
        test_cases=[{'input': [[0, 0, 0], [1, 1, 0], [0, 0, 0]], 'expected': 4}, {'input': [[0, 1], [1, 0]], 'expected': -1}],
        hints=['💡 İpucu 1: BFS için queue kullan: [(0,0,0)]  # (satır, sütun, adım)', '💡 İpucu 2: Ziyaret edilenleri takip et: visited = set(); visited.add((0,0))', '💡 İpucu 3: 4 yön: [(-1,0),(1,0),(0,-1),(0,1)]; sınır ve duvar kontrolü yap.'],
        explanation="""**En Kısa Yol (BFS)** sorusu, **Algoritmalar** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** Bir 2D grid'de (0=geçit, 1=duvar) baştan (0,0) hedefe (n-1,m-1) en kısa yol kaç adım?

**Yaklaşım:**

```python
def shortest_path(grid: list) -> int:
    # ...implementasyon...
```

**Kategori ipuçları (Algoritmalar):**
- arama bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Intermediate seviye mülakatlarda algoritmalar bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['algorithms', 'intermediate', 'interview'],
        related_question_ids=[1, 2, 3],
        tags=['bfs', 'algorithms', 'intermediate'],
    ),
    Question(
        id=70,
        title='En Yakın Rakam Toplamı',
        category='algorithms',
        level='intermediate',
        description='''Bir sayı dizisinde, toplamı hedef sayıya en yakın olan iki elemanı bul.
Birden fazla çözüm varsa, herhangi birini döndürmek yeterli.
Sonuç: [eleman1, eleman2] şeklinde liste döndür.
Örnek: [1, 2, 3, 4, 5], hedef = 8 → [3, 5] (toplam 8, tam isabet)
Örnek: [1, 2, 3, 4], hedef = 10 → [4, 4] veya [1, 4] (en yakın toplam 9)''',
        starter_code='''def find_closest_pair(numbers: list, target: int) -> list:
    # İki elemanın toplamı hedefe en yakın olsun
    pass''',
        test_cases=[{'input': {'numbers': [1, 2, 3, 4, 5], 'target': 8}, 'expected': [3, 5]}, {'input': {'numbers': [1, 2, 3, 4], 'target': 10}, 'expected': [4, 4]}, {'input': {'numbers': [3, 3, 3], 'target': 6}, 'expected': [3, 3]}, {'input': {'numbers': [-1, -2, -3, -4], 'target': -5}, 'expected': [-1, -4]}, {'input': {'numbers': [1, 5, 9, 13], 'target': 11}, 'expected': [-1, -1]}],
        hints=['💡 İpucu 1: Önce listeyi sırala (sıralanmış liste ile çalışmak daha kolay).', '💡 İpucu 2: İki işaretçi tekniği kullan — biri başta, biri sonda.', '💡 İpucu 3: current_sum = arr[left] + arr[right]; hedefe göre işaretçileri hareket ettir.'],
        explanation="""**En Yakın Rakam Toplamı** sorusu, **Algoritmalar** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** Bir sayı dizisinde, toplamı hedef sayıya en yakın olan iki elemanı bul.

**Yaklaşım:**

```python
def find_closest_pair(numbers: list, target: int) -> list:
    # ...implementasyon...
```

**Kategori ipuçları (Algoritmalar):**
- arama bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Intermediate seviye mülakatlarda algoritmalar bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['algorithms', 'intermediate', 'interview'],
        related_question_ids=[1, 2],
        tags=['algorithms', 'intermediate'],
    ),
    Question(
        id=71,
        title='Tekrarlanan Karakter Zinciri',
        category='algorithms',
        level='intermediate',
        description="""Bir string'de art arda tekrar eden karakterlerden oluşan
en uzun zinciri bul.
Sonuç: (karakter, zincir uzunluğu) şeklinde tuple döndür.
Örnek: 'aabbbcccddaaa' → ('b', 3) veya ('a', 3)
Örnek: 'abcdef' → ('a', 1) (tüm karakterler 1'er)""",
        starter_code='''def longest_char_chain(s: str) -> tuple:
    # Art arda tekrar eden en uzun zinciri bul
    pass''',
        test_cases=[{'input': 'aabbbcccddaaa', 'expected': ('b', 3)}, {'input': 'abcdef', 'expected': ('a', 1)}, {'input': 'aaaaa', 'expected': ('a', 5)}, {'input': 'abbaa', 'expected': ('a', 2)}, {'input': '', 'expected': ('', 0)}, {'input': 'abccdeeeffg', 'expected': ('e', 3)}],
        hints=['💡 İpucu 1: İki değişken tut: mevcut karakter ve mevcut sayı.', '💡 İpucu 2: Her yeni karakter için: aynıysa sayıyı artır, farklıysa sıfırla.', '💡 İpucu 3: En uzun zinciri ve karakterini takip et.'],
        explanation="""**Tekrarlanan Karakter Zinciri** sorusu, **Algoritmalar** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** Bir string'de art arda tekrar eden karakterlerden oluşan

**Yaklaşım:**

```python
def longest_char_chain(s: str) -> tuple:
    # ...implementasyon...
```

**Kategori ipuçları (Algoritmalar):**
- arama bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Intermediate seviye mülakatlarda algoritmalar bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['algorithms', 'intermediate', 'interview'],
        related_question_ids=[1, 2],
        tags=['algorithms', 'intermediate'],
    ),
    Question(
        id=72,
        title='Alt Dizi Toplam Kontrolü',
        category='algorithms',
        level='intermediate',
        description='''Bir sayı listesi ve bir hedef sayı veriliyor.
Listedeki herhangi bir alt dizinin (continuous subsequence)
toplamının hedef sayıya eşit olup olmadığını kontrol et.
⚠️ Tüm alt dizileri brute-force deneme O(n²) yapma.
Daha verimli bir yöntem düşün.''',
        starter_code='''def has_subarray_with_sum(nums: list, target: int) -> bool:
    # Alt dizi toplamı hedefe eşit mi?
    pass''',
        test_cases=[{'input': {'nums': [1, 4, 20, 3, 10, 5], 'target': 33}, 'expected': True}, {'input': {'nums': [1, 2, 3, 4], 'target': 15}, 'expected': False}, {'input': {'nums': [1, 2, 3], 'target': 6}, 'expected': True}, {'input': {'nums': [0, 0], 'target': 0}, 'expected': True}, {'input': {'nums': [-2, -1, 0, 1, 2], 'target': 0}, 'expected': True}],
        hints=['💡 İpucu 1: Sliding window tekniği düşün — başlangıç ve bitiş işaretçileri.', '💡 İpucu 2: Mevcut toplam hedefi aştıysa, başlangıcı kaydır.', '💡 İpucu 3: Negatif sayılar varsa sliding window çalışmaz — prefix sum + hashmap dene.'],
        explanation="""**Alt Dizi Toplam Kontrolü** sorusu, **Algoritmalar** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** Bir sayı listesi ve bir hedef sayı veriliyor.

**Yaklaşım:**

```python
def has_subarray_with_sum(nums: list, target: int) -> bool:
    # ...implementasyon...
```

**Kategori ipuçları (Algoritmalar):**
- arama bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Intermediate seviye mülakatlarda algoritmalar bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['algorithms', 'intermediate', 'interview'],
        related_question_ids=[1, 2],
        tags=['algorithms', 'intermediate'],
    ),
    Question(
        id=73,
        title='Benzersiz Alt Dizgi Sayısı',
        category='algorithms',
        level='intermediate',
        description="""Bir string'deki tüm benzersiz alt dizgilerin (substring)
sayısını bul.
Boş alt dizgi sayılmaz.
Örnek: 'abc' → 'a','b','c','ab','bc','abc' → 6
Örnek: 'aaa' → 'a','aa','aaa' → 2 (tekrarlar sayılmaz)
Örnek: '' → 0""",
        starter_code='''def count_unique_substrings(s: str) -> int:
    # Tüm benzersiz alt dizgilerin sayısını bul
    pass''',
        test_cases=[{'input': 'abc', 'expected': 6}, {'input': 'aaa', 'expected': 2}, {'input': '', 'expected': 0}, {'input': 'abcd', 'expected': 10}, {'input': 'aab', 'expected': 4}],
        hints=['💡 İpucu 1: Her karakterden başlayarak tüm alt dizgileri oluştur.', '💡 İpucu 2: Bir set() kullanarak benzersiz olanları sakla.', '💡 İpucu 3: İç içe döngü yerine, her i için j=i+1,...,len(s) alt dizgisini sete ekle.'],
        explanation="""**Benzersiz Alt Dizgi Sayısı** sorusu, **Algoritmalar** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** Bir string'deki tüm benzersiz alt dizgilerin (substring)

**Yaklaşım:**

```python
def count_unique_substrings(s: str) -> int:
    # ...implementasyon...
```

**Kategori ipuçları (Algoritmalar):**
- arama bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Intermediate seviye mülakatlarda algoritmalar bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['algorithms', 'intermediate', 'interview'],
        related_question_ids=[1, 2, 3],
        tags=['algorithms', 'intermediate'],
    ),
    Question(
        id=84,
        title='Cift Sayilari Filtrele ve Karelerini Topla',
        category='python-basics',
        level='beginner',
        description='''Bir sayi listesi var. Listedeki SADECE cift sayilarin karelerini al ve topla.
Tek sayilar yok sayilir (sadece ciftler).
Ornek: [2, 3, 4, 5, 6] -> 4+16+36 = 56''',
        starter_code='''def sum_of_even_squares(nums: list) -> int:
    # Listedeki cift sayilarin kareleri toplami
    pass''',
        test_cases=[{'input': [2, 3, 4, 5, 6], 'expected': 56}, {'input': [1, 3, 5, 7], 'expected': 0}, {'input': [10], 'expected': 100}, {'input': [], 'expected': 0}],
        hints=['💡 Ipucu 1: x % 2 == 0 ile cift sayilari filtrele.', '💡 Ipucu 2: sum() icinde generator expression kullan.', '💡 Ipucu 3: sum(x*x for x in nums if x % 2 == 0) tek satirda coz.'],
        explanation="""**İç içe döngü**, Python'un en temel yapılarından biridir. Bir döngü içinde başka bir döngü çalıştırmak, 2D veri yapıları (matris, tablo, satır-sütun) oluşturmak için idealdir.

**Problem:** n x n çarpım tablosu matrisi oluştur.

**Çözüm:**

```python
def carpim_tablosu(n: int) -> list:
    matris = []
    for i in range(1, n + 1):
        satir = []
        for j in range(1, n + 1):
            satir.append(i * j)
        matris.append(satir)
    return matris
```

**Liste comprehension ile tek satır:**

```python
def carpim_tablosu(n: int) -> list:
    return [[i * j for j in range(1, n + 1)] for i in range(1, n + 1)]
```

**Zaman/Bellek karmaşıklığı:** O(n²) — n arttıkça bellek ve süre karesel büyür.

**Gerçek hayat kullanımı:** Excel tabloları, oyun tahtaları (satranç, sudoku), piksel ızgaraları, sinema salonu koltuk seçimi.""",
        complexity='O(n²) zaman, O(n²) bellek',
        related_concepts=['iç içe döngü', 'matris', 'list comprehension', '2D array'],
        related_question_ids=[1, 2, 9, 12, 85, 86, 87, 88],
        tags=['beginner', 'python_basics'],
        tutorial_slug='python-degisken-nedir',
    ),
    Question(
        id=85,
        title='Iki String Arasindaki Ortak Karakterler',
        category='python-basics',
        level='beginner',
        description='Iki string veriliyor. Her iki stringde de GECEN (kucuk harf duyarsiz) benzersiz\nkarakterleri alfabetik sirada dondur.\nOrnek: "Merhaba" ve "Araba" -> [\'a\', \'r\'] (sirali)',
        starter_code='''def common_chars(a: str, b: str) -> list:
    # Iki stringde ortak olan benzersiz karakterler (kucuk harf), alfabetik sirali
    pass''',
        test_cases=[{'input': ['Merhaba', 'Araba'], 'expected': ['a', 'r']}, {'input': ['Python', 'Java'], 'expected': ['a']}, {'input': ['abc', 'def'], 'expected': []}, {'input': ['AAA', 'aaa'], 'expected': ['a']}],
        hints=['💡 Ipucu 1: set(a.lower()) & set(b.lower()) -> kesisim.', '💡 Ipucu 2: sorted() ile alfabetik siraya koy.', '💡 Ipucu 3: list(sorted(set(a.lower()) & set(b.lower()))) tek satir.'],
        explanation="""**Pisagor teoremi**, dik üçgenlerin temelidir. M.Ö. 6. yüzyılda Yunan filozof Pisagor tarafından formüle edilmiştir.

**Teorem:** Bir dik üçgende, dik açının karşısındaki kenarın (hipotenüs) karesi, diğer iki kenarın karelerinin toplamına eşittir.

```
a² + b² = c²
```

Burada:
- a, b: dik kenarlar
- c: hipotenüs (en uzun kenar)

**Python'da hesaplama:**

```python
import math

def hipotenus(a, b):
    # Negatif sayılar için mutlak değer
    a, b = abs(a), abs(b)
    # Pisagor: c = sqrt(a² + b²)
    return math.sqrt(a * a + b * b)
```

**Ünlü Pisagor üçlüleri:**
- (3, 4, 5) — en küçük
- (5, 12, 13)
- (8, 15, 17)
- (7, 24, 25)

**Kullanım alanları:** GPS mesafe hesaplama, mimari, bilgisayar grafikleri (2 nokta arası mesafe), oyun geliştirme.

**Alternatif:** `math.hypot(a, b)` aynı işi yapar ama edge case'leri (negatif sayılar) kendiniz handle etmeniz beklenir.""",
        complexity='O(1) zaman, O(1) bellek',
        related_concepts=['math.sqrt', 'pisagor teoremi', 'mutlak değer', 'math.hypot'],
        related_question_ids=[1, 5, 7, 12, 84, 86, 88],
        tags=['beginner', 'python_basics'],
        tutorial_slug='python-if-else-kosullar',
    ),
    Question(
        id=86,
        title='Listedeki En Sik Tekrar Eden Eleman',
        category='python-basics',
        level='beginner',
        description="""Bir liste var. En sik gecen elemani dondur.
Birden fazla esit siklik varsa en kucuk sayiyi veya alfabetik ilk olani dondur.
Ornek: [1, 3, 2, 3, 4, 1, 1] -> 1 (4 kez)
Ornek: ['a', 'b', 'a', 'c'] -> 'a' (2 kez, alfabetik ilk)""",
        starter_code='''def most_frequent(items: list) -> object:
    # En sik gecen eleman
    pass''',
        test_cases=[{'input': [1, 3, 2, 3, 4, 1, 1], 'expected': 1}, {'input': ['a', 'b', 'a', 'c'], 'expected': 'a'}, {'input': [5, 5, 3, 3, 1], 'expected': 3}, {'input': [1], 'expected': 1}],
        hints=['💡 Ipucu 1: from collections import Counter -> Counter(items).most_common().', '💡 Ipucu 2: max_count = max(c.values()) -> en yuksek frekans.', '💡 Ipucu 3: candidates = [k for k,v in c.items() if v == max_count]; min(candidates) ile coz.'],
        explanation="""**Sayıların rakamları toplamı**, mülakatlarda ve matematik olimpiyatlarında sıkça karşılaşılan klasik bir sorudur. Sayı tabanı dönüşümü, rakam sayısı bulma, basamak analizi gibi problemlerin temelidir.

**Problem:** Bir tam sayının tüm rakamlarını topla.

**Üç yaklaşım:**

```python
# 1. String'e çevir (önerilen)
def rakam_toplami(n):
    return sum(int(rakam) for rakam in str(abs(n)))

# 2. Matematiksel (mod 10)
def rakam_toplami(n):
    n = abs(n)
    toplam = 0
    while n > 0:
        toplam += n % 10  # son rakam
        n //= 10          # son rakamı at
    return toplam

# 3. Recursive
def rakam_toplami(n):
    n = abs(n)
    if n < 10:
        return n
    return (n % 10) + rakam_toplami(n // 10)
```

**Neden `abs(n)`?** Negatif sayılarda `-12345` → `'-12345'` string'inin `-` karakteri patlar.

**Performans:** Üçü de O(log₁₀ n) — çünkü n'in kaç rakamı varsa o kadar adım.

**İleri seviye:** Aynı toplamı tekrar tekrar uygularsan **digital root** bulursun. Örn: 12345 → 15 → 6 → 6 (1-9 arası tek rakam).""",
        complexity='O(log₁₀ n) zaman, O(1) bellek',
        related_concepts=['string conversion', 'modulo', 'while loop', 'digital root'],
        related_question_ids=[1, 3, 7, 84, 85, 87, 88],
        tags=['beginner', 'python_basics'],
        tutorial_slug='python-degisken-nedir',
    ),
    Question(
        id=87,
        title='Donen Dizi Kontrolu',
        category='python-basics',
        level='beginner',
        description="""Bir liste veriliyor. Liste dondurulmus (rotated) sirali mi kontrol et.
Donduerme: sirali bir diziyi herhangi bir noktadan kesip sona ekle. [3,4,5,1,2] sirali [1,2,3,4,5]'in
rotasyonudur (3 kesildi).
Tek elemanli liste her zaman True. Bos liste True.
Iki kez ayni eleman art arda olursa False (sirali degil).""",
        starter_code='''def is_rotated_sorted(nums: list) -> bool:
    # Liste dondurulerek sirali mi?
    pass''',
        test_cases=[{'input': [3, 4, 5, 1, 2], 'expected': True}, {'input': [1, 2, 3, 4, 5], 'expected': True}, {'input': [2, 1, 3], 'expected': False}, {'input': [1], 'expected': True}, {'input': [], 'expected': True}, {'input': [2, 2, 2, 2, 1, 2], 'expected': False}],
        hints=['💡 Ipucu 1: Sirali dizide en fazla 1 i var ki nums[i] > nums[i+1] olur (rotasyon noktasi).', '💡 Ipucu 2: count = sum(1 for i in range(n) if nums[i] > nums[(i+1)%n]).', '💡 Ipucu 3: count == 0 (zaten sirali) veya count == 1 (rotasyon) -> True.'],
        explanation='**String parçalama (split)**, metin işlemenin temelidir. NLP, veri temizleme, log analizi ve form işleme gibi her alanda karşına çıkar.\n\n**Problem:** Cümleyi kelimelerine ayır.\n\n**Çözüm:**\n\n```python\ndef cumleyi_kelimeye_ayir(cumle):\n    return cumle.split()  # bosluklara göre ayırır, fazla boslukları temizler\n```\n\n**`str.split()` metodu:**\n- `split()` (parantez boş): Tüm boşluk karakterlerini (space, tab, newline) splitter olarak kullanır ve ardışık splitter\'ları tek sayar.\n- `split(\' \')` (tek boşluk): Sadece tek boşluğa göre ayırır, fazla boşlukları korur.\n\n**Örnek:**\n\n```python\n"  ali   veli  ".split()      # → [\'ali\', \'veli\'] ✅\n"  ali   veli  ".split(\' \')   # → [\'\', \'\', \'ali\', \'\', \'\', \'veli\', \'\', \'\'] ❌\n```\n\n**Neden bu önemli?** Gerçek dünya verisi (kullanıcı girişi, log dosyaları, web scraping) neredeyse her zaman düzensizdir. `split()` ile güvenli parsing yaparsın.\n\n**İleri:** `re.split(r\'\\s+\', cumle.strip())` — regex ile aynı iş, ama `split()` yeterli.',
        complexity='O(n) zaman, O(n) bellek (n=cümle uzunluğu)',
        related_concepts=['str.split', 'string parsing', 'whitespace', 'text processing'],
        related_question_ids=[1, 3, 13, 14, 16, 86, 88],
        tags=['beginner', 'python_basics'],
        tutorial_slug='python-degisken-nedir',
    ),
    Question(
        id=88,
        title='Sayilari Toplami Hedefe Esit Olan Ciftler',
        category='algorithms',
        level='intermediate',
        description='''Bir liste ve bir hedef sayi var. Listedeki hangi iki sayinin toplami hedefe esit?
Tum benzersiz ciftleri (kucuk, buyuk) sirali liste olarak dondur.
Ayni eleman iki kez kullanilamaz.
Hic cift yoksa bos liste dondur.
Ornek: nums=[2,7,11,15], target=9 -> [[2,7]]''',
        starter_code="""def two_sum_pairs(nums: list, target: int) -> list:
    # Toplami target'a esit olan benzersiz ciftler
    pass""",
        test_cases=[{'input': ([2, 7, 11, 15], 9), 'expected': [[2, 7]]}, {'input': ([1, 5, 3, 7, 9], 12), 'expected': [[3, 9], [5, 7]]}, {'input': ([1, 2, 3], 10), 'expected': []}, {'input': ([3, 3], 6), 'expected': [[3, 3]]}, {'input': ([-1, -2, -3, 4, 5], 2), 'expected': [[-3, 5], [-1, 3]]}],
        hints=['💡 Ipucu 1: Set kullan: seen = set(). Her num icin target-num sette mi kontrol et.', '💡 Ipucu 2: pair = sorted([num, target-num]); result.add(tuple(pair)).', '💡 Ipucu 3: set() ile tekrarlari otomatik onle, sorted() ile sirala.'],
        explanation='**İndeksleme (indexing)**, Python string\'lerinin temelidir. Her karakter sıfırdan başlayan bir indekste durur.\n\n**Problem:** İlk ve son karakteri al, \'-\' ile birleştir.\n\n**Çözüm:**\n\n```python\ndef ilk_ve_son(s):\n    if not s:           # boş string kontrolü\n        return \'\'\n    return f\'{s[0]}-{s[-1]}\'  # ilk ve son karakter\n```\n\n**Python indeksleme kuralları:**\n- `s[0]` → ilk karakter\n- `s[-1]` → son karakter\n- `s[-2]` → sondan ikinci\n- Boş string\'de `s[0]` → IndexError! Bu yüzden kontrol gerekli.\n\n**f-string (formatted string literal):** Python 3.6+ ile geldi. `\'merhaba\'[0]` → `\'m\'`, `\'merhaba\'[-1]` → `\'a\'`. Birleştirilince `"m-a"`.\n\n**Kullanım alanları:** Kısaltma oluşturma (`"Ankara" → "A-a"`), ilk-son harf kontrolü (palindrome), dosya uzantısı kontrolü.\n\n**Tek karakterli edge case:** `"a"` → `"a-a"` (ilk ve son aynı). Negatif indeks bu yüzden güçlü — uzunluktan bağımsız.',
        complexity='O(1) zaman, O(1) bellek',
        related_concepts=['string indexing', 'negative index', 'f-string', 'edge case'],
        related_question_ids=[1, 3, 13, 86, 87],
        tags=['algorithms', 'intermediate'],
        tutorial_slug='python-degisken-nedir',
    ),
    Question(
        id=89,
        title='Rotasyon Adimini Bul',
        category='algorithms',
        level='intermediate',
        description="""Bir liste veriliyor. Bu liste sirali bir dizinin rotasyonu.
Rotasyon adimini bul (kac kez sola donduruldu).
[3,4,5,1,2] sirali [1,2,3,4,5]'in 3 sola rotasyonu -> 3 dondur.
Zaten sirali ise 0.
[1,2,3,4,5] -> 0
[5,1,2,3,4] -> 1 (sola)
Not: Rotasyon adimi 0 ile len(nums)-1 arasinda.""",
        starter_code='''def rotation_count(nums: list) -> int:
    # Sirali dizinin kac adim sola donduruldugunu bul
    pass''',
        test_cases=[{'input': [3, 4, 5, 1, 2], 'expected': 3}, {'input': [1, 2, 3, 4, 5], 'expected': 0}, {'input': [5, 1, 2, 3, 4], 'expected': 1}, {'input': [2, 3, 4, 5, 1], 'expected': 4}, {'input': [1], 'expected': 0}],
        hints=['💡 Ipucu 1: Minimum elemanin indexini bul.', '💡 Ipucu 2: min_idx = nums.index(min(nums)).', '💡 Ipucu 3: return min_idx (0 = zaten sirali, min_idx = kac adim sola).'],
        explanation="""**Rotasyon Adimini Bul** sorusu, **Algoritmalar** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** Bir liste veriliyor. Bu liste sirali bir dizinin rotasyonu.

**Yaklaşım:**

```python
def rotation_count(nums: list) -> int:
    # ...implementasyon...
```

**Kategori ipuçları (Algoritmalar):**
- arama bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Intermediate seviye mülakatlarda algoritmalar bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['algorithms', 'intermediate', 'interview'],
        related_question_ids=[1, 2],
        tags=['algorithms', 'intermediate'],
    ),
    Question(
        id=90,
        title="String'i Tersine Cevir (Kelime Bazli)",
        category='python-basics',
        level='intermediate',
        description="""Bir cumle var. Kelime sirasini tersine cevir, kelime icindeki harfler ayni kalsin.
Ornek: 'Merhaba dunya nasilsin' -> 'nasilsin dunya Merhaba'
Fazla bosluklari tek bosluga indir.""",
        starter_code='''def reverse_words(s: str) -> str:
    # Cumleyi kelime bazli tersine cevir
    pass''',
        test_cases=[{'input': 'Merhaba dunya nasilsin', 'expected': 'nasilsin dunya Merhaba'}, {'input': 'Python   harika  bir dil', 'expected': 'dil bir harika Python'}, {'input': 'tek', 'expected': 'tek'}, {'input': '', 'expected': ''}, {'input': '  bosluklu   cumle  ', 'expected': 'cumle bosluklu'}],
        hints=['💡 Ipucu 1: s.split() -> bosluklari otomatik normalize eder.', '💡 Ipucu 2: words[::-1] ile kelime listesini tersine cevir.', '💡 Ipucu 3: " ".join(words[::-1]) ile birlestir.'],
        explanation="""**String'i Tersine Cevir (Kelime Bazli)** sorusu, **String Islemleri** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** Bir cumle var. Kelime sirasini tersine cevir, kelime icindeki harfler ayni kalsin.

**Yaklaşım:**

```python
def reverse_words(s: str) -> str:
    # ...implementasyon...
```

**Kategori ipuçları (String Islemleri):**
- string method bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Intermediate seviye mülakatlarda string islemleri bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['strings', 'intermediate', 'interview'],
        related_question_ids=[1, 2],
        tags=['strings', 'string_methods', 'manipulation', 'intermediate'],
    ),
    Question(
        id=91,
        title='Liste Icinde Yinelenenleri Kaldir (Sirayi Koru)',
        category='python-basics',
        level='beginner',
        description='''Bir liste var. Listedeki tekrarlari kaldir, ilk gorunme sirasini koru.
Ornek: [1, 3, 2, 3, 4, 1, 5] -> [1, 3, 2, 4, 5] (3 ve 1 tekrari atlanir)''',
        starter_code='''def remove_duplicates(items: list) -> list:
    # Yinelenenleri kaldir, ilk gorunme sirasini koru
    pass''',
        test_cases=[{'input': [1, 3, 2, 3, 4, 1, 5], 'expected': [1, 3, 2, 4, 5]}, {'input': ['a', 'b', 'a', 'c', 'b'], 'expected': ['a', 'b', 'c']}, {'input': [1, 2, 3], 'expected': [1, 2, 3]}, {'input': [], 'expected': []}, {'input': [1, 1, 1], 'expected': [1]}],
        hints=['💡 Ipucu 1: seen = set() ile takip et.', '💡 Ipucu 2: if x not in seen: result.append(x); seen.add(x).', '💡 Ipucu 3: dict.fromkeys(items) ile tek satirda coz (Python 3.7+ dict sira korur).'],
        explanation="""**Liste Icinde Yinelenenleri Kaldir (Sirayi Koru)** sorusu, **Python Temelleri** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** Bir liste var. Listedeki tekrarlari kaldir, ilk gorunme sirasini koru.

**Yaklaşım:**

```python
def remove_duplicates(items: list) -> list:
    # ...implementasyon...
```

**Kategori ipuçları (Python Temelleri):**
- degisken bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Beginner seviye mülakatlarda python temelleri bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['python-basics', 'beginner', 'interview'],
        related_question_ids=[1, 2],
        tags=['beginner', 'python_basics'],
    ),
    Question(
        id=92,
        title='Matris Cevirme (Transpose Etme)',
        category='python-basics',
        level='beginner',
        description='''Bir 2D matris var. Satirlari sutun, sutunlari satir yap.
Ornek: [[1,2,3], [4,5,6]] -> [[1,4], [2,5], [3,6]]
Dikdortgen matrisler icin calissin (tum satirlar ayni uzunlukta).''',
        starter_code='''def transpose(matrix: list) -> list:
    # 2D matrisi transpoze et
    pass''',
        test_cases=[{'input': [[1, 2, 3], [4, 5, 6]], 'expected': [[1, 4], [2, 5], [3, 6]]}, {'input': [[1, 2], [3, 4], [5, 6]], 'expected': [[1, 3, 5], [2, 4, 6]]}, {'input': [[1]], 'expected': [[1]]}, {'input': [[1, 2, 3]], 'expected': [[1], [2], [3]]}],
        hints=['💡 Ipucu 1: zip(*matrix) ile transpoze et (Pythonic).', '💡 Ipucu 2: list(zip(*matrix)) tuple listesi doner, list(map(list, ...)) ile liste listesi yap.', '💡 Ipucu 3: Manuel: [[matrix[r][c] for r in range(len(matrix))] for c in range(len(matrix[0]))].'],
        explanation="""**Matris Cevirme (Transpose Etme)** sorusu, **Python Temelleri** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** Bir 2D matris var. Satirlari sutun, sutunlari satir yap.

**Yaklaşım:**

```python
def transpose(matrix: list) -> list:
    # ...implementasyon...
```

**Kategori ipuçları (Python Temelleri):**
- degisken bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Beginner seviye mülakatlarda python temelleri bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['python-basics', 'beginner', 'interview'],
        related_question_ids=[1, 2],
        tags=['beginner', 'python_basics'],
        tutorial_slug='python-python-basics-matris-cevirme-transpose-etme',
    ),
    Question(
        id=93,
        title='Ilk Tekrar Etmeyen Karakter',
        category='python-basics',
        level='intermediate',
        description="""Bir string veriliyor. Ilk kez tekrarlanMAYAN (unique) karakteri bul.
Yoksa bos string dondur.
Ornek: 'swiss' -> 'w' (s ve i tekrar eder, w sadece 1 kez)
Ornek: 'aabbcc' -> '' (hepsi tekrar)""",
        starter_code='''def first_unique_char(s: str) -> str:
    # Ilk tekrar etmeyen karakter
    pass''',
        test_cases=[{'input': 'swiss', 'expected': 'w'}, {'input': 'aabbcc', 'expected': ''}, {'input': 'programming', 'expected': 'p'}, {'input': 'aabb', 'expected': ''}, {'input': 'z', 'expected': 'z'}],
        hints=['💡 Ipucu 1: from collections import Counter -> c = Counter(s).', '💡 Ipucu 2: for ch in s: if c[ch] == 1: return ch.', "💡 Ipucu 3: Bos string icin '' dondur (return ch if any(c[ch]==1 for ch in s) else '')."],
        explanation="""**Ilk Tekrar Etmeyen Karakter** sorusu, **String Islemleri** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** Bir string veriliyor. Ilk kez tekrarlanMAYAN (unique) karakteri bul.

**Yaklaşım:**

```python
def first_unique_char(s: str) -> str:
    # ...implementasyon...
```

**Kategori ipuçları (String Islemleri):**
- string method bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Intermediate seviye mülakatlarda string islemleri bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['strings', 'intermediate', 'interview'],
        related_question_ids=[1, 2],
        tags=['strings', 'string_methods', 'manipulation', 'intermediate'],
    ),
    Question(
        id=94,
        title='Sirali Dizide Ilk ve Son Occurrence',
        category='algorithms',
        level='intermediate',
        description='''Sirali bir dizide target degerin ILK ve SON indeksini bul.
Yoksa [-1, -1] dondur.
find_first = lower bound, find_last = upper bound.
Ornek: nums=[5,7,7,8,8,10], target=8 -> [3, 4]
Ornek: nums=[5,7,7,8,8,10], target=6 -> [-1, -1]''',
        starter_code="""def search_range(nums: list, target: int) -> list:
    # Sirali dizide target'in ilk ve son indeksini bul
    # O(log n) zaman karmasikligi hedefle
    pass""",
        test_cases=[{'input': ([5, 7, 7, 8, 8, 10], 8), 'expected': [3, 4]}, {'input': ([5, 7, 7, 8, 8, 10], 6), 'expected': [-1, -1]}, {'input': ([], 0), 'expected': [-1, -1]}, {'input': ([1], 1), 'expected': [0, 0]}, {'input': ([1, 2, 3, 4, 5], 3), 'expected': [2, 2]}],
        hints=['💡 Ipucu 1: Iki binary search: biri lower bound, biri upper bound.', '💡 Ipucu 2: nums[mid] < target -> sol = mid + 1; degilse sag = mid.', '💡 Ipucu 3: Ilk occurrence icin >= target, son occurrence icin > target kullan.'],
        explanation="""**Sirali Dizide Ilk ve Son Occurrence** sorusu, **Algoritmalar** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** Sirali bir dizide target degerin ILK ve SON indeksini bul.

**Yaklaşım:**

```python
def search_range(nums: list, target: int) -> list:
    # ...implementasyon...
```

**Kategori ipuçları (Algoritmalar):**
- arama bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Intermediate seviye mülakatlarda algoritmalar bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['algorithms', 'intermediate', 'interview'],
        related_question_ids=[1, 2],
        tags=['algorithms', 'intermediate'],
        tutorial_slug='python-algorithms-sirali-dizide-ilk-ve-son-occurrence',
    ),
    Question(
        id=95,
        title='Dondurulmus Sirali Dizide Arama',
        category='algorithms',
        level='intermediate',
        description='''Dondurulmus (rotated) sirali bir dizide target degerini ara.
Dizi ornek: [4,5,6,7,0,1,2], target=0 -> 4 (indeks).
Yoksa -1 dondur.
O(log n) zaman karmasikligi hedefle (duz linear arama degil).''',
        starter_code="""def search_rotated(nums: list, target: int) -> int:
    # Dondurulmus sirali dizide target'i bul
    pass""",
        test_cases=[{'input': ([4, 5, 6, 7, 0, 1, 2], 0), 'expected': 4}, {'input': ([4, 5, 6, 7, 0, 1, 2], 3), 'expected': -1}, {'input': ([1], 0), 'expected': -1}, {'input': ([1, 3], 3), 'expected': 1}, {'input': ([5, 1, 3], 5), 'expected': 0}],
        hints=['💡 Ipucu 1: Her adimda bir yari SORTED (sol veya sag).', '💡 Ipucu 2: nums[low] <= nums[mid] ise sol yari sirali; kontrol et target sol aralikta mi.', '💡 Ipucu 3: Aksi halde sag yari sirali; kontrol et target sag aralikta mi.'],
        explanation="""**Dondurulmus Sirali Dizide Arama** sorusu, **Algoritmalar** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** Dondurulmus (rotated) sirali bir dizide target degerini ara.

**Yaklaşım:**

```python
def search_rotated(nums: list, target: int) -> int:
    # ...implementasyon...
```

**Kategori ipuçları (Algoritmalar):**
- arama bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Intermediate seviye mülakatlarda algoritmalar bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['algorithms', 'intermediate', 'interview'],
        related_question_ids=[1, 2],
        tags=['binary_search', 'algorithms', 'intermediate'],
    ),
    Question(
        id=96,
        title='Dizide En Yuksek Dag (Peak Element)',
        category='algorithms',
        level='intermediate',
        description='''Bir dizide peak element: nums[i-1] < nums[i] > nums[i+1].
Sadece komusuna bakarak (O(log n)) peak bul.
Birkac peak varsa herhangi birini dondur.
Dizi sinirlarinda -sonsuz kabul edilir (ilk ve son elemanlar her zaman peak olabilir).''',
        starter_code='''def find_peak(nums: list) -> int:
    # Binary search ile peak element bul
    pass''',
        test_cases=[{'input': [1, 2, 3, 1], 'expected': 2}, {'input': [1, 2, 1, 3, 5, 6, 4], 'expected': 5}, {'input': [1], 'expected': 0}, {'input': [1, 2], 'expected': 1}, {'input': [2, 1], 'expected': 0}],
        hints=['💡 Ipucu 1: nums[mid] < nums[mid+1] ise peak sag tarafta.', '💡 Ipucu 2: nums[mid] > nums[mid+1] ise peak sol tarafta (veya mid kendisi).', '💡 Ipucu 3: low < high dongusu kullan, return low.'],
        explanation="""**Dizide En Yuksek Dag (Peak Element)** sorusu, **Algoritmalar** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** Bir dizide peak element: nums[i-1] < nums[i] > nums[i+1].

**Yaklaşım:**

```python
def find_peak(nums: list) -> int:
    # ...implementasyon...
```

**Kategori ipuçları (Algoritmalar):**
- arama bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Intermediate seviye mülakatlarda algoritmalar bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['algorithms', 'intermediate', 'interview'],
        related_question_ids=[1, 2],
        tags=['algorithms', 'intermediate'],
    ),
    Question(
        id=97,
        title='Iki Isaretci ile Palindrom Kontrolu',
        category='algorithms',
        level='intermediate',
        description="""Bir string'in palindrom olup olmadigini iki isaretci ile kontrol et.
Alfabetik olmayan karakterleri (bosluk, noktalama, buyuk/kucuk harf) yok say.
Sadece alfanumerik karakterlere bak.
O(n) zaman, O(1) ek alan.""",
        starter_code='''def is_palindrome_two_pointer(s: str) -> bool:
    # Iki isaretci ile palindrom kontrolu (alfanumerik only)
    pass''',
        test_cases=[{'input': 'A man, a plan, a canal: Panama', 'expected': True}, {'input': 'race a car', 'expected': False}, {'input': ' ', 'expected': True}, {'input': 'No lemon, no melon', 'expected': True}, {'input': '12321', 'expected': True}],
        hints=['💡 Ipucu 1: left=0, right=len(s)-1 ile basla, iki uca isaretci koy.', '💡 Ipucu 2: Alfanumerik degilse skip et (s[left].isalnum()).', '💡 Ipucu 3: s[left].lower() != s[right].lower() ise False dondur.'],
        explanation="""**Iki Isaretci ile Palindrom Kontrolu** sorusu, **Algoritmalar** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** Bir string'in palindrom olup olmadigini iki isaretci ile kontrol et.

**Yaklaşım:**

```python
def is_palindrome_two_pointer(s: str) -> bool:
    # ...implementasyon...
```

**Kategori ipuçları (Algoritmalar):**
- arama bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Intermediate seviye mülakatlarda algoritmalar bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['algorithms', 'intermediate', 'interview'],
        related_question_ids=[1, 2],
        tags=['algorithms', 'intermediate'],
    ),
    Question(
        id=98,
        title='Sag ve Sol En Uzun Karaktersiz Alt Dizi',
        category='python-basics',
        level='intermediate',
        description="""Bir string var. En uzun benzersiz (tekrarsiz) karakter iceren alt dizinin uzunlugunu bul.
O(n) zaman karmasikligi hedefle (sliding window).
Ornek: 'abcabcbb' -> 3 ('abc')
Ornek: 'bbbbb' -> 1 ('b')
Ornek: 'pwwkew' -> 3 ('wke')""",
        starter_code='''def length_of_longest_substring(s: str) -> int:
    # En uzun tekrarsiz karakter alt dizisi
    pass''',
        test_cases=[{'input': 'abcabcbb', 'expected': 3}, {'input': 'bbbbb', 'expected': 1}, {'input': 'pwwkew', 'expected': 3}, {'input': '', 'expected': 0}, {'input': 'abcdef', 'expected': 6}],
        hints=['💡 Ipucu 1: Sliding window: left ve right isaretcileri, bir set ile tutulan karakterleri izle.', "💡 Ipucu 2: s[right] sette varsa, left'ten baslayarak setten cikar, left++.", '💡 Ipucu 3: Her adimda max(max_len, right - left + 1) guncelle.'],
        explanation="""**Sag ve Sol En Uzun Karaktersiz Alt Dizi** sorusu, **String Islemleri** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** Bir string var. En uzun benzersiz (tekrarsiz) karakter iceren alt dizinin uzunlugunu bul.

**Yaklaşım:**

```python
def length_of_longest_substring(s: str) -> int:
    # ...implementasyon...
```

**Kategori ipuçları (String Islemleri):**
- string method bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Intermediate seviye mülakatlarda string islemleri bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['strings', 'intermediate', 'interview'],
        related_question_ids=[1, 2],
        tags=['strings', 'string_methods', 'manipulation', 'intermediate'],
        tutorial_slug='python-strings-sag-ve-sol-en-uzun-karaktersiz-alt-dizi',
    ),
    Question(
        id=99,
        title='Iki Isaretci Ile Ters Ciftleri Say',
        category='algorithms',
        level='intermediate',
        description='''Bir dizide, dizideki elemanlarin toplami daha buyuk olan (ters) ciftleri say.
Ornek: [2, 4, 1, 3, 5] -> (4,1), (4,3), (5,1), (5,3) = 4 cift.
O(n log n) veya O(n) hedef.''',
        starter_code='''def count_inversions(nums: list) -> int:
    # Dizideki ters ciftlerin sayisi
    pass''',
        test_cases=[{'input': [2, 4, 1, 3, 5], 'expected': 3}, {'input': [5, 4, 3, 2, 1], 'expected': 10}, {'input': [1, 2, 3, 4, 5], 'expected': 0}, {'input': [1], 'expected': 0}, {'input': [], 'expected': 0}],
        hints=['💡 Ipucu 1: Merge sort yaklasimi - bol ve fethet.', '💡 Ipucu 2: Sayaci merge sirasinda artir: sol[i] > sag[j] ise count += len(sol) - i.', '💡 Ipucu 3: Daha basit O(n^2): her cifti kontrol et (ama yavas).'],
        explanation="""**Iki Isaretci Ile Ters Ciftleri Say** sorusu, **Algoritmalar** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** Bir dizide, dizideki elemanlarin toplami daha buyuk olan (ters) ciftleri say.

**Yaklaşım:**

```python
def count_inversions(nums: list) -> int:
    # ...implementasyon...
```

**Kategori ipuçları (Algoritmalar):**
- arama bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Intermediate seviye mülakatlarda algoritmalar bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['algorithms', 'intermediate', 'interview'],
        related_question_ids=[1, 2],
        tags=['algorithms', 'intermediate'],
    ),
    Question(
        id=100,
        title='En Sik K Eleman (Top K Frequent)',
        category='algorithms',
        level='intermediate',
        description='''Bir dizide en sik gecen K elemani bul.
Siralama onemli degil.
Ornek: nums=[1,1,1,2,2,3], k=2 -> [1, 2]
O(n log k) hedef.''',
        starter_code='''def top_k_frequent(nums: list, k: int) -> list:
    # En sik K eleman
    pass''',
        test_cases=[{'input': ([1, 1, 1, 2, 2, 3], 2), 'expected': [1, 2]}, {'input': ([1], 1), 'expected': [1]}, {'input': ([1, 2, 3, 4, 5], 5), 'expected': [1, 2, 3, 4, 5]}, {'input': ([4, 4, 4, 5, 5, 6], 1), 'expected': [4]}],
        hints=['💡 Ipucu 1: Counter ile frekanslari say.', '💡 Ipucu 2: most_common(k) -> tek satirda coz (heap altyapili).', '💡 Ipucu 3: Manuel heap: heappush/pop ile O(n log k).'],
        explanation="""**En Sik K Eleman (Top K Frequent)** sorusu, **Algoritmalar** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** Bir dizide en sik gecen K elemani bul.

**Yaklaşım:**

```python
def top_k_frequent(nums: list, k: int) -> list:
    # ...implementasyon...
```

**Kategori ipuçları (Algoritmalar):**
- arama bilgisi temel
- Tipik çözüm 5-15 satır Python kodu içerir
- Test senaryoları genelde 2-3 edge case içerir

**Neden bu soru:**
Intermediate seviye mülakatlarda algoritmalar bilgisi sınanır. Benzer sorular aynı kategoride komşu ID'lerde bulunur (related_question_ids).

**Pratik tavsiye:**
- Önce brute-force çöz, sonra optimize et
- Algoritma sorularında time complexity'yi düşün (O(n), O(n²), O(log n))
- Test case'leri dikkatle oku, edge case ipucu taşır""",
        complexity='O(n)',
        related_concepts=['algorithms', 'intermediate', 'interview'],
        related_question_ids=[1, 2],
        tags=['algorithms', 'intermediate'],
        tutorial_slug='python-algorithms-en-sik-k-eleman-top-k-frequent',
    ),
    Question(
        id=101,
        title='Iki Dizi Kesisimi (Set Ile)',
        category='algorithms',
        level='beginner',
        description='''Iki dizinin kesisimini (ortak elemanlar) dondur.
Tekrarlar olmasin, siralama onemli degil.
Ornek: nums1=[1,2,2,1], nums2=[2,2] -> [2]
O(n+m) zaman, O(n) ek alan.''',
        starter_code='''def intersection(nums1: list, nums2: list) -> list:
    # Iki dizinin kesisimi (benzersiz)
    pass''',
        test_cases=[{'input': ([1, 2, 2, 1], [2, 2]), 'expected': [2]}, {'input': ([4, 9, 5], [9, 4, 9, 8, 4]), 'expected': [9, 4]}, {'input': ([1, 2, 3], [4, 5, 6]), 'expected': []}, {'input': ([1, 1, 1], [1]), 'expected': [1]}],
        hints=['💡 Ipucu 1: set(nums1) & set(nums2) -> Pythonic cozum.', '💡 Ipucu 2: Kucuk diziyi sete cevir, buyuk diziyi iterate et.', '💡 Ipucu 3: Tekrarlari onle: result.append(x); seen.add(x) ile takip et.'],
        explanation='''Liste döndürme, en temel veri yapısı sorularındandır.

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

**Performans:** Tüm yaklaşımlar O(n). Slicing en hızlı çünkü C-level implementasyon.''',
        complexity='O(n)',
        related_concepts=['slicing', 'reversed', 'in-place', 'immutable vs mutable'],
        related_question_ids=[13, 102],
        tags=['algorithms', 'beginner'],
    ),
    Question(
        id=102,
        title='En Uzun Consecutive Sequence',
        category='algorithms',
        level='intermediate',
        description='''Bir dizideki en uzun ard arda gelen sayi dizisinin uzunlugunu bul.
O(n) zaman karmasikligi hedefle.
Ornek: [100, 4, 200, 1, 3, 2] -> 4 (1,2,3,4 dizisi)
Ornek: [0,3,7,2,5,8,4,6,0,1] -> 9 (0-8)''',
        starter_code='''def longest_consecutive(nums: list) -> int:
    # En uzun ard arda gelen sayi dizisi
    pass''',
        test_cases=[{'input': [100, 4, 200, 1, 3, 2], 'expected': 4}, {'input': [0, 3, 7, 2, 5, 8, 4, 6, 0, 1], 'expected': 9}, {'input': [], 'expected': 0}, {'input': [1, 2, 3, 4], 'expected': 4}, {'input': [10], 'expected': 1}],
        hints=['💡 Ipucu 1: Tum sayilari sete koy: num_set = set(nums).', '💡 Ipucu 2: Sadece dizi baslangici olan sayilari kontrol et: x-1 not in num_set.', '💡 Ipucu 3: Oradan baslayarak while x+1 in set: x+=1. count tut.'],
        explanation="""Sözlük birleştirme (merge), veri işlemede sık yapılan işlem.

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
        complexity='O(n + m)',
        related_concepts=['dict unpacking', 'union operatörü', 'merge', 'key collision'],
        related_question_ids=[103],
        tags=['algorithms', 'intermediate'],
    ),
    Question(
        id=103,
        title='Anagram Kontrolu (Hash Table)',
        category='algorithms',
        level='beginner',
        description="""Iki string'in anagram olup olmadigini kontrol et (harfler ayni, siralama farkli).
O(n) zaman hedefle (sorted O(n log n) daha yavas).
Ornek: 'anagram', 'nagaram' -> True
Ornek: 'listen', 'silent' -> True
Ornek: 'hello', 'world' -> False""",
        starter_code='''def is_anagram(s: str, t: str) -> bool:
    # Iki string anagram mi? (hash ile)
    pass''',
        test_cases=[{'input': ['anagram', 'nagaram'], 'expected': True}, {'input': ['listen', 'silent'], 'expected': True}, {'input': ['hello', 'world'], 'expected': False}, {'input': ['a', 'b'], 'expected': False}, {'input': ['', ''], 'expected': True}],
        hints=['💡 Ipucu 1: Counter ile frekans say: Counter(s) == Counter(t).', "💡 Ipucu 2: Manuel: 26 harflik dizi, s'de +1, t'de -1; hepsi 0 mi?", '💡 Ipucu 3: sorted(s) == sorted(t) ile kisa cozum (yavas ama basit).'],
        explanation="""Sözlük erişim güvenliği, Python'da **en sık yapılan hatanın** (KeyError) çözümüdür.

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
        complexity='O(1) ortalama',
        related_concepts=['dict.get', 'defaultdict', 'KeyError', 'try/except'],
        related_question_ids=[102],
        tags=['algorithms', 'beginner'],
    ),
    Question(
        id=110,
        title='Tekrarlayan Elemanları Bul',
        category='data-structures',
        level='beginner',
        description='''Bir koleksiyonda birden fazla geçen elemanları bulun.
Koleksiyon tipini sen seç: hangi yapı en verimli?''',
        starter_code='''def find_duplicates(items):
    # Birden fazla gecen elemanlari liste olarak dondur
    # Liste 1 kez, hangi elemanlar birden fazla geciyor?
    pass''',
        test_cases=[{'input': [1, 2, 3, 4, 2, 3, 5], 'expected': [2, 3]}, {'input': ['a', 'b', 'a', 'c', 'b'], 'expected': ['a', 'b']}, {'input': [1, 2, 3], 'expected': []}],
        hints=["💡 İpucu 1: Birden fazla geçen elemanları saymak için 'frekans' sayacı lazım.", '💡 İpucu 2: Counter veya dict.items() kullanabilirsin — hangisi daha okunur?', '💡 İpucu 3: count > 1 olanları filtreleyip liste yap.'],
        explanation='''**Tekrarlayan Elemanları Bul** sorusu, **Veri Yapilari** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** Bir koleksiyonda birden fazla geçen elemanları bulun.

**Beklenen yaklasim:**
- Yapıyı sen seç (list, dict, set, vs.) — karar senin.
- O(n) — dict ile tek geçiş

**Baglantili kavramlar:** dict, Counter, collections, frequency

**Mulakat notu:** Bu tip sorularda amac "dogru cevap" degil, senin hangi veri yapisini neden sectigin. Aciklamalarla birlikte sun. Mulakat yapıyoruz — kullanici karar versin!''',
        complexity='O(n) — dict ile tek geçiş',
        related_concepts=['dict', 'Counter', 'collections', 'frequency'],
        related_question_ids=[27, 28, 29],
        tags=['data_structures', 'beginner', 'interview'],
    ),
    Question(
        id=111,
        title='İki Listenin Kesişimi',
        category='data-structures',
        level='beginner',
        description='''İki koleksiyondaki ortak elemanları bul.
Performans senin kararın: O(n²) mi, O(n) mi?''',
        starter_code="""def intersection(a, b):
    # a ve b'de ORTAK olan elemanlari liste olarak dondur
    pass""",
        test_cases=[{'input': {'a': [1, 2, 3, 4], 'b': [3, 4, 5, 6]}, 'expected': [3, 4]}, {'input': {'a': ['x', 'y'], 'b': ['y', 'z']}, 'expected': ['y']}, {'input': {'a': [1, 2], 'b': [3, 4]}, 'expected': []}],
        hints=['💡 İpucu 1: İki döngü O(n*m). Daha hızlı yol: birini okumaya hazır yap.', '💡 İpucu 2: Hangi veri yapısı arama (lookup) için O(1)?', '💡 İpucu 3: set yapısı O(1) arama yapar. set(a) & set(b).'],
        explanation='''**İki Listenin Kesişimi** sorusu, **Veri Yapilari** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** İki koleksiyondaki ortak elemanları bul.

**Beklenen yaklasim:**
- Yapıyı sen seç (list, dict, set, vs.) — karar senin.
- O(n+m) — set kullanırsan

**Baglantili kavramlar:** set, intersection, membership test, O(1) lookup

**Mulakat notu:** Bu tip sorularda amac "dogru cevap" degil, senin hangi veri yapisini neden sectigin. Aciklamalarla birlikte sun. Mulakat yapıyoruz — kullanici karar versin!''',
        complexity='O(n+m) — set kullanırsan',
        related_concepts=['set', 'intersection', 'membership test', 'O(1) lookup'],
        related_question_ids=[29, 110, 26],
        tags=['data_structures', 'beginner', 'interview'],
    ),
    Question(
        id=112,
        title='En Sık Geçen Eleman',
        category='data-structures',
        level='beginner',
        description='''Bir koleksiyonda en çok geçen elemanı bul.
Birden fazla aynı frekansta varsa ilkini döndür.''',
        starter_code='''def most_frequent(items):
    # En cok gecen elemani dondur
    pass''',
        test_cases=[{'input': [1, 2, 3, 2, 4, 2, 5], 'expected': 2}, {'input': ['a', 'b', 'a', 'c'], 'expected': 'a'}, {'input': [1, 2], 'expected': 1}],
        hints=['💡 İpucu 1: Her elemanın frekansını tut.', '💡 İpucu 2: collections.Counter kullanabilirsin veya dict.', '💡 İpucu 3: counter.most_common(1) ile en sık olanı al.'],
        explanation='''**En Sık Geçen Eleman** sorusu, **Veri Yapilari** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** Bir koleksiyonda en çok geçen elemanı bul.

**Beklenen yaklasim:**
- Yapıyı sen seç (list, dict, set, vs.) — karar senin.
- O(n) — tek geçiş

**Baglantili kavramlar:** Counter, frequency, most_common

**Mulakat notu:** Bu tip sorularda amac "dogru cevap" degil, senin hangi veri yapisini neden sectigin. Aciklamalarla birlikte sun. Mulakat yapıyoruz — kullanici karar versin!''',
        complexity='O(n) — tek geçiş',
        related_concepts=['Counter', 'frequency', 'most_common'],
        related_question_ids=[110, 19],
        tags=['data_structures', 'beginner', 'interview'],
    ),
    Question(
        id=113,
        title='Stack ve Queue Simülasyonu',
        category='data-structures',
        level='intermediate',
        description="""FIFO (queue) ve LIFO (stack) davranışını tek fonksiyonla yönet.
'queue' modu: eklenenler baştan çıkar.
'stack' modu: eklenenler üstten çıkar.
İlk eleman None olduğunda None döndür.""",
        starter_code="""def container(mode='queue'):
    # mode='queue' ise FIFO, 'stack' ise LIFO calissin
    # icerideki yapıyı sen sec
    pass""",
        test_cases=[],
        hints=["💡 İpucu 1: Closure kullan — dıştaki 'storage' korunur.", "💡 İpucu 2: mode='queue' ise append/pop(0) veya collections.deque.", "💡 İpucu 3: mode='stack' ise append/pop()."],
        explanation='''**Stack ve Queue Simülasyonu** sorusu, **Veri Yapilari** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** FIFO (queue) ve LIFO (stack) davranışını tek fonksiyonla yönet.

**Beklenen yaklasim:**
- Yapıyı sen seç (list, dict, set, vs.) — karar senin.
- O(1) — deque ile her operasyon

**Baglantili kavramlar:** queue, stack, deque, FIFO, LIFO, closure

**Mulakat notu:** Bu tip sorularda amac "dogru cevap" degil, senin hangi veri yapisini neden sectigin. Aciklamalarla birlikte sun. Mulakat yapıyoruz — kullanici karar versin!''',
        complexity='O(1) — deque ile her operasyon',
        related_concepts=['queue', 'stack', 'deque', 'FIFO', 'LIFO', 'closure'],
        related_question_ids=[33, 32],
        tags=['data_structures', 'intermediate', 'interview'],
    ),
    Question(
        id=114,
        title='Otomatik Gruplama',
        category='data-structures',
        level='intermediate',
        description="""Çiftlerden (key, value) otomatik gruplanmış sözlük oluştur.
'A elma' ve 'A armut' → {'A': ['elma', 'armut']}""",
        starter_code='''def group_pairs(pairs):
    # pairs: [(key, value), ...] -> {key: [value list], ...}
    pass''',
        test_cases=[{'input': [('A', 'elma'), ('A', 'armut'), ('B', 'muz')], 'expected': {'A': ['elma', 'armut'], 'B': ['muz']}}, {'input': [('x', 1)], 'expected': {'x': [1]}}],
        hints=["💡 İpucu 1: Sıradan dict'te her key için önce kontrol gerekir (if x not in d).", '💡 İpucu 2: defaultdict(list) ile ilk erişimde boş liste oluşur.', "💡 İpucu 3: 'd[key].append(value)' ile direkt ekle."],
        explanation='''**Otomatik Gruplama** sorusu, **Veri Yapilari** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** Çiftlerden (key, value) otomatik gruplanmış sözlük oluştur.

**Beklenen yaklasim:**
- Yapıyı sen seç (list, dict, set, vs.) — karar senin.
- O(n)

**Baglantili kavramlar:** defaultdict, grouping, collections, dict

**Mulakat notu:** Bu tip sorularda amac "dogru cevap" degil, senin hangi veri yapisini neden sectigin. Aciklamalarla birlikte sun. Mulakat yapıyoruz — kullanici karar versin!''',
        complexity='O(n)',
        related_concepts=['defaultdict', 'grouping', 'collections', 'dict'],
        related_question_ids=[28, 27],
        tags=['data_structures', 'intermediate', 'interview'],
    ),
    Question(
        id=115,
        title='Düzleştirme (Tek Seviye)',
        category='data-structures',
        level='beginner',
        description='''İç içe 1 seviye listeyi düzleştir.
[[1,2], [3,4], [5]] → [1, 2, 3, 4, 5]
Hangi yol daha okunur?''',
        starter_code='''def flatten(nested):
    # nested: 2D liste -> 1D liste
    pass''',
        test_cases=[{'input': [[1, 2], [3, 4], [5]], 'expected': [1, 2, 3, 4, 5]}, {'input': [['a', 'b'], ['c']], 'expected': ['a', 'b', 'c']}],
        hints=['💡 İpucu 1: List comprehension ile iç içe döngü.', '💡 İpucu 2: functools.reduce + operator.add.', '💡 İpucu 3: itertools.chain.from_iterable(nested).'],
        explanation='''**Düzleştirme (Tek Seviye)** sorusu, **Veri Yapilari** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** İç içe 1 seviye listeyi düzleştir.

**Beklenen yaklasim:**
- Yapıyı sen seç (list, dict, set, vs.) — karar senin.
- O(n)

**Baglantili kavramlar:** itertools, chain, flatten, list comprehension

**Mulakat notu:** Bu tip sorularda amac "dogru cevap" degil, senin hangi veri yapisini neden sectigin. Aciklamalarla birlikte sun. Mulakat yapıyoruz — kullanici karar versin!''',
        complexity='O(n)',
        related_concepts=['itertools', 'chain', 'flatten', 'list comprehension'],
        related_question_ids=[114, 26],
        tags=['data_structures', 'beginner', 'interview'],
    ),
    Question(
        id=116,
        title='Lazy Üretici',
        category='data-structures',
        level='intermediate',
        description='''Bellek tasarrufu için generator (yield) kullan.
Tüm listeyi oluşturmadan tek tek üretir.
[0..N-1] → generator döndür, sum() ile tüketilebilir olmalı.''',
        starter_code="""def range_gen(n):
    # 0'dan n-1'e kadar sayilari veren bir generator
    pass""",
        test_cases=[{'input': 5, 'expected': [0, 1, 2, 3, 4]}, {'input': 0, 'expected': []}],
        hints=["💡 İpucu 1: 'def' içinde 'yield' yaz → otomatik generator olur.", '💡 İpucu 2: list(range_gen(5)) → [0, 1, 2, 3, 4]', '💡 İpucu 3: range() de generator döndürür, aynı mantık.'],
        explanation='''**Lazy Üretici** sorusu, **Veri Yapilari** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** Bellek tasarrufu için generator (yield) kullan.

**Beklenen yaklasim:**
- Yapıyı sen seç (list, dict, set, vs.) — karar senin.
- O(1) bellek — üretildikçe tüketilir

**Baglantili kavramlar:** generator, yield, lazy evaluation, iterator

**Mulakat notu:** Bu tip sorularda amac "dogru cevap" degil, senin hangi veri yapisini neden sectigin. Aciklamalarla birlikte sun. Mulakat yapıyoruz — kullanici karar versin!''',
        complexity='O(1) bellek — üretildikçe tüketilir',
        related_concepts=['generator', 'yield', 'lazy evaluation', 'iterator'],
        related_question_ids=[115, 117],
        tags=['data_structures', 'intermediate', 'interview'],
    ),
    Question(
        id=117,
        title='Sıralı Dizide Hızlı Arama',
        category='data-structures',
        level='intermediate',
        description='''Sıralı bir koleksiyonda belirli bir değeri hızlıca bul.
O(n) lineer arama yerine binary search düşün.
Varsa True, yoksa False döndür.''',
        starter_code='''def in_sorted(sorted_items, value):
    # sorted_items sirali, value ara, varsa True yoksa False
    pass''',
        test_cases=[{'input': {'sorted_items': [1, 3, 5, 7, 9], 'value': 5}, 'expected': True}, {'input': {'sorted_items': [1, 3, 5, 7, 9], 'value': 4}, 'expected': False}, {'input': {'sorted_items': [], 'value': 1}, 'expected': False}],
        hints=['💡 İpucu 1: Doğrusal arama O(n), binary search O(log n).', '💡 İpucu 2: İki işaretçi (sol, sağ), orta nokta bul.', '💡 İpucu 3: bisect modülü hazır binary search sağlar.'],
        explanation='''**Sıralı Dizide Hızlı Arama** sorusu, **Veri Yapilari** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** Sıralı bir koleksiyonda belirli bir değeri hızlıca bul.

**Beklenen yaklasim:**
- Yapıyı sen seç (list, dict, set, vs.) — karar senin.
- O(log n) — binary search

**Baglantili kavramlar:** binary search, bisect, two pointers, sorted

**Mulakat notu:** Bu tip sorularda amac "dogru cevap" degil, senin hangi veri yapisini neden sectigin. Aciklamalarla birlikte sun. Mulakat yapıyoruz — kullanici karar versin!''',
        complexity='O(log n) — binary search',
        related_concepts=['binary search', 'bisect', 'two pointers', 'sorted'],
        related_question_ids=[46, 16, 33],
        tags=['data_structures', 'intermediate', 'interview'],
    ),
    Question(
        id=118,
        title='Top-K En Küçük Eleman',
        category='data-structures',
        level='intermediate',
        description='''Bir koleksiyondaki en küçük K elemanı döndür.
Listeyi tam sıralama (O(n log n)) yapmadan çöz.''',
        starter_code='''def top_k_smallest(items, k):
    # En kucuk k elemani liste olarak dondur
    pass''',
        test_cases=[{'input': {'items': [5, 2, 8, 1, 9, 3], 'k': 3}, 'expected': [1, 2, 3]}, {'input': {'items': [10, 20, 5, 15], 'k': 2}, 'expected': [5, 10]}],
        hints=['💡 İpucu 1: sorted(items)[:k] basit ama O(n log n).', '💡 İpucu 2: heapq modülü heap (min-heap) verir.', '💡 İpucu 3: heapq.nsmallest(k, items) — O(n log k).'],
        explanation='''**Top-K En Küçük Eleman** sorusu, **Veri Yapilari** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** Bir koleksiyondaki en küçük K elemanı döndür.

**Beklenen yaklasim:**
- Yapıyı sen seç (list, dict, set, vs.) — karar senin.
- O(n log k) — heap ile

**Baglantili kavramlar:** heapq, priority queue, heap, top-k

**Mulakat notu:** Bu tip sorularda amac "dogru cevap" degil, senin hangi veri yapisini neden sectigin. Aciklamalarla birlikte sun. Mulakat yapıyoruz — kullanici karar versin!''',
        complexity='O(n log k) — heap ile',
        related_concepts=['heapq', 'priority queue', 'heap', 'top-k'],
        related_question_ids=[100, 117, 33],
        tags=['data_structures', 'intermediate', 'interview'],
    ),
    Question(
        id=119,
        title='Kelime Frekansı',
        category='data-structures',
        level='beginner',
        description='''Bir metindeki kelime frekanslarını dict olarak döndür.
Noktalama ve büyük/küçük harf duyarlı olmasın.''',
        starter_code='''def word_frequency(text):
    # text -> {kelime: tekrar_sayisi, ...}
    pass''',
        test_cases=[{'input': 'Python çok güzel. Python mülakat için.', 'expected': {'python': 2, 'çok': 1, 'güzel': 1, 'mülakat': 1, 'için': 1}}],
        hints=['💡 İpucu 1: .lower() ve regex ile kelimeleri ayır.', '💡 İpucu 2: Counter kullan — en kısa yol.', '💡 İpucu 3: dict.items() ile manual sayım da olur.'],
        explanation='''**Kelime Frekansı** sorusu, **Veri Yapilari** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** Bir metindeki kelime frekanslarını dict olarak döndür.

**Beklenen yaklasim:**
- Yapıyı sen seç (list, dict, set, vs.) — karar senin.
- O(n)

**Baglantili kavramlar:** Counter, regex, frequency

**Mulakat notu:** Bu tip sorularda amac "dogru cevap" degil, senin hangi veri yapisini neden sectigin. Aciklamalarla birlikte sun. Mulakat yapıyoruz — kullanici karar versin!''',
        complexity='O(n)',
        related_concepts=['Counter', 'regex', 'frequency'],
        related_question_ids=[112, 19],
        tags=['data_structures', 'beginner', 'interview'],
    ),
    Question(
        id=120,
        title='Zip ile Ters Çevirme',
        category='data-structures',
        level='beginner',
        description="""Aynı uzunluktaki birden fazla listeyi tek bir liste oluştur.
Liste-içinde-liste yap.
[(1, 'a', 'x'), (2, 'b', 'y')] döndürecek yapıyı oluştur.""",
        starter_code='''def cols_to_rows(*columns):
    # Birden fazla listeyi satir listesi yaparak dondur
    pass''',
        test_cases=[{'input': [[1, 2, 3], ['a', 'b', 'c']], 'expected': [[1, 'a'], [2, 'b'], [3, 'c']]}, {'input': [[1, 2], [3, 4], [5, 6]], 'expected': [[1, 3, 5], [2, 4, 6]]}],
        hints=["💡 İpucu 1: zip(*columns) sihirli bir araç — 'unpacking' yapısı.", '💡 İpucu 2: list(zip(*columns)) her satır tuple verir.', '💡 İpucu 3: list içinde [list(row) for row in zip(*columns)] ile düzleştir.'],
        explanation='''**Zip ile Ters Çevirme** sorusu, **Veri Yapilari** kategorisinde **beginner** seviye bir mülakat sorusudur.

**Problem:** Aynı uzunluktaki birden fazla listeyi tek bir liste oluştur.

**Beklenen yaklasim:**
- Yapıyı sen seç (list, dict, set, vs.) — karar senin.
- O(n)

**Baglantili kavramlar:** zip, unpacking, transpose

**Mulakat notu:** Bu tip sorularda amac "dogru cevap" degil, senin hangi veri yapisini neden sectigin. Aciklamalarla birlikte sun. Mulakat yapıyoruz — kullanici karar versin!''',
        complexity='O(n)',
        related_concepts=['zip', 'unpacking', 'transpose'],
        related_question_ids=[115, 30],
        tags=['data_structures', 'beginner', 'interview'],
    ),
    Question(
        id=121,
        title='Çoklu Anahtara Göre Sıralama',
        category='data-structures',
        level='intermediate',
        description='''Bir sözlük listesini çoklu anahtara göre sırala.
Önce yaşa göre artan, sonra ada göre alfabetik.
Yapıyı sen seç.''',
        starter_code="""def sort_people(people):
    # people: [{'name', 'age', 'salary'}, ...]
    # yasa gore artan, ayni yasta isme gore sirali liste dondur
    pass""",
        test_cases=[{'input': [{'name': 'Ali', 'age': 30}, {'name': 'Ayşe', 'age': 25}, {'name': 'Mehmet', 'age': 30}, {'name': 'Ayşe', 'age': 25}], 'expected': [{'name': 'Ayşe', 'age': 25}, {'name': 'Ayşe', 'age': 25}, {'name': 'Ali', 'age': 30}, {'name': 'Mehmet', 'age': 30}]}],
        hints=["💡 İpucu 1: sorted()'da key parametresi tuple döndürebilir.", "💡 İpucu 2: key=lambda p: (p['age'], p['name']) önce age, sonra name sıralar.", '💡 İpucu 3: reverse=True ile azalan sıralama yapılabilir.'],
        explanation='''**Çoklu Anahtara Göre Sıralama** sorusu, **Veri Yapilari** kategorisinde **intermediate** seviye bir mülakat sorusudur.

**Problem:** Bir sözlük listesini çoklu anahtara göre sırala.

**Beklenen yaklasim:**
- Yapıyı sen seç (list, dict, set, vs.) — karar senin.
- O(n log n) — sorting

**Baglantili kavramlar:** sorted, tuple comparison, multi-key sort, lambda

**Mulakat notu:** Bu tip sorularda amac "dogru cevap" degil, senin hangi veri yapisini neden sectigin. Aciklamalarla birlikte sun. Mulakat yapıyoruz — kullanici karar versin!''',
        complexity='O(n log n) — sorting',
        related_concepts=['sorted', 'tuple comparison', 'multi-key sort', 'lambda'],
        related_question_ids=[33, 28, 110],
        tags=['data_structures', 'intermediate', 'interview'],
    ),
]
