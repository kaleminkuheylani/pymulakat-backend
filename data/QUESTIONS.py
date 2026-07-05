# data/QUESTIONS.py
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
    # 🆕 SEO alanları
    explanation: str = ""              # Çözüm yaklaşımı (200-400 kelime, markdown)
    complexity: str = "O(n)"           # Big-O notasyonu
    related_concepts: List[str] = field(default_factory=list)  # ['string', 'regex', 'palindrome']
    related_question_ids: List[int] = field(default_factory=list) # Benzer sorular
    tutorial_slug: Optional[str] = None  # /guides/[slug] URL'i (varsa)
    slug: Optional[str] = None  # Canonical URL slug (DB'den)
    # 🆕 Curriculum (84 günlük müfredat)
    day: int = 0                       # 1-84
    week: int = 0                      # 1-12
    theme: str = ""                    # "🎮 RPG Karakter Oluşturucu" gibi
    difficulty: int = 1                # 1-5


QUESTIONS: List[Question] = [

    Question(
        id=1,
        title='Palindrome Checker',
        category='python-basics',
        level='beginner',
        description="""Bir kelimenin veya cümlenin palindrome olup olmadığını kontrol et.
Büyük/küçük harf fark etmesin, boşluk ve noktalama işaretlerini yok say.
Örnek: 'A man a plan a canal Panama' → True""",
        starter_code="""def is_palindrome(text: str) -> bool:
    # Buraya kodunu yaz
    pass""",
        test_cases=[
            {'input': 'radar', 'expected': True},
            {'input': 'Python', 'expected': False},
            {'input': 'A man a plan a canal Panama', 'expected': True},
            {'input': 'hello', 'expected': False},
        ],
        hints=[
            "💡 İpucu 1: Önce metnin yalnızca harf ve rakamlardan oluşan temiz halini oluştur. ''.join(...) ve str.isalnum() kullanabilirsin.",
            '💡 İpucu 2: Büyük/küçük harf farkını ortadan kaldırmak için .lower() metodunu kullan.',
            "💡 İpucu 3: Temizlenmiş string'i tersiyle karşılaştır: cleaned == cleaned[::-1]",
        ],
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
        starter_code="""def emoji_fizzbuzz(n: int) -> list:
    result = []
    for i in range(1, n+1):
        # Kodunu buraya yaz
        pass
    return result""",
        test_cases=[
            {'input': 5, 'expected': ['1', '2', 'Fizz🎉', '4', 'Buzz🚀']},
            {'input': 15, 'expected': ['1', '2', 'Fizz🎉', '4', 'Buzz🚀', 'Fizz🎉', '7', '8', 'Fizz🎉', 'Buzz🚀', '11', 'Fizz🎉', '13', '14', 'FizzBuzz🎊']},
        ],
        hints=[
            "💡 İpucu 1: Önce hem 3 hem 5'e bölünme durumunu kontrol et (FizzBuzz🎊). Sıra önemli!",
            '💡 İpucu 2: Bölünebilirlik için % (modulo) operatörünü kullan: i % 3 == 0',
            "💡 İpucu 3: Hiçbir koşula uymuyorsa sayıyı string'e çevir: str(i)",
        ],
    ),

    Question(
        id=3,
        title='Kelimelerin En Uzunu',
        category='python-basics',
        level='beginner',
        description="""Bir cümledeki en uzun kelimeyi ve uzunluğunu döndür.
Birden fazla aynı uzunlukta kelime varsa ilkini döndür.
Not: Sonuç [kelime, uzunluk] şeklinde liste olmalı.""",
        starter_code="""def longest_word(sentence: str) -> list:
    # Düşün: split() ile kelimeleri ayır, max ile bul
    # Döndür: [en_uzun_kelime, uzunlugu]
    pass""",
        test_cases=[
            {'input': 'Python çok eğlenceli bir dil', 'expected': ['eğlenceli', 9]},
            {'input': 'Merhaba dünya', 'expected': ['Merhaba', 7]},
            {'input': 'a bb ccc', 'expected': ['ccc', 3]},
        ],
        hints=[
            '💡 İpucu 1: sentence.split() ile cümleyi kelimelere ayır.',
            '💡 İpucu 2: max(words, key=len) ile en uzun kelimeyi bul.',
            '💡 İpucu 3: Sonucu liste olarak döndür: [word, len(word)]',
        ],
    ),

    Question(
        id=4,
        title='Sihirli Kare Kontrolü',
        category='python-basics',
        level='beginner',
        description="""Verilen 3x3 liste bir sihirli kare mi?
Satır, sütun ve iki çapraz toplamların hepsi eşit olmalı.""",
        starter_code="""def is_magic_square(grid: list) -> bool:
    # Her satır, sütun ve çaprazın toplamını karşılaştır
    pass""",
        test_cases=[
            {'input': [[2, 7, 6], [9, 5, 1], [4, 3, 8]], 'expected': True},
            {'input': [[1, 2, 3], [4, 5, 6], [7, 8, 9]], 'expected': False},
        ],
        hints=[
            '💡 İpucu 1: Hedef toplamı belirle: target = sum(grid[0])',
            '💡 İpucu 2: Sütunlar için: sum(grid[r][c] for r in range(3)) şeklinde döngü kur.',
            '💡 İpucu 3: Çaprazlar: grid[0][0]+grid[1][1]+grid[2][2] ve grid[0][2]+grid[1][1]+grid[2][0]',
        ],
    ),

    Question(
        id=5,
        title='Sayı Tahmin Skoru',
        category='python-basics',
        level='beginner',
        description="""Kullanıcının tahminleri ve gerçek sayı verildiğinde,
kaç tahminin tam doğru, kaç tahminin ±5 içinde, kaç tahminin uzak olduğunu döndür.""",
        starter_code="""def score_guesses(guesses: list, secret: int) -> dict:
    # {'exact': x, 'close': y, 'far': z} döndür
    pass""",
        test_cases=[
            {'input': {'guesses': [10, 12, 50, 11], 'secret': 10}, 'expected': {'exact': 1, 'close': 2, 'far': 1}},
            {'input': {'guesses': [1, 2, 3], 'secret': 100}, 'expected': {'exact': 0, 'close': 0, 'far': 3}},
        ],
        hints=[
            '💡 İpucu 1: abs(guess - secret) ile farkın mutlak değerini al.',
            "💡 İpucu 2: diff == 0 ise 'exact', diff <= 5 ise 'close', değilse 'far'.",
            '💡 İpucu 3: Sonuçları sayacak bir dict oluştur ve döngüde güncelle.',
        ],
    ),


    Question(
        id=7,
        title='Asal Sayı Kontrolü',
        category='python-basics',
        level='beginner',
        description="""Verilen sayının asal olup olmadığını kontrol et.
1 ve altındaki sayılar asal değildir.""",
        starter_code="""def is_prime(n: int) -> bool:
    # Asal sayı: yalnızca 1 ve kendisine bölünür
    pass""",
        test_cases=[
            {'input': 2, 'expected': True},
            {'input': 17, 'expected': True},
            {'input': 1, 'expected': False},
            {'input': 9, 'expected': False},
        ],
        hints=[
            '💡 İpucu 1: n <= 1 ise direkt False döndür.',
            "💡 İpucu 2: 2'den √n'e kadar bölenleri kontrol et: range(2, int(n**0.5)+1)",
            '💡 İpucu 3: Herhangi bir bölen bulursan False, döngü biterse True döndür.',
        ],
    ),

    Question(
        id=8,
        title='Liste Düzleştirme',
        category='python-basics',
        level='beginner',
        description="""İç içe geçmiş listeyi tek seviyeli listeye dönüştür.
Yalnızca bir seviye derinlik garantilidir.""",
        starter_code="""def flatten(nested: list) -> list:
    # [[1,2],[3,4],[5]] -> [1,2,3,4,5]
    pass""",
        test_cases=[
            {'input': [[1, 2], [3, 4], [5]], 'expected': [1, 2, 3, 4, 5]},
            {'input': [[10], [20, 30], [40, 50, 60]], 'expected': [10, 20, 30, 40, 50, 60]},
        ],
        hints=[
            '💡 İpucu 1: Boş bir liste oluştur ve her alt listeyi üzerine extend() et.',
            '💡 İpucu 2: List comprehension ile: [item for sublist in nested for item in sublist]',
            '💡 İpucu 3: itertools.chain.from_iterable(nested) de çalışır.',
        ],
    ),

    Question(
        id=9,
        title='Fibonacci Dizisi',
        category='python-basics',
        level='beginner',
        description="""İlk n Fibonacci sayısını liste olarak döndür.
F(0)=0, F(1)=1, F(n)=F(n-1)+F(n-2)""",
        starter_code="""def fibonacci(n: int) -> list:
    # İlk n elemanı hesapla
    pass""",
        test_cases=[
            {'input': 7, 'expected': [0, 1, 1, 2, 3, 5, 8]},
            {'input': 1, 'expected': [0]},
            {'input': 2, 'expected': [0, 1]},
        ],
        hints=[
            '💡 İpucu 1: Özel durumlar: n==1 → [0], n==2 → [0,1]',
            '💡 İpucu 2: [0, 1] ile başla, döngüde fib[-1]+fib[-2] ekle.',
            '💡 İpucu 3: while len(fib) < n: fib.append(fib[-1]+fib[-2])',
        ],
    ),

    Question(
        id=10,
        title='Anagram Kontrolü',
        category='python-basics',
        level='beginner',
        description="""İki kelimenin anagram olup olmadığını kontrol et.
Büyük/küçük harf ve boşluk fark etmesin.""",
        starter_code="""def is_anagram(word1: str, word2: str) -> bool:
    # Anagram: aynı harfleri farklı sırada kullanan kelimeler
    pass""",
        test_cases=[
            {'input': {'word1': 'listen', 'word2': 'silent'}, 'expected': True},
            {'input': {'word1': 'hello', 'word2': 'world'}, 'expected': False},
            {'input': {'word1': 'Astronomer', 'word2': 'Moon starer'}, 'expected': True},
        ],
        hints=[
            "💡 İpucu 1: Her iki string'i .lower() yap ve boşlukları kaldır.",
            '💡 İpucu 2: sorted() ile harfleri sırala ve karşılaştır: sorted(a) == sorted(b)',
            '💡 İpucu 3: Ya da Counter(a) == Counter(b) ile frekans karşılaştır.',
        ],
    ),

    Question(
        id=11,
        title='Kelime Tersleyici',
        category='python-basics',
        level='beginner',
        description="""Cümledeki kelimelerin sırasını tersine çevir,
fakat kelimelerin kendisini tersine çevirme.""",
        starter_code="""def reverse_words(sentence: str) -> str:
    # "Merhaba Dünya" -> "Dünya Merhaba"
    pass""",
        test_cases=[
            {'input': 'Merhaba Dünya', 'expected': 'Dünya Merhaba'},
            {'input': 'Python çok güzel', 'expected': 'güzel çok Python'},
        ],
        hints=[
            '💡 İpucu 1: sentence.split() ile kelimelere ayır.',
            '💡 İpucu 2: words[::-1] veya reversed(words) ile sırayı tersine çevir.',
            "💡 İpucu 3: ' '.join(...) ile tekrar birleştir.",
        ],
    ),

    Question(
        id=12,
        title='İkinci En Büyük',
        category='python-basics',
        level='beginner',
        description="""Bir listedeki ikinci en büyük eşsiz sayıyı döndür.
Eğer yoksa None döndür.""",
        starter_code="""def second_largest(numbers: list):
    # Tekrar eden sayıları dikkate alma
    pass""",
        test_cases=[
            {'input': [3, 1, 4, 1, 5, 9, 2, 6], 'expected': 6},
            {'input': [5, 5, 5], 'expected': None},
            {'input': [10, 20], 'expected': 10},
        ],
        hints=[
            '💡 İpucu 1: Önce set() ile tekrarları kaldır.',
            '💡 İpucu 2: sorted() veya max() kullanarak en büyükleri bul.',
            '💡 İpucu 3: len(unique) < 2 ise None döndür, yoksa sorted(unique)[-2]',
        ],
    ),

    Question(
        id=13,
        title='Sezar Şifresi',
        category='python-basics',
        level='beginner',
        description="""Metni n karakter kaydırarak şifrele (yalnızca İngilizce harfler).
Büyük/küçük harf korunmalı, diğer karakterler değişmemeli.""",
        starter_code="""def caesar_cipher(text: str, shift: int) -> str:
    # Her harfi alfabede shift kadar ilerlet
    pass""",
        test_cases=[
            {'input': {'text': 'Hello', 'shift': 3}, 'expected': 'Khoor'},
            {'input': {'text': 'xyz', 'shift': 3}, 'expected': 'abc'},
            {'input': {'text': 'Hello, World!', 'shift': 13}, 'expected': 'Uryyb, Jbeyq!'},
        ],
        hints=[
            '💡 İpucu 1: ord() ile karakterin ASCII kodunu al, chr() ile geri dönüştür.',
            "💡 İpucu 2: Büyük harf için: chr((ord(c) - ord('A') + shift) % 26 + ord('A'))",
            '💡 İpucu 3: Harf olmayanları (noktalama vb.) olduğu gibi bırak.',
        ],
    ),

    Question(
        id=14,
        title='Matris Transpozu',
        category='python-basics',
        level='beginner',
        description="""Bir matrisin transpozunu al (satırları sütun, sütunları satır yap).""",
        starter_code="""def transpose(matrix: list) -> list:
    # [[1,2,3],[4,5,6]] -> [[1,4],[2,5],[3,6]]
    pass""",
        test_cases=[
            {'input': [[1, 2, 3], [4, 5, 6]], 'expected': [[1, 4], [2, 5], [3, 6]]},
            {'input': [[1, 2], [3, 4], [5, 6]], 'expected': [[1, 3, 5], [2, 4, 6]]},
        ],
        hints=[
            '💡 İpucu 1: zip(*matrix) sihirli bir araçtır — satırları transpose eder.',
            '💡 İpucu 2: [list(row) for row in zip(*matrix)] ile sonucu listele.',
            '💡 İpucu 3: Manuel yol: result[j][i] = matrix[i][j] ile iç içe döngü.',
        ],
    ),


    Question(
        id=16,
        title='Parantez Dengesi',
        category='strings',
        level='beginner',
        description="""Verilen bir string'deki parantezlerin dengeli olup olmadığını kontrol et.
( ) [ ] { } desteklenir.""",
        starter_code="""def is_balanced(s: str) -> bool:
    # Stack (yığın) veri yapısını kullan
    pass""",
        test_cases=[
            {'input': '([]{})', 'expected': True},
            {'input': '([)]', 'expected': False},
            {'input': '', 'expected': True},
            {'input': '(((', 'expected': False},
        ],
        hints=[
            '💡 İpucu 1: Bir yığın (stack = []) kullan.',
            '💡 İpucu 2: Açık parantez görünce yığına ekle (push). Kapalı görünce yığından çıkar (pop) ve eşleş mi kontrol et.',
            '💡 İpucu 3: Sonunda yığın boşsa True, doluysa False döndür.',
        ],
    ),


    Question(
        id=18,
        title='Run-Length Encoding',
        category='strings',
        level='beginner',
        description="""Bir string'i run-length encoding ile sıkıştır.
'aaabbc' → '3a2b1c'""",
        starter_code="""def rle_encode(s: str) -> str:
    # Ardışık aynı karakterleri say ve sıkıştır
    pass""",
        test_cases=[
            {'input': 'aaabbc', 'expected': '3a2b1c'},
            {'input': 'aabbccdd', 'expected': '2a2b2c2d'},
            {'input': 'abc', 'expected': '1a1b1c'},
        ],
        hints=[
            '💡 İpucu 1: Mevcut karakteri ve sayısını tut: current_char, count.',
            '💡 İpucu 2: Karakter değişince sonucu ekle: result += str(count) + current_char',
            '💡 İpucu 3: Döngü bittikten sonra son grubu da eklemeyi unutma.',
        ],
    ),

    Question(
        id=19,
        title='Kelime Sıklığı',
        category='strings',
        level='beginner',
        description="""Bir metindeki en sık geçen k kelimeyi döndür.
Büyük/küçük harf duyarlı olmasın, noktalama işaretlerini yok say.""",
        starter_code="""def top_k_words(text: str, k: int) -> list:
    # En sık geçen k kelimeyi liste olarak döndür
    pass""",
        test_cases=[
            {'input': {'text': 'bir iki bir üç iki bir', 'k': 2}, 'expected': ['bir', 'iki']},
            {'input': {'text': 'the cat sat on the mat the', 'k': 1}, 'expected': ['the']},
        ],
        hints=[
            '💡 İpucu 1: .lower() ve .split() ile kelimeleri ayır.',
            '💡 İpucu 2: collections.Counter(words) ile frekans sözlüğü oluştur.',
            '💡 İpucu 3: counter.most_common(k) ile en sık k kelimeyi al.',
        ],
    ),

    Question(
        id=20,
        title='String Sıkıştırma',
        category='strings',
        level='beginner',
        description="""Bir string'i sıkıştır: art arda tekrar eden karakterleri tek karaktere indir.
'aabbcc' → 'abc', 'aabba' → 'aba'""",
        starter_code="""def compress(s: str) -> str:
    # Art arda tekrarları kaldır
    pass""",
        test_cases=[
            {'input': 'aabbcc', 'expected': 'abc'},
            {'input': 'aabba', 'expected': 'aba'},
            {'input': 'abcdef', 'expected': 'abcdef'},
        ],
        hints=[
            '💡 İpucu 1: Boş string durumunu kontrol et.',
            '💡 İpucu 2: result = s[0] ile başla, sonraki karakter öncekinden farklıysa ekle.',
            '💡 İpucu 3: itertools.groupby(s) ile de çözebilirsin.',
        ],
    ),

    Question(
        id=21,
        title='Roman Numerals',
        category='strings',
        level='intermediate',
        description="""1-3999 arasındaki bir tam sayıyı Roma rakamlarına çevir.""",
        starter_code="""def to_roman(num: int) -> str:
    values = [1000,900,500,400,100,90,50,40,10,9,5,4,1]
    symbols = ['M','CM','D','CD','C','XC','L','XL','X','IX','V','IV','I']
    # Buraya kodunu yaz
    pass""",
        test_cases=[
            {'input': 3, 'expected': 'III'},
            {'input': 58, 'expected': 'LVIII'},
            {'input': 1994, 'expected': 'MCMXCIV'},
        ],
        hints=[
            '💡 İpucu 1: values ve symbols listesi zaten verilmiş, sırayla karşılaştır.',
            '💡 İpucu 2: num >= value iken: result += symbol, num -= value',
            '💡 İpucu 3: CM=900, CD=400 gibi özel durumlar listeye dahil edilmiş, endişelenme.',
        ],
    ),

    Question(
        id=22,
        title='Pangram Kontrolü',
        category='strings',
        level='beginner',
        description="""Bir cümle pangram mı? (İngiliz alfabesinin tüm harflerini içeriyor mu?)
Büyük/küçük harf duyarlı olmasın.""",
        starter_code="""def is_pangram(sentence: str) -> bool:
    # 26 İngilizce harfin hepsi var mı?
    pass""",
        test_cases=[
            {'input': 'The quick brown fox jumps over the lazy dog', 'expected': True},
            {'input': 'Hello World', 'expected': False},
        ],
        hints=[
            '💡 İpucu 1: sentence.lower() ile küçük harfe çevir.',
            '💡 İpucu 2: set() ile unique harfleri bul.',
            "💡 İpucu 3: set('abcdefghijklmnopqrstuvwxyz').issubset(set(sentence.lower()))",
        ],
    ),


    Question(
        id=25,
        title='DNA Tamamlayıcısı',
        category='strings',
        level='beginner',
        description="""Bir DNA zincirinin tamamlayıcısını bul.
A↔T, C↔G  kuralını uygula ve sonucu tersine çevir.""",
        starter_code="""def dna_complement(strand: str) -> str:
    # ATCG -> CGAT (önce tamamlayıcı sonra ters)
    pass""",
        test_cases=[
            {'input': 'ATCG', 'expected': 'CGAT'},
            {'input': 'TTAA', 'expected': 'TTAA'},
        ],
        hints=[
            "💡 İpucu 1: Bir eşleşme dict'i oluştur: {'A':'T','T':'A','C':'G','G':'C'}",
            "💡 İpucu 2: Her karakteri eşleşme dict'inden bul: comp[c]",
            '💡 İpucu 3: Tamamlayıcıyı oluşturduktan sonra [::-1] ile tersine çevir.',
        ],
    ),

    Question(
        id=26,
        title='İki Listeyi Birleştir',
        category='list-dict',
        level='beginner',
        description="""İki sıralı listeyi birleştirerek yeni bir sıralı liste oluştur.
sort() kullanmadan yap.""",
        starter_code="""def merge_sorted(a: list, b: list) -> list:
    # İki işaretçi (pointer) tekniği kullan
    pass""",
        test_cases=[
            {'input': {'a': [1, 3, 5], 'b': [2, 4, 6]}, 'expected': [1, 2, 3, 4, 5, 6]},
            {'input': {'a': [1, 2], 'b': [3, 4, 5, 6]}, 'expected': [1, 2, 3, 4, 5, 6]},
            {'input': {'a': [], 'b': [1, 2, 3]}, 'expected': [1, 2, 3]},
        ],
        hints=[
            '💡 İpucu 1: İki işaretçi: i=0 (a için), j=0 (b için)',
            "💡 İpucu 2: Her adımda küçük olanı result'a ekle ve o işaretçiyi ilerlet.",
            '💡 İpucu 3: Döngü bitince kalan elemanları result.extend(a[i:]) ile ekle.',
        ],
    ),

    Question(
        id=27,
        title='Sözlük Birleştirme',
        category='list-dict',
        level='beginner',
        description="""İki sözlüğü birleştir. Aynı anahtarlar varsa değerlerini topla.""",
        starter_code="""def merge_dicts(d1: dict, d2: dict) -> dict:
    # {"a":1,"b":2} + {"b":3,"c":4} -> {"a":1,"b":5,"c":4}
    pass""",
        test_cases=[
            {'input': {'d1': {'a': 1, 'b': 2}, 'd2': {'b': 3, 'c': 4}}, 'expected': {'a': 1, 'b': 5, 'c': 4}},
            {'input': {'d1': {}, 'd2': {'x': 10}}, 'expected': {'x': 10}},
        ],
        hints=[
            "💡 İpucu 1: d1.copy() ile başla, d2'nin öğelerini üzerine ekle.",
            '💡 İpucu 2: result.get(key, 0) + value ile birleştirme yap.',
            '💡 İpucu 3: collections.Counter da bu iş için kullanılabilir.',
        ],
    ),

    Question(
        id=28,
        title='Gruplama',
        category='list-dict',
        level='beginner',
        description="""Bir sayı listesini 'tek' ve 'çift' olarak grupla.
Sonuç: {'tek': [...], 'çift': [...]}""",
        starter_code="""def group_by_parity(items: list) -> dict:
    # Sayıları tek ve çift olarak grupla
    pass""",
        test_cases=[
            {'input': [1, 2, 3, 4, 5, 6], 'expected': {'tek': [1, 3, 5], 'çift': [2, 4, 6]}},
            {'input': [10, 15, 20, 25], 'expected': {'tek': [15, 25], 'çift': [10, 20]}},
        ],
        hints=[
            "💡 İpucu 1: Boş bir dict oluştur: result = {'tek': [], 'çift': []}",
            "💡 İpucu 2: Her öğe için: if n % 2 == 0 → 'çift', else → 'tek'",
            "💡 İpucu 3: result['tek'].append(n) veya result['çift'].append(n)",
        ],
    ),

    Question(
        id=29,
        title='Fark Listesi',
        category='list-dict',
        level='beginner',
        description="""İki liste arasındaki farkları bul: yalnızca A'da, yalnızca B'de ve ikisinde birden olan elemanlar.""",
        starter_code="""def list_diff(a: list, b: list) -> dict:
    # {'only_a': [...], 'only_b': [...], 'common': [...]} döndür
    pass""",
        test_cases=[
            {'input': {'a': [1, 2, 3, 4], 'b': [3, 4, 5, 6]}, 'expected': {'only_a': [1, 2], 'only_b': [5, 6], 'common': [3, 4]}},
        ],
        hints=[
            '💡 İpucu 1: set() dönüşümü yap: sa=set(a), sb=set(b)',
            '💡 İpucu 2: only_a = sorted(sa - sb), only_b = sorted(sb - sa)',
            '💡 İpucu 3: common = sorted(sa & sb)  (kesişim)',
        ],
    ),

    Question(
        id=30,
        title='Matris Çarpımı',
        category='list-dict',
        level='intermediate',
        description="""İki matrisi çarp (nokta çarpımı). numpy kullanma.""",
        starter_code="""def matrix_multiply(a: list, b: list) -> list:
    # C[i][j] = sum(A[i][k] * B[k][j] for k in range(...))
    pass""",
        test_cases=[
            {'input': {'a': [[1, 2], [3, 4]], 'b': [[5, 6], [7, 8]]}, 'expected': [[19, 22], [43, 50]]},
        ],
        hints=[
            '💡 İpucu 1: Boyutlar: a = m×n, b = n×p → sonuç m×p',
            '💡 İpucu 2: Üç iç içe döngü: i (satır a), j (sütun b), k (ortak boyut)',
            '💡 İpucu 3: C[i][j] += A[i][k] * B[k][j]',
        ],
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
        test_cases=[
            {'input': ['+elma:10', '-elma:3', '+armut:5'], 'expected': {'elma': 7, 'armut': 5}},
            {'input': ['+kalem:100', '+kalem:50', '-kalem:30'], 'expected': {'kalem': 120}},
        ],
        hints=[
            "💡 İpucu 1: Her harekette sign = m[0], geri kalanını ':' ile böl.",
            "💡 İpucu 2: item, qty = m[1:].split(':'); qty = int(qty)",
            "💡 İpucu 3: sign=='+' ise ekle, '-' ise çıkar.",
        ],
    ),

    Question(
        id=32,
        title='Hareketli Ortalama',
        category='list-dict',
        level='beginner',
        description="""k elemanlı hareketli ortalama hesapla.
Yeterli eleman olmayan başlangıç pencerelerini atla.""",
        starter_code="""def moving_average(nums: list, k: int) -> list:
    # Her k'lı pencere için ortalamayı hesapla
    pass""",
        test_cases=[
            {'input': {'nums': [1, 2, 3, 4, 5], 'k': 3}, 'expected': [2.0, 3.0, 4.0]},
            {'input': {'nums': [10, 20, 30, 40], 'k': 2}, 'expected': [15.0, 25.0, 35.0]},
        ],
        hints=[
            '💡 İpucu 1: range(k-1, len(nums)) ile kayan pencere için döngü kur.',
            '💡 İpucu 2: Her adımda dilim: nums[i-k+1:i+1]',
            "💡 İpucu 3: sum(window)/k ile ortalmayı hesapla ve result'a ekle.",
        ],
    ),

    Question(
        id=33,
        title='En Uzun Artan Alt Dizi',
        category='list-dict',
        level='intermediate',
        description="""Bir dizideki en uzun sürekli artan alt dizinin uzunluğunu bul.""",
        starter_code="""def longest_increasing_subsequence(nums: list) -> int:
    # Sürekli artan: her eleman bir öncekinden büyük
    pass""",
        test_cases=[
            {'input': [1, 3, 5, 4, 7], 'expected': 3},
            {'input': [2, 2, 2, 2, 2], 'expected': 1},
            {'input': [1, 2, 3, 4, 5], 'expected': 5},
        ],
        hints=[
            '💡 İpucu 1: current ve max_len sayaçları tut.',
            '💡 İpucu 2: nums[i] > nums[i-1] ise current += 1, değilse current = 1',
            '💡 İpucu 3: Her adımda max_len = max(max_len, current) güncelle.',
        ],
    ),

    Question(
        id=34,
        title='Fiyat Analizi',
        category='list-dict',
        level='beginner',
        description="""Ürün fiyatlarının bulunduğu bir sözlükten
min, max ve ortalama fiyatı döndür.""",
        starter_code="""def price_analysis(prices: dict) -> dict:
    # {'elma':5,'armut':8,'muz':3} -> {'min':3,'max':8,'avg':5.33}
    pass""",
        test_cases=[
            {'input': {'elma': 5, 'armut': 8, 'muz': 3}, 'expected': {'min': 3, 'max': 8, 'avg': 5.33}},
        ],
        hints=[
            '💡 İpucu 1: values = list(prices.values()) ile değerleri al.',
            '💡 İpucu 2: min(), max() ve sum()/len() ile istatistikleri hesapla.',
            '💡 İpucu 3: round(avg, 2) ile yuvarla.',
        ],
    ),

    Question(
        id=35,
        title='Kümülatif Toplam',
        category='list-dict',
        level='beginner',
        description="""Bir listenin kümülatif (birikimli) toplamını döndür.
[1,2,3,4] → [1,3,6,10]""",
        starter_code="""def cumulative_sum(nums: list) -> list:
    # Her eleman, o noktaya kadar olan toplam olmalı
    pass""",
        test_cases=[
            {'input': [1, 2, 3, 4], 'expected': [1, 3, 6, 10]},
            {'input': [5, 5, 5, 5, 5], 'expected': [5, 10, 15, 20, 25]},
        ],
        hints=[
            '💡 İpucu 1: Döngü başında running_total = 0 tut.',
            "💡 İpucu 2: Her elemanda running_total += n, ardından result'a ekle.",
            '💡 İpucu 3: itertools.accumulate(nums) de aynı sonucu verir.',
        ],
    ),

    Question(
        id=36,
        title='Favori Renk Anketi',
        category='pandas',
        level='beginner',
        description="""Bir anket sonucu sözlüğü veriliyor. En popüler rengi bul.
(pandas kullanmadan, saf Python ile yap)""",
        starter_code="""def favorite_color(poll_data: dict) -> str:
    # poll_data = {"Ahmet": "Mavi", "Ayşe": "Kırmızı", ...}
    # En çok tekrar eden rengi döndür
    pass""",
        test_cases=[
            {'input': {'A': 'Mavi', 'B': 'Kırmızı', 'C': 'Mavi', 'D': 'Yeşil', 'E': 'Mavi'}, 'expected': 'Mavi'},
            {'input': {'X': 'Siyah', 'Y': 'Siyah'}, 'expected': 'Siyah'},
        ],
        hints=[
            '💡 İpucu 1: Boş bir dict oluştur: counts = {}',
            '💡 İpucu 2: Her değer için counts[color] = counts.get(color, 0) + 1',
            '💡 İpucu 3: max(counts, key=counts.get) ile en yüksek frekanslıyı bul.',
        ],
    ),

    Question(
        id=37,
        title='Eksik Değer Doldurma',
        category='pandas',
        level='beginner',
        description="""Bir sayı listesindeki None değerleri, listenin ortalamasıyla doldur.
(pandas kullanmadan, saf Python ile)""",
        starter_code="""def fill_missing(numbers: list) -> list:
    # [1, None, 3, None, 5] -> [1, 3.0, 3, 3.0, 5]
    pass""",
        test_cases=[
            {'input': [1, None, 3, None, 5], 'expected': [1, 3.0, 3, 3.0, 5]},
            {'input': [10, None, 20], 'expected': [10, 15.0, 20]},
        ],
        hints=[
            '💡 İpucu 1: Önce sadece sayısal değerlerin ortalamasını hesapla.',
            '💡 İpucu 2: nums = [x for x in numbers if x is not None]',
            "💡 İpucu 3: Ortalama = sum(nums) / len(nums); sonra None'ları bu değerle değiştir.",
        ],
    ),

    Question(
        id=38,
        title='Satış Raporu',
        category='pandas',
        level='beginner',
        description="""Satış verisini ürün bazında grupla, toplam satışı hesapla ve en çok satan ürünü döndür.""",
        starter_code="""def top_selling_product(sales_data: list) -> str:
    # [{'product':'A','amount':100}, ...] -> en çok satan ürün adı
    pass""",
        test_cases=[
            {'input': [{'product': 'A', 'amount': 100}, {'product': 'B', 'amount': 200}, {'product': 'A', 'amount': 150}], 'expected': 'A'},
        ],
        hints=[
            '💡 İpucu 1: Bir dict ile ürün → toplam satış tut: totals = {}',
            '💡 İpucu 2: Her kayıt için totals[product] = totals.get(product, 0) + amount',
            '💡 İpucu 3: max(totals, key=totals.get) ile en yüksek satışlı ürünü bul.',
        ],
    ),

    Question(
        id=39,
        title='Günlük Ortalama',
        category='pandas',
        level='intermediate',
        description="""Günlük veri sözlüğünden haftalık ortalama hesapla.
Her hafta 7 günlük gruplara böl ve ortalamasını al.""",
        starter_code="""def weekly_average(daily_data: dict) -> list:
    # {'2024-01-01': 10, '2024-01-02': 20, ...} -> [hafta1_ort, hafta2_ort, ...]
    pass""",
        test_cases=[
            {'input': {'d1': 10, 'd2': 20, 'd3': 30, 'd4': 40, 'd5': 50, 'd6': 60, 'd7': 70, 'd8': 80}, 'expected': [40.0, 80.0]},
        ],
        hints=[
            '💡 İpucu 1: Değerleri listeye al: values = list(daily_data.values())',
            "💡 İpucu 2: 7'şerlik gruplara böl: [values[i:i+7] for i in range(0, len(values), 7)]",
            '💡 İpucu 3: Her grubun ortalamasını al: sum(group)/len(group)',
        ],
    ),

    Question(
        id=40,
        title='Korelasyon Analizi',
        category='pandas',
        level='intermediate',
        description="""İki sayı listesi arasındaki Pearson korelasyonunu hesapla ve yorumla.
0.7+ güçlü, 0.4-0.7 orta, <0.4 zayıf.""",
        starter_code="""def correlation_analysis(x: list, y: list) -> dict:
    # {'correlation': float, 'strength': str} döndür
    pass""",
        test_cases=[
            {'input': {'x': [1, 2, 3, 4, 5], 'y': [2, 4, 6, 8, 10]}, 'expected': {'correlation': 1.0, 'strength': 'güçlü'}},
            {'input': {'x': [1, 2, 3, 4, 5], 'y': [5, 4, 3, 2, 1]}, 'expected': {'correlation': -1.0, 'strength': 'güçlü'}},
        ],
        hints=[
            '💡 İpucu 1: Pearson formülü: r = Σ((xi-x̄)(yi-ȳ)) / √(Σ(xi-x̄)² · Σ(yi-ȳ)²)',
            '💡 İpucu 2: Önce x_bar = sum(x)/len(x), y_bar = sum(y)/len(y) hesapla.',
            "💡 İpucu 3: abs(r) >= 0.7 → 'güçlü', >= 0.4 → 'orta', else → 'zayıf'",
        ],
    ),

    Question(
        id=41,
        title='Tekrar Eden Satırlar',
        category='pandas',
        level='beginner',
        description="""Bir listedeki tekrar eden öğeleri kaldır ve kaç tane kaldırıldığını döndür.
Sonuç: (temizlenmiş_liste, kaldırılan_sayısı)""",
        starter_code="""def remove_duplicates(items: list) -> list:
    # (temizlenmiş_liste, kaldırılan_sayısı) döndür
    pass""",
        test_cases=[
            {'input': [1, 2, 2, 3, 3, 3, 4], 'expected': [[1, 2, 3, 4], 3]},
            {'input': ['a', 'b', 'a', 'c'], 'expected': [['a', 'b', 'c'], 1]},
        ],
        hints=[
            '💡 İpucu 1: seen = set() ile görülen öğeleri takip et.',
            '💡 İpucu 2: Her öğe için: if item not in seen → ekle, else → sayacı artır.',
            '💡 İpucu 3: Sonuç: [clean_list, removed_count]',
        ],
    ),

    Question(
        id=42,
        title='Yaş Grubu Segmentasyonu',
        category='pandas',
        level='beginner',
        description="""Yaş listesini gruplara ayır: 0-17 'Genç', 18-64 'Yetişkin', 65+ 'Yaşlı'.""",
        starter_code="""def age_segment(ages: list) -> list:
    # [15, 25, 70, 5] -> ['Genç', 'Yetişkin', 'Yaşlı', 'Genç']
    pass""",
        test_cases=[
            {'input': [15, 25, 70, 5, 45], 'expected': ['Genç', 'Yetişkin', 'Yaşlı', 'Genç', 'Yetişkin']},
        ],
        hints=[
            '💡 İpucu 1: Her yaş için koşullu kontrol yap.',
            "💡 İpucu 2: if age <= 17: 'Genç', elif age <= 64: 'Yetişkin', else: 'Yaşlı'",
            '💡 İpucu 3: List comprehension kullan: [segment(a) for a in ages]',
        ],
    ),

    Question(
        id=43,
        title='Grup Toplamı',
        category='pandas',
        level='intermediate',
        description="""Satış verisinden bölge bazında toplam satışı hesapla.
Sonuç: {bölge: toplam_satış} sözlüğü""",
        starter_code="""def region_totals(sales: list) -> dict:
    # [{'region':'A','sales':100}, ...] -> {'A': 250, 'B': 150}
    pass""",
        test_cases=[
            {'input': [{'region': 'A', 'sales': 100}, {'region': 'B', 'sales': 50}, {'region': 'A', 'sales': 150}, {'region': 'B', 'sales': 100}], 'expected': {'A': 250, 'B': 150}},
        ],
        hints=[
            '💡 İpucu 1: Boş bir dict: totals = {}',
            '💡 İpucu 2: Her kayıt için totals[region] = totals.get(region, 0) + sales',
            "💡 İpucu 3: totals dict'ini döndür.",
        ],
    ),

    Question(
        id=44,
        title='Aykırı Değer Tespiti',
        category='pandas',
        level='intermediate',
        description="""IQR yöntemiyle aykırı değerleri tespit et.
Q1-1.5*IQR altındakiler veya Q3+1.5*IQR üstündekiler aykırıdır.
Sonuç: aykırı değerlerin indeks listesi.""",
        starter_code="""def detect_outliers(data: list) -> list:
    # Aykırı değerlerin indekslerini döndür
    pass""",
        test_cases=[
            {'input': [1, 2, 2, 3, 3, 3, 100], 'expected': [6]},
            {'input': [10, 11, 12, 13, 14, 15], 'expected': []},
        ],
        hints=[
            '💡 İpucu 1: Sıralı listeden Q1 (25. yüzdelik) ve Q3 (75. yüzdelik) hesapla.',
            '💡 İpucu 2: IQR = Q3 - Q1; alt sınır = Q1 - 1.5*IQR, üst sınır = Q3 + 1.5*IQR',
            '💡 İpucu 3: [i for i, x in enumerate(data) if x < lower or x > upper]',
        ],
    ),

    Question(
        id=45,
        title='Rolling Ortalama',
        category='pandas',
        level='intermediate',
        description="""k pencereli rolling (kayan) ortalama hesapla.
İlk k-1 değer için sonuç None olsun.""",
        starter_code="""def rolling_average(data: list, k: int) -> list:
    # k pencereli kayan ortalama
    pass""",
        test_cases=[
            {'input': {'data': [1, 2, 3, 4, 5], 'k': 3}, 'expected': [None, None, 2.0, 3.0, 4.0]},
            {'input': {'data': [10, 20, 30, 40], 'k': 2}, 'expected': [None, 15.0, 25.0, 35.0]},
        ],
        hints=[
            '💡 İpucu 1: İlk k-1 değer için None döndür.',
            '💡 İpucu 2: i >= k-1 için: sum(data[i-k+1:i+1]) / k',
            '💡 İpucu 3: Sonuç listesi oluştur ve her adımda ekle.',
        ],
    ),

    Question(
        id=46,
        title='İkili Arama',
        category='algorithms',
        level='beginner',
        description="""Sıralı bir listede binary search ile hedef sayının indeksini döndür.
Bulunamazsa -1 döndür.""",
        starter_code="""def binary_search(arr: list, target: int) -> int:
    # O(log n) zaman karmaşıklığı hedefle
    pass""",
        test_cases=[
            {'input': {'arr': [1, 3, 5, 7, 9, 11], 'target': 7}, 'expected': 3},
            {'input': {'arr': [1, 3, 5, 7, 9, 11], 'target': 6}, 'expected': -1},
            {'input': {'arr': [1], 'target': 1}, 'expected': 0},
        ],
        hints=[
            '💡 İpucu 1: left=0, right=len(arr)-1 ile başla.',
            '💡 İpucu 2: mid = (left+right)//2; arr[mid]>target ise right=mid-1, küçükse left=mid+1',
            "💡 İpucu 3: arr[mid]==target ise mid'i döndür. Döngü biterse -1.",
        ],
    ),

    Question(
        id=47,
        title='Bubble Sort',
        category='algorithms',
        level='beginner',
        description="""Bubble sort algoritmasıyla bir listeyi küçükten büyüğe sırala.
Orijinal listeyi değiştirme, kopyasını döndür.""",
        starter_code="""def bubble_sort(arr: list) -> list:
    # Her geçişte büyük elemanları sona taşı
    pass""",
        test_cases=[
            {'input': [64, 34, 25, 12, 22, 11, 90], 'expected': [11, 12, 22, 25, 34, 64, 90]},
            {'input': [5, 1, 4, 2, 8], 'expected': [1, 2, 4, 5, 8]},
        ],
        hints=[
            '💡 İpucu 1: arr = arr[:] ile kopya al.',
            '💡 İpucu 2: İki iç içe döngü: dış n kez, iç komşuları karşılaştırır.',
            '💡 İpucu 3: arr[j] > arr[j+1] ise swap yap: arr[j], arr[j+1] = arr[j+1], arr[j]',
        ],
    ),

    Question(
        id=68,
        title='İki Maaş Bordrosunu Birleştir',
        category='algorithms',
        level='intermediate',
        description="""İK ekibindesin. Elinde iki bölümün maaş listesi var:
  - mühendislik (azalan sırada, en yüksek maaş başta)
  - pazarlama (artan sırada, en düşük maaş başta)

İki listeyi **birleştirip tek maaş listesi** oluşturman lazım.
Sonuç azalan sırada olmalı (en yüksek maaş başta).

📌 Önemli: Her iki girdi listesi de kendi içinde sıralı.
   Bu sana avantaj sağlıyor — sıfırdan sıralama yapma.

⚠️ sorted()/sort() KULLANMA. Mülakat sorusu olarak
   O(n+m) yerine O(n log n) yazarsan eleniyorsun.

💡 İpucu (gizli): İki sıralı listeyi tek sıralı liste yapmak için
   klasik bir algoritma var — ismi "merge". İnternette
   'merge two sorted lists' diye aratabilirsin ama önce kendin dene.""",
        starter_code="""def merge_salaries(engineering: list, marketing: list) -> list:
    # İki sıralı listeyi birleştir, sonuç azalan sırada
    # engineering: azalan sırada (örn [12000, 9000, 8000])
    # marketing:  artan sırada  (örn [4000, 5000, 6500])
    # Sonuç: azalan sırada, tüm maaşlar
    pass""",
        test_cases=[
            # Temel durum — 3+3
            {
                'input': ([12000, 9000, 8000], [4000, 5000, 6500]),
                'expected': [12000, 9000, 8000, 6500, 5000, 4000],
            },
            # Sınır durumu — biri boş
            {'input': ([], [3000, 5000]), 'expected': [5000, 3000]},
            {'input': ([10000, 5000], []), 'expected': [10000, 5000]},
            # İkisi de boş
            {'input': ([], []), 'expected': []},
            # Karışık değerler
            {
                'input': ([15000, 11000, 7000], [8500, 6000, 4000]),
                'expected': [15000, 11000, 8500, 7000, 6000, 4000],
            },
        ],
        hints=[
            '💡 İpucu 1: İki pointer kullan — biri engineering, biri marketing için. İlk elemanları karşılaştır.',
            '💡 İpucu 2: Engineering azalan (büyük → küçük), marketing artan (küçük → büyük). Yani engineering[0] en büyük, marketing[0] en küçük.',
            '💡 İpucu 3: Hangisinin maaşı daha büyükse onu sonuca ekle, o pointer’ı ilerlet. Biri bitince diğerini olduğu gibi ekle.',
        ],
        explanation="""**Çözüm: Two-Pointer Merge (Klasik Merge Adımı)**

Bu soru merge sort algoritmasının temel parçasıdır:
**"İki sıralı listeyi tek sıralı liste yap"**.

```python
def merge_salaries(engineering, marketing):
    result = []
    i, j = 0, 0
    while i < len(engineering) and j < len(marketing):
        # engineering azalan (büyük başta), marketing artan (küçük başta)
        # En büyük maaşı engineering[0] veya marketing[-1] tutar
        if engineering[i] >= marketing[len(marketing) - 1 - j]:
            result.append(engineering[i])
            i += 1
        else:
            result.append(marketing[len(marketing) - 1 - j])
            j += 1
    # Kalanları olduğu gibi ekle
    result.extend(engineering[i:])
    result.extend(reversed(marketing[:len(marketing) - j]))
    return result
```

**Daha temiz yaklaşım (iki listeyi aynı yöne çevir):**

```python
def merge_salaries(engineering, marketing):
    # engineering azalan, marketing artan → ikisini azalana çevir
    m = sorted(marketing, reverse=True)  # sadece marketing için
    # Artık ikisi de azalan sırada
    result, i, j = [], 0, 0
    while i < len(engineering) and j < len(m):
        if engineering[i] >= m[j]:
            result.append(engineering[i])
            i += 1
        else:
            result.append(m[j])
            j += 1
    result.extend(engineering[i:])
    result.extend(m[j:])
    return result
```

**Karmaşıklık:**
- Zaman: **O(n + m)** — her eleman bir kez ziyaret edilir
- Alan: **O(n + m)** — sonuç listesi

**Neden bu önemli?**
Bu "merge" adımı merge sort'un (O(n log n)) temel taşıdır.
Eğer bu adımı sorted() ile yaparsan → O((n+m) log(n+m)) olur, mülakatta elenme sebebi.

**Mülakat metaforu:**
"İki klasörün sıralı sayfalarını tek masada birleştiriyorsun" — bu da aynı şey.""",
        complexity="O(n+m) — iki sıralı listenin tek geçişte birleştirilmesi",
    ),

    Question(
        id=48,
        title='Bozuk Para Hesabı (Greedy)',
        category='algorithms',
        level='beginner',
        description="""Verilen miktarı en az sayıda bozuk para ile öde.
Kullanılabilir bozukluklar: [100,50,25,10,5,1] kuruş.""",
        starter_code="""def make_change(amount: int) -> dict:
    # {100:x, 50:y, ...} kaç tane hangi bozukluktan
    coins = [100, 50, 25, 10, 5, 1]
    pass""",
        test_cases=[
            {'input': 187, 'expected': {100: 1, 50: 1, 25: 1, 10: 1, 5: 0, 1: 2}},
            {'input': 75, 'expected': {100: 0, 50: 1, 25: 1, 10: 0, 5: 0, 1: 0}},
        ],
        hints=[
            '💡 İpucu 1: Her bozukluk için: count = amount // coin',
            '💡 İpucu 2: amount = amount % coin ile kalanı güncelle.',
            '💡 İpucu 3: Sonuçları result[coin] = count olarak sakla.',
        ],
    ),

    Question(
        id=49,
        title='Kaplama Problemi',
        category='algorithms',
        level='intermediate',
        description="""n merdiven basamağı var. Her adımda 1 veya 2 basamak çıkabilirsin.
Kaç farklı yol var? (Dinamik programlama)""",
        starter_code="""def climb_stairs(n: int) -> int:
    # DP ile çöz: dp[i] = dp[i-1] + dp[i-2]
    pass""",
        test_cases=[
            {'input': 2, 'expected': 2},
            {'input': 3, 'expected': 3},
            {'input': 5, 'expected': 8},
        ],
        hints=[
            '💡 İpucu 1: Bu aslında Fibonacci dizisi! dp[1]=1, dp[2]=2',
            '💡 İpucu 2: dp[i] = dp[i-1] + dp[i-2] (bir önceki veya iki önceki basamaktan gelir)',
            '💡 İpucu 3: Hafıza optimizasyonu için yalnızca son iki değeri tut.',
        ],
    ),

    Question(
        id=50,
        title='En Kısa Yol (BFS)',
        category='algorithms',
        level='intermediate',
        description="""Bir 2D grid'de (0=geçit, 1=duvar) baştan (0,0) hedefe (n-1,m-1) en kısa yol kaç adım?
Yol yoksa -1 döndür.""",
        starter_code="""def shortest_path(grid: list) -> int:
    # BFS ile en kısa yol
    pass""",
        test_cases=[
            {'input': [[0, 0, 0], [1, 1, 0], [0, 0, 0]], 'expected': 4},
            {'input': [[0, 1], [1, 0]], 'expected': -1},
        ],
        hints=[
            '💡 İpucu 1: BFS için queue kullan: [(0,0,0)]  # (satır, sütun, adım)',
            '💡 İpucu 2: Ziyaret edilenleri takip et: visited = set(); visited.add((0,0))',
            '💡 İpucu 3: 4 yön: [(-1,0),(1,0),(0,-1),(0,1)]; sınır ve duvar kontrolü yap.',
        ],
    ),
    Question(
        id=70,
        title='En Yakın Rakam Toplamı',
        category='algorithms',
        level='intermediate',
        description="""Bir sayı dizisinde, toplamı hedef sayıya en yakın olan iki elemanı bul.
Birden fazla çözüm varsa, herhangi birini döndürmek yeterli.
Sonuç: [eleman1, eleman2] şeklinde liste döndür.\nÖrnek: [1, 2, 3, 4, 5], hedef = 8 → [3, 5] (toplam 8, tam isabet)
Örnek: [1, 2, 3, 4], hedef = 10 → [4, 4] veya [1, 4] (en yakın toplam 9)""",
        starter_code="""def find_closest_pair(numbers: list, target: int) -> list:
    # İki elemanın toplamı hedefe en yakın olsun
    pass""",
        test_cases=[
            {'input': {'numbers': [1, 2, 3, 4, 5], 'target': 8}, 'expected': [3, 5]},
            {'input': {'numbers': [1, 2, 3, 4], 'target': 10}, 'expected': [4, 4]},
            {'input': {'numbers': [3, 3, 3], 'target': 6}, 'expected': [3, 3]},
            {'input': {'numbers': [-1, -2, -3, -4], 'target': -5}, 'expected': [-1, -4]},
            {'input': {'numbers': [1, 5, 9, 13], 'target': 11}, 'expected': [-1, -1]},
        ],
        hints=[
            '💡 İpucu 1: Önce listeyi sırala (sıralanmış liste ile çalışmak daha kolay).',
            '💡 İpucu 2: İki işaretçi tekniği kullan — biri başta, biri sonda.',
            '💡 İpucu 3: current_sum = arr[left] + arr[right]; hedefe göre işaretçileri hareket ettir.',
        ],
    ),

    Question(
        id=71,
        title='Tekrarlanan Karakter Zinciri',
        category='algorithms',
        level='intermediate',
        description="""Bir string'de art arda tekrar eden karakterlerden oluşan
en uzun zinciri bul.
Sonuç: (karakter, zincir uzunluğu) şeklinde tuple döndür.\nÖrnek: 'aabbbcccddaaa' → ('b', 3) veya ('a', 3)
Örnek: 'abcdef' → ('a', 1) (tüm karakterler 1'er)""",
        starter_code="""def longest_char_chain(s: str) -> tuple:
    # Art arda tekrar eden en uzun zinciri bul
    pass""",
        test_cases=[
            {'input': 'aabbbcccddaaa', 'expected': ('b', 3)},
            {'input': 'abcdef', 'expected': ('a', 1)},
            {'input': 'aaaaa', 'expected': ('a', 5)},
            {'input': 'abbaa', 'expected': ('a', 2)},
            {'input': '', 'expected': ('', 0)},
            {'input': 'abccdeeeffg', 'expected': ('e', 3)},
        ],
        hints=[
            '💡 İpucu 1: İki değişken tut: mevcut karakter ve mevcut sayı.',
            '💡 İpucu 2: Her yeni karakter için: aynıysa sayıyı artır, farklıysa sıfırla.',
            '💡 İpucu 3: En uzun zinciri ve karakterini takip et.',
        ],
    ),

    Question(
        id=72,
        title='Alt Dizi Toplam Kontrolü',
        category='algorithms',
        level='intermediate',
        description="""Bir sayı listesi ve bir hedef sayı veriliyor.
Listedeki herhangi bir alt dizinin (continuous subsequence)
toplamının hedef sayıya eşit olup olmadığını kontrol et.\n⚠️ Tüm alt dizileri brute-force deneme O(n²) yapma.
Daha verimli bir yöntem düşün.""",
        starter_code="""def has_subarray_with_sum(nums: list, target: int) -> bool:
    # Alt dizi toplamı hedefe eşit mi?
    pass""",
        test_cases=[
            {'input': {'nums': [1, 4, 20, 3, 10, 5], 'target': 33}, 'expected': True},
            {'input': {'nums': [1, 2, 3, 4], 'target': 15}, 'expected': False},
            {'input': {'nums': [1, 2, 3], 'target': 6}, 'expected': True},
            {'input': {'nums': [0, 0], 'target': 0}, 'expected': True},
            {'input': {'nums': [-2, -1, 0, 1, 2], 'target': 0}, 'expected': True},
        ],
        hints=[
            '💡 İpucu 1: Sliding window tekniği düşün — başlangıç ve bitiş işaretçileri.',
            '💡 İpucu 2: Mevcut toplam hedefi aştıysa, başlangıcı kaydır.',
            '💡 İpucu 3: Negatif sayılar varsa sliding window çalışmaz — prefix sum + hashmap dene.',
        ],
    ),

    Question(
        id=73,
        title='Benzersiz Alt Dizgi Sayısı',
        category='algorithms',
        level='intermediate',
        description="""Bir string'deki tüm benzersiz alt dizgilerin (substring)
sayısını bul.
Boş alt dizgi sayılmaz.\nÖrnek: 'abc' → 'a','b','c','ab','bc','abc' → 6
Örnek: 'aaa' → 'a','aa','aaa' → 2 (tekrarlar sayılmaz)
Örnek: '' → 0""",
        starter_code="""def count_unique_substrings(s: str) -> int:
    # Tüm benzersiz alt dizgilerin sayısını bul
    pass""",
        test_cases=[
            {'input': 'abc', 'expected': 6},
            {'input': 'aaa', 'expected': 2},
            {'input': '', 'expected': 0},
            {'input': 'abcd', 'expected': 10},
            {'input': 'aab', 'expected': 4},
        ],
        hints=[
            '💡 İpucu 1: Her karakterden başlayarak tüm alt dizgileri oluştur.',
            '💡 İpucu 2: Bir set() kullanarak benzersiz olanları sakla.',
            '💡 İpucu 3: İç içe döngü yerine, her i için j=i+1,...,len(s) alt dizgisini sete ekle.',
        ],
    ),

    # ════════════════════════════════════════════════════════════════
    # 84: İç İçe Döngü — Çarpım Tablosu (donguler kategorisi yok,
    #     en yakin kategori: python-basics)
    # Kullanici: ic ice dongu pratiği, ipucu YOK
    # NOT: Frontend QUESTION_META 74-83 ID'lerini kullanıyor, 84+ uygun
    # ════════════════════════════════════════════════════════════════


    Question(
        id=84,
        title="Cift Sayilari Filtrele ve Karelerini Topla",
        category="python-basics",
        level="beginner",
        description="""Bir sayi listesi var. Listedeki SADECE cift sayilarin karelerini al ve topla.
Tek sayilar yok sayilir (sadece ciftler).
Ornek: [2, 3, 4, 5, 6] -> 4+16+36 = 56""",
        starter_code="""def sum_of_even_squares(nums: list) -> int:
    # Listedeki cift sayilarin kareleri toplami
    pass""",
        test_cases=[
            {'input': [2, 3, 4, 5, 6], 'expected': 56},
            {'input': [1, 3, 5, 7], 'expected': 0},
            {'input': [10], 'expected': 100},
            {'input': [], 'expected': 0},
        ],
        hints=[
            "💡 Ipucu 1: x % 2 == 0 ile cift sayilari filtrele.",
            "💡 Ipucu 2: sum() icinde generator expression kullan.",
            "💡 Ipucu 3: sum(x*x for x in nums if x % 2 == 0) tek satirda coz.",
        ],
    ),

    Question(
        id=85,
        title="Iki String Arasindaki Ortak Karakterler",
        category="python-basics",
        level="beginner",
        description="""Iki string veriliyor. Her iki stringde de GECEN (kucuk harf duyarsiz) benzersiz
karakterleri alfabetik sirada dondur.
Ornek: "Merhaba" ve "Araba" -> ['a', 'r'] (sirali)""",
        starter_code="""def common_chars(a: str, b: str) -> list:
    # Iki stringde ortak olan benzersiz karakterler (kucuk harf), alfabetik sirali
    pass""",
        test_cases=[
            {'input': ['Merhaba', 'Araba'], 'expected': ['a', 'r']},
            {'input': ['Python', 'Java'], 'expected': ['a']},
            {'input': ['abc', 'def'], 'expected': []},
            {'input': ['AAA', 'aaa'], 'expected': ['a']},
        ],
        hints=[
            "💡 Ipucu 1: set(a.lower()) & set(b.lower()) -> kesisim.",
            "💡 Ipucu 2: sorted() ile alfabetik siraya koy.",
            "💡 Ipucu 3: list(sorted(set(a.lower()) & set(b.lower()))) tek satir.",
        ],
    ),

    Question(
        id=86,
        title="Listedeki En Sik Tekrar Eden Eleman",
        category="python-basics",
        level="beginner",
        description="""Bir liste var. En sik gecen elemani dondur.
Birden fazla esit siklik varsa en kucuk sayiyi veya alfabetik ilk olani dondur.
Ornek: [1, 3, 2, 3, 4, 1, 1] -> 1 (4 kez)
Ornek: ['a', 'b', 'a', 'c'] -> 'a' (2 kez, alfabetik ilk)""",
        starter_code="""def most_frequent(items: list) -> object:
    # En sik gecen eleman
    pass""",
        test_cases=[
            {'input': [1, 3, 2, 3, 4, 1, 1], 'expected': 1},
            {'input': ['a', 'b', 'a', 'c'], 'expected': 'a'},
            {'input': [5, 5, 3, 3, 1], 'expected': 3},
            {'input': [1], 'expected': 1},
        ],
        hints=[
            "💡 Ipucu 1: from collections import Counter -> Counter(items).most_common().",
            "💡 Ipucu 2: max_count = max(c.values()) -> en yuksek frekans.",
            "💡 Ipucu 3: candidates = [k for k,v in c.items() if v == max_count]; min(candidates) ile coz.",
        ],
    ),

    Question(
        id=87,
        title="Donen Dizi Kontrolu",
        category="python-basics",
        level="beginner",
        description="""Bir liste veriliyor. Liste dondurulmus (rotated) sirali mi kontrol et.
Donduerme: sirali bir diziyi herhangi bir noktadan kesip sona ekle. [3,4,5,1,2] sirali [1,2,3,4,5]'in
rotasyonudur (3 kesildi).
Tek elemanli liste her zaman True. Bos liste True.
Iki kez ayni eleman art arda olursa False (sirali degil).""",
        starter_code="""def is_rotated_sorted(nums: list) -> bool:
    # Liste dondurulerek sirali mi?
    pass""",
        test_cases=[
            {'input': [3, 4, 5, 1, 2], 'expected': True},
            {'input': [1, 2, 3, 4, 5], 'expected': True},
            {'input': [2, 1, 3], 'expected': False},
            {'input': [1], 'expected': True},
            {'input': [], 'expected': True},
            {'input': [2, 2, 2, 2, 1, 2], 'expected': False},
        ],
        hints=[
            "💡 Ipucu 1: Sirali dizide en fazla 1 i var ki nums[i] > nums[i+1] olur (rotasyon noktasi).",
            "💡 Ipucu 2: count = sum(1 for i in range(n) if nums[i] > nums[(i+1)%n]).",
            "💡 Ipucu 3: count == 0 (zaten sirali) veya count == 1 (rotasyon) -> True.",
        ],
    ),

    Question(
        id=88,
        title="Sayilari Toplami Hedefe Esit Olan Ciftler",
        category="algorithms",
        level="intermediate",
        description="""Bir liste ve bir hedef sayi var. Listedeki hangi iki sayinin toplami hedefe esit?
Tum benzersiz ciftleri (kucuk, buyuk) sirali liste olarak dondur.
Ayni eleman iki kez kullanilamaz.
Hic cift yoksa bos liste dondur.
Ornek: nums=[2,7,11,15], target=9 -> [[2,7]]""",
        starter_code="""def two_sum_pairs(nums: list, target: int) -> list:
    # Toplami target'a esit olan benzersiz ciftler
    pass""",
        test_cases=[
            {'input': ([2, 7, 11, 15], 9), 'expected': [[2, 7]]},
            {'input': ([1, 5, 3, 7, 9], 12), 'expected': [[3, 9], [5, 7]]},
            {'input': ([1, 2, 3], 10), 'expected': []},
            {'input': ([3, 3], 6), 'expected': [[3, 3]]},
            {'input': ([-1, -2, -3, 4, 5], 2), 'expected': [[-3, 5], [-1, 3]]},
        ],
        hints=[
            "💡 Ipucu 1: Set kullan: seen = set(). Her num icin target-num sette mi kontrol et.",
            "💡 Ipucu 2: pair = sorted([num, target-num]); result.add(tuple(pair)).",
            "💡 Ipucu 3: set() ile tekrarlari otomatik onle, sorted() ile sirala.",
        ],
    ),

    Question(
        id=89,
        title="Rotasyon Adimini Bul",
        category="algorithms",
        level="intermediate",
        description="""Bir liste veriliyor. Bu liste sirali bir dizinin rotasyonu.
Rotasyon adimini bul (kac kez sola donduruldu).
[3,4,5,1,2] sirali [1,2,3,4,5]'in 3 sola rotasyonu -> 3 dondur.
Zaten sirali ise 0.
[1,2,3,4,5] -> 0
[5,1,2,3,4] -> 1 (sola)
Not: Rotasyon adimi 0 ile len(nums)-1 arasinda.""",
        starter_code="""def rotation_count(nums: list) -> int:
    # Sirali dizinin kac adim sola donduruldugunu bul
    pass""",
        test_cases=[
            {'input': [3, 4, 5, 1, 2], 'expected': 3},
            {'input': [1, 2, 3, 4, 5], 'expected': 0},
            {'input': [5, 1, 2, 3, 4], 'expected': 1},
            {'input': [2, 3, 4, 5, 1], 'expected': 4},
            {'input': [1], 'expected': 0},
        ],
        hints=[
            "💡 Ipucu 1: Minimum elemanin indexini bul.",
            "💡 Ipucu 2: min_idx = nums.index(min(nums)).",
            "💡 Ipucu 3: return min_idx (0 = zaten sirali, min_idx = kac adim sola).",
        ],
    ),

    Question(
        id=90,
        title="String'i Tersine Cevir (Kelime Bazli)",
        category="strings",
        level="intermediate",
        description="""Bir cumle var. Kelime sirasini tersine cevir, kelime icindeki harfler ayni kalsin.
Ornek: 'Merhaba dunya nasilsin' -> 'nasilsin dunya Merhaba'
Fazla bosluklari tek bosluga indir.""",
        starter_code="""def reverse_words(s: str) -> str:
    # Cumleyi kelime bazli tersine cevir
    pass""",
        test_cases=[
            {'input': 'Merhaba dunya nasilsin', 'expected': 'nasilsin dunya Merhaba'},
            {'input': 'Python   harika  bir dil', 'expected': 'dil bir harika Python'},
            {'input': 'tek', 'expected': 'tek'},
            {'input': '', 'expected': ''},
            {'input': '  bosluklu   cumle  ', 'expected': 'cumle bosluklu'},
        ],
        hints=[
            "💡 Ipucu 1: s.split() -> bosluklari otomatik normalize eder.",
            "💡 Ipucu 2: words[::-1] ile kelime listesini tersine cevir.",
            '💡 Ipucu 3: " ".join(words[::-1]) ile birlestir.',
        ],
    ),

    Question(
        id=91,
        title="Liste Icinde Yinelenenleri Kaldir (Sirayi Koru)",
        category="python-basics",
        level="beginner",
        description="""Bir liste var. Listedeki tekrarlari kaldir, ilk gorunme sirasini koru.
Ornek: [1, 3, 2, 3, 4, 1, 5] -> [1, 3, 2, 4, 5] (3 ve 1 tekrari atlanir)""",
        starter_code="""def remove_duplicates(items: list) -> list:
    # Yinelenenleri kaldir, ilk gorunme sirasini koru
    pass""",
        test_cases=[
            {'input': [1, 3, 2, 3, 4, 1, 5], 'expected': [1, 3, 2, 4, 5]},
            {'input': ['a', 'b', 'a', 'c', 'b'], 'expected': ['a', 'b', 'c']},
            {'input': [1, 2, 3], 'expected': [1, 2, 3]},
            {'input': [], 'expected': []},
            {'input': [1, 1, 1], 'expected': [1]},
        ],
        hints=[
            "💡 Ipucu 1: seen = set() ile takip et.",
            "💡 Ipucu 2: if x not in seen: result.append(x); seen.add(x).",
            "💡 Ipucu 3: dict.fromkeys(items) ile tek satirda coz (Python 3.7+ dict sira korur).",
        ],
    ),

    Question(
        id=92,
        title="Matris Cevirme (Transpose Etme)",
        category="python-basics",
        level="beginner",
        description="""Bir 2D matris var. Satirlari sutun, sutunlari satir yap.
Ornek: [[1,2,3], [4,5,6]] -> [[1,4], [2,5], [3,6]]
Dikdortgen matrisler icin calissin (tum satirlar ayni uzunlukta).""",
        starter_code="""def transpose(matrix: list) -> list:
    # 2D matrisi transpoze et
    pass""",
        test_cases=[
            {'input': [[1, 2, 3], [4, 5, 6]], 'expected': [[1, 4], [2, 5], [3, 6]]},
            {'input': [[1, 2], [3, 4], [5, 6]], 'expected': [[1, 3, 5], [2, 4, 6]]},
            {'input': [[1]], 'expected': [[1]]},
            {'input': [[1, 2, 3]], 'expected': [[1], [2], [3]]},
        ],
        hints=[
            "💡 Ipucu 1: zip(*matrix) ile transpoze et (Pythonic).",
            "💡 Ipucu 2: list(zip(*matrix)) tuple listesi doner, list(map(list, ...)) ile liste listesi yap.",
            "💡 Ipucu 3: Manuel: [[matrix[r][c] for r in range(len(matrix))] for c in range(len(matrix[0]))].",
        ],
    ),

    Question(
        id=93,
        title="Ilk Tekrar Etmeyen Karakter",
        category="strings",
        level="intermediate",
        description="""Bir string veriliyor. Ilk kez tekrarlanMAYAN (unique) karakteri bul.
Yoksa bos string dondur.
Ornek: 'swiss' -> 'w' (s ve i tekrar eder, w sadece 1 kez)
Ornek: 'aabbcc' -> '' (hepsi tekrar)""",
        starter_code="""def first_unique_char(s: str) -> str:
    # Ilk tekrar etmeyen karakter
    pass""",
        test_cases=[
            {'input': 'swiss', 'expected': 'w'},
            {'input': 'aabbcc', 'expected': ''},
            {'input': 'programming', 'expected': 'p'},
            {'input': 'aabb', 'expected': ''},
            {'input': 'z', 'expected': 'z'},
        ],
        hints=[
            "💡 Ipucu 1: from collections import Counter -> c = Counter(s).",
            "💡 Ipucu 2: for ch in s: if c[ch] == 1: return ch.",
            "💡 Ipucu 3: Bos string icin '' dondur (return ch if any(c[ch]==1 for ch in s) else '').",
        ],
    ),

]
# 1783001822
