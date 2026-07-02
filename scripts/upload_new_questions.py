"""
Supabase interwiews tablosuna yeni soruları (id 69-73) yükler.
Bu script LOCAL'de calistirilir — Supabase URL ve anon key gerekir.

Kullanim:
    SUPABASE_URL=https://xxx.supabase.co \
    SUPABASE_ANON_KEY=eyJxxx \
    python scripts/upload_new_questions.py
"""

import os
import sys
import warnings
from dataclasses import dataclass, field
from typing import List, Dict, Any

warnings.filterwarnings("ignore")

# ═══ Dataclass — QUESTIONS.py ile aynı ═══
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
    explanation: str = ""
    complexity: str = "O(n)"
    related_concepts: List[str] = field(default_factory=list)
    related_question_ids: List[int] = field(default_factory=list)
    tutorial_slug: str = ""
    slug: str = ""
    day: int = 0
    week: int = 0
    theme: str = ""
    difficulty: int = 1


# ═══ Yeni sorulari tanimla (id 69-73) ═══
NEW_QUESTIONS: List[Question] = [

    Question(
        id=69,
        title="İki Sıralı Listeyi Birleştir (Merge)",
        category="algorithms",
        level="intermediate",
        description="""İki sıralı liste veriliyor (her ikisi de artan düzende).
Bu iki listeyi tek bir sıralı liste halinde birleştir.
Orijinal listeleri değiştirme, yeni bir liste döndür.\n⚠️ sorted() veya .sort() KULLANMA.
Mülakatta O(n+m) çözüm beklenir.""",
        starter_code="""def merge_sorted_lists(list1: list, list2: list) -> list:
    # İki sıralı listeyi birleştir, sonuç sıralı olsun
    # O(n+m) zaman karmaşıklığı hedefle
    pass""",
        test_cases=[
            {'input': {'list1': [1, 3, 5, 7], 'list2': [2, 4, 6, 8]}, 'expected': [1, 2, 3, 4, 5, 6, 7, 8]},
            {'input': {'list1': [1, 2, 3], 'list2': [4, 5, 6]}, 'expected': [1, 2, 3, 4, 5, 6]},
            {'input': {'list1': [], 'list2': [1, 2, 3]}, 'expected': [1, 2, 3]},
            {'input': {'list1': [1, 1, 1], 'list2': [1, 1]}, 'expected': [1, 1, 1, 1, 1]},
        ],
        hints=[
            "💡 İpucu 1: İki işaretçi (pointer) kullan — biri list1, biri list2 için.",
            "💡 İpucu 2: Her adımda hangisi küçükse onu sonuca ekle ve o işaretçiyi ilerlet.",
            "💡 İpucu 3: Biri bitince kalanları olduğu gibi sonuca extend et.",
        ],
    ),

    Question(
        id=70,
        title="En Yakın Rakam Toplamı",
        category="algorithms",
        level="intermediate",
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
            "💡 İpucu 1: Önce listeyi sırala (sıralanmış liste ile çalışmak daha kolay).",
            "💡 İpucu 2: İki işaretçi tekniği kullan — biri başta, biri sonda.",
            "💡 İpucu 3: current_sum = arr[left] + arr[right]; hedefe göre işaretçileri hareket ettir.",
        ],
    ),

    Question(
        id=71,
        title="Tekrarlanan Karakter Zinciri",
        category="algorithms",
        level="intermediate",
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
            "💡 İpucu 1: İki değişken tut: mevcut karakter ve mevcut sayı.",
            "💡 İpucu 2: Her yeni karakter için: aynıysa sayıyı artır, farklıysa sıfırla.",
            "💡 İpucu 3: En uzun zinciri ve karakterini takip et.",
        ],
    ),

    Question(
        id=72,
        title="Alt Dizi Toplam Kontrolü",
        category="algorithms",
        level="intermediate",
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
            "💡 İpucu 1: Sliding window tekniği düşün — başlangıç ve bitiş işaretçileri.",
            "💡 İpucu 2: Mevcut toplam hedefi aştıysa, başlangıcı kaydır.",
            "💡 İpucu 3: Negatif sayılar varsa sliding window çalışmaz — prefix sum + hashmap dene.",
        ],
    ),

    Question(
        id=73,
        title="Benzersiz Alt Dizgi Sayısı",
        category="algorithms",
        level="intermediate",
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
            "💡 İpucu 1: Her karakterden başlayarak tüm alt dizgileri oluştur.",
            "💡 İpucu 2: Bir set() kullanarak benzersiz olanları sakla.",
            "💡 İpucu 3: İç içe döngü yerine, her i için j=i+1,...,len(s) alt dizgisini set'e ekle.",
        ],
    ),

]


def main():
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print("❌ SUPABASE_URL ve SUPABASE_ANON_KEY environment variable'ları gerekli!")
        print("   export SUPABASE_URL=https://xxx.supabase.co")
        print("   export SUPABASE_ANON_KEY=eyJxxx")
        sys.exit(1)

    print(f"✅ Supabase URL: {SUPABASE_URL}")

    # Supabase client
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        print("✅ Supabase client oluşturuldu")
    except ImportError:
        print("❌ supabase paketi yüklü değil: pip install supabase")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Supabase bağlantı hatası: {e}")
        sys.exit(1)

    # Payload hazırla
    payload = []
    for q in NEW_QUESTIONS:
        # Listeye çevir (array kolonlar)
        test_cases = q.test_cases if isinstance(q.test_cases, list) else [q.test_cases]
        hints = q.hints if isinstance(q.hints, list) else [q.hints]
        related_concepts = q.related_concepts if isinstance(q.related_concepts, list) else []
        related_question_ids = q.related_question_ids if isinstance(q.related_question_ids, list) else []

        payload.append({
            "id": q.id,
            "title": q.title,
            "category": q.category,
            "level": q.level,
            "description": q.description,
            "starter_code": q.starter_code,
            "test_cases": test_cases,
            "hints": hints,
        })

    print(f"📦 {len(payload)} soru Supabase'e yükleniyor...")

    try:
        result = (
            supabase.table("interwiews")
            .upsert(payload, on_conflict="id")
            .execute()
        )
        print(f"✅ {len(payload)} soru başarıyla yüklendi/güncellendi!")
        if result.data:
            for item in result.data:
                print(f"   - id={item['id']}: {item['title']}")
    except Exception as e:
        print(f"❌ Supabase hatası: {e}")
        print("\n💡 Olası çözümler:")
        print("   1. RLS kapat: ALTER TABLE interwiews DISABLE ROW LEVEL SECURITY;")
        print("   2. Veya service role key kullan (anon key yetmeyebilir)")
        sys.exit(1)


if __name__ == "__main__":
    main()
