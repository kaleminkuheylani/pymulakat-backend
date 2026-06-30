"""Her soruya SEO-friendly Türkçe açıklama, complexity, related_concepts ve related_question_ids ekler.

Bu modül QUESTIONS listesini mutate eder. İlk import'tan sonra çağrılmalı.
"""

from data.QUESTIONS import QUESTIONS

# Her soru için SEO içeriği: (id) -> { explanation, complexity, related_concepts, related_question_ids, tutorial_slug }
SEO_DATA = {
    # ═══ PYTHON BASICS ═══
    1: {
        "explanation": """Palindrome kontrolü, **string manipülasyonu** sorularının klasiğidir. Python'da üç temel yaklaşım var:

1. **String slicing ile ters çevirme** — `text[::-1]` en kısa yol.
2. **İki pointer tekniği** — Baştan ve sondan karşılaştırarak O(1) ek bellek.
3. **Manuel karşılaştırma** — `re.sub()` ile sadece alfanumerik karakterleri bırak, sonra `lower()` ile normalize et.

**Sıralama önemli:** Önce string'i temizle (noktalama, boşluk kaldır), sonra büyük/küçük harf normalizasyonu yap, en son karşılaştır.

Bu soru genellikle **Junior Python mülakatlarında** sorulur ve string metotlarına hakimiyetinizi ölçer. Gerçek dünyada veri temizleme (data cleaning) görevlerinde sıkça karşılaşılan bir pattern.""",
        "complexity": "O(n) zaman, O(n) bellek",
        "related_concepts": ["string", "slicing", "regex", "string metotları", "veri temizleme"],
        "related_question_ids": [3, 51, 52],
        "tutorial_slug": "python-palindrome-cozum",
    },
    2: {
        "explanation": """**FizzBuzz** programlama dünyasının "Hello World"üdür — hemen her mülakat sorulur.

Algoritmanın **3 kuralı**:
- 3'e bölünürse → "Fizz🎉"
- 5'e bölünürse → "Buzz🚀"
- İkisine de bölünürse → "FizzBuzz🎊"

**Kritik detay:** Sıra önemli! Önce **en spesifik** durumu kontrol et (FizzBuzz), sonra genel olanları. `if/elif/else` zincirinde sıra değişirse sonuçlar yanlış olur.

Modulo operatörü (`%`) burada anahtar. Python'da `i % 3 == 0` hem 0 hem de negatif sayılarda doğru çalışır.

Bu soru **Junior ve staj mülakatlarında** en sık çıkan algoritmadır. Şirketler adayın temel kontrol yapılarını (if/else, for loop, modulo) anlayıp anlamadığını test eder.""",
        "complexity": "O(n) zaman, O(1) ek bellek",
        "related_concepts": ["modulo operatörü", "kontrol yapıları", "string formatting", "döngüler"],
        "related_question_ids": [1, 4, 6],
        "tutorial_slug": "python-fizzbuzz-algoritma",
    },
    3: {
        "explanation": """**En uzun kelime bulma** sorusu, Python'da string + liste operasyonlarına hakimiyeti ölçer.

**İki yaklaşım:**
1. **`max()` + `key=len`** → `max(words, key=len)` tek satırda çözer.
2. **Manuel döngü** → uzunluk takip ederek ilerle.

**Detay:** `split()` metodu varsayılan olarak **boşluk** ile ayırır. Eğer soruda noktalama varsa (`"Merhaba, dünya!"`), önce regex ile temizlemek gerekir.

**Edge case'ler:**
- Boş string → `[]` dönmeli
- Tek kelime → o kelime
- Aynı uzunlukta birden fazla → ilkini döndür (`max()` doğal olarak bunu yapar).

Bu soru genellikle **orta seviye Python developer pozisyonlarında** sorulur ve `lambda`, `max()`, `sorted()` gibi fonksiyonel programlama bilgisini test eder.""",
        "complexity": "O(n) zaman, O(1) ek bellek",
        "related_concepts": ["string split", "max fonksiyonu", "lambda", "liste comprehension"],
        "related_question_ids": [1, 51],
        "tutorial_slug": None,
    },
    4: {
        "explanation": """**Sihirli kare (magic square)**, 3x3 matrisin satır, sütun ve çapraz toplamlarının eşit olup olmadığını kontrol eder.

**Algoritma:**
1. **Hızlı kontrol:** Ortanca (1,1) değeri 5 olmalı (1-9 toplamı = 45, /3 satır = 15, ortanca 5).
2. **Tam kontrol:** 8 satır/sütun/çapraz için toplam hesapla, hepsi eşit mi bak.

**Optimizasyon:** Python'da `sum()` ve `zip()` kullanarak **iç içe döngüyü** tek satıra indirgeyebilirsin. `all()` ile kısa devre (short-circuit) yapabilirsin.

**Bu algoritma nerede kullanılır:** Matris işleme, oyun geliştirme (özellikle bulmaca oyunları), veri bilimi (pandas DataFrame kontrolleri).""",
        "complexity": "O(n²) zaman, O(1) bellek (sabit 3x3 matris)",
        "related_concepts": ["iç içe liste", "zip fonksiyonu", "all fonksiyonu", "matris operasyonları"],
        "related_question_ids": [5, 15],
        "tutorial_slug": None,
    },
    5: {
        "explanation": """**Sayı tahmin oyunu**, kullanıcı deneyimi (UX) ve oyun mantığını birleştiren bir sorudur.

**Temel mantık:**
- Bilgisayar rastgele sayı seçer (`random.randint(1, 100)`).
- Kullanıcı tahmin eder, geri bildirim verilir ("daha büyük" / "daha küçük").
- Tahmin sayısı ve süre puanlanır.

**İleri seviye:** Score hesabı **zaman + deneme sayısı**'na göre yapılabilir. Binary search stratejisi kullanan bir oyuncu en yüksek skoru alır.

**Python özellikleri:**
- `random` modülü
- `input()` ile kullanıcı girdisi (her zaman `str` döner, `int()` ile çevirmek gerekir)
- `while` döngüsü veya özyinelemeli fonksiyon""",
        "complexity": "O(log n) en iyi, O(n) en kötü (kullanıcı stratejisine bağlı)",
        "related_concepts": ["random modülü", "input/output", "oyun döngüsü", "binary search"],
        "related_question_ids": [6, 14],
        "tutorial_slug": None,
    },
    6: {
        "explanation": """**Karakter sayacı**, `collections.Counter` veya `dict` kullanımını ölçer.

**Üç yaklaşım:**
1. **`Counter`** → `Counter(text)` en kısa ve en hızlı yol.
2. **`dict.get(key, 0) + 1`** → Manuel sayaç.
3. **`defaultdict(int)`** → İlk yaklaşıma benzer ama daha okunabilir.

**Performans:** Çok büyük string'lerde (örneğin 1MB metin) `Counter` C implementasyonu sayesinde en hızlıdır.

**Gerçek dünya:** Karakter sıklığı analizi, şifre gücü kontrolü, doğal dil işleme (NLP), kriptografi.""",
        "complexity": "O(n) zaman, O(k) bellek (k = unique karakter sayısı)",
        "related_concepts": ["collections.Counter", "defaultdict", "dict get", "karakter sıklığı"],
        "related_question_ids": [7, 51],
        "tutorial_slug": None,
    },
    7: {
        "explanation": """**Anagram kontrolü**, iki string'in aynı harfleri aynı sayıda içerip içermediğini kontrol eder.

**İki yaklaşım:**
1. **`Counter`** ile — `Counter(s1) == Counter(s2)`, O(n) süre.
2. **Sıralama** ile — `sorted(s1) == sorted(s2)`, O(n log n) süre ama daha basit.

**Edge case:** Boşluk ve büyük/küçük harf duyarlılığı önemli. Önce `replace(" ", "").lower()` ile normalize et.

**Kullanım alanları:** Kelime oyunları (Scrabble), biyoinformatik (DNA dizilimleri), şifreleme, kelime bulmaca çözücüleri.""",
        "complexity": "O(n) Counter ile, O(n log n) sıralama ile",
        "related_concepts": ["collections.Counter", "sorted", "anagram", "string normalize"],
        "related_question_ids": [1, 6, 51],
        "tutorial_slug": None,
    },
    8: {
        "explanation": """**Rakam toplamı**, özyinelemeli (recursive) düşünceyi ölçer.

**İki yaklaşım:**
1. **Özyinelemeli:** `n % 10 + sum_of_digits(n // 10)`, base case `n == 0`.
2. **Iteratif:** `while n > 0: total += n % 10; n //= 10`.

**Özyinelemeli yaklaşım daha okunabilir ama** Python'da recursion limiti var (default 1000). Çok büyük sayılar için iteratif tercih edilir.

**Bonus:** Negatif sayılar için `abs(n)` veya sign'i korumak.

**Gerçek dünya:** Sayı doğrulama (Luhn algoritması), vergi hesaplama, dijital kök (digital root) hesaplama.""",
        "complexity": "O(log n) — basamak sayısı kadar",
        "related_concepts": ["özyineleme", "modulo", "while döngüsü", "sayı basamakları"],
        "related_question_ids": [9, 16],
        "tutorial_slug": None,
    },
    9: {
        "explanation": """**Asal sayı kontrolü (Eratosthenes)** klasik bir algoritma sorusudur.

**Naive:** 2'den √n'e kadar tüm sayıları dene → O(√n).
**Eratosthenes:** 2'den n'e kadar işaretle, katlarını eleme → O(n log log n). Çok sayıda asal kontrolünde çok hızlı.

**Optimizasyon:**
- 2'den başla, sadece tek sayıları kontrol et.
- `n % i == 0` veya `any(n % i == 0 for i in range(2, int(n**0.5) + 1))`.

**Kullanım:** Kriptografi (RSA), sayı teorisi, hashing.""",
        "complexity": "O(√n) naive, O(n log log n) sieve",
        "related_concepts": ["Eratosthenes eleği", "matematik", "asal sayılar", "kriptografi"],
        "related_question_ids": [16, 23],
        "tutorial_slug": "python-asal-sayi-algoritma",
    },
    10: {
        "explanation": """**Dizi toplamı (cumulative sum)** finans, veri analizi ve makine öğrenmesinde çok kullanılır.

**Yaklaşımlar:**
1. **`itertools.accumulate`** → C-level implementasyon, en hızlı.
2. **Manuel döngü** → `cumsum[i] = cumsum[i-1] + arr[i]`.
3. **List comprehension** → `[sum(arr[:i+1]) for i in range(len(arr))]` (O(n²), yavaş).

**Pandas:** `df.cumsum()` ile DataFrame üzerinde direkt hesaplanabilir.

**Kullanım:** Kümülatif satışlar, portföy değeri, sinyal işleme, eğri altı alan hesabı.""",
        "complexity": "O(n) her yaklaşım için",
        "related_concepts": ["itertools.accumulate", "list comprehension", "pandas cumsum", "cumulative"],
        "related_question_ids": [4, 13],
        "tutorial_slug": None,
    },
    11: {
        "explanation": """**İki sayının OBEB'i (EBOB/GCD)** Öklid algoritması ile hesaplanır.

**Öklid:** `gcd(a, b) = gcd(b, a % b)`, base case `gcd(a, 0) = a`. Python 3.5+ ile `math.gcd()` builtin var.

**Özyinelemeli:**
```python
def gcd(a, b):
    return a if b == 0 else gcd(b, a % b)
```

**Kullanım:** Kesir sadeleştirme, RSA kriptografi, periyodik olaylar (örneğin saat hesabı), müzik teorisi (nota aralıkları).""",
        "complexity": "O(log(min(a, b)))",
        "related_concepts": ["Öklid algoritması", "özyineleme", "math.gcd", "modulo"],
        "related_question_ids": [8, 9],
        "tutorial_slug": "python-obeb-oklid",
    },
    12: {
        "explanation": """**Üçgen tipi kontrolü** geometri sorularının basit ama dikkat gerektiren versiyonudur.

**Üçgen eşitsizliği:** Her kenar, diğer iki kenarın toplamından küçük olmalı. En kısa yol `if a + b > c and a + c > b and b + c > a`.

**Tipler:**
- Eşkenar: a = b = c
- İkizkenar: iki kenar eşit
- Çeşitkenar: hepsi farklı

**Edge case:** Negatif veya sıfır kenarlar geçersiz üçgen.""",
        "complexity": "O(1)",
        "related_concepts": ["koşullu ifadeler", "geometri", "üçgen eşitsizliği"],
        "related_question_ids": [4, 13],
        "tutorial_slug": None,
    },
    13: {
        "explanation": """**Ters çevirme (reversal)** string ve liste için klasik mülakat sorusu.

**String için:** `s[::-1]` en kısa yol. `''.join(reversed(s))` de çalışır.
**Liste için:** `lst[::-1]` veya `list(reversed(lst))`.

**Manuel:** Çift index swap — `lst[i], lst[-i-1] = lst[-i-1], lst[i]` (palindrome kontrolünde de kullanılır).

**In-place vs yeni liste:** Orijinali değiştirmek (in-place) O(1) bellek, yeni liste O(n) bellek.""",
        "complexity": "O(n) zaman, O(1) veya O(n) bellek",
        "related_concepts": ["slicing", "reversed", "in-place reverse", "tuple swap"],
        "related_question_ids": [1, 3],
        "tutorial_slug": None,
    },
    14: {
        "explanation": """**İkili arama (binary search)** sıralı dizide hedef bulmanın en hızlı yoludur.

**Algoritma:**
1. Sol ve sağ index belirle.
2. Ortanca elemanı al.
3. Hedef ortancadan küçükse sağa, büyükse sola kaydır.
4. `left <= right` iken devam, aksi halde `-1` döndür.

**Recursive vs iterative:** Iterative tercih edilir (Python recursion limiti 1000).

**Kullanım:** Sözlükler (aslen binary search tree), veri tabanları (B-tree indeksleri), oyun motorları.""",
        "complexity": "O(log n)",
        "related_concepts": ["binary search", "döngü", "indeks hesaplama", "sıralı dizi"],
        "related_question_ids": [5, 9],
        "tutorial_slug": "python-binary-search",
    },
    15: {
        "explanation": """**Matris çarpımı**, lineer cebirin temelidir.

**Naive:** Üç iç içe döngü, O(n³). NumPy ile `np.dot(A, B)` veya `A @ B` C implementasyonu sayesinde O(n²·⁸⁰) veya daha hızlı.

**Optimizasyon:** Strassen algoritması O(n^2.807) ama pratikte sadece büyük matrisler için avantajlı.

**Kullanım:** Grafik işleme, makine öğrenmesi (nöral ağlar), fizik simülasyonları.""",
        "complexity": "O(n³) naive, NumPy ile O(n²·⁸⁰)",
        "related_concepts": ["iç içe döngü", "NumPy", "matris", "lineer cebir"],
        "related_question_ids": [4, 10],
        "tutorial_slug": None,
    },
    # ═══ STRINGS ═══
    51: {
        "explanation": """**Emoji duygu analizi**, metin işleme ve basit NLP sorusudur.

**Yaklaşım:**
1. Metni kelimelere ayır.
2. Her kelimenin pozitif/negatif puanını bul (sözlük veya embedding).
3. Toplam skoru hesapla.

**Emoji'ler:** Modern yaklaşımda Unicode emoji'lerini saymak için `emoji` kütüphanesi veya regex kullanılır.

**Gerçek dünya:** Sosyal medya monitoring, müşteri geri bildirim analizi, marka algısı ölçümü.""",
        "complexity": "O(n) metin uzunluğu, O(1) lookup",
        "related_concepts": ["NLP", "emoji", "regex", "sözlük lookup", "text classification"],
        "related_question_ids": [52, 53],
        "tutorial_slug": None,
    },
    52: {
        "explanation": """**Gizli emoji mesajı**, steganografi (veri gizleme) ve string encoding sorusudur.

**Yaklaşımlar:**
1. **Zero-width characters:** Normal metin arasına görünmez Unicode karakterler (U+200B, U+FEFF) gizlenir.
2. **Emoji variation selectors:** Bazı karakterlerin ardına farklı görünüm ekleyen selector karakterleri.
3. **Mod-16 encoding:** Her ASCII karakterin 4 bitlik kısmı emoji'lerin ardına gizlenir.

**Kullanım:** Güvenli iletişim, watermarking, mesajlaşma uygulamalarında metadata.""",
        "complexity": "O(n) metin işleme, O(n) decode",
        "related_concepts": ["steganografi", "unicode", "zero-width characters", "encoding"],
        "related_question_ids": [51, 53],
        "tutorial_slug": None,
    },
    53: {
        "explanation": """**Emoji FizzBuzz** klasik FizzBuzz'ın modern emoji versiyonudur. Junior mülakatlarda **en sık** çıkan sorulardan biridir.

Algoritma:
- 3'e bölünürse → Fizz🎉
- 5'e bölünürse → Buzz🚀
- İkisine de → FizzBuzz🎊

**Sıra önemli:** Önce **en spesifik** durumu (ikisine birden) kontrol et.""",
        "complexity": "O(n)",
        "related_concepts": ["FizzBuzz", "modulo", "emoji", "kontrol yapıları"],
        "related_question_ids": [2, 51, 52],
        "tutorial_slug": "python-fizzbuzz-algoritma",
    },
    54: {
        "explanation": """**Türkçe karakter normalizasyonu** veri temizleme ve metin madenciliğinde kritik.

**Sorun:** "İSTANBUL" vs "istanbul" vs "İstanbul" aynı şey mi?

**Yaklaşım:**
1. `lower()` → "i̇stanbul" (sorunlu)
2. `casefold()` → "istanbul" (doğru, Unicode-aware)
3. Türkçe'ye özel `I → ı` mapping.

**Kullanım:** Arama motorları, kullanıcı girişi doğrulama, veri analizi, ETL.""",
        "complexity": "O(n) string uzunluğu",
        "related_concepts": ["casefold", "Unicode", "Türkçe locale", "string normalizasyon"],
        "related_question_ids": [1, 51, 55],
        "tutorial_slug": None,
    },
    55: {
        "explanation": """**String şifreleme** temel güvenlik sorularındandır.

**Yaklaşımlar:**
1. **Caesar cipher** → basit kaydırma.
2. **Vigenère cipher** → anahtar kelime ile kaydırma.
3. **AES** → modern simetrik şifreleme (`cryptography` kütüphanesi).

**Mülakatlarda:** Genellikle Caesar veya ROT13 sorulur, gerçek projelerde asla kullanılmaz (kırılması çok kolay).""",
        "complexity": "O(n)",
        "related_concepts": ["Caesar cipher", "şifreleme", "ASCII", "string encoding"],
        "related_question_ids": [52, 56],
        "tutorial_slug": None,
    },
    56: {
        "explanation": """**URL slug üretimi**, SEO için kritik. "Python Mülakat Hazırlığı" → "python-mulakat-hazirligi".

**Yaklaşımlar:**
1. **`re.sub('[^a-z0-9]+', '-', text.lower())`** — ASCII-only.
2. **`python-slugify` kütüphanesi** — Unicode desteği, Türkçe karakterleri korur.
3. **`django.utils.text.slugify`** — Django kullanıyorsan hazır.

**İpuçları:** Trailing dash temizle, max uzunluk koy, stopwords kaldır.""",
        "complexity": "O(n)",
        "related_concepts": ["regex", "slug", "URL", "SEO", "string normalization"],
        "related_question_ids": [1, 54],
        "tutorial_slug": None,
    },
    # ═══ LIST-DICT ═══
    101: {
        "explanation": """**Liste döndürme (reverse)** temel veri yapısı sorusudur.

**Yaklaşımlar:**
1. **Slicing:** `lst[::-1]` — en kısa ve hızlı.
2. **`list(reversed(lst))`** — yeni liste döner.
3. **`lst.reverse()`** — in-place, orijinali değiştirir.

**In-place vs yeni liste:** Orijinali korumak istiyorsan `[::-1]` veya `reversed()`; değiştirmek istiyorsan `.reverse()`.""",
        "complexity": "O(n)",
        "related_concepts": ["list slicing", "reversed", "in-place"],
        "related_question_ids": [13, 102],
        "tutorial_slug": None,
    },
    102: {
        "explanation": """**Sözlük birleştirme** (merge) veri işlemede sık yapılan işlem.

**Yaklaşımlar:**
1. **`{**d1, **d2}`** → Python 3.5+, en okunabilir.
2. **`d1 | d2`** → Python 3.9+, union operatörü.
3. **`dict.update()`** → in-place, d2 değerleri d1'i override eder.

**Çakışma:** Aynı key varsa **sağdaki** kazanır (`d2`'deki değer). Çakışma kontrolü istiyorsan manuel merge yap.""",
        "complexity": "O(n + m)",
        "related_concepts": ["dict unpacking", "dict update", "merge", "Python 3.9+"],
        "related_question_ids": [103, 104],
        "tutorial_slug": None,
    },
    103: {
        "explanation": """**Sözlük erişim güvenliği** Python'da en sık yapılan hatadır.

**Yaklaşımlar:**
1. **`d.get('key', default)`** → default değer döner.
2. **`d.setdefault('key', default)`** → yoksa ekler.
3. **`defaultdict`** → Otomatik default üreten sözlük.
4. **`try/except KeyError`** → Açık hata yönetimi.

**Performans:** `get()` en hızlı, defaultdict constructor'ı pahalı ama toplu işlemlerde hızlı.""",
        "complexity": "O(1) ortalama",
        "related_concepts": ["dict.get", "defaultdict", "KeyError", "try/except"],
        "related_question_ids": [102, 104],
        "tutorial_slug": None,
    },
    104: {
        "explanation": """**Sözlük sıralama**, veri sunumu için önemli.

**Yaklaşımlar:**
1. **`sorted(d.items(), key=lambda x: x[1])`** — değere göre.
2. **`sorted(d)`** → anahtara göre sıralı liste.
3. **`collections.OrderedDict`** → ekleme sırasını korur (Python 3.7+ normal dict de korur).

**Çoklu anahtar:** `sorted(items, key=lambda x: (x[1], x[0]))` — önce değer, sonra anahtar.""",
        "complexity": "O(n log n)",
        "related_concepts": ["sorted", "lambda", "OrderedDict", "tuple sorting"],
        "related_question_ids": [102, 103],
        "tutorial_slug": None,
    },
    105: {
        "explanation": """**Liste birleştirme (merge)**, sıralı iki listenin birleştirilmesi klasik algoritma sorusudur.

**Yaklaşım:**
1. **İki pointer:** Her iki listede de işaretçi, küçük olanı ekle.
2. **`heapq.merge()`** → Python'ın optimize edilmiş versiyonu.

**Karmaşıklık:** O(n + m). Sıralı olmayan listeler için önce sırala, O((n+m) log(n+m)).""",
        "complexity": "O(n + m)",
        "related_concepts": ["iki pointer", "heapq.merge", "sorted merge"],
        "related_question_ids": [106, 107],
        "tutorial_slug": None,
    },
    106: {
        "explanation": """**Liste düzleştirme (flatten)**, iç içe listeleri tek listeye çevirir.

**Yaklaşımlar:**
1. **Özyinelemeli:** Tip kontrolü ile iç içe yapıyı aç.
2. **`itertools.chain.from_iterable`** → Sadece 1 seviye için.
3. **`sum(lst, [])`** → Yavaş ama kısa (O(n²)).

**Çoklu seviye:** Deep flatten için recursion + isinstance check.""",
        "complexity": "O(n) toplam eleman",
        "related_concepts": ["özyineleme", "itertools.chain", "isinstance", "iç içe yapılar"],
        "related_question_ids": [105, 107],
        "tutorial_slug": None,
    },
    107: {
        "explanation": """**Liste parçalama (chunking)**, büyük veriyi işlerken batch'lere bölmek için kullanılır.

**Yaklaşımlar:**
1. **List comprehension:** `[lst[i:i+n] for i in range(0, len(lst), n)]`.
2. **`itertools.batched`** → Python 3.12+, lazy evaluation.
3. **Generator:** Bellek dostu, büyük veri için.

**Kullanım:** API pagination, batch processing, veri analizi (chunked CSV okuma).""",
        "complexity": "O(n)",
        "related_concepts": ["itertools.batched", "list slicing", "generator", "batch processing"],
        "related_question_ids": [105, 106],
        "tutorial_slug": None,
    },
    108: {
        "explanation": """**Liste tekilleştirme (unique)** koruma sırasıyla veya sırasız yapılabilir.

**Yaklaşımlar:**
1. **`list(dict.fromkeys(lst))`** → sırayı korur (Python 3.7+).
2. **`set(lst)`** → sıra garantisi yok, en hızlı.
3. **Manuel:** `seen = set(); [x for x in lst if x not in seen and not seen.add(x)]`.

**Kullanım:** Veri temizleme, unique kullanıcı listesi, tag sistemi.""",
        "complexity": "O(n) ortalama",
        "related_concepts": ["set", "dict.fromkeys", "unique", "veri temizleme"],
        "related_question_ids": [102, 109],
        "tutorial_slug": None,
    },
    109: {
        "explanation": """**Liste karşılaştırma**, ortak elemanları bulma veya farkı bulma.

**Yaklaşımlar:**
1. **`set(lst1) & set(lst2)`** → kesişim.
2. **`set(lst1) - set(lst2)`** → fark.
3. **`set(lst1) ^ set(lst2)`** → simetrik fark.

**Sıra korumak için:** `[x for x in lst1 if x in set(lst2)]`.""",
        "complexity": "O(n + m)",
        "related_concepts": ["set operations", "kesişim", "fark", "veri analizi"],
        "related_question_ids": [102, 108],
        "tutorial_slug": None,
    },
    110: {
        "explanation": """**Sözlük gruplama** bir listeyi key'e göre gruplara ayırır.

**Yaklaşımlar:**
1. **`itertools.groupby`** → sıralı veri için.
2. **`defaultdict(list)`** → en esnek, sırasız.
3. **`dict.setdefault`** → tek satır ama yavaş.

**Kullanım:** Kategorize etme, rapor oluşturma, ETL süreçleri.""",
        "complexity": "O(n)",
        "related_concepts": ["itertools.groupby", "defaultdict", "groupby"],
        "related_question_ids": [102, 103, 111],
        "tutorial_slug": None,
    },
    111: {
        "explanation": """**Liste frekans sayımı** en sık kullanılan veri analizi sorularından.

**Yaklaşımlar:**
1. **`Counter(lst)`** → en hızlı ve okunabilir.
2. **`defaultdict(int)`** → manuel sayaç.
3. **`dict.get(key, 0) + 1`** → klasik yaklaşım.

**Çıktı:** `most_common(n)` ile en sık n elemanı alabilirsin.""",
        "complexity": "O(n)",
        "related_concepts": ["collections.Counter", "defaultdict", "most_common"],
        "related_question_ids": [6, 110, 112],
        "tutorial_slug": None,
    },
    112: {
        "explanation": """**Liste sıralama**, custom key ile sıralama ileri seviye konudur.

**Yaklaşımlar:**
1. **`sorted(lst, key=lambda x: ...)`** → yeni liste döner.
2. **`lst.sort(key=...)`** → in-place, orijinali değiştirir.

**Çoklu key:** `key=lambda x: (x[1], x[0])` — tuple otomatik sıralanır.

**Stabilite:** Python'un sort algoritması **TimSort**, eşit elemanların orijinal sırasını korur.""",
        "complexity": "O(n log n)",
        "related_concepts": ["sorted", "list.sort", "TimSort", "tuple sorting"],
        "related_question_ids": [105, 109],
        "tutorial_slug": None,
    },
    113: {
        "explanation": """**Sözlük ters çevirme** key-value yer değiştirir. Aynı value'da birden fazla key varsa, value'lar liste olur.

**Yaklaşım:**
```python
inv = {}
for k, v in d.items():
    inv.setdefault(v, []).append(k)
```

**Sıralı:** `inv = {v: k for k, v in sorted(d.items(), reverse=True)}`.

**Kullanım:** İndeks tersine çevirme, lookup optimizasyonu.""",
        "complexity": "O(n)",
        "related_concepts": ["dict comprehension", "ters sözlük", "setdefault"],
        "related_question_ids": [102, 110],
        "tutorial_slug": None,
    },
    # ═══ PANDAS ═══
    201: {
        "explanation": """**Pandas DataFrame filtreleme**, veri analizinin temelidir.

**Yaklaşımlar:**
1. **Boolean indexing:** `df[df['column'] > value]` — en yaygın.
2. **`.query()`** → SQL benzeri syntax.
3. **`.loc[]`** → label-based.

**Çoklu koşul:** `df[(df['a'] > 5) & (df['b'] == 'x')]` → parantez önemli!

**Performans:** 1M+ satır için `.query()` veya numpy backend'li pandas.""",
        "complexity": "O(n)",
        "related_concepts": ["boolean indexing", "query", "loc/iloc", "Pandas"],
        "related_question_ids": [202, 203],
        "tutorial_slug": None,
    },
    202: {
        "explanation": """**Pandas groupby**, SQL'deki GROUP BY'a eşdeğer. **Split-Apply-Combine** pattern'i.

**Yaklaşım:**
```python
df.groupby('category')['value'].agg(['mean', 'sum', 'count'])
```

**Çoklu kolon:** `df.groupby(['cat1', 'cat2']).agg({'col1': 'sum', 'col2': 'mean'})`.

**Kullanım:** Raporlama, ETL, müşteri segmentasyonu, A/B test analizi.""",
        "complexity": "O(n)",
        "related_concepts": ["groupby", "agg", "split-apply-combine"],
        "related_question_ids": [201, 203, 204],
        "tutorial_slug": "pandas-groupby-rehberi",
    },
    203: {
        "explanation": """**Pandas merge/join**, iki DataFrame'i key üzerinden birleştirir.

**Yaklaşımlar:**
1. **`pd.merge(df1, df2, on='key')`** → SQL benzeri.
2. **`df1.join(df2)`** → index-based join.
3. **`pd.concat([df1, df2])`** → alt alta/yan yana birleştirme.

**Join tipleri:** `how='inner'`, `'left'`, `'right'`, `'outer'`.

**Performans:** 1M+ satır için key'i önceden sırala, `merge(..., sort=False)`.""",
        "complexity": "O(n + m) hash join",
        "related_concepts": ["merge", "join", "concat", "SQL JOIN"],
        "related_question_ids": [201, 202, 204],
        "tutorial_slug": None,
    },
    204: {
        "explanation": """**Pandas apply**, satır/sütun bazlı özel fonksiyon uygular. **Yavaş ama esnek**.

**Yaklaşımlar:**
1. **`df.apply(lambda x: ...)`** → satır/sütun bazlı.
2. **`df['col'].map(func)`** → Series bazlı, daha hızlı.
3. **`df['col'].str.func()`** → string metotları için vectorized.

**Performans:** 100K+ satır için **vectorized** operasyonları tercih et (apply'den 100x hızlı).""",
        "complexity": "O(n) Python overhead",
        "related_concepts": ["apply", "map", "vectorization", "lambda"],
        "related_question_ids": [201, 205],
        "tutorial_slug": None,
    },
    205: {
        "explanation": """**Pandas pivot_table**, long → wide format dönüşümü.

**Yaklaşım:**
```python
df.pivot_table(values='value', index='row', columns='col', aggfunc='mean')
```

**Çoklu aggregation:** `aggfunc={'value': 'sum', 'count': 'mean'}`.

**Kullanım:** Rapor tabloları, Excel benzeri pivot, A/B test analizi.""",
        "complexity": "O(n)",
        "related_concepts": ["pivot_table", "melt", "wide/long format"],
        "related_question_ids": [201, 202, 206],
        "tutorial_slug": None,
    },
    206: {
        "explanation": """**Pandas missing data** yönetimi, gerçek dünya veri temizleme için kritik.

**Yaklaşımlar:**
1. **Tespit:** `df.isnull()`, `df.notnull()`, `df.isna()`.
2. **Doldurma:** `df.fillna(value)`, `df.fillna(method='ffill')`.
3. **Silme:** `df.dropna()`, `df.dropna(subset=['col'])`.

**Strateji:** %5'ten az missing → sil, %5-30 → fill (mean/median/mode), %30+ → kolonu kaldır veya ML imputation.""",
        "complexity": "O(n)",
        "related_concepts": ["isnull", "fillna", "dropna", "missing data"],
        "related_question_ids": [201, 207],
        "tutorial_slug": None,
    },
    207: {
        "explanation": """**Pandas string metotları**, `.str` accessor ile vectorized string işlemleri.

**Yaklaşımlar:**
1. **`df['col'].str.lower()`** → tüm satırları küçük harf.
2. **`df['col'].str.contains('pattern')`** → regex eşleşme.
3. **`df['col'].str.replace('a', 'b')`** → değiştirme.
4. **`df['col'].str.extract('regex')`** → grup yakalama.

**Performans:** `.apply(lambda x: x.lower())`'den 50-100x hızlı.""",
        "complexity": "O(n)",
        "related_concepts": ["str accessor", "regex", "vectorization", "Pandas"],
        "related_question_ids": [201, 208],
        "tutorial_slug": None,
    },
    208: {
        "explanation": """**Pandas datetime** işlemleri, zaman serisi analizi için vazgeçilmez.

**Yaklaşımlar:**
1. **Parse:** `pd.to_datetime(df['col'])`.
2. **Extract:** `df['date'].dt.month`, `.year`, `.day_name()`.
3. **Filter:** `df[df['date'] > '2024-01-01']`.
4. **Resample:** `df.resample('M').sum()` — aylık toplam.

**Timezone:** `df['date'].dt.tz_localize('UTC').dt.tz_convert('Europe/Istanbul')`.""",
        "complexity": "O(n)",
        "related_concepts": ["to_datetime", "dt accessor", "resample", "time series"],
        "related_question_ids": [201, 209],
        "tutorial_slug": None,
    },
    209: {
        "explanation": """**Pandas çıktı alma**, veri kaydetme ve raporlama için kritik.

**Yaklaşımlar:**
1. **CSV:** `df.to_csv('file.csv', index=False)`.
2. **Excel:** `df.to_excel('file.xlsx', sheet_name='Sheet1')`.
3. **JSON:** `df.to_json('file.json', orient='records')`.
4. **Parquet:** `df.to_parquet('file.parquet')` — sıkıştırılmış, hızlı.

**Performans:** Büyük veri için Parquet veya Feather tercih edilir (CSV'den 10x hızlı okuma).""",
        "complexity": "O(n)",
        "related_concepts": ["to_csv", "to_excel", "to_parquet", "veri export"],
        "related_question_ids": [201, 210],
        "tutorial_slug": None,
    },
    210: {
        "explanation": """**Pandas read_csv**, veri yükleme fonksiyonu.

**Yaklaşımlar:**
1. **Basit:** `pd.read_csv('file.csv')`.
2. **Chunked:** `pd.read_csv('file.csv', chunksize=10000)` → büyük dosyalar için.
3. **Optimization:** `dtype={'col': 'int32'}` → bellek tasarrufu.

**Performans:** 1GB+ dosyalar için `pyarrow` engine veya Parquet kullan.""",
        "complexity": "O(n)",
        "related_concepts": ["read_csv", "chunksize", "dtype optimization"],
        "related_question_ids": [201, 209],
        "tutorial_slug": None,
    },
    # ═══ ALGORITHMS ═══
    301: {
        "explanation": """**İki sayı toplamı (Two Sum)**, en klasik mülakat sorusudur.

**Yaklaşımlar:**
1. **Brute force:** Her çifti kontrol et, O(n²).
2. **Hash map:** `seen = {}; for i, n in enumerate(nums): if target - n in seen: return [seen[target-n], i]`. O(n).

**Optimizasyon:** Hash map tek geçişte çözüm, O(n) zaman O(n) bellek.

**Kullanım:** Finansal hesaplamalar, eşleştirme problemleri.""",
        "complexity": "O(n) hash ile, O(n²) brute force",
        "related_concepts": ["hash map", "enumerate", "two pointers"],
        "related_question_ids": [302, 303],
        "tutorial_slug": "python-two-sum",
    },
    302: {
        "explanation": """**Sıralı dizide hedef arama**, en temel algoritma sorularındandır.

**Yaklaşımlar:**
1. **Linear search:** O(n), basit.
2. **Binary search:** O(log n), sıralı dizi için en hızlı.

**Recursive vs iterative:** Iterative tercih edilir (stack overflow riski yok).

**Kullanım:** Veri tabanları, sıralı listeler, indeksleme.""",
        "complexity": "O(log n)",
        "related_concepts": ["binary search", "two pointers", "sıralı dizi"],
        "related_question_ids": [14, 301],
        "tutorial_slug": "python-binary-search",
    },
    303: {
        "explanation": """**Dizi döndürme**, in-place dizi döndürme algoritması.

**Yaklaşımlar:**
1. **Naive:** Yeni dizi oluştur, O(n) bellek.
2. **Üç ters çevirme:** Tüm diziyi, ilk k'yı, son k'yı ters çevir. O(1) bellek.
3. **`collections.deque.rotate`** → O(k).

**Üç ters çevirme en zarif:** `[1,2,3,4,5,6,7], k=3 → [5,6,7,1,2,3,4]`.""",
        "complexity": "O(n) zaman, O(1) bellek",
        "related_concepts": ["in-place reversal", "deque", "array rotation"],
        "related_question_ids": [13, 301, 304],
        "tutorial_slug": None,
    },
    304: {
        "explanation": """**Linked List reverse**, klasik veri yapısı sorusudur.

**Yaklaşım:**
```python
def reverse(head):
    prev, curr = None, head
    while curr:
        nxt = curr.next
        curr.next = prev
        prev = curr
        curr = nxt
    return prev
```

**Karmaşıklık:** O(n) zaman, O(1) bellek. Üç pointer swap.

**Kullanım:** OS kernel, dosya sistemi, tarayıcı geçmişi, undo/redo.""",
        "complexity": "O(n) zaman, O(1) bellek",
        "related_concepts": ["linked list", "pointer manipulation", "in-place"],
        "related_question_ids": [303, 305],
        "tutorial_slug": None,
    },
    305: {
        "explanation": """**Stack kullanımı**, **DFS, parenthes matching, expression evaluation** için temel.

**Yaklaşımlar:**
1. **`list` (append/pop)** → O(1) amortized.
2. **`collections.deque`** → O(1) guaranteed.

**Kullanım:** Fonksiyon çağrı yığını, undo/redo, parantez eşleştirme, syntax parser, tarayıcı history.""",
        "complexity": "O(1) amortized",
        "related_concepts": ["stack", "deque", "LIFO", "DFS"],
        "related_question_ids": [304, 306],
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

    # Default değer ata (tüm sorular için)
    for q in QUESTIONS:
        if not q.explanation:
            q.explanation = f"{q.title} sorusu, Python'da {q.category} kategorisinde {q.level} seviyesinde bir mülakat sorusudur. Detaylı açıklama yakında eklenecek."
        if not q.complexity:
            q.complexity = "O(n)"
        if not q.related_concepts:
            q.related_concepts = [q.category]
        if not q.related_question_ids:
            # Aynı kategoriden 1-3 benzer soru öner
            same_cat = [o.id for o in QUESTIONS if o.category == q.category and o.id != q.id][:3]
            q.related_question_ids = same_cat

    print(f"✅ SEO içeriği uygulandı: {applied}/{len(QUESTIONS)} soruya detaylı içerik eklendi")
    return applied


if __name__ == "__main__":
    apply_seo_content()
    # Örnekler yazdır
    for q in QUESTIONS[:3]:
        print(f"\n#{q.id} {q.title}")
        print(f"  complexity: {q.complexity}")
        print(f"  related_concepts: {q.related_concepts}")
        print(f"  related_question_ids: {q.related_question_ids}")
        print(f"  tutorial_slug: {q.tutorial_slug}")
        print(f"  explanation (ilk 100): {q.explanation[:100]}...")