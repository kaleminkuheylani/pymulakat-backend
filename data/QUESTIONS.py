# data/QUESTIONS.py
from dataclasses import dataclass, field
from typing import List, Dict, Any

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
        id=6,
        title='Karakter Sayacı',
        category='python-basics',
        level='beginner',
        description="""Bir metindeki her karakterin kaç kez geçtiğini döndür.
Boşlukları sayma. Büyük/küçük harf duyarlı olmasın.""",
        starter_code="""def char_count(text: str) -> dict:
    # Boşluk hariç her karakterin frekansını döndür
    pass""",
        test_cases=[
            {'input': 'Hello World', 'expected': {'h': 1, 'e': 1, 'l': 3, 'o': 2, 'w': 1, 'r': 1, 'd': 1}},
            {'input': 'aabbcc', 'expected': {'a': 2, 'b': 2, 'c': 2}},
        ],
        hints=[
            '💡 İpucu 1: text.lower() ile metni küçük harfe çevir.',
            "💡 İpucu 2: Her karakter için boşluk kontrolü: if c != ' '",
            '💡 İpucu 3: dict.get(c, 0) + 1 ile sayacı artır ya da collections.Counter kullan.',
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
        id=15,
        title='Sayı Heceleme',
        category='python-basics',
        level='beginner',
        description="""0-999 arası bir sayıyı Türkçe olarak hecelere yaz.
Örnek: 42 → 'kırk iki', 100 → 'yüz'""",
        starter_code="""def number_to_words(n: int) -> str:
    ones = ['','bir','iki','üç','dört','beş','altı','yedi','sekiz','dokuz']
    tens = ['','on','yirmi','otuz','kırk','elli','altmış','yetmiş','seksen','doksan']
    # Buraya kodunu yaz
    pass""",
        test_cases=[
            {'input': 0, 'expected': 'sıfır'},
            {'input': 15, 'expected': 'on beş'},
            {'input': 42, 'expected': 'kırk iki'},
            {'input': 100, 'expected': 'yüz'},
            {'input': 256, 'expected': 'iki yüz elli altı'},
        ],
        hints=[
            "💡 İpucu 1: n == 0 ise 'sıfır' döndür.",
            "💡 İpucu 2: Yüzler basamağı: n // 100 → 'X yüz', onlar: (n % 100) // 10, birler: n % 10",
            "💡 İpucu 3: Parçaları bir listeye ekle, boşlukla birleştir: ' '.join(parts)",
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
        id=17,
        title='Slug Oluşturucu',
        category='strings',
        level='beginner',
        description="""Bir başlığı URL-dostu slug'a çevir.
Küçük harf, boşlukları tire ile değiştir, özel karakterleri kaldır.""",
        starter_code="""def create_slug(title: str) -> str:
    # "Merhaba Dünya! Python öğreniyorum" → "merhaba-dunya-python-ogreniyorum"
    pass""",
        test_cases=[
            {'input': 'Merhaba Dünya', 'expected': 'merhaba-dunya'},
            {'input': 'Python 3.11 Neler Getirdi?', 'expected': 'python-311-neler-getirdi'},
        ],
        hints=[
            '💡 İpucu 1: .lower() ile küçük harfe çevir.',
            "💡 İpucu 2: Türkçe karakterleri değiştir: 'ş'→'s', 'ğ'→'g', vb.",
            "💡 İpucu 3: Harf/rakam olmayanları kaldır, boşlukları '-' yap.",
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
        id=23,
        title='Kelime Sayısı (Gelişmiş)',
        category='strings',
        level='beginner',
        description="""Bir metinde her satırdaki kelime sayısını döndür.
Boş satırları sıfır olarak say.""",
        starter_code="""def word_count_per_line(text: str) -> list:
    # Satır satır böl, her satırdaki kelime sayısını döndür
    pass""",
        test_cases=[
            {'input': 'Merhaba dünya\nPython öğreniyorum\n', 'expected': [2, 2, 0]},
            {'input': 'bir\n\nüç', 'expected': [1, 0, 1]},
        ],
        hints=[
            "💡 İpucu 1: text.split('\\n') ile satırlara böl.",
            '💡 İpucu 2: Her satır için len(line.split()) kelime sayısını verir.',
            '💡 İpucu 3: List comprehension: [len(line.split()) for line in lines]',
        ],
    ),

    Question(
        id=24,
        title='Cümle Başlığı',
        category='strings',
        level='beginner',
        description="""Her kelimenin ilk harfini büyük yap (Title Case),
ama bağlaçları ('ve','ile','ya','ya da') küçük bırak.""",
        starter_code="""def smart_title(sentence: str) -> str:
    exceptions = {'ve','ile','ya','veya','de','da'}
    # İlk kelime her zaman büyük, diğerleri kural dahilinde
    pass""",
        test_cases=[
            {'input': 'python ve django ile web geliştirme', 'expected': 'Python ve Django ile Web Geliştirme'},
            {'input': 'merhaba dünya', 'expected': 'Merhaba Dünya'},
        ],
        hints=[
            '💡 İpucu 1: Kelimelere ayır, ilk kelimeyi her zaman büyük yap.',
            '💡 İpucu 2: Diğer kelimeler için: exceptions setinde varsa küçük, yoksa .capitalize()',
            "💡 İpucu 3: ' '.join(result_words) ile birleştir.",
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
        id=51,
        title='💖 Emoji Envanteri: Sosyal Medya Duygu Analizi',
        category='strings',
        level='intermediate',
        description="""Sosyal medya platformumuzdaki gönderilerin genel duygu tonunu anlamak için hızlı bir analiz aracına ihtiyacımız var! 📊 Göreviniz, verilen bir metin içindeki belirli pozitif, negatif ve nötr emojileri sayarak bir 'duygu envanteri' oluşturmaktır. Fonksiyonunuz, metni taramalı ve her kategoriye ait emojilerin toplam sayısını içeren bir sözlük döndürmelidir. 🕵️‍♀️ Bu, içerik yöneticilerimizin etkileşimi daha iyi anlamasına yardımcı olacak! 

**Emoji Kategorileri (Örnekler):**
- **Pozitif:** 😂, 👍, ❤️, ✨, 🥳
- **Negatif:** 😠, 👎, 😔, 💔, 😭
- **Nötr:** 💡, 📍, 📚, ⏰, 🤔

**Örnek Kullanım:**
Input: "Harika bir gün! ✨ Çok eğlendim 😂👍 ama biraz da düşündürücü 🤔"
Output: {"pozitif": 3, "negatif": 0, "nötr": 1}""",
        starter_code="""def emoji_analizcisi(metin: str) -> dict:
    # Bu alan, pozitif, negatif ve nötr emojileri tanımladığınız yer olacak.
    pozitif_emojiler = ['😂', '👍', '❤️', '✨', '🥳']
    negatif_emojiler = ['😠', '👎', '😔', '💔', '😭']
    notr_emojiler = ['💡', '📍', '📚', '⏰', '🤔']

    # Başlangıçta sayaçları sıfırlayın
    sayaclar = {
        "pozitif": 0,
        "negatif": 0,
        "nötr": 0
    }

    # Metin üzerinde karakter karakter gezinerek emojileri sayın.
    pass""",
        test_cases=[
            {'input': 'Harika bir gün! ✨ Çok eğlendim 😂👍', 'expected': {'pozitif': 3, 'negatif': 0, 'nötr': 0}},
            {'input': 'Çok üzgünüm 😔 neden böyle oldu ki 💔😭', 'expected': {'pozitif': 0, 'negatif': 3, 'nötr': 0}},
            {'input': 'Ders çalışıyorum 📚 yeni bir fikir💡 çıktı ama henüz emin değilim 🤔', 'expected': {'pozitif': 0, 'negatif': 0, 'nötr': 3}},
            {'input': 'Bugün hava güzel.☕️ Kahve içtim. Hava karardı.', 'expected': {'pozitif': 0, 'negatif': 0, 'nötr': 0}},
            {'input': 'Karışık duygular: 😂😔👍💔📚💡', 'expected': {'pozitif': 2, 'negatif': 2, 'nötr': 2}},
            {'input': '', 'expected': {'pozitif': 0, 'negatif': 0, 'nötr': 0}},
            {'input': 'Sadece bir metin parçasıdır, emoji yok.', 'expected': {'pozitif': 0, 'negatif': 0, 'nötr': 0}},
            {'input': '🥳✨🥳✨ Bu bir parti! 🎉', 'expected': {'pozitif': 4, 'negatif': 0, 'nötr': 0}},
            {'input': 'Her şey çok kötü 😭😠👎', 'expected': {'pozitif': 0, 'negatif': 3, 'nötr': 0}},
        ],
        hints=[
            "💡 İpucu 1: Fonksiyonun başında, pozitif, negatif ve nötr emojileri ayrı Python listeleri (veya setleri) olarak tanımlayın. Örneğin: `pozitif_emojiler = ['😂', '👍', '❤️']`",
            '💡 İpucu 2: Sonuçları tutmak için `{"pozitif": 0, "negatif": 0, "nötr": 0}` şeklinde bir sözlük (dictionary) oluşturarak başlayın.',
            "💡 İpucu 3: Gelen `metin` parametresi üzerinde bir `for` döngüsü kullanarak her bir karakteri (emoji dahil) tek tek kontrol edin. Python'da emojiler de tek karakter gibi işlenir.",
            '💡 İpucu 4: Her karakteri kontrol ederken, `if karakter in pozitif_emojiler:` gibi koşullu ifadeler kullanarak karakterin hangi emoji kategorisine ait olduğunu belirleyin ve ilgili sayacı artırın.',
        ],
    ),

    Question(
        id=52,
        title='🕵️\u200d♀️ Emoji Gizemleri: Gizli Mesajı Bul! 🔍',
        category='strings',
        level='beginner',
        description="""Sosyal medyada arkadaşlarınla emoji dolu mesajlar paylaşıyorsun! 🥳 Bazı mesajlar ise özel bir gizem taşıyor. Belirli bir emoji deseniyle başlayan (⭐✨🌟) ve yine belirli bir emoji deseniyle biten (🌟✨⭐) mesajlar içinde gizli bir anahtar kelime saklı. Senin görevin, verilen bir mesajın bu gizemli formatta olup olmadığını kontrol etmek ve eğer öyleyse, o gizli anahtar kelimeyi bulup çıkarmak! 🤫

**Örnek Kullanım:**

Girdi: `⭐✨🌟PythonHarika🌟✨⭐`
Çıktı: `PythonHarika`

Girdi: `Merhaba dünya! 👋`
Çıktı: `None`

Girdi: `⭐✨🌟🌟✨⭐`
Çıktı: `''` (boş string)""",
        starter_code="""def gizli_mesaji_bul(mesaj: str) -> str | None:
    # Mesajın belirli emoji desenleriyle başlayıp bitmediğini kontrol et.
    # Eğer öyleyse, bu desenleri mesajdan çıkararak gizli anahtar kelimeyi bul.
    pass""",
        test_cases=[
            {'input': '⭐✨🌟PythonHarika🌟✨⭐', 'expected': 'PythonHarika'},
            {'input': '⭐✨🌟KodlamakEglenceli🌟✨⭐', 'expected': 'KodlamakEglenceli'},
            {'input': '⭐✨🌟🌟✨⭐', 'expected': ''},
            {'input': 'Merhaba dünya! 👋', 'expected': None},
            {'input': '🚀✨🌟Merhaba🌟✨⭐', 'expected': None},
            {'input': '⭐✨🌟Merhaba🌟✨🚀', 'expected': None},
            {'input': 'Sadece normal bir mesaj.', 'expected': None},
            {'input': 'Bu mesajda ⭐✨🌟gizli🌟✨⭐ var ama format hatalı.', 'expected': None},
            {'input': '⭐✨Merhaba🌟✨⭐', 'expected': None},
            {'input': '⭐✨🌟Kısa🌟✨⭐', 'expected': 'Kısa'},
            {'input': '⭐✨🌟Biraz uzunca bir gizemli mesaj🌟✨⭐', 'expected': 'Biraz uzunca bir gizemli mesaj'},
        ],
        hints=[
            "💡 İpucu 1: Bir string'in belirli bir alt string ile başlayıp başlamadığını kontrol etmek için `.startswith()` metodunu kullanabilirsin.",
            "💡 İpucu 2: Benzer şekilde, bir string'in belirli bir alt string ile bitip bitmediğini kontrol etmek için `.endswith()` metodunu kullanabilirsin.",
            '💡 İpucu 3: Eğer mesaj gizli formata uyuyorsa, gizli anahtar kelimeyi bulmak için string dilimleme (slicing) kullanabilirsin. Başlangıç ve bitiş desenlerinin uzunluklarına dikkat et! Her iki desen de 3 emoji karakter uzunluğunda.',
        ],
    ),

    Question(
        id=53,
        title='🚀 Sosyal Medya Post Kontrolcüsü: Trend ve Temiz Mi?',
        category='strings',
        level='intermediate',
        description="""Bir sosyal medya platformunda içerik moderatörü olarak çalışıyorsun! 📝 Amacın, kullanıcıların gönderdiği mesajların belirli kriterlere uyup uymadığını kontrol etmek. Mesaj, en az bir trendy hashtag içermeli VE yasaklı kelimelerden veya emojilerden hiçbirini barındırmamalıdır. Fonksiyonunuz, bir mesajın bu iki koşulu da sağlıyorsa `True`, aksi takdirde `False` döndürmelidir. Unutmayın, hashtagler ve yasaklı kelimeler/emojiler için kontrol yaparken büyük/küçük harf veya emoji duyarlılığına dikkat edin (kelimeler küçük harf duyarsız, emojiler duyarlı kalmalı).""",
        starter_code="""def post_kontrol_et(mesaj: str, trend_hashtagler: list[str], yasakli_kelimeler_ve_emojiler: list[str]) -> bool:
    # Kullanıcının mesajını belirli kurallara göre kontrol eder.
    # - En az bir trend hashtag içermeli.
    # - Hiçbir yasaklı kelime/emoji içermemeli.
    pass""",
        test_cases=[
            {'input': {'mesaj': 'Harika bir #Python projesi üzerinde çalışıyorum! #Gelişim', 'trend_hashtagler': ['#python', '#yapayzeka'], 'yasakli_kelimeler_ve_emojiler': ['yasaklı', 'spam']}, 'expected': True},
            {'input': {'mesaj': 'Bu spam mesajı lütfen bildirin! #Önemli', 'trend_hashtagler': ['#önemli'], 'yasakli_kelimeler_ve_emojiler': ['spam', 'virüs']}, 'expected': False},
            {'input': {'mesaj': 'Bugün hava çok güzel!', 'trend_hashtagler': ['#güneş', '#plaj'], 'yasakli_kelimeler_ve_emojiler': []}, 'expected': False},
            {'input': {'mesaj': 'Sıkıcı bir gün 😠', 'trend_hashtagler': ['#mood'], 'yasakli_kelimeler_ve_emojiler': ['sıkıcı', '😠']}, 'expected': False},
            {'input': {'mesaj': 'Yeni bir #PYTHON dersi! #öğren', 'trend_hashtagler': ['#python', '#ders'], 'yasakli_kelimeler_ve_emojiler': []}, 'expected': True},
            {'input': {'mesaj': 'Bu bir YASAKLI kelimedir! #Uyarı', 'trend_hashtagler': ['#uyarı'], 'yasakli_kelimeler_ve_emojiler': ['yasaklı']}, 'expected': False},
            {'input': {'mesaj': 'Her şey yolunda! #Mutlu', 'trend_hashtagler': [], 'yasakli_kelimeler_ve_emojiler': []}, 'expected': False},
            {'input': {'mesaj': 'Süper bir gün! #Hava', 'trend_hashtagler': ['#hava'], 'yasakli_kelimeler_ve_emojiler': []}, 'expected': True},
        ],
        hints=[
            '💡 İpucu 1: Mesajın tamamını küçük harfe çevirerek hem trendy hashtag hem de yasaklı kelime kontrollerini (emoji dışındaki) kolaylaştırabilirsiniz.',
            '💡 İpucu 2: Trendy hashtag kontrolü için bir döngü kullanarak `any()` fonksiyonunu düşünebilirsiniz. En az bir tanesi mesajda varsa, ilk koşul sağlanmış demektir.',
            '💡 İpucu 3: Yasaklı kelimeler/emojiler için de benzer bir döngü kurun. Eğer mesajda herhangi bir yasaklı kelime/emoji bulunursa, hemen `False` döndürebilirsiniz.',
            "💡 İpucu 4: Python'daki `in` operatörü string içinde alt string aramak için çok kullanışlıdır.",
        ],
    ),

    Question(
        id=54,
        title='🍽️ Emoji Sipariş Fiyatı Hesaplayıcı',
        category='list-dict',
        level='intermediate',
        description="""Mahallenin en popüler kafesi, modern çağa ayak uydurarak sadece emojilerle sipariş alıyor! 📲 Bu sistemde, her bir yiyecek ve içecek emojisi belirli bir fiyata sahip. Görevin, müşterinin verdiği emoji dolu sipariş stringini (örn: '🍕🍔🍟🥤') analiz ederek toplam tutarı hesaplayan bir fonksiyon yazmak. Dikkatli ol, bazı emojiler listede olmayabilir, onların fiyatı 0'dır.""",
        starter_code="""def hesapla_emoji_siparis_fiyati(siparis_stringi: str) -> float:
    # Her bir emoji için fiyatları tutan bir sözlük tanımlayalım.
    emoji_fiyatlari = {
        "🍕": 15.00,
        "🍔": 12.50,
        "🍟": 7.00,
        "🥤": 5.00,
        "☕": 6.00,
        "🍩": 8.50,
        "🍦": 9.00,
        "🥪": 10.00,
        "🍰": 11.00,
        "🍎": 4.00
    }
    # Toplam fiyatı hesaplamak için kodu buraya yazın.
    pass""",
        test_cases=[
            {'input': '🍕🍔🥤', 'expected': 32.5},
            {'input': '🍟🍟🥤', 'expected': 19.0},
            {'input': '🍕✨🍔', 'expected': 27.5},
            {'input': '☕🍩🍦', 'expected': 23.5},
            {'input': '🍎🥪', 'expected': 14.0},
            {'input': '', 'expected': 0.0},
            {'input': '🌟😊', 'expected': 0.0},
            {'input': '🍕🍕🍕🥤', 'expected': 50.0},
        ],
        hints=[
            '💡 Sipariş stringi içindeki her bir emoji karakteri üzerinde döngü (loop) kurmayı düşünün.',
            '💡 `emoji_fiyatlari` sözlüğünden her bir emojinin fiyatını alırken `.get(emoji, 0.0)` metodunu kullanarak, menüde olmayan emojiler için varsayılan bir değer (0.0) döndürebilirsiniz.',
            '💡 Toplam fiyatı tutmak için döngüden önce bir değişken tanımlayın ve her emojinin fiyatını bu değişkene ekleyin.',
        ],
    ),

    Question(
        id=55,
        title='Viral Potansiyel Skoru Hesapla 📈🚀',
        category='strings',
        level='intermediate',
        description="""Sosyal medya yöneticisi olarak, platformunuzda hangi gönderilerin daha fazla etkileşim yaratabileceğini öngörmeniz gerekiyor. Bu görevde, kullanıcıların paylaştığı gönderi metinlerini analiz ederek 'Viral Potansiyel Skoru' hesaplayan bir fonksiyon yazmalısınız. Fonksiyonunuz, metindeki belirli trend kelimelerin ve pozitif emojilerin kullanımına göre bir skor döndürecektir. Her trend kelime +5 puan, her pozitif emoji +3 puan değerindedir. Kelime aramalarında küçük/büyük harf duyarlılığı olmamalıdır.""",
        starter_code="""def hesapla_viral_skor(gonderi_metni: str, trend_kelimeler: list[str], pozitif_emojiler: list[str]) -> int:
    # Gönderi metninin viral potansiyel skorunu hesaplayan kodunuzu buraya yazın.
    pass""",
        test_cases=[
            {'input': {'gonderi_metni': 'Harika bir gün! #python çok eğlenceli 🚀🔥', 'trend_kelimeler': ['python', 'eğlenceli', 'kodlama'], 'pozitif_emojiler': ['🚀', '🔥', '✨']}, 'expected': 16},
            {'input': {'gonderi_metni': 'Bu challenge gerçekten eğlenceli! Kodlama öğrenmek harika! 😊👍', 'trend_kelimeler': ['challenge', 'eğlenceli', 'kodlama', 'öğrenmek'], 'pozitif_emojiler': ['😊', '👍', '💡']}, 'expected': 26},
            {'input': {'gonderi_metni': 'Sıradan bir metin. Hiçbir viral potansiyel yok.', 'trend_kelimeler': ['viral', 'popüler', 'challenge'], 'pozitif_emojiler': ['🎉', '🥳']}, 'expected': 0},
            {'input': {'gonderi_metni': 'PyThOn çok iyi! EğLenceli! Ve bu bir CHALLENGE! 🎉', 'trend_kelimeler': ['python', 'eğlenceli', 'challenge'], 'pozitif_emojiler': ['🎉']}, 'expected': 18},
            {'input': {'gonderi_metni': 'Bugün hava güzel. ☀️', 'trend_kelimeler': ['güneş', 'hava', 'güzel'], 'pozitif_emojiler': ['✨', '🌈']}, 'expected': 0},
        ],
        hints=[
            '💡 İpucu 1: Metindeki kelimeleri karşılaştırırken küçük/büyük harf duyarlılığını ortadan kaldırmak için `lower()` metodunu kullanmayı unutmayın.',
            '💡 İpucu 2: Gönderi metnini kelimelere ayırmak için `split()` veya düzenli ifadeler (regex) kullanabilirsiniz. Ancak basit bir `split()` metodu da iş görecektir, noktalama işaretlerini temizlemeyi düşünebilirsiniz.',
            '💡 İpucu 3: Emojileri saymak için, her bir pozitif emojinin gönderi metninde kaç kez geçtiğini kontrol eden bir döngü yazabilirsiniz. `string.count()` metodu bu konuda size yardımcı olabilir.',
        ],
    ),

    Question(
        id=56,
        title='😎 Ruh Hali Emoji Dedektörü',
        category='strings',
        level='intermediate',
        description="""Merhaba sevgili geleceğin veri bilimcileri! 👩‍💻 Sosyal medya platformları, kullanıcılarının duygularını anlamak için sürekli yeni yollar arıyor. Bu görevde, bir kullanıcının paylaştığı metindeki emojilere bakarak genel ruh halini tespit eden bir Python fonksiyonu yazacaksın. ✨ Fonksiyonun, girdi olarak bir sosyal medya gönderisi (string) ve farklı ruh hallerini (örneğin, 'mutlu', 'üzgün') temsil eden emoji listelerini içeren bir sözlük (dict) alacak. Hangi ruh halinden daha fazla emoji varsa, o ruh halini döndürmelisin. Eğer bilinen bir emoji bulunamazsa veya birden fazla ruh hali eşit sayıda emoji içeriyorsa, 'belirsiz' döndürmelisin. 🤔

Örnek Girdi ve Çıktılar:
post = "Bugün hava harika! 😊☀️"
mood_map = {"mutlu": ["😊", "😄"], "üzgün": ["😢", "😔"]}
Çıktı: "mutlu"

post = "Çok sıkıcı bir gün 😭",
mood_map = {"mutlu": ["😊", "😄"], "üzgün": ["😢", "😔"]}
Çıktı: "üzgün"

post = "Sadece metin var."
mood_map = {"mutlu": ["😊", "😄"], "üzgün": ["😢", "😔"]}
Çıktı: "belirsiz""",
        starter_code="""def emoji_ruh_hali_dedektoru(post: str, mood_map: dict) -> str:
    # Her bir ruh hali için emoji sayılarını tutacak bir sayaç sözlüğü oluştur.
    # Gönderideki her karakteri kontrol et.
    # Eğer karakter bir emoji ise ve mood_map içinde tanımlıysa, ilgili ruh halinin sayacını artır.
    # En yüksek sayaca sahip ruh halini bul.
    # Beraberlik veya emoji olmaması durumlarını yönetmeyi unutma!
    pass""",
        test_cases=[
            {'input': {'post': 'Bugün hava çok güzel! 😊😄', 'mood_map': {'mutlu': ['😊', '😄', '🥳', '✨'], 'üzgün': ['😢', '😭', '😔', '💔'], 'şaşkın': ['😮', '🤯', '😳']}}, 'expected': 'mutlu'},
            {'input': {'post': 'Çok yorgunum ve üzgünüm 😔😢', 'mood_map': {'mutlu': ['😊', '😄', '🥳', '✨'], 'üzgün': ['😢', '😭', '😔', '💔'], 'şaşkın': ['😮', '🤯', '😳']}}, 'expected': 'üzgün'},
            {'input': {'post': 'Şaşırtıcı bir haber aldım! 🤯😳 Ama yine de mutluyum 😊', 'mood_map': {'mutlu': ['😊', '😄', '🥳', '✨'], 'üzgün': ['😢', '😭', '😔', '💔'], 'şaşkın': ['😮', '🤯', '😳']}}, 'expected': 'şaşkın'},
            {'input': {'post': 'Sadece metin var.', 'mood_map': {'mutlu': ['😊', '😄', '🥳', '✨'], 'üzgün': ['😢', '😭', '😔', '💔'], 'şaşkın': ['😮', '🤯', '😳']}}, 'expected': 'belirsiz'},
            {'input': {'post': '🤔🤷\u200d♀️ Bu ne demek?', 'mood_map': {'mutlu': ['😊', '😄', '🥳', '✨'], 'üzgün': ['😢', '😭', '😔', '💔'], 'şaşkın': ['😮', '🤯', '😳']}}, 'expected': 'belirsiz'},
            {'input': {'post': 'Mutluluk ve biraz hüzün 😊😔', 'mood_map': {'mutlu': ['😊', '😄', '🥳', '✨'], 'üzgün': ['😢', '😭', '😔', '💔'], 'şaşkın': ['😮', '🤯', '😳']}}, 'expected': 'belirsiz'},
            {'input': {'post': '', 'mood_map': {'mutlu': ['😊', '😄', '🥳', '✨'], 'üzgün': ['😢', '😭', '😔', '💔'], 'şaşkın': ['😮', '🤯', '😳']}}, 'expected': 'belirsiz'},
            {'input': {'post': 'Harika bir gün ✨✨✨', 'mood_map': {'mutlu': ['😊', '😄', '🥳', '✨'], 'üzgün': ['😢', '😭', '😔', '💔'], 'şaşkın': ['😮', '🤯', '😳']}}, 'expected': 'mutlu'},
            {'input': {'post': 'Of be 💔', 'mood_map': {'mutlu': ['😊', '😄', '🥳', '✨'], 'üzgün': ['😢', '😭', '😔', '💔'], 'şaşkın': ['😮', '🤯', '😳']}}, 'expected': 'üzgün'},
        ],
        hints=[
            '💡 İlk adım olarak, gönderideki her bir karakteri tek tek kontrol etmelisin. Bir döngü (for loop) kullanmak işini kolaylaştıracaktır. 🔁',
            "💡 Her bir karakterin hangi ruh haline ait olduğunu bulmak için, 'mood_map' sözlüğünün değerlerini (emoji listeleri) kontrol etmelisin. Bir karakterin bu listelerden birinde olup olmadığını 'in' operatörü ile kontrol edebilirsin. 🧐",
            "💡 Emojilerin sayılarını takip etmek için bir sayaç sözlüğü oluşturabilirsin. Örneğin, `emoji_sayilari = {'mutlu': 0, 'üzgün': 0}` gibi. Bulduğun her emoji için ilgili ruh halinin sayacını artır. ➕",
            '💡 Tüm emojileri saydıktan sonra, hangi ruh halinin en yüksek sayaca sahip olduğunu bulman gerekecek. `max()` fonksiyonunu, `key` parametresiyle kullanarak sözlük değerlerine göre maksimum olanı bulabilirsin. Ama dikkat et, beraberlik durumunda ne yapacağını unutma! 🤯',
            "💡 Eğer hiçbir emoji bulunamazsa veya en yüksek sayıya sahip birden fazla ruh hali varsa, 'belirsiz' döndürdüğünden emin olmalısın. Bu kontrolü, sonuçları değerlendirdikten sonra yapabilirsin. 😉",
        ],
    ),

    Question(
        id=57,
        title='🌟 Sosyal Medya İçerik Avcısı: Trendleri Yakala!',
        category='strings',
        level='intermediate',
        description="""Merhaba sevgili içerik avcıları! 🏹 Popüler bir sosyal medya platformunda görevlisiniz ve göreviniz, "viral" olabilecek gönderileri tespit etmek. Bir gönderinin viral potansiyeli taşıması için iki temel koşulu sağlaması gerekiyor:
1. Gönderi metni, size verilen trend hashtag'lerden en az birini içermeli (büyük/küçük harf duyarsız olmalı!).
2. Gönderi metninde, belirtilen minimum emoji sayısına eşit veya daha fazla emoji bulunmalı. Emojileri sayarken, Unicode karakter setindeki yaygın emoji aralıklarını (örn: U+1F600 - U+1F64F arası gülümsemeler, U+1F300 - U+1F5FF arası semboller vb.) dikkate almalısınız.
Fonksiyonunuz, bir gönderinin bu kriterlere uyup uymadığını belirten `True` veya `False` döndürmelidir.

Örnek Kullanım:
analyze_social_post("Harika bir gün! #PythonChallenge 🚀", ["#pythonchallenge", "#coding"], 1)  çıktı: True
analyze_social_post("Sadece biraz kod yazdım.", ["#javascript"], 0) çıktı: False
analyze_social_post("Çok mutluyum! 😊", ["#mutluluk"], 2) çıktı: False""",
        starter_code="""def analyze_social_post(post_text: str, trending_hashtags: list[str], min_emoji_count: int) -> bool:
    # Gönderinin viral potansiyelini belirlemek için hashtag ve emoji kontrolü yapın.
    pass""",
        test_cases=[
            {'input': {'post_text': 'Python öğrenmek çok eğlenceli! #PyDev #codingchallenge 🐍', 'trending_hashtags': ['#pydev', '#datascience'], 'min_emoji_count': 1}, 'expected': True},
            {'input': {'post_text': 'Hafta sonu planları! Kahve keyfi ☕', 'trending_hashtags': ['#tatil', '#gezi'], 'min_emoji_count': 2}, 'expected': False},
            {'input': {'post_text': 'Yeni bir başlangıç! 🚀', 'trending_hashtags': ['#yenibaşlangıç', '#motivasyon'], 'min_emoji_count': 1}, 'expected': True},
            {'input': {'post_text': 'Bugün hava çok güzel.', 'trending_hashtags': ['#güneşli', '#keyif'], 'min_emoji_count': 0}, 'expected': False},
            {'input': {'post_text': 'Harika bir gün! 😊🌞', 'trending_hashtags': [], 'min_emoji_count': 1}, 'expected': False},
            {'input': {'post_text': 'Sadece metin var, emoji yok.', 'trending_hashtags': ['#metin', '#yok'], 'min_emoji_count': 1}, 'expected': False},
            {'input': {'post_text': 'Büyük bir indirim! 🎉💸 Hemen tıkla!', 'trending_hashtags': ['#indirim', '#alışveriş'], 'min_emoji_count': 2}, 'expected': True},
            {'input': {'post_text': 'Merhaba Dünya! 👋', 'trending_hashtags': ['#merhaba', '#dünya'], 'min_emoji_count': 0}, 'expected': True},
            {'input': {'post_text': 'Emoji yok, hashtag var. #test', 'trending_hashtags': ['#test'], 'min_emoji_count': 1}, 'expected': False},
            {'input': {'post_text': 'Çok güzel bir gün! ❤️', 'trending_hashtags': ['#hava', '#güzel'], 'min_emoji_count': 0}, 'expected': False},
        ],
        hints=[
            "💡 İpucu 1: Hashtag kontrolü için, `trending_hashtags` listesindeki her bir hashtag'i `post_text` içinde arayabilirsiniz. Büyük/küçük harf duyarsız arama için hem gönderi metnini hem de hashtag'leri küçük harfe (`.lower()`) dönüştürmek iyi bir başlangıç olabilir.",
            '💡 İpucu 2: Emoji sayımı için, gönderi metnindeki her karakteri tek tek kontrol etmeniz gerekecek. Bir karakterin emoji olup olmadığını basitçe anlamak için `ord(karakter)` fonksiyonunu kullanarak Unicode değerine bakabilir ve yaygın emoji aralıklarında olup olmadığını kontrol edebilirsiniz (örneğin, `0x1F600` ile `0x1F64F` arası gülümsemeler, `0x2600` ile `0x26FF` arası semboller gibi).',
            "💡 İpucu 3: Her iki koşulun (en az bir trend hashtag ve minimum emoji sayısı) da sağlanması gerektiği için, bu iki kontrolü ayrı ayrı yapıp sonucunu `and` operatörüyle birleştirebilirsiniz. Unutmayın, herhangi bir trend hashtag'in bulunması yeterlidir.",
        ],
    ),

    Question(
        id=58,
        title='🤩 Emoji Ruh Hali Analizi',
        category='list-dict',
        level='intermediate',
        description="""Sen, popüler bir mesajlaşma uygulamasının geliştiricisisin ve kullanıcılar, uzun emoji dizilerinin genel ruh halini hızla anlamak istiyor. Amacın, verilen bir emoji dizisini analiz ederek 'Pozitif', 'Negatif', 'Nötr', 'Karışık Ruh Hali' veya 'Belirsiz' kategorilerinden hangisinin baskın olduğunu bulan bir Python fonksiyonu yazmaktır. Fonksiyon, her bir emoji türünü saymalı ve aşağıdaki kurallara göre dominant ruh halini belirlemelidir. Diğer emojiler göz ardı edilecektir.

**Kategoriler ve Kurallar:**
*   **Pozitif:** 👍, 😄, 😍, 🎉, 🚀
*   **Negatif:** 👎, 😠, 😞, 😤, 😭
*   **Nötr:** 😐, 🤔, 😴, 🤷, 💬
*   Eğer pozitif, negatif veya nötr ruh hallerinden biri diğer ikisinden kesin olarak fazlaysa, o ruh hali döner.
*   Eğer Pozitif ve Negatif sayıları eşit ve diğerlerinden (Nötr) fazlaysa: "Karışık Ruh Hali".
*   Diğer tüm eşitlik durumlarında (örn: tümü eşit veya iki tanesi eşit ama üçüncüsü daha az değil): "Belirsiz".

**Örnek Kullanım:**
`emoji_ruh_hali("👍👍😠😄👎😐")`  çıktısı `Pozitif Ruh Hali` olmalı.
`emoji_ruh_hali("👎👎😠😠")`  çıktısı `Negatif Ruh Hali` olmalı.
`emoji_ruh_hali("👍👎😐")` çıktısı `Belirsiz` olmalı.""",
        starter_code="""def emoji_ruh_hali(emoji_dizisi: str) -> str:
    \"\"\"
    Verilen emoji dizisinin baskın ruh halini analiz eder.
    \"\"\"
    # Emojileri kategorize etmek için başlangıç setleri veya sözlükler tanımlayın.
    # Diziyi gezerek her kategori için sayım yapın.
    # Sayımlara göre dominant ruh halini belirlemek için koşullu ifadeler kullanın.
    pass""",
        test_cases=[
            {'input': '👍👍😠😄👎😐🚀', 'expected': 'Pozitif Ruh Hali'},
            {'input': '👎👎😠😠👍🤔', 'expected': 'Negatif Ruh Hali'},
            {'input': '😐🤔😴🤷👍👎', 'expected': 'Nötr Ruh Hali'},
            {'input': '👍👎😄😠', 'expected': 'Karışık Ruh Hali'},
            {'input': '👍👎😐', 'expected': 'Belirsiz'},
            {'input': '👍😐🤔😄', 'expected': 'Belirsiz'},
            {'input': 'abcxyz', 'expected': 'Belirsiz'},
            {'input': '', 'expected': 'Belirsiz'},
            {'input': '😍😍😍', 'expected': 'Pozitif Ruh Hali'},
            {'input': '👍😄👎😠😐🤔', 'expected': 'Belirsiz'},
        ],
        hints=[
            "💡 İpucu 1: Emojileri hızlıca kontrol etmek için her kategori için ayrı bir `set` kullanmak işinizi kolaylaştırır. Örneğin: `pozitif_emojiler = {'👍', '😄', ...}`.",
            '💡 İpucu 2: Emoji dizisindeki her karakteri tek tek gezmek için bir `for` döngüsü kullanın ve `if/elif` koşullarıyla hangi kategoriye ait olduğunu kontrol ederek sayımlarınızı artırın.',
            "💡 İpucu 3: Tüm sayımlar yapıldıktan sonra, sayımlarınızı karşılaştırmak için koşullu ifadeler (`if/elif/else`) kullanın. Eşitlik durumlarını ve 'Karışık Ruh Hali' kuralını dikkatlice ele almayı unutmayın.",
        ],
    ),

    Question(
        id=59,
        title='👾 Sosyal Medya Yorum Sensörü!',
        category='list-dict',
        level='intermediate',
        description="""Popüler bir sosyal medya platformu için yorum denetleme botu geliştiriyorsunuz. Kullanıcıların gönderdiği mesajlardaki belirli 'yasaklı' kelimeleri tespit edip, bunları gizlilik emojileriyle (örn: '🤫') değiştiren bir Python fonksiyonu yazmanız gerekiyor. Fonksiyonunuz, hem sansürlenmiş mesajı hem de hangi yasaklı kelimelerin (küçük harfe dönüştürülmüş halleriyle) kaç kez sansürlendiğini raporlayan bir sözlüğü içeren bir liste döndürmelidir. Kelime eşleştirmesi büyük/küçük harf duyarsız olmalı ve kelimelerin başındaki/sonundaki noktalama işaretleri dikkate alınmalıdır.""",
        starter_code="""import string

def yorum_sansurle(mesaj: str, yasakli_kelimeler: list[str], sansur_emoji: str = "🤫") -> list:
    \"\"\"
    Mesajdaki yasaklı kelimeleri sansür emojisiyle değiştirir ve sansürlenen kelimelerin sayısını raporlar.
    Kelime eşleştirmesi büyük/küçük harf duyarsızdır ve noktalama işaretleri dikkate alınır.

    Args:
        mesaj (str): Sansürlenecek metin.
        yasakli_kelimeler (list[str]): Sansürlenmesi gereken kelimelerin listesi.
        sansur_emoji (str, optional): Yasaklı kelimelerin yerine kullanılacak emoji. Varsayılan '🤫'.

    Returns:
        list: [sansürlenmiş_mesaj: str, sansürlenen_kelimeler_sayısı: dict[str, int]]
    \"\"\"
    # İpuçları:
    # 1. yasakli_kelimeler listesini küçük harfli bir kümeye (set) dönüştürerek hızlı arama yapabilirsiniz.
    # 2. string.punctuation modülünü kullanarak kelimelerin başındaki/sonundaki noktalama işaretlerini ayırabilirsiniz.
    # 3. Mesajı boşluklara göre ayırıp her kelimeyi ayrı ayrı işleyebilirsiniz.
    # 4. Sansürlenen kelimelerin sayısını tutmak için bir sözlük kullanın.
    pass""",
        test_cases=[
            {'input': {'mesaj': 'Merhaba bu yorumda küfür! var.', 'yasakli_kelimeler': ['küfür'], 'sansur_emoji': '🤫'}, 'expected': ['Merhaba bu yorumda 🤫! var.', {'küfür': 1}]},
            {'input': {'mesaj': 'Bu mesajda hakaret ve tehdit kelimeleri bulunuyor. Tehdit edenlere yer yok.', 'yasakli_kelimeler': ['hakaret', 'tehdit'], 'sansur_emoji': '🚫'}, 'expected': ['Bu mesajda 🚫 ve 🚫 kelimeleri bulunuyor. 🚫 edenlere yer yok.', {'hakaret': 1, 'tehdit': 2}]},
            {'input': {'mesaj': 'Harika bir gün! Her şey yolunda.', 'yasakli_kelimeler': ['kötü', 'çirkin'], 'sansur_emoji': '🤐'}, 'expected': ['Harika bir gün! Her şey yolunda.', {}]},
            {'input': {'mesaj': 'Ah, ne korkunç bir kelime... O kelime, gerçekten korkunç.', 'yasakli_kelimeler': ['korkunç', 'kelime'], 'sansur_emoji': '🤐'}, 'expected': ['Ah, ne 🤐 bir 🤐... O 🤐, gerçekten 🤐.', {'korkunç': 2, 'kelime': 2}]},
        ],
        hints=[
            "💡 İpucu 1: `yasakli_kelimeler` listesini hızlı arama için küçük harfli bir `set`'e dönüştürün. Mesajı boşluklara göre kelimelere ayırmak için `mesaj.split()` kullanın.",
            '💡 İpucu 2: Her bir kelime için `string.punctuation` modülünü kullanarak başındaki/sonundaki noktalama işaretlerini ayırın. Kelimenin noktalama işaretsiz ve küçük harfli halini yasaklı kelimeler setinde arayın.',
            '💡 İpucu 3: Eğer bir kelime yasaklıysa, sayacını güncelleyin ve orijinal noktalama işaretleriyle birlikte sansür emojisiyle değiştirin. Tüm kelimeleri işledikten sonra, sansürlenmiş mesajı ve sayım sözlüğünü içeren bir liste döndürün.',
        ],
    ),

    Question(
        id=60,
        title='🔐 Emoji Şifresi Dedektörü',
        category='strings',
        level='intermediate',
        description="""Merhaba, emoji meraklısı! 🚀 Bir sosyal medya platformunda, kullanıcıların "Emoji Şifreleri" oluşturması gerekiyor. Amacımız, verilen bir emoji şifresinin belirlenen kurallara uyup uymadığını kontrol eden bir Python fonksiyonu yazmak. Şifrelerin güvenli sayılması için şu kriterleri karşılaması gerekmekte:
1. Şifre, belirlenen bir "anahtar emoji" ile başlamalıdır.
2. Şifre, "zorunlu emojiler" listesinden en az birini içermelidir.
3. Şifre, "yasaklı emojiler" listesindeki hiçbir emojiyi içermemelidir.
4. Şifre, minimum uzunluğa sahip olmalıdır.
Fonksiyonunuz, bir emoji şifresini ve kuralları (anahtar emoji, zorunlu emojiler, yasaklı emojiler, minimum uzunluk) parametre olarak alıp, şifre geçerliyse True, değilse False döndürmelidir.

Örnek Girdi:
`sifre = "🔑🌟🚀🎉"`
`anahtar = "🔑"`
`zorunlu = ["🚀", "🔥"]`
`yasakli = ["💀", "👹"]`
`min_uzunluk = 3`
Örnek Çıktı:
`True`

Örnek Girdi:
`sifre = "🚀🌟🎉"`
`anahtar = "🔑"`
`zorunlu = ["🚀", "🔥"]`
`yasakli = ["💀", "👹"]`
`min_uzunluk = 3`
Örnek Çıktı:
`False` (Çünkü anahtar emoji ile başlamıyor)""",
        starter_code="""def emoji_sifre_gecerli_mi(sifre: str, anahtar_emoji: str, zorunlu_emojiler: list[str], yasakli_emojiler: list[str], min_uzunluk: int) -> bool:
    # Bu fonksiyon, verilen emoji şifresinin belirlenen kurallara uyup uymadığını kontrol eder.
    pass""",
        test_cases=[
            {'input': {'sifre': '🔑🌟🚀🎉', 'anahtar_emoji': '🔑', 'zorunlu_emojiler': ['🚀', '🔥'], 'yasakli_emojiler': ['💀', '👹'], 'min_uzunluk': 3}, 'expected': True},
            {'input': {'sifre': '🚀🌟🎉', 'anahtar_emoji': '🔑', 'zorunlu_emojiler': ['🚀', '🔥'], 'yasakli_emojiler': ['💀', '👹'], 'min_uzunluk': 3}, 'expected': False},
            {'input': {'sifre': '🔑✨🌈', 'anahtar_emoji': '🔑', 'zorunlu_emojiler': ['🚀', '🔥'], 'yasakli_emojiler': ['💀', '👹'], 'min_uzunluk': 3}, 'expected': False},
            {'input': {'sifre': '🔑🌟🚀💀', 'anahtar_emoji': '🔑', 'zorunlu_emojiler': ['🚀', '🔥'], 'yasakli_emojiler': ['💀', '👹'], 'min_uzunluk': 3}, 'expected': False},
            {'input': {'sifre': '🔑🚀', 'anahtar_emoji': '🔑', 'zorunlu_emojiler': ['🚀', '🔥'], 'yasakli_emojiler': ['💀', '👹'], 'min_uzunluk': 3}, 'expected': False},
            {'input': {'sifre': '🔑😊👍', 'anahtar_emoji': '🔑', 'zorunlu_emojiler': ['👍', '👋'], 'yasakli_emojiler': [], 'min_uzunluk': 3}, 'expected': True},
            {'input': {'sifre': '🔓✨🎉😎🔥', 'anahtar_emoji': '🔓', 'zorunlu_emojiler': ['✨', '🔥'], 'yasakli_emojiler': ['🚫', '💩', '🦠'], 'min_uzunluk': 5}, 'expected': True},
            {'input': {'sifre': '🔑🌈🌟🚀💀', 'anahtar_emoji': '🔑', 'zorunlu_emojiler': ['🌈', '🌟', '🚀'], 'yasakli_emojiler': ['💀', '👹'], 'min_uzunluk': 4}, 'expected': False},
            {'input': {'sifre': '🔑🌟🚀', 'anahtar_emoji': '🔑', 'zorunlu_emojiler': ['🚀'], 'yasakli_emojiler': [], 'min_uzunluk': 0}, 'expected': True},
        ],
        hints=[
            "💡 İpucu 1: Bir string'in belirli bir substring ile başlayıp başlamadığını kontrol etmek için `.startswith()` metodunu kullanabilirsiniz.",
            "💡 İpucu 2: String'in uzunluğunu kontrol etmek için `len()` fonksiyonunu kullanın.",
            '💡 İpucu 3: Bir listenin içindeki her bir zorunlu emojinin şifrede olup olmadığını kontrol etmek için bir döngü veya `any()` fonksiyonunu kullanabilirsiniz. `any(emoji in sifre for emoji in zorunlu_emojiler)` yapısı işinize yarayabilir.',
            '💡 İpucu 4: Yasaklı emojiler için de benzer şekilde bir döngü veya `any()` fonksiyonunu kullanabilirsiniz. Ancak bu durumda, herhangi bir yasaklı emoji bulunursa `False` döndürmeniz gerekir. Yani `not any(emoji in sifre for emoji in yasakli_emojiler)` ifadesi işinizi görecektir.',
        ],
    ),

    Question(
        id=61,
        title='🚀 Sosyal Medya Gönderisi Hype Yaratıcısı',
        category='strings',
        level='intermediate',
        description="""Merhaba sevgili sosyal medya guruları! Bir gönderi hazırladınız ama biraz daha 'hype' katmak istiyorsunuz, öyle değil mi? Bu soruda, size verilen bir gönderi metnindeki 'sıkıcı' kelimeleri daha havalı hashtag'ler veya dikkat çekici emojilerle değiştiren bir fonksiyon yazmanızı bekliyoruz. Amacımız, gönderinizi daha etkileşimli ve dikkat çekici hale getirmek! Fonksiyonunuz, metni kelime kelime işlerken, büyük/küçük harf fark etmeksizin eşleştirme yapmalı ve varsa sondaki noktalama işaretlerini korumalıdır.""",
        starter_code="""import string

def optimize_social_post(post_text: str, replacements: dict) -> str:
    \"\"\"
    Verilen sosyal medya gönderi metnindeki 'sıkıcı' kelimeleri, 
    'hype' yaratacak hashtagler veya emojilerle değiştirir.
    Kelimeler büyük/küçük harf fark etmeksizin eşleştirilir ve 
    varsa sondaki noktalama işaretleri korunur.
    \"\"\"
    # Metni boşluklara göre kelimelere ayırın.
    # Her kelimeyi döngüde işlerken, varsa sondaki noktalama işaretini (örn. nokta, virgül) ayırın.
    # Kelimenin küçük harf versiyonunu 'replacements' sözlüğünde kontrol edin.
    # Eğer kelime bulunursa, sözlükteki karşılığı olan değeri ve orijinal noktalama işaretini birleştirin.
    # Bulunmazsa, kelimeyi ve noktalama işaretini orijinal haliyle koruyun.
    # Tüm işlenmiş kelimeleri tekrar boşluklarla birleştirerek nihai metni oluşturun.
    pass""",
        test_cases=[
            {'input': {'post_text': 'Bugün hava çok güzeldi. Harika bir gün geçirdim.', 'replacements': {'güzeldi': '#Harika', 'harika': '✨', 'çok': 'süper'}}, 'expected': 'Bugün hava süper #Harika. ✨ bir gün geçirdim.'},
            {'input': {'post_text': 'Bu film gerçekten harikaydı! Mükemmel bir deneyimdi.', 'replacements': {'harikaydı': '🎬', 'mükemmel': '🤩'}}, 'expected': 'Bu film gerçekten 🎬! 🤩 bir deneyimdi.'},
            {'input': {'post_text': 'Yemekler pek iyi değildi. Kötü bir tecrübe oldu.', 'replacements': {'iyi': '🤤', 'kötü': '👎'}}, 'expected': 'Yemekler pek 🤤 değildi. 👎 bir tecrübe oldu.'},
            {'input': {'post_text': 'Yarın iş var, hadi bakalım.', 'replacements': {'iş': '#Work', 'hadi': '🚀'}}, 'expected': 'Yarın #Work var, 🚀 bakalım.'},
            {'input': {'post_text': 'Büyük bir indirim var! Kaçırma fırsatını.', 'replacements': {'büyük': 'MEGA', 'fırsatını': '🔥'}}, 'expected': 'MEGA bir indirim var! Kaçırma 🔥.'},
            {'input': {'post_text': 'Bu çok güzel bir gün. Neşe dolu!', 'replacements': {'çok': 'oldukça', 'güzel': 'muhteşem', 'neşe': 'mutluluk'}}, 'expected': 'Bu oldukça muhteşem bir gün. mutluluk dolu!'},
            {'input': {'post_text': 'Python harika bir dil. Öğrenmesi eğlenceli.', 'replacements': {'harika': '✨', 'eğlenceli': '🚀'}}, 'expected': 'Python ✨ bir dil. Öğrenmesi 🚀.'},
            {'input': {'post_text': 'Merhaba dünya, nasılsın?', 'replacements': {}}, 'expected': 'Merhaba dünya, nasılsın?'},
        ],
        hints=[
            "💡 Metni boşluklara göre 'split()' ederek kelimelere ayırmak ilk adımınız olmalı.",
            "💡 Her kelimenin sonundaki noktalama işaretlerini (virgül, nokta, ünlem vb.) ayırt etmek için 'string.punctuation' modülünden faydalanabilirsiniz. Örneğin, 'word.rstrip(string.punctuation)' ile kelimenin noktalama işaretsiz halini alabilir, ve geri kalan kısmı noktalama işareti olarak saklayabilirsiniz.",
            "💡 Kelimeyi 'replacements' sözlüğünde ararken büyük/küçük harf duyarsızlığı için '.lower()' metodunu kullanmayı unutmayın.",
            "💡 İşlenmiş kelimelerinizi bir listeye ekleyip, son olarak tüm kelimeleri tekrar ' '.join() ile birleştirerek sonuç metnini oluşturmalısınız.",
        ],
    ),

    Question(
        id=62,
        title='✨ Sosyal Medya Şifresi: Yıldız Tayfası Mesajlarını Çöz!',
        category='strings',
        level='intermediate',
        description="""Gizemli 'Yıldız Tayfası' fan kulübü, sosyal medyada özel bir dil kullanıyor! Bu dil, belirli anahtar kelimeler ve 'güç emojileri' içeriyor. Senin görevin, verilen bir sosyal medya yorumunun bir 'Yıldız Tayfası' mesajı olup olmadığını tespit etmek ve içindeki anahtar kelimeler ile güç emojilerini bulup bir liste olarak dönmek. Bir yorumun geçerli bir 'Yıldız Tayfası' mesajı sayılması için **hem en az bir anahtar kelime hem de en az bir güç emojisi** içermesi gereklidir. Aksi halde, boş bir liste dönmelisin. Bulunan öğelerin sırası önemli değil ve her öğe listede sadece bir kez bulunmalıdır.""",
        starter_code="""def decode_fan_message(comment: str) -> list[str]:
    secret_keywords = ["galaksi", "yıldız", "tayfa", "parlak", "ışık"]
    power_emojis = ["✨", "🚀", "🌟", "💫", "🌠"]
    
    # İpucu: Hem anahtar kelime hem de güç emojisi içeren bir mesajın geçerli olduğunu unutma!
    # Çözümlediğin kelime ve emojileri bir liste içinde sakla.
    pass""",
        test_cases=[
            {'input': 'Bugün tayfa olarak galaksiye 🚀 doğru yeni bir ışık saçtık! ✨', 'expected': ['tayfa', 'galaksi', 'ışık', '🚀', '✨']},
            {'input': 'Yıldızlar çok parlak 🌟 görünüyor.', 'expected': ['yıldız', 'parlak', '🌟']},
            {'input': 'Bu sadece bir galaksi denemesi.', 'expected': []},
            {'input': 'Ne kadar da güzel bir gün! ✨🚀', 'expected': []},
            {'input': 'Merhaba dünya!', 'expected': []},
            {'input': '', 'expected': []},
            {'input': 'Tayfa, bu ışık galaksiye doğru ilerliyor! 🚀 Işık!', 'expected': ['tayfa', 'ışık', 'galaksi', '🚀']},
            {'input': 'Bizim tayfa ✨ her zaman parlak ✨ bir ışık saçar!', 'expected': ['tayfa', 'parlak', 'ışık', '✨']},
        ],
        hints=[
            '💡 İpucu 1: İlk olarak, yorum (comment) içinde `secret_keywords` listesindeki her bir anahtar kelimenin olup olmadığını kontrol edin. Aynı şekilde `power_emojis` listesindeki emojileri de kontrol edin.',
            '💡 İpucu 2: Yorumda en az bir anahtar kelime ve en az bir güç emojisi bulunup bulunmadığını takip etmek için iki ayrı boolean değişken (örneğin `found_keyword = False`, `found_emoji = False`) kullanabilirsiniz.',
            '💡 İpucu 3: Eğer her iki koşul (anahtar kelime ve emoji bulunması) da sağlanıyorsa, o zaman yorumda bulunan tüm anahtar kelimeleri ve güç emojilerini bir liste halinde toplamaya başlayın.',
            '💡 İpucu 4: Bulunan öğeleri bir listede toplarken, tekrar eden öğeleri engellemek için listeye eklemeden önce öğenin listede olup olmadığını kontrol edebilirsiniz (`if item not in found_items:`).',
        ],
    ),

    Question(
        id=63,
        title='✨ Trend Hashtag Temizleyici',
        category='strings',
        level='intermediate',
        description="""TrendSpotter adlı yeni bir sosyal medya analiz platformunda çalışıyorsunuz. Göreviniz, ham trend konularından (genellikle emoji, sayı ve özel karakterlerle dolu) temiz, anlamlı kelimeleri çıkarmak ve gerçek trendleri belirlemek. Bir hashtag string'ini alacak ve aşağıdaki kurallara göre temizleyerek sadece geçerli kelimelerin bir listesini döndürecek bir fonksiyon yazın:
1. Tüm karakterleri küçük harfe dönüştürün.
2. Sayıları (0-9) ve yaygın özel karakterleri (`!@#$%^&*()_+-=[]{};:'"\|,./<>?`) boşlukla değiştirin.
3. Emojileri ve diğer alfabetik olmayan karakterleri de boşlukla değiştirin.
4. Oluşan string'i boşluklara göre ayırın ve boş kalan kelimeleri (örneğin art arda gelen boşluklardan oluşan) sonuç listesinden çıkarın.""",
        starter_code="""def clean_hashtag_trends(raw_hashtag: str) -> list[str]:
    # Hashtag'i temizleyerek anlamlı kelimeler listesi döndürür.
    pass""",
        test_cases=[
            {'input': 'Python🔥Kodlama🤓Haftası!', 'expected': ['python', 'kodlama', 'haftası']},
            {'input': '#LearnPython2023 🚀', 'expected': ['learnpython']},
            {'input': '🎉Data_Science-Projesi?!!', 'expected': ['data', 'science', 'projesi']},
            {'input': '   Süper  Proje  Bugün!!!  ', 'expected': ['süper', 'proje', 'bugün']},
            {'input': '123Merhaba Dünya!123', 'expected': ['merhaba', 'dünya']},
            {'input': 'SadeceEmojiler🤯🤔😵', 'expected': ['sadeceemojiler']},
            {'input': '', 'expected': []},
            {'input': '      ', 'expected': []},
            {'input': 'PyThOn Is FuN 🐍', 'expected': ['python', 'is', 'fun']},
        ],
        hints=[
            "💡 İpucu 1: İlk olarak, string'i küçük harfe çevirerek başlayın.",
            "💡 İpucu 2: İkinci adımda, boş bir string oluşturun. Gelen string'deki her karakteri bir döngü ile gezin. Eğer karakter bir harfse (`char.isalpha()` metodu ile kontrol edilebilir) veya boşluksa, oluşturduğunuz string'e ekleyin. Aksi takdirde (sayı, özel karakter, emoji vb.), bir boşluk karakteri ekleyin.",
            "💡 İpucu 3: Oluşan yeni string'i `split()` metodunu kullanarak boşluklara göre ayırın. Birden fazla boşluktan kaynaklanan sorunları `split()` metodu genellikle kendiliğinden halleder.",
            "💡 İpucu 4: Son olarak, liste anlama (list comprehension) veya bir döngü kullanarak, oluşan listedeki boş string'leri (`''`) filtreleyin.",
        ],
    ),

    Question(
        id=64,
        title='🚀 Viral Başlık Avcısı: Etkileşim Skoru Hesaplayıcı',
        category='strings',
        level='intermediate',
        description="""Sosyal medyada içerik üreten bir fenomen olduğunu hayal et! Paylaşımlarının daha fazla etkileşim alması için başlıklarını optimize etmen gerekiyor. Bu görevde, sana verilen bir başlığın 'viral potansiyelini' bir skor ile ölçeceksin. Başlıkta geçen belirli anahtar kelimeler ve emojiler puan kazandırırken, aşırı ünlem işaretleri puan kaybettirecek, soru işaretleri ise ekstra puan kazandıracak. Amaç, verilen başlığı analiz ederek toplam 'etkileşim skorunu' hesaplayan bir Python fonksiyonu yazmak.""",
        starter_code="""def viral_baslik_skoru(baslik: str) -> int:
    # Anahtar kelimelerin ve emojilerin puanlarını birer sözlükte tut
    anahtar_kelime_puanlari = {
        "viral": 10, "şok": 8, "inanılmaz": 7, "asla": 5, "bunu izle": 6,
        "nasıl yapılır": 4, "görmeden geçme": 9, "hemen öğren": 5
    }
    emoji_puanlari = {
        "🎉": 5, "🔥": 6, "🤯": 8, "😱": 7, "😂": 3, "✨": 4
    }
    
    toplam_skor = 0
    baslik_kucuk = baslik.lower()
    
    # Anahtar kelimeler için puanları hesapla
    for kelime, puan in anahtar_kelime_puanlari.items():
        if kelime in baslik_kucuk:
            toplam_skor += puan
            
    # Emojiler için puanları hesapla
    # İpucu: Her bir emoji karakterini başlıkta arayabilirsin
    
    # Ünlem ve soru işaretleri için bonus/ceza puanlarını hesapla
    # İpucu: string.count() metodunu kullanabilirsin.
    # Ünlem işareti: İlk 3 ünlemden sonraki her ünlem -2 puan.
    # Soru işareti: Her soru işareti +3 puan.
    
    return toplam_skor""",
        test_cases=[
            {'input': 'Bu inanılmaz haberi görmeden geçme! 🔥😱🤯', 'expected': 37},
            {'input': 'Python öğrenmek nasıl yapılır? Hemen öğren 🎉', 'expected': 17},
            {'input': 'Sıradan bir gün...', 'expected': 0},
            {'input': 'Şok!!! Bunu izle ve asla inanamayacaksın!!!!', 'expected': 11},
            {'input': 'Yeni nesil teknolojiler: Nasıl kullanılır?', 'expected': 7},
            {'input': '🎉 Viral bir gelişme ✨', 'expected': 19},
            {'input': 'Bu ne şimdi????', 'expected': 12},
            {'input': 'Deneme metni', 'expected': 0},
        ],
        hints=[
            '💡 İlk olarak, başlığı küçük harfe çevirerek anahtar kelime kontrollerini kolaylaştırabilirsin.',
            '💡 `anahtar_kelime_puanlari` ve `emoji_puanlari` sözlükleri üzerinde döngü (for loop) kullanarak her bir kelime veya emoji için başlıkta arama yap.',
            "💡 Bir stringin belirli bir alt dizeyi veya karakteri içerip içermediğini kontrol etmek için `in` operatörünü kullanabilirsin (örneğin: `if 'kelime' in baslik:`).",
            "💡 Ünlem ve soru işaretlerinin sayısını bulmak için `baslik.count('!')` ve `baslik.count('?')` metodlarını kullanabilirsin. Unutma, ünlem cezasını ilk 3 ünlemden sonraki fazlalıklar için uygula.",
        ],
    ),

    Question(
        id=65,
        title='🕵️ Emoji Gizemini Çöz: Gizli Mesaj Dekoderi',
        category='strings',
        level='intermediate',
        description=""""Emoji Enigma" adında gizli bir topluluk, mesajlarını emojilerle şifreler. Her emoji belirli bir harfi temsil eder ve kelimeler `#` sembolüyle ayrılır. Senin görevin, verilen şifreli bir mesajı ve emoji-harf eşleştirmesini kullanarak mesajı deşifre eden bir Python fonksiyonu yazmak. Şifreli mesajdaki her `#` sembolü bir boşluk karakterine dönüştürülmelidir. Haritada bulunmayan emojiler `?` karakteriyle temsil edilmelidir.

Örnek Kullanım:
Girdi:
`encoded_message`: "🍎🐍🐍🍎#🍋🍎🌴🍎"
`emoji_map`: `{'🍎': 'A', '🐍': 'S', '🍋': 'L', '🌴': 'P'}`
Çıktı: "ASSA LAPA""",
        starter_code="""def decode_emoji_message(encoded_message: str, emoji_map: dict) -> str:
    # Şifreli mesajı emoji haritasını kullanarak deşifre eden kodu buraya yazın.
    pass""",
        test_cases=[
            {'input': {'encoded_message': '🚀🐍🐍🚀#🌕🌎🌎🌕', 'emoji_map': {'🚀': 'R', '🐍': 'S', '🌕': 'M', '🌎': 'O'}}, 'expected': 'RSSR MOOM'},
            {'input': {'encoded_message': '🍎🐍🔥🍎#🍋🍎🌴🍎', 'emoji_map': {'🍎': 'A', '🐍': 'S', '🍋': 'L', '🌴': 'P'}}, 'expected': 'AS?A LAPA'},
            {'input': {'encoded_message': '', 'emoji_map': {'🍎': 'A'}}, 'expected': ''},
            {'input': {'encoded_message': '🚀🐍##🌕🌎', 'emoji_map': {'🚀': 'R', '🐍': 'S', '🌕': 'M', '🌎': 'O'}}, 'expected': 'RS  MO'},
            {'input': {'encoded_message': '#✨👋🌳🌳👋##🌞🌍#', 'emoji_map': {'✨': 'H', '👋': 'E', '🌳': 'L', '🌞': 'W', '🌍': 'R'}}, 'expected': ' HELL  WER '},
            {'input': {'encoded_message': '⭐', 'emoji_map': {'⭐': 'S'}}, 'expected': 'S'},
            {'input': {'encoded_message': '❌', 'emoji_map': {'⭐': 'S'}}, 'expected': '?'},
        ],
        hints=[
            '💡 İpucu 1: Sonuç stringini oluşturmak için boş bir liste (örneğin `decoded_chars = []`) kullanabilir, ardından `str.join()` ile birleştirebilirsiniz.',
            '💡 İpucu 2: Şifreli mesajdaki her karakteri (emoji veya `#`) tek tek kontrol etmek için bir `for` döngüsü kullanın.',
            '💡 İpucu 3: Eğer karakter `#` ise, `decoded_chars` listesine bir boşluk karakteri ekleyin.',
            "💡 İpucu 4: Eğer karakter bir emoji ise, `emoji_map` sözlüğünde karşılığını arayın. `dict.get(emoji, '?')` metodunu kullanarak, haritada olmayan emojiler için `?` karakterini otomatik olarak ekleyebilirsiniz.",
            '💡 İpucu 5: `decoded_chars` listesindeki tüm karakterleri `"".join(decoded_chars)` ile birleştirerek son mesajı oluşturun.',
        ],
    ),

    Question(
        id=66,
        title='✨ Pozitif Yorum Filtresi',
        category='strings',
        level='intermediate',
        description="""Sosyal medya fenomenleri, yorum bölümlerini daha pozitif hale getirmek için senin yardımına ihtiyaç duyuyor! Amacın, verilen bir yorum metnindeki "negatif" kelimeleri sihirli bir `✨` emojisiyle değiştiren bir Python fonksiyonu yazmak. Fonksiyon, büyük/küçük harf ayrımı yapmamalıdır. Yani "Kötü", "kötü" veya "KÖTÜ" kelimeleri aynı şekilde değiştirilmelidir. Kelimenin geçtiği her yeri (büyük/küçük harf fark etmeksizin) emoji ile değiştir.""",
        starter_code="""import re

def pozitif_yorum_filtresi(yorum: str, yasakli_kelimeler: list[str]) -> str:
    # Yorumu döngü içinde yasaklı kelimelerle kontrol et ve değiştir.
    pass""",
        test_cases=[
            {'input': {'yorum': 'Bu çok kötü bir yorum!', 'yasakli_kelimeler': ['kötü']}, 'expected': 'Bu çok ✨ bir yorum!'},
            {'input': {'yorum': 'Berbat, iğrenç bir durum bu.', 'yasakli_kelimeler': ['berbat', 'iğrenç']}, 'expected': '✨, ✨ bir durum bu.'},
            {'input': {'yorum': 'Bu KÖTÜ bir gün, kötü düşüncelerim var.', 'yasakli_kelimeler': ['kötü']}, 'expected': 'Bu ✨ bir gün, ✨ düşüncelerim var.'},
            {'input': {'yorum': 'Her şey harika, çok güzel!', 'yasakli_kelimeler': ['kötü', 'berbat']}, 'expected': 'Her şey harika, çok güzel!'},
            {'input': {'yorum': 'Kötü bir başlangıç ama iyi bitti. Çok kötü!', 'yasakli_kelimeler': ['kötü']}, 'expected': '✨ bir başlangıç ama iyi bitti. Çok ✨!'},
            {'input': {'yorum': 'Bu yorum gerçekten saçma ve berbat.', 'yasakli_kelimeler': ['saçma', 'berbat']}, 'expected': 'Bu yorum gerçekten ✨ ve ✨.'},
            {'input': {'yorum': 'Hiçbir şey yok', 'yasakli_kelimeler': []}, 'expected': 'Hiçbir şey yok'},
            {'input': {'yorum': 'Kötülük yapanlar kötü', 'yasakli_kelimeler': ['kötü']}, 'expected': '✨lük yapanlar ✨'},
        ],
        hints=[
            "💡 İpucu 1: Python'daki `re` (regular expression) modülünü incelemek, bu tür metin değiştirme işlemleri için çok güçlü araçlar sunar.",
            '💡 İpucu 2: `re.sub()` fonksiyonu, bir metin içindeki belirli bir deseni (pattern) başka bir şeyle değiştirmek için kullanılır. Bu fonksiyona dikkat et!',
            '💡 İpucu 3: `re.sub()` kullanırken, büyük/küçük harf duyarlılığını kapatmak için `flags=re.IGNORECASE` parametresini kullanmalısın.',
            '💡 İpucu 4: Yasaklı kelimeler listesindeki her kelime için ayrı ayrı değiştirme işlemi yapman gerekecek. Bunu bir `for` döngüsü içinde düşünebilirsin.',
        ],
    ),

    Question(
        id=67,
        title='✨ Tweet Mood Enhancer',
        category='strings',
        level='intermediate',
        description="""Popüler bir sosyal medya platformu için tweetleri daha canlı ve etkileşimli hale getiren bir araç geliştireceksin. Görevin, bir kullanıcının girdiği metni (tweeti) ve belirli anahtar kelimelere karşılık gelen emojileri içeren bir sözlüğü alarak, metindeki her kelimeyi kontrol etmek ve eğer kelime (büyük/küçük harf fark etmeksizin) sözlükteki bir anahtar kelimeyle tam eşleşiyorsa, o kelimeyi karşılık gelen emoji ile değiştirmektir. Metindeki noktalama işaretlerini (virgül, nokta, ünlem vb.) kelimelerden ayırıp, emojiye dönüştürdükten sonra geri eklemeye dikkat etmelisin. Amacımız, basit ama akıllıca bir emoji entegrasyonu sağlamak!""",
        starter_code="""def tweet_mood_enhancer(tweet_metni: str, emoji_haritasi: dict) -> str:
    # Metindeki kelimeleri noktalama işaretlerinden ayır, 
    # büyük/küçük harf duyarlılığı olmadan emoji_haritasi'nda ara ve değiştir.
    # Sonra kelimeleri ve noktalama işaretlerini tekrar birleştir.
    pass""",
        test_cases=[
            {'input': {'tweet_metni': 'Bugün hava çok güzel, mutlu hissediyorum!', 'emoji_haritasi': {'güzel': '☀️', 'mutlu': '😊'}}, 'expected': 'Bugün hava çok ☀️, 😊 hissediyorum!'},
            {'input': {'tweet_metni': 'Hava harika. MUTLU bir gün!', 'emoji_haritasi': {'harika': '🌈', 'mutlu': '😄', 'hava': '☁️'}}, 'expected': '☁️ 🌈. 😄 bir gün!'},
            {'input': {'tweet_metni': 'Sıradan bir gün.', 'emoji_haritasi': {'yorgun': '😴'}}, 'expected': 'Sıradan bir gün.'},
            {'input': {'tweet_metni': 'Hava güzel, çok güzel.', 'emoji_haritasi': {'güzel': '🌷'}}, 'expected': 'Hava 🌷, çok 🌷.'},
            {'input': {'tweet_metni': 'Merhaba Dünya! Python öğrenmek harika.', 'emoji_haritasi': {'merhaba': '👋', 'dünya': '🌍', 'harika': '✨'}}, 'expected': '👋 🌍! Python öğrenmek ✨.'},
        ],
        hints=[
            '💡 İpucu 1: `str.split()` metodunu kullanarak metni kelimelere ayırabilirsiniz. Ancak kelimelerdeki noktalama işaretlerini de dikkate almanız gerekecek.',
            "💡 İpucu 2: Her kelimeyi kontrol etmeden önce, sonundaki noktalama işaretlerini (varsa) ayırın ve kelimenin kendisini küçük harfe dönüştürerek `emoji_haritasi` içinde arayın. Örneğin, 'güzel,' kelimesinden virgülü ayırıp 'güzel'i arayın.",
            '💡 İpucu 3: Bir kelimeyi emoji ile değiştirdikten sonra, ayırdığınız orijinal noktalama işaretini tekrar emojiye eklemeyi unutmayın. Son olarak, işlenmiş kelimeleri tekrar birleştirmek için `str.join()` metodunu kullanın.',
        ],
    ),

]
