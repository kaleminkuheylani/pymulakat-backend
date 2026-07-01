#!/usr/bin/env python3
"""
AI Soru Fabrikası — OpenAI Provider + SEO Konsepti
====================================================

Mevcut data/QUESTIONS.py ile %100 uyumlu, OpenAI destekli soru üretici.

Mevcut SEO fieldları (QUESTIONS.py ile aynı):
    id, title, category, level, description, starter_code, test_cases,
    hints, explanation, complexity, related_concepts, related_question_ids,
    tutorial_slug, day, week, theme, difficulty

CSV (23 kolon) + DB (interviews tablosu) ile birebir uyumlu.

═══════════════════════════════════════════════════════════════
🚀 NASIL ÇALIŞTIRILIR (5 ADIM)
═══════════════════════════════════════════════════════════════

1️⃣  OpenAI API Key Al
    • https://platform.openai.com/api-keys adresine git
    • "Create new secret key" tıkla, kopyala
    • Kullanım: ~$0.001-0.01/soru (gpt-4o-mini ile)

2️⃣  API Key'i Tanımla
    a) Geçici (terminal session):
       export OPENAI_API_KEY="sk-..."
       # veya Windows:
       set OPENAI_API_KEY=sk-...

    b) Kalıcı (.env dosyası — önerilen):
       pymulakat-backend/.env dosyasına ekle:
       OPENAI_API_KEY=sk-...
       OPENAI_MODEL=gpt-4o-mini   # veya gpt-4o

    c) Doğrula:
       python3 -c "import os; print(os.getenv('OPENAI_API_KEY')[:10] + '...')"

3️⃣  Sanal Ortam Aktifleştir
    cd pymulakat-backend
    source .venv/bin/activate       # Linux/Mac
    # veya: .venv\Scripts\activate  # Windows

4️⃣  OpenAI Paketi Kur
    pip install openai python-dotenv
    # veya tüm bağımlılıklar:
    pip install -r requirements.txt

5️⃣  Çalıştır!
    # Tüm müfredat tier uretimi (25 intermediate soru)
    python3 scripts/ai_question_factory.py --all --tier intermediate --per-category 5

    # Engagement zincir (mevcut 67'den devam)
    python3 scripts/ai_question_factory.py --engagement --count 10

    # Yaratıcı sorular
    python3 scripts/ai_question_factory.py --generate-creative --count 5

    # Belirli kategoriler
    python3 scripts/ai_question_factory.py --categories algorithms strings --tier advanced --per-category 3

═══════════════════════════════════════════════════════════════
📋 TÜM KOMUTLAR
═══════════════════════════════════════════════════════════════

Temel:
    --day N                  Tek gun ID (ornek: 68)
    --week N                 Bir hafta (1-12)
    --range START-END        Aralik (ornek: 68-75)
    --all                    Tum kategoriler icin tier uretimi

Tier Bazli:
    --tier {beginner_plus,intermediate,advanced}
    --per-category N         Her kategoriden kac soru
    --categories cat1 cat2   Sadece belirli kategoriler

Ozel Modlar:
    --engagement             Mevcut sorulardan engagement zincir
    --generate-creative      Yaratici engagement sorulari
    --count N                Soru sayisi (varsayilan: 5)

Cikti Kontrol:
    --no-save                Sadece uret, kaydetme (test icin)
    --csv-only               Sadece CSV export, .py yazma

═══════════════════════════════════════════════════════════════
💰 MALİYET TAHMİNİ (gpt-4o-mini)
═══════════════════════════════════════════════════════════════
    --all --tier beginner_plus --per-category 3   =  15 soru  ≈ $0.05
    --all --tier intermediate --per-category 5    =  25 soru  ≈ $0.10
    --all --tier advanced --per-category 2        =  10 soru  ≈ $0.05
    --engagement --count 10                       =  10 soru  ≈ $0.04
    --generate-creative --count 5                 =   5 soru  ≈ $0.02

═══════════════════════════════════════════════════════════════
🔧 SORUN GİDERME
═══════════════════════════════════════════════════════════════

Hata: "Incorrect API key"
    → OPENAI_API_KEY yanlis veya tanimli degil
    → Kontrol: echo $OPENAI_API_KEY
    → Yeniden: export OPENAI_API_KEY="sk-..."

Hata: "Rate limit reached"
    → OpenAI hesabinda limit asildi
    → Bekle 1-2 dakika veya yukle yap
    → https://platform.openai.com/account/limits

Hata: "openai yüklü değil"
    → pip install openai
    → Veya: pip install -r requirements.txt

Hata: "ModuleNotFoundError: dotenv"
    → pip install python-dotenv

Hata: JSON parse hatasi
    → OpenAI bazen markdown code block ile donduruyor
    → Script otomatik temizliyor ama bazen yetersiz
    → Prompt sicakligini dusur: temperature=0.7

Hata: "Bu soru zaten var"
    → OpenAI mevcut basliklara bakarak uretiyor
    → Cok benzer sonuclar geliyorsa tier'i degistir

═══════════════════════════════════════════════════════════════
📁 ÇIKTI DOSYALARI
═══════════════════════════════════════════════════════════════

    data/QUESTIONS.py            → Mevcut + yeni sorular (import edilebilir)
    data/QUESTIONS_FACTORY.csv   → Sadece yeni sorular (CSV, 23 kolon)

DB'ye aktarmak icin:
    # Backend calisiyorsa admin endpoint:
    curl -X POST https://pymulakat-backend-production.up.railway.app/admin/migrate/questions-factory

    # Veya Railway shell'den:
    python3 scripts/migrate_factory.py

═══════════════════════════════════════════════════════════════
"""

import os
import sys
import io
import json
import csv
import re
import argparse
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict

# Windows UTF-8 fix
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# OpenAI provider (Gemini yerine)
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("⚠️ openai yüklü değil: pip install openai")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ════════════════════════════════════════════════════════════
# AYARLAR
# ════════════════════════════════════════════════════════════

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
QUESTIONS_FILE = os.path.join(DATA_DIR, "QUESTIONS.py")
CSV_FILE = os.path.join(DATA_DIR, "QUESTIONS.csv")
EXPORT_CSV = os.path.join(DATA_DIR, "QUESTIONS_FACTORY.csv")

# ════════════════════════════════════════════════════════════
# KATEGORİ META (mevcut yapıyla uyumlu — 5 kategori)
# ════════════════════════════════════════════════════════════

CATEGORY_META = {
    "python-basics": {
        "tr": "Python Temelleri",
        "topics": ["degisken", "operator", "kosul", "dongu", "fonksiyon", "scope",
                   "lambda", "decorator", "generator", "context manager"],
        "seo_focus": "temel Python kavramlari, veri tipleri, kontrol yapilari",
    },
    "strings": {
        "tr": "String İşlemleri",
        "topics": ["indexing", "slicing", "split/join", "regex", "format",
                   "encode", "unicode", "string algoritmalari"],
        "seo_focus": "metin isleme, duzenli ifadeler, formatlama",
    },
    "list-dict": {
        "tr": "Liste ve Sözlük",
        "topics": ["list", "dict", "tuple", "set", "comprehension", "nested",
                   "heapq", "defaultdict", "counter", "itertools"],
        "seo_focus": "veri yapilari, koleksiyon, iterasyon",
    },
    "pandas": {
        "tr": "Pandas Veri Analizi",
        "topics": ["series", "dataframe", "filter", "groupby", "merge", "apply",
                   "pivot", "multiindex", "time series"],
        "seo_focus": "veri analizi, DataFrame, istatistik",
    },
    "algorithms": {
        "tr": "Algoritmalar",
        "topics": ["sort", "search", "recursion", "dp", "greedy",
                   "graph", "backtracking", "memoization", "complexity"],
        "seo_focus": "algoritma tasarimi, karmaasiklik analizi, problem cozme",
    },
}

# Tier bazli engagement tanimlari
ENGAGEMENT_TIERS = {
    "beginner_plus": {
        "level": "beginner",
        "count_per_cat": 3,
        "focus": "Real-world scenario + edge cases",
        "seo_keywords": ["temel", "baslangic", "ornekli", "pratik"],
    },
    "intermediate": {
        "level": "intermediate",
        "count_per_cat": 5,
        "focus": "Multi-step, edge cases, optimization",
        "seo_keywords": ["ileri", "optimizasyon", "gercek hayat", "production"],
    },
    "advanced": {
        "level": "advanced",
        "count_per_cat": 2,
        "focus": "Production-ready, trade-off analysis",
        "seo_keywords": ["production", "performans", "tasarim karari", "trade-off"],
    },
}

# ════════════════════════════════════════════════════════════
# QUESTION DATACLASS — MEVCUT YAPI İLE UYUMLU
# ════════════════════════════════════════════════════════════

@dataclass
class Question:
    """Mevcut data/QUESTIONS.py formatı ile %100 uyumlu"""
    id: int
    title: str
    category: str
    level: str
    description: str
    starter_code: str
    test_cases: List[Dict[str, Any]]
    hints: List[str] = field(default_factory=list)

    # SEO alanları (mevcut yapı)
    explanation: str = ""
    complexity: str = "O(n)"
    related_concepts: List[str] = field(default_factory=list)
    related_question_ids: List[int] = field(default_factory=list)
    tutorial_slug: Optional[str] = None

    # Curriculum (opsiyonel)
    day: int = 0
    week: int = 0
    theme: str = ""
    difficulty: int = 1


# ════════════════════════════════════════════════════════════
# HELPER FONKSİYONLAR
# ════════════════════════════════════════════════════════════

def slugify(text: str) -> str:
    """Türkçe karakterleri slugify"""
    tr = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    text = text.lower().translate(tr)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text).strip('-')
    return text[:80]


def get_openai_client() -> Optional["OpenAI"]:
    """OpenAI client oluştur"""
    if not HAS_OPENAI:
        return None
    if not OPENAI_API_KEY:
        print("⚠️ OPENAI_API_KEY tanimli degil")
        return None
    return OpenAI(api_key=OPENAI_API_KEY)


def get_next_id() -> int:
    """QUESTIONS.py'deki en son ID + 1"""
    if not os.path.exists(QUESTIONS_FILE):
        return 1
    try:
        with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        ids = re.findall(r'\bid=(\d+)\b', content)
        if ids:
            return max(int(i) for i in ids) + 1
    except Exception as e:
        print(f"⚠️ QUESTIONS.py okuma hatasi: {e}")
    return 1


def load_existing_questions() -> List[Question]:
    """QUESTIONS.py'yi import ederek mevcut sorulari yukle"""
    if not os.path.exists(QUESTIONS_FILE):
        return []
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("questions_module", QUESTIONS_FILE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return list(module.QUESTIONS)
    except Exception as e:
        print(f"⚠️ QUESTIONS.py yuklenemedi: {e}")
        return []


def load_existing_titles() -> List[str]:
    """Mevcut basliklari yukle (tekrari onlemek icin)"""
    questions = load_existing_questions()
    return [q.title for q in questions]


# ════════════════════════════════════════════════════════════
# OPENAI PROMPT ŞABLONLARI — SEO KONSEPTİ
# ════════════════════════════════════════════════════════════

def build_prompt_seo(category: str, level: str, tier: str,
                     prev_questions: List[str], q_id: int) -> str:
    """SEO uyumlu, mevcut 16 alanla uyumlu soru üret"""
    meta = CATEGORY_META.get(category, {})

    return f"""Sen bir Python egitim platformu icerik yazarisin. Asagidaki kriterlere uygun bir soru uret.

KATEGORI: {category} ({meta.get('tr', category)})
SEVIYE: {level}
TIER: {tier}
ODAK: {ENGAGEMENT_TIERS.get(tier, {}).get('focus', 'pratik')}

SEO BILGILERI:
- Kategori odak: {meta.get('seo_focus', '')}
- Tier anahtar kelimeler: {', '.join(ENGAGEMENT_TIERS.get(tier, {}).get('seo_keywords', []))}

MEVCUT 67 SORUNUN BASLIKLARI (tekrarlama!):
{chr(10).join(f"- {t}" for t in prev_questions[:15])}

CIKTI — SADECE JSON (markdown code block KULLANMA):

{{
  "title": "Engagement cekici baslik. Turkce, max 60 karakter, EMOJI YOK. SEO uyumlu (anahtar kelime icersin)",
  "category": "{category}",
  "level": "{level}",
  "description": "Net problem tanimi. 2-4 cumle. Gercek hayat senaryosu tercih et. ornek girdi/cikti goster.",
  "starter_code": "def function_name(param: type) -> return_type:\\n    # TODO - kisa yorum\\n    pass",
  "test_cases": [
    {{"input": "...", "expected": "..."}},
    {{"input": "...", "expected": "..."}}
  ],
  "hints": [
    "Ipucu 1: adim adim",
    "Ipucu 2:",
    "Ipucu 3:"
  ],
  "explanation": "Cozum yaklasimi 200-400 kelime, Markdown formatinda (## Baslik, kod blogu). Neden bu algoritma, trade-off, optimizasyon",
  "complexity": "O(n) - aciklama",
  "related_concepts": ["kavram1", "kavram2", "kavram3"],
  "tutorial_slug": "/guides/ilgili-tutorial-slug veya bos string",
  "day": 0,
  "week": 0,
  "theme": "Tema/aciklama (1 cumle, emoji YOK)",
  "difficulty": 1-5
}}

KURALLAR (siki):
1. EMOJI KULLANMA — hicbir alanda (title, description, hints, theme dahil)
2. SEO uyumlu: title icinde anahtar kelime, description acik
3. Engagement: gercek hayat senaryosu, sirket mulakat tonu
4. test_cases min 2, max 4
5. starter_code TODO/pass ile bitsin, type hint zorunlu
6. explanation 200-400 kelime, Markdown, kod ornegi icersin
7. complexity Big-O notasyonu + aciklama
8. related_concepts: 3-5 kavram, SEO dostu
9. related_question_ids: simdilik bos liste []
10. tutorial_slug: varsa ilgili tutorial, yoksa ""
11. TEK bir JSON objesi dondur, baska sey yazma
12. onceki sorulari tekrarlama
"""


def build_prompt_engagement(category: str, level: str, q_id: int,
                            prev_id: int, theme: str = "") -> str:
    """Engagement odakli — onceki soruya bagli zincir"""
    meta = CATEGORY_META.get(category, {})

    return f"""Sen populer bir Python egitim platformunun senior icerik yazarisin.
Amac: etkilesimi (engagement) yuksek, gercek hayat senaryolu bir soru uretmek.

BILGI:
- ID: {q_id}
- Kategori: {category} ({meta.get('tr', category)})
- Seviye: {level}
- Onceki bag: #{prev_id}
- {f'Tema: {theme}' if theme else ''}

CIKTI — SADECE JSON:

{{
  "title": "Engagement cekici baslik (Turkce, EMOJI YOK, max 60 karakter)",
  "category": "{category}",
  "level": "{level}",
  "description": "3-5 cumle. Mulakat sorusu gibi, gercek sirket senaryosu. Onceki cozumle iliskilendir. Ornek kullanim goster.",
  "starter_code": "def function_name(param: type) -> return_type:\\n    # TODO\\n    pass",
  "test_cases": [
    {{"input": "deger1", "expected": "sonuc1"}},
    {{"input": "deger2", "expected": "sonuc2"}},
    {{"input": "deger3", "expected": "sonuc3"}}
  ],
  "hints": [
    "Ipucu 1: ilk adim",
    "Ipucu 2: optimizasyon ipucu",
    "Ipucu 3: edge case cozumu"
  ],
  "explanation": "200-400 kelime Markdown cozum. Neden bu algoritma, alternative yaklasimlar, production'da ne yapilir",
  "complexity": "O(n) - detayli aciklama",
  "related_concepts": ["kavram1", "kavram2", "kavram3", "kavram4"],
  "related_question_ids": [{prev_id}],
  "tutorial_slug": "",
  "day": 0,
  "week": 0,
  "theme": "{theme}",
  "difficulty": 3
}}

KURALLAR:
1. EMOJI YOK (baslik, description, hints, theme dahil)
2. Engagement: senaryo, gercek hayat, mulakat tonu
3. Onceki soruyla iliskilendir (related_question_ids: [{prev_id}])
4. Tek bir JSON objesi
"""


# ════════════════════════════════════════════════════════════
# OPENAI ÇAĞRISI
# ════════════════════════════════════════════════════════════

def call_openai(prompt: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
    """OpenAI API çağrısı — retry + backoff"""
    client = get_openai_client()
    if not client:
        return None

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Sen JSON cikti veren bir Python icerik uzmanisin."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.8,
                max_tokens=2500,
            )
            text = response.choices[0].message.content.strip()
            return json.loads(text)
        except Exception as e:
            print(f"  ! OpenAI hatasi (deneme {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

    return None


def call_openai_simple(prompt: str) -> Optional[Dict[str, Any]]:
    """response_format desteklemeyen eski modeller icin"""
    client = get_openai_client()
    if not client:
        return None
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Sen JSON cikti veren bir Python icerik uzmanisin. Sadece JSON dondur, baska sey yazma."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
            max_tokens=2500,
        )
        text = response.choices[0].message.content.strip()
        # JSON temizle
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'^```\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        return json.loads(text)
    except Exception as e:
        print(f"  ! OpenAI hatasi: {e}")
        return None


# ════════════════════════════════════════════════════════════
# GENERATOR CLASS — MEVCUT YAPIYLA UYUMLU
# ════════════════════════════════════════════════════════════

class AIQuestionFactory:
    """OpenAI + SEO konsepti ile soru uretici"""

    def __init__(self):
        self.existing_questions = load_existing_questions()
        self.existing_titles = [q.title for q in self.existing_questions]
        self.next_id = self._get_next_id()

    def _get_next_id(self) -> int:
        """Son ID + 1"""
        if not self.existing_questions:
            return 1
        return max(q.id for q in self.existing_questions) + 1

    def _parse_question(self, data: Dict[str, Any]) -> Optional[Question]:
        """JSON dict'i Question dataclass'a donustur"""
        try:
            return Question(
                id=int(data.get("id", self.next_id)),
                title=str(data.get("title", "")).strip(),
                category=str(data.get("category", "python-basics")),
                level=str(data.get("level", "beginner")),
                description=str(data.get("description", "")),
                starter_code=str(data.get("starter_code", "")),
                test_cases=data.get("test_cases", []),
                hints=data.get("hints", []),
                explanation=str(data.get("explanation", "")),
                complexity=str(data.get("complexity", "O(n)")),
                related_concepts=data.get("related_concepts", []),
                related_question_ids=data.get("related_question_ids", []),
                tutorial_slug=data.get("tutorial_slug") or None,
                day=int(data.get("day", 0)),
                week=int(data.get("week", 0)),
                theme=str(data.get("theme", "")),
                difficulty=int(data.get("difficulty", 1)),
            )
        except Exception as e:
            print(f"  ! Parse hatasi: {e}")
            return None

    def generate_seo_question(self, category: str, level: str = "intermediate",
                              tier: str = "intermediate") -> Optional[Question]:
        """SEO uyumlu soru uret"""
        prompt = build_prompt_seo(
            category=category,
            level=level,
            tier=tier,
            prev_questions=self.existing_titles,
            q_id=self.next_id,
        )

        data = call_openai(prompt)
        if not data:
            return None

        question = self._parse_question(data)
        if question:
            question.id = self.next_id
            self.next_id += 1
            self.existing_titles.append(question.title)
        return question

    def generate_engagement_question(self, category: str, level: str,
                                     prev_id: int, theme: str = "") -> Optional[Question]:
        """Engagement odakli soru — onceki soruya bagli"""
        prompt = build_prompt_engagement(
            category=category,
            level=level,
            q_id=self.next_id,
            prev_id=prev_id,
            theme=theme,
        )

        data = call_openai(prompt)
        if not data:
            return None

        question = self._parse_question(data)
        if question:
            question.id = self.next_id
            question.related_question_ids = [prev_id]
            self.next_id += 1
            self.existing_titles.append(question.title)
        return question

    def generate_creative_question(self, q_id: int, category: str,
                                   level: str) -> Optional[Question]:
        """Yaratici engagement sorusu"""
        prompt = f"""Sen popüler bir Python eğitim platformunun içerik yöneticisisin.
{q_id} ID'li, {category}/{level} seviyesinde, etkileşimi yüksek bir soru üret.

Senaryo: gerçek hayat, sosyal medya, oyun mekaniği, gizli mesaj gibi eğlenceli durumlar.
Seviye: {'başlangıç' if level == 'beginner' else 'orta'}.
Zorluk: çok zor değil ama tatmin edici.

SADECE JSON (markdown code block KULLANMA):

{{
  "title": "Engagement cekici baslik (Turkce, EMOJI YOK)",
  "category": "{category}",
  "level": "{level}",
  "description": "3-5 cumle senaryo + ornek kullanim",
  "starter_code": "def function_name(param: type) -> return_type:\\n    # TODO\\n    pass",
  "test_cases": [
    {{"input": "deger1", "expected": "sonuc1"}},
    {{"input": "deger2", "expected": "sonuc2"}}
  ],
  "hints": ["Ipucu 1", "Ipucu 2", "Ipucu 3"],
  "explanation": "150-250 kelime cozum yaklasimi",
  "complexity": "O(n)",
  "related_concepts": ["k1", "k2", "k3"],
  "related_question_ids": [],
  "tutorial_slug": "",
  "theme": "",
  "difficulty": 2
}}

KURALLAR:
1. EMOJI YOK
2. test_cases min 2, max 4
3. starter_code type hint ile
4. related_question_ids bos liste
"""

        data = call_openai(prompt)
        if not data:
            return None

        question = self._parse_question(data)
        if question:
            question.id = q_id
        return question

    # ════════════════════════════════════════════════════════
    # TOPLU ÜRETİM
    # ════════════════════════════════════════════════════════

    def generate_seo_batch(self, tier: str = "intermediate",
                          per_category: int = 5,
                          categories: Optional[List[str]] = None) -> List[Question]:
        """Tier bazli toplu SEO uretim"""
        if categories is None:
            categories = list(CATEGORY_META.keys())

        tier_meta = ENGAGEMENT_TIERS.get(tier, ENGAGEMENT_TIERS["intermediate"])
        questions: List[Question] = []

        print(f"\n{'='*60}")
        print(f"TOPLU SEO URETIM — tier={tier}, per_category={per_category}")
        print(f"{'='*60}")

        for category in categories:
            print(f"\n[{category}] {per_category} soru uretiliyor...")

            for i in range(per_category):
                q = self.generate_seo_question(
                    category=category,
                    level=tier_meta["level"],
                    tier=tier,
                )
                if q:
                    questions.append(q)
                    print(f"  ✓ #{q.id}: {q.title}")
                else:
                    print(f"  ✗ Basarisiz")

        return questions

    def generate_engagement_batch(self, count: int = 10) -> List[Question]:
        """Engagement zincir — mevcut sorulari baz alarak devam"""
        if not self.existing_questions:
            print("⚠️ Mevcut soru yok, once QUESTIONS.py olustur")
            return []

        questions: List[Question] = []
        print(f"\n{'='*60}")
        print(f"ENGAGEMENT ZINCIR — {count} yeni soru")
        print(f"{'='*60}")

        # Son N soruyu baz al
        base_questions = self.existing_questions[-count:] if len(self.existing_questions) >= count else self.existing_questions

        for prev_q in base_questions:
            print(f"\n[BAG] #{prev_q.id} {prev_q.title} → devam...")

            # Engagement seviye artisi
            new_level = "intermediate" if prev_q.level == "beginner" else "advanced"
            new_difficulty = min(prev_q.difficulty + 1, 5)

            q = self.generate_engagement_question(
                category=prev_q.category,
                level=new_level,
                prev_id=prev_q.id,
                theme=prev_q.theme,
            )
            if q:
                q.difficulty = new_difficulty
                q.related_question_ids = [prev_q.id]
                questions.append(q)
                print(f"  ✓ #{q.id}: {q.title} ({new_level})")

        return questions

    # ════════════════════════════════════════════════════════
    # KAYDETME — MEVCUT FORMATLA UYUMLU
    # ════════════════════════════════════════════════════════

    def save_to_python_file(self, questions: List[Question], filepath: str):
        """QUESTIONS.py'ye ekle — mevcut yapı korunur"""
        existing = load_existing_questions()
        existing_ids = {q.id for q in existing}
        new_questions = [q for q in questions if q.id not in existing_ids]
        all_questions = sorted(existing + new_questions, key=lambda q: q.id)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# data/QUESTIONS.py\n")
            f.write("# Mevcut SEO alanlariyla uyumlu\n")
            f.write("from dataclasses import dataclass, field\n")
            f.write("from typing import List, Dict, Any, Optional\n\n\n")
            f.write("@dataclass\n")
            f.write("class Question:\n")
            f.write("    id: int\n")
            f.write("    title: str\n")
            f.write("    category: str\n")
            f.write("    level: str\n")
            f.write("    description: str\n")
            f.write("    starter_code: str\n")
            f.write("    test_cases: List[Dict[str, Any]]\n")
            f.write("    hints: List[str] = field(default_factory=list)\n")
            f.write("    # SEO alanlari\n")
            f.write("    explanation: str = \"\"\n")
            f.write("    complexity: str = \"O(n)\"\n")
            f.write("    related_concepts: List[str] = field(default_factory=list)\n")
            f.write("    related_question_ids: List[int] = field(default_factory=list)\n")
            f.write("    tutorial_slug: Optional[str] = None\n")
            f.write("    # Curriculum\n")
            f.write("    day: int = 0\n")
            f.write("    week: int = 0\n")
            f.write("    theme: str = \"\"\n")
            f.write("    difficulty: int = 1\n\n\n")
            f.write("QUESTIONS: List[Question] = [\n\n")

            for q in all_questions:
                desc = q.description.replace('"""', '\\"\\"\\"')
                starter = q.starter_code.replace('"""', '\\"\\"\\"')
                explanation = q.explanation.replace('"""', '\\"\\"\\"')

                f.write(f"    Question(\n")
                f.write(f"        id={q.id},\n")
                f.write(f"        title={repr(q.title)},\n")
                f.write(f"        category={repr(q.category)},\n")
                f.write(f"        level={repr(q.level)},\n")
                f.write(f"        description=\"\"\"{desc}\"\"\",\n")
                f.write(f"        starter_code=\"\"\"{starter}\"\"\",\n")

                # test_cases
                tc_str = "[\n"
                for tc in q.test_cases:
                    tc_str += f"            {repr(tc)},\n"
                tc_str += "        ]"

                # hints
                h_str = "[\n"
                for h in q.hints:
                    h_str += f"            {repr(h)},\n"
                h_str += "        ]"

                f.write(f"        test_cases={tc_str},\n")
                f.write(f"        hints={h_str},\n")
                f.write(f"        explanation=\"\"\"{explanation}\"\"\",\n")
                f.write(f"        complexity={repr(q.complexity)},\n")
                f.write(f"        related_concepts={repr(q.related_concepts)},\n")
                f.write(f"        related_question_ids={repr(q.related_question_ids)},\n")
                f.write(f"        tutorial_slug={repr(q.tutorial_slug)},\n")
                f.write(f"        day={q.day},\n")
                f.write(f"        week={q.week},\n")
                f.write(f"        theme={repr(q.theme)},\n")
                f.write(f"        difficulty={q.difficulty},\n")
                f.write(f"    ),\n\n")

            f.write("]\n")

        print(f"\n✅ {len(all_questions)} soru {filepath} dosyasina kaydedildi")
        print(f"   (+{len(new_questions)} yeni)")

    def save_to_csv(self, questions: List[Question], filepath: str):
        """CSV export — 23 kolon (mevcut CSV ile uyumlu)"""
        fieldnames = [
            "category", "title", "level", "description", "starter_code",
            "test_cases", "hints", "id", "slug", "explanation", "complexity",
            "related_concepts", "related_question_ids", "tutorial_slug",
            "meta_title", "meta_description", "meta_keywords",
            "reading_time_minutes", "tags", "updated_at", "created_at",
            "day", "week", "theme", "difficulty",
        ]

        now = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for q in questions:
                writer.writerow({
                    "category": q.category,
                    "title": q.title,
                    "level": q.level,
                    "description": q.description,
                    "starter_code": q.starter_code,
                    "test_cases": json.dumps(q.test_cases, ensure_ascii=False),
                    "hints": json.dumps(q.hints, ensure_ascii=False),
                    "id": q.id,
                    "slug": slugify(q.title),
                    "explanation": q.explanation,
                    "complexity": q.complexity,
                    "related_concepts": json.dumps(q.related_concepts, ensure_ascii=False),
                    "related_question_ids": json.dumps(q.related_question_ids, ensure_ascii=False),
                    "tutorial_slug": q.tutorial_slug or "",
                    "meta_title": q.title[:60],
                    "meta_description": q.description[:160],
                    "meta_keywords": f"python,{q.category},{q.level}",
                    "reading_time_minutes": 5,
                    "tags": json.dumps(["engagement", "seo"], ensure_ascii=False),
                    "updated_at": now,
                    "created_at": now,
                    "day": q.day,
                    "week": q.week,
                    "theme": q.theme,
                    "difficulty": q.difficulty,
                })

        print(f"✅ {len(questions)} soru CSV'ye yazildi: {filepath}")


# ════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="AI Soru Fabrikasi — OpenAI + SEO konsepti (data/QUESTIONS.py ile uyumlu)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
═══════════════════════════════════════════════════════════════
🚀 HIZLI BAŞLANGIÇ
═══════════════════════════════════════════════════════════════

1) export OPENAI_API_KEY="sk-..."
2) cd pymulakat-backend && source .venv/bin/activate
3) python3 scripts/ai_question_factory.py --all --tier intermediate --per-category 5

═══════════════════════════════════════════════════════════════
📌 KULLANIM ÖRNEKLERİ
═══════════════════════════════════════════════════════════════

  Tum kategoriler, 5'er intermediate soru (67 → 92):
    python3 ai_question_factory.py --all --tier intermediate --per-category 5

  Engagement zincir (mevcut sorulardan devam):
    python3 ai_question_factory.py --engagement --count 10

  Yaratıcı sorular:
    python3 ai_question_factory.py --generate-creative --count 5

  Sadece algorithms + strings, advanced tier:
    python3 ai_question_factory.py --categories algorithms strings \\
      --tier advanced --per-category 3

  Test modu (kaydetme yok):
    python3 ai_question_factory.py --generate-creative --count 1 --no-save

  Sadece CSV export (QUESTIONS.py yazma):
    python3 ai_question_factory.py --generate-creative --count 5 --csv-only

═══════════════════════════════════════════════════════════════
💰 MALİYET (gpt-4o-mini)
═══════════════════════════════════════════════════════════════
  --all --tier intermediate --per-category 5   ≈ $0.10  (25 soru)
  --engagement --count 10                       ≈ $0.04  (10 soru)
  --generate-creative --count 5                 ≈ $0.02  (5  soru)

Detaylı bilgi icin: python3 scripts/ai_question_factory.py (dosya basindaki docstring)
        """,
    )
    parser.add_argument("--day", type=int, help="Tek gun ID (ornek: 68)")
    parser.add_argument("--week", type=int, help="Bir hafta (1-12)")
    parser.add_argument("--range", type=str, help="Aralik (ornek: 68-75)")
    parser.add_argument("--tier", choices=list(ENGAGEMENT_TIERS.keys()),
                        default="intermediate", help="Engagement tier (varsayilan: intermediate)")
    parser.add_argument("--per-category", type=int, default=None,
                        help="Her kategoriden kac soru (tier defaultunu ezer)")
    parser.add_argument("--categories", nargs="+", default=None,
                        help="Sadece belirli kategoriler (orn: algorithms strings)")
    parser.add_argument("--generate-creative", action="store_true",
                        help="Yaratici engagement sorulari (count ile)")
    parser.add_argument("--count", type=int, default=5,
                        help="Yaratici/engagement soru sayisi (varsayilan: 5)")
    parser.add_argument("--engagement", action="store_true",
                        help="Mevcut 67 sorudan engagement zincir uret")
    parser.add_argument("--all", action="store_true",
                        help="Tum 5 kategori icin tier uretimi")
    parser.add_argument("--no-save", action="store_true",
                        help="Sadece uret, kaydetme (test modu)")
    parser.add_argument("--csv-only", action="store_true",
                        help="Sadece CSV export, QUESTIONS.py yazma")

    args = parser.parse_args()

    print("=" * 60)
    print("AI SORU FABRIKASI — OpenAI + SEO Konsepti")
    print("=" * 60)

    factory = AIQuestionFactory()

    # OPENAI_API_KEY kontrol
    if not OPENAI_API_KEY:
        print("\n⚠️  OPENAI_API_KEY tanimli degil!")
        print("")
        print("   Cozum 1 (terminal):")
        print('     export OPENAI_API_KEY="sk-..."')
        print("")
        print("   Cozum 2 (.env dosyasi — pymulakat-backend/.env):")
        print("     OPENAI_API_KEY=sk-...")
        print("     OPENAI_MODEL=gpt-4o-mini")
        print("")
        print("   Sonra: python3 scripts/ai_question_factory.py --help")
        return

    print(f"\n📊 Mevcut: {len(factory.existing_questions)} soru")
    print(f"📊 Sonraki ID: {factory.next_id}")
    print(f"📊 Model: {OPENAI_MODEL}")

    generated: List[Question] = []

    # Komutlari isle
    if args.generate_creative:
        # Yaratici sorular
        print(f"\n🎨 Yaratici mod: {args.count} soru")
        for i in range(args.count):
            cat = list(CATEGORY_META.keys())[i % len(CATEGORY_META)]
            lvl = "beginner" if i % 2 == 0 else "intermediate"
            q = factory.generate_creative_question(
                q_id=factory.next_id + i,
                category=cat,
                level=lvl,
            )
            if q:
                generated.append(q)
                print(f"  ✓ #{q.id} [{cat}/{lvl}]: {q.title}")
                factory.next_id = max(factory.next_id, q.id) + 1

    elif args.engagement:
        # Engagement zincir
        print(f"\n🔗 Engagement zincir: {args.count} soru")
        generated = factory.generate_engagement_batch(count=args.count)

    elif args.all:
        # Tum kategoriler tier uretimi
        tier_meta = ENGAGEMENT_TIERS[args.tier]
        per_cat = args.per_category or tier_meta["count_per_cat"]
        print(f"\n📚 Tier uretimi: {args.tier} × {per_cat}/kategori")
        if args.categories:
            print(f"   Filtre: {args.categories}")
        generated = factory.generate_seo_batch(
            tier=args.tier,
            per_category=per_cat,
            categories=args.categories,
        )

    elif args.day:
        # Tek gun
        cat = list(CATEGORY_META.keys())[args.day % len(CATEGORY_META)]
        print(f"\n📝 Tek gun: ID={args.day}, kategori={cat}")
        q = factory.generate_seo_question(category=cat, level="intermediate", tier=args.tier)
        if q:
            generated.append(q)
            print(f"  ✓ #{q.id}: {q.title}")

    else:
        print("\n📌 Kullanim ornekleri:")
        print("")
        print("  # 67 → 92 soru (25 intermediate)")
        print("  python3 scripts/ai_question_factory.py --all --tier intermediate --per-category 5")
        print("")
        print("  # Engagement zincir (10 yeni)")
        print("  python3 scripts/ai_question_factory.py --engagement --count 10")
        print("")
        print("  # Yaratıcı (5 yeni)")
        print("  python3 scripts/ai_question_factory.py --generate-creative --count 5")
        print("")
        print("  # Sadece algorithms + strings")
        print("  python3 scripts/ai_question_factory.py --categories algorithms strings \\")
        print("      --tier advanced --per-category 3")
        print("")
        print("  # Test (kaydetme yok)")
        print("  python3 scripts/ai_question_factory.py --generate-creative --count 1 --no-save")
        return

    if not generated:
        print("\n❌ Hicbir soru uretilmedi (OPENAI_API_KEY veya rate limit kontrol et)")
        return

    print(f"\n📦 Toplam: {len(generated)} yeni soru")

    # Kaydet
    if not args.no_save:
        if args.csv_only:
            factory.save_to_csv(generated, EXPORT_CSV)
        else:
            factory.save_to_python_file(generated, QUESTIONS_FILE)
            factory.save_to_csv(generated, EXPORT_CSV)
        print(f"\n💾 Cikti dosyalari:")
        print(f"   • {QUESTIONS_FILE}")
        print(f"   • {EXPORT_CSV}")
    else:
        print("\n🔍 Test modu — kaydedilmedi (--no-save)")


if __name__ == "__main__":
    main()