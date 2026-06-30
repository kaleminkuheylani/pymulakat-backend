import os
import json
import sys
import io
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import google.generativeai as genai
from dotenv import load_dotenv

# Windows terminal UTF-8 encoding fix
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

load_dotenv()

# Gemini API yapılandırması
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


@dataclass
class Question:
    """Mevcut backend Question formatı ile uyumlu"""
    id: int
    title: str
    category: str
    level: str
    description: str
    starter_code: str
    test_cases: List[Dict[str, Any]]
    hints: List[str] = field(default_factory=list)


class AIQuestionGenerator:
    """AI ile Python soruları üreten servis — 84 günlük müfredat"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.curriculum = self._load_curriculum()
    
    def _load_curriculum(self) -> List[Dict[str, Any]]:
        """84 günlük eğitim müfredatı"""
        return [
            # ═══════════════════════════════════════════════════════
            # HAFTA 1: Python Temelleri (beginner)
            # ═══════════════════════════════════════════════════════
            {"day": 1, "week": 1, "topic": "Değişkenler ve Veri Tipleri",
             "category": "python-basics", "level": "beginner",
             "theme": "🎮 RPG Karakter Oluşturucu", "difficulty": 1},
            {"day": 2, "week": 1, "topic": "Operatörler ve İfadeler",
             "category": "python-basics", "level": "beginner",
             "theme": "💰 Market Kasası Hesaplama", "difficulty": 1},
            {"day": 3, "week": 1, "topic": "Koşul İfadeleri (if/elif/else)",
             "category": "python-basics", "level": "beginner",
             "theme": "🎢 Lunapark Bilet Sistemi", "difficulty": 1},
            {"day": 4, "week": 1, "topic": "Döngüler (for, while)",
             "category": "python-basics", "level": "beginner",
             "theme": "🏃 Koşu Sayacı ve Hedef", "difficulty": 2},
            {"day": 5, "week": 1, "topic": "Fonksiyonlar ve Parametreler",
             "category": "python-basics", "level": "beginner",
             "theme": "🍳 Tarif Dönüştürücü", "difficulty": 2},
            {"day": 6, "week": 1, "topic": "Scope ve Variable Lifetime",
             "category": "python-basics", "level": "beginner",
             "theme": "🎭 Tiyatro Sahne Yönetimi", "difficulty": 2},
            {"day": 7, "week": 1, "topic": "Haftalık Özet ve Pratik",
             "category": "python-basics", "level": "beginner",
             "theme": "🎲 Zar Atma Simülasyonu", "difficulty": 2},

            # ═══════════════════════════════════════════════════════
            # HAFTA 2: Veri Yapıları (beginner)
            # ══════════════════════════════════════════════════════
            {"day": 8, "week": 2, "topic": "Listeler ve Liste Metodları",
             "category": "list-dict", "level": "beginner",
             "theme": "🎵 Playlist Yöneticisi", "difficulty": 2},
            {"day": 9, "week": 2, "topic": "Tuple ve Set",
             "category": "list-dict", "level": "beginner",
             "theme": "🎴 Poker Eli Analizi", "difficulty": 2},
            {"day": 10, "week": 2, "topic": "Sözlükler (Dictionaries)",
             "category": "list-dict", "level": "beginner",
             "theme": "📞 Telefon Rehberi", "difficulty": 2},
            {"day": 11, "week": 2, "topic": "İç İçe Veri Yapıları",
             "category": "list-dict", "level": "beginner",
             "theme": "🏨 Otel Rezervasyon Sistemi", "difficulty": 3},
            {"day": 12, "week": 2, "topic": "List Comprehension",
             "category": "list-dict", "level": "beginner",
             "theme": "🎨 Piksel Renk Filtresi", "difficulty": 3},
            {"day": 13, "week": 2, "topic": "String Manipülasyonu",
             "category": "strings", "level": "beginner",
             "theme": "🔐 Sezar Şifresi Kırıcı", "difficulty": 3},
            {"day": 14, "week": 2, "topic": "Haftalık Proje",
             "category": "list-dict", "level": "beginner",
             "theme": "🛒 Akıllı Alışveriş Sepeti", "difficulty": 3},

            # ═══════════════════════════════════════════════════════
            # HAFTA 3: İleri Fonksiyonlar (beginner → intermediate)
            # ═══════════════════════════════════════════════════════
            {"day": 15, "week": 3, "topic": "İleri Fonksiyon Kavramları",
             "category": "python-basics", "level": "beginner",
             "theme": "🎯 Hedef Vurma Oyunu", "difficulty": 2},
            {"day": 16, "week": 3, "topic": "Lambda Fonksiyonları",
             "category": "python-basics", "level": "beginner",
             "theme": "🧮 Hesap Makinesi Fabrikası", "difficulty": 2},
            {"day": 17, "week": 3, "topic": "Higher-Order Functions (map, filter, reduce)",
             "category": "python-basics", "level": "intermediate",
             "theme": "🏭 Veri İşleme Hattı", "difficulty": 3},
            {"day": 18, "week": 3, "topic": "Decorators (Giriş)",
             "category": "python-basics", "level": "intermediate",
             "theme": "️ Performans Ölçer", "difficulty": 3},
            {"day": 19, "week": 3, "topic": "Generators ve Iterators",
             "category": "python-basics", "level": "intermediate",
             "theme": "♾️ Sonsuz Fibonacci Akışı", "difficulty": 3},
            {"day": 20, "week": 3, "topic": "Modüller ve Paketler",
             "category": "python-basics", "level": "beginner",
             "theme": "📦 Paket Yönetim Sistemi", "difficulty": 2},
            {"day": 21, "week": 3, "topic": "Haftalık Proje",
             "category": "python-basics", "level": "intermediate",
             "theme": "🎰 Slot Makinesi", "difficulty": 3},

            # ═══════════════════════════════════════════════════════
            # HAFTA 4: Hata Yönetimi ve Dosya İşlemleri (beginner → intermediate)
            # ══════════════════════════════════════════════════════
            {"day": 22, "week": 4, "topic": "Exception Handling (try/except)",
             "category": "python-basics", "level": "beginner",
             "theme": "🚨 Acil Durum Yöneticisi", "difficulty": 2},
            {"day": 23, "week": 4, "topic": "Custom Exceptions",
             "category": "python-basics", "level": "intermediate",
             "theme": "🏦 Banka Hata Sistemi", "difficulty": 3},
            {"day": 24, "week": 4, "topic": "Dosya Okuma/Yazma",
             "category": "python-basics", "level": "beginner",
             "theme": "📔 Günlük Uygulaması", "difficulty": 2},
            {"day": 25, "week": 4, "topic": "JSON ve CSV İşlemleri",
             "category": "python-basics", "level": "intermediate",
             "theme": "📊 Veri Dönüştürücü", "difficulty": 3},
            {"day": 26, "week": 4, "topic": "Context Managers (with statement)",
             "category": "python-basics", "level": "intermediate",
             "theme": "🔒 Kasa Yöneticisi", "difficulty": 3},
            {"day": 27, "week": 4, "topic": "Logging ve Debugging",
             "category": "python-basics", "level": "intermediate",
             "theme": "🕵️ Dedektif Log Sistemi", "difficulty": 2},
            {"day": 28, "week": 4, "topic": "Haftalık Proje",
             "category": "python-basics", "level": "intermediate",
             "theme": "📝 Not Defteri Uygulaması", "difficulty": 3},

            # ═══════════════════════════════════════════════════════
            # HAFTA 5: OOP — Nesne Yönelimli Programlama (intermediate)
            # ═══════════════════════════════════════════════════════
            {"day": 29, "week": 5, "topic": "Classes ve Objects",
             "category": "algorithms", "level": "intermediate",
             "theme": "🐾 Sanal Evcil Hayvan", "difficulty": 2},
            {"day": 30, "week": 5, "topic": "__init__ ve Self",
             "category": "algorithms", "level": "intermediate",
             "theme": " Araba Garajı", "difficulty": 2},
            {"day": 31, "week": 5, "topic": "Inheritance (Kalıtım)",
             "category": "algorithms", "level": "intermediate",
             "theme": "🦁 Hayvanat Bahçesi", "difficulty": 3},
            {"day": 32, "week": 5, "topic": "Polymorphism",
             "category": "algorithms", "level": "intermediate",
             "theme": "🎵 Müzik Çalar", "difficulty": 3},
            {"day": 33, "week": 5, "topic": "Encapsulation",
             "category": "algorithms", "level": "intermediate",
             "theme": "🏧 ATM Makinesi", "difficulty": 3},
            {"day": 34, "week": 5, "topic": "Magic Methods (__str__, __repr__)",
             "category": "algorithms", "level": "intermediate",
             "theme": "🃏 Kart Oyunu", "difficulty": 3},
            {"day": 35, "week": 5, "topic": "Haftalık Proje: OOP Tasarımı",
             "category": "algorithms", "level": "intermediate",
             "theme": "🏰 RPG Savaş Sistemi", "difficulty": 4},

            # ═══════════════════════════════════════════════════════
            # HAFTA 6: Algoritmalar ve Veri Yapıları (intermediate)
            # ═══════════════════════════════════════════════════════
            {"day": 36, "week": 6, "topic": "Stack ve Queue Implementasyonu",
             "category": "algorithms", "level": "intermediate",
             "theme": "🥞 Pancake Kulesi", "difficulty": 3},
            {"day": 37, "week": 6, "topic": "Linked Lists",
             "category": "algorithms", "level": "intermediate",
             "theme": "🚂 Tren Vagonları", "difficulty": 3},
            {"day": 38, "week": 6, "topic": "Trees ve Binary Search Trees",
             "category": "algorithms", "level": "intermediate",
             "theme": "🌳 Aile Ağacı", "difficulty": 4},
            {"day": 39, "week": 6, "topic": "Sorting Algoritmaları",
             "category": "algorithms", "level": "intermediate",
             "theme": " Kart Sıralama Turnuvası", "difficulty": 3},
            {"day": 40, "week": 6, "topic": "Searching Algoritmaları",
             "category": "algorithms", "level": "intermediate",
             "theme": "🗺️ Hazine Avı", "difficulty": 3},
            {"day": 41, "week": 6, "topic": "Time ve Space Complexity",
             "category": "algorithms", "level": "intermediate",
             "theme": "⏳ Zaman Yarışı", "difficulty": 3},
            {"day": 42, "week": 6, "topic": "Haftalık Proje",
             "category": "algorithms", "level": "intermediate",
             "theme": " Tetris Mantığı", "difficulty": 4},

            # ═══════════════════════════════════════════════════════
            # HAFTA 7: İleri Python Konuları (intermediate)
            # ═══════════════════════════════════════════════════════
            {"day": 43, "week": 7, "topic": "Functional Programming Paradigması",
             "category": "algorithms", "level": "intermediate",
             "theme": "🧬 DNA Eşleştirme", "difficulty": 3},
            {"day": 44, "week": 7, "topic": "Closures ve Decorators (İleri)",
             "category": "algorithms", "level": "intermediate",
             "theme": " Şifre Üreteci", "difficulty": 4},
            {"day": 45, "week": 7, "topic": "Type Hinting ve MyPy",
             "category": "algorithms", "level": "intermediate",
             "theme": "📋 Tip Denetçisi", "difficulty": 2},
            {"day": 46, "week": 7, "topic": "Unit Testing (pytest)",
             "category": "algorithms", "level": "intermediate",
             "theme": "🧪 Laboratuvar Testleri", "difficulty": 3},
            {"day": 47, "week": 7, "topic": "Test-Driven Development",
             "category": "algorithms", "level": "intermediate",
             "theme": "🏗️ Bina İnşa Simülasyonu", "difficulty": 4},
            {"day": 48, "week": 7, "topic": "Code Review Best Practices",
             "category": "algorithms", "level": "intermediate",
             "theme": "👨‍🏫 Kod Mentor", "difficulty": 3},
            {"day": 49, "week": 7, "topic": "Haftalık Proje",
             "category": "algorithms", "level": "intermediate",
             "theme": "🎲 Sudoku Çözücü", "difficulty": 4},

            # ═══════════════════════════════════════════════════════
            # HAFTA 8: Veri Analizi ve Pandas (intermediate)
            # ═══════════════════════════════════════════════════════
            {"day": 50, "week": 8, "topic": "NumPy Temelleri",
             "category": "pandas", "level": "intermediate",
             "theme": "📐 Geometri Hesaplayıcı", "difficulty": 3},
            {"day": 51, "week": 8, "topic": "Pandas Series ve DataFrame",
             "category": "pandas", "level": "intermediate",
             "theme": "📈 Borsa Takibi", "difficulty": 3},
            {"day": 52, "week": 8, "topic": "Veri Temizleme ve Dönüştürme",
             "category": "pandas", "level": "intermediate",
             "theme": " Kirli Veri Temizleyici", "difficulty": 3},
            {"day": 53, "week": 8, "topic": "Groupby ve Aggregation",
             "category": "pandas", "level": "intermediate",
             "theme": "🏆 Spor Ligi İstatistikleri", "difficulty": 3},
            {"day": 54, "week": 8, "topic": "Merge, Join ve Concatenate",
             "category": "pandas", "level": "intermediate",
             "theme": "🤝 Veri Birleştirme", "difficulty": 4},
            {"day": 55, "week": 8, "topic": "Time Series Analysis",
             "category": "pandas", "level": "intermediate",
             "theme": "🌡️ Hava Durumu Analizi", "difficulty": 4},
            {"day": 56, "week": 8, "topic": "Haftalık Proje",
             "category": "pandas", "level": "intermediate",
             "theme": "📊 E-Ticaret Raporu", "difficulty": 4},

            # ═══════════════════════════════════════════════════════
            # HAFTA 9: Web Scraping ve API'ler (intermediate)
            # ═══════════════════════════════════════════════════════
            {"day": 57, "week": 9, "topic": "HTTP ve REST API Temelleri",
             "category": "algorithms", "level": "intermediate",
             "theme": "🌐 API Keşif Rehberi", "difficulty": 3},
            {"day": 58, "week": 9, "topic": "Requests Kütüphanesi",
             "category": "algorithms", "level": "intermediate",
             "theme": " Hava Durumu Servisi", "difficulty": 3},
            {"day": 59, "week": 9, "topic": "BeautifulSoup ile Web Scraping",
             "category": "algorithms", "level": "intermediate",
             "theme": "🕷️ Haber Toplayıcı", "difficulty": 4},
            {"day": 60, "week": 9, "topic": "API Authentication",
             "category": "algorithms", "level": "intermediate",
             "theme": "🔑 Token Yöneticisi", "difficulty": 3},
            {"day": 61, "week": 9, "topic": "Rate Limiting ve Error Handling",
             "category": "algorithms", "level": "intermediate",
             "theme": "🚦 Trafik Kontrolü", "difficulty": 4},
            {"day": 62, "week": 9, "topic": "Veri İşleme ve Analiz",
             "category": "algorithms", "level": "intermediate",
             "theme": "🛡️ Dayanıklı İstemci", "difficulty": 3},
            {"day": 63, "week": 9, "topic": "Haftalık Proje",
             "category": "algorithms", "level": "intermediate",
             "theme": "📰 Haber Aggregator", "difficulty": 4},

            # ═══════════════════════════════════════════════════════
            # HAFTA 10: Veritabanı ve ORM (intermediate)
            # ══════════════════════════════════════════════════════
            {"day": 64, "week": 10, "topic": "SQL Temelleri",
             "category": "algorithms", "level": "intermediate",
             "theme": "🗄️ Kütüphane Kayıt Sistemi", "difficulty": 3},
            {"day": 65, "week": 10, "topic": "SQLite ve Python",
             "category": "algorithms", "level": "intermediate",
             "theme": "📱 Mobil Uygulama Veritabanı", "difficulty": 3},
            {"day": 66, "week": 10, "topic": "SQLAlchemy ORM",
             "category": "algorithms", "level": "intermediate",
             "theme": " Mağaza Yönetim Sistemi", "difficulty": 4},
            {"day": 67, "week": 10, "topic": "CRUD Operasyonları",
             "category": "algorithms", "level": "intermediate",
             "theme": "👥 Kullanıcı Yönetim Paneli", "difficulty": 3},
            {"day": 68, "week": 10, "topic": "Relationships ve Joins",
             "category": "algorithms", "level": "intermediate",
             "theme": " Öğrenci-Ders İlişkisi", "difficulty": 4},
            {"day": 69, "week": 10, "topic": "Migration ve Schema Management",
             "category": "algorithms", "level": "intermediate",
             "theme": "🔄 Veritabanı Versiyonlama", "difficulty": 3},
            {"day": 70, "week": 10, "topic": "Haftalık Proje",
             "category": "algorithms", "level": "intermediate",
             "theme": " Blog Platformu Backend", "difficulty": 4},

            # ═══════════════════════════════════════════════════════
            # HAFTA 11: Asenkron Programlama (intermediate+)
            # ═══════════════════════════════════════════════════════
            {"day": 71, "week": 11, "topic": "Concurrency vs Parallelism",
             "category": "algorithms", "level": "intermediate",
             "theme": "🏭 Fabrika Üretim Hattı", "difficulty": 3},
            {"day": 72, "week": 11, "topic": "Threading",
             "category": "algorithms", "level": "intermediate",
             "theme": " Çok Oyunculu Oyun Sunucusu", "difficulty": 3},
            {"day": 73, "week": 11, "topic": "Multiprocessing",
             "category": "algorithms", "level": "intermediate",
             "theme": "🖼️ Resim İşleme Pipeline'ı", "difficulty": 4},
            {"day": 74, "week": 11, "topic": "Async/Await Temelleri",
             "category": "algorithms", "level": "intermediate",
             "theme": " Web Socket Chat Uygulaması", "difficulty": 4},
            {"day": 75, "week": 11, "topic": "Asyncio ve Event Loop",
             "category": "algorithms", "level": "intermediate",
             "theme": "⚡ Yüksek Performanslı Crawler", "difficulty": 4},
            {"day": 76, "week": 11, "topic": "Async HTTP Requests",
             "category": "algorithms", "level": "intermediate",
             "theme": "📡 Gerçek Zamanlı Veri Toplama", "difficulty": 4},
            {"day": 77, "week": 11, "topic": "Haftalık Proje",
             "category": "algorithms", "level": "intermediate",
             "theme": "💬 Canlı Mesajlaşma Uygulaması", "difficulty": 5},

            # ═══════════════════════════════════════════════════════
            # HAFTA 12: Proje ve Deployment (intermediate+)
            # ═══════════════════════════════════════════════════════
            {"day": 78, "week": 12, "topic": "Proje Planlama ve Mimari",
             "category": "algorithms", "level": "intermediate",
             "theme": "📋 Proje Yönetim Aracı", "difficulty": 2},
            {"day": 79, "week": 12, "topic": "Code Organization ve Best Practices",
             "category": "algorithms", "level": "intermediate",
             "theme": "🧹 Kod Temizleme Asistanı", "difficulty": 3},
            {"day": 80, "week": 12, "topic": "Documentation (Sphinx)",
             "category": "algorithms", "level": "intermediate",
             "theme": "📖 Otomatik Dokümantasyon", "difficulty": 3},
            {"day": 81, "week": 12, "topic": "Packaging ve Distribution",
             "category": "algorithms", "level": "intermediate",
             "theme": "📦 Python Paket Yayınlama", "difficulty": 4},
            {"day": 82, "week": 12, "topic": "CI/CD Temelleri",
             "category": "algorithms", "level": "intermediate",
             "theme": "🔄 Otomatik Test Pipeline'ı", "difficulty": 4},
            {"day": 83, "week": 12, "topic": "Docker ve Containerization",
             "category": "algorithms", "level": "intermediate",
             "theme": "🐳 Container Yönetim Sistemi", "difficulty": 4},
            {"day": 84, "week": 12, "topic": "Final Proje",
             "category": "algorithms", "level": "intermediate",
             "theme": "🚀 Full-Stack Uygulama", "difficulty": 5},
        ]
    
    def _get_next_day(self) -> int:
        """Son üretilen gün + 1 döndür"""
        # Eğer QUESTIONS.py dosyası varsa, son id'yi oku
        questions_file = os.path.join(os.path.dirname(__file__), "..", "data", "QUESTIONS.py")
        if os.path.exists(questions_file):
            try:
                with open(questions_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                # id= satırlarını bul
                import re
                ids = re.findall(r'id=(\d+)', content)
                if ids:
                    return max(int(i) for i in ids) + 1
            except Exception:
                pass
        return 1
    
    def _build_prompt(self, day_info: Dict[str, Any]) -> str:
        """AI için prompt oluştur"""
        stars = "⭐" * day_info["difficulty"]
        
        return f"""
Sen uzman bir Python eğitmenisin. {day_info['day']}. gün için eğlenceli ve öğretici bir soru üret.

**Konu**: {day_info['topic']}
**Kategori**: {day_info['category']}
**Seviye**: {day_info['level']}
**Tema**: {day_info['theme']}
**Zorluk**: {stars}

**Gereksinimler**:
1. Gerçek dünya senaryosu kullan (oyun, günlük hayat, iş dünyası)
2. Starter code başlangıç seviyesinde olmalı (pass ile biten fonksiyon)
3. 2-3 test case ekle (basitten zora)
4. 3 ipucu ekle (adım adım çözüm)
5. Eğlenceli ve motive edici olsun

**Format (Python dict)**:
{{
    "id": {day_info['day']},
    "title": "Emoji ile Başlık",
    "category": "{day_info['category']}",
    "level": "{day_info['level']}",
    "description": "3-5 cümlelik açıklama + örnek kullanım",
    "starter_code": "def function_name(param1: type, param2: type) -> return_type:\\n    # Yorum satırı\\n    pass",
    "test_cases": [
        {{"input": {{"param1": value1, "param2": value2}}, "expected": [result1, result2]}},
        {{"input": {{"param1": value3, "param2": value4}}, "expected": [result3, result4]}}
    ],
    "hints": [
        "💡 İpucu 1: İlk adım...",
        "💡 İpucu 2: İkinci adım...",
        "💡 İpucu 3: Son adım..."
    ]
}}

**ÖNEMLİ KURALLAR**:
1. test_cases input'u dict ise parametre adları fonksiyon parametreleriyle eşleşmeli
2. test_cases expected'i LIST kullan (tuple değil): [value1, value2]
3. Fonksiyon parametreleri type hint ile tanımlanmalı
4. description'da örnek kullanım göster
5. hints "💡 İpucu N: ..." formatında olmalı
6. Sadece tek parametre alan fonksiyonlarda input dict DEĞİL direkt değer olmalı: {{"input": "merhaba", "expected": "MERHABA"}}

Sadece JSON formatında döndür, başka açıklama ekleme.
"""
    
    def generate_question(self, day: Optional[int] = None) -> Question:
        """AI ile tek soru üret"""
        try:
            if day is None:
                day = self._get_next_day()
            
            day_info = next((d for d in self.curriculum if d["day"] == day), None)
            if not day_info:
                raise ValueError(f"Gün {day} müfredatta bulunamadı")
            
            print(f"📝 Gün {day} için soru üretiliyor: {day_info['theme']}")
            
            prompt = self._build_prompt(day_info)
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            
            question_data = json.loads(response.text)
            
            question = Question(
                id=question_data["id"],
                title=question_data["title"],
                category=question_data["category"],
                level=question_data["level"],
                description=question_data["description"],
                starter_code=question_data["starter_code"],
                test_cases=question_data["test_cases"],
                hints=question_data["hints"],
            )
            
            print(f"✅ Gün {day} sorusu başarıyla üretildi: {question.title}")
            return question
            
        except Exception as e:
            print(f"❌ Soru üretim hatası: {e}")
            raise
    
    def generate_week(self, week: int) -> List[Question]:
        """Bir haftalık soru üret (7 gün)"""
        questions = []
        
        for day in range((week - 1) * 7 + 1, week * 7 + 1):
            try:
                question = self.generate_question(day)
                questions.append(question)
                print(f"  ✅ Gün {day} tamamlandı")
            except Exception as e:
                print(f"  ❌ Gün {day} başarısız: {e}")
        
        return questions
    
    def generate_full_curriculum(self) -> List[Question]:
        """Tüm 84 günlük müfredatı üret"""
        all_questions = []
        
        for week in range(1, 13):
            print(f"\n📅 Hafta {week} üretiliyor...")
            week_questions = self.generate_week(week)
            all_questions.extend(week_questions)
            print(f"✅ Hafta {week} tamamlandı ({len(week_questions)} soru)")
        
        return all_questions
    
    def _write_to_file(self, questions: List[Question], filepath: str):
        """Soruları Python dosyasına kaydet — mevcut backend formatıyla uyumlu"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# data/QUESTIONS.py\n")
            f.write("from dataclasses import dataclass, field\n")
            f.write("from typing import List, Dict, Any\n\n")
            f.write("@dataclass\n")
            f.write("class Question:\n")
            f.write("    id: int\n")
            f.write("    title: str\n")
            f.write("    category: str\n")
            f.write("    level: str\n")
            f.write("    description: str\n")
            f.write("    starter_code: str\n")
            f.write("    test_cases: List[Dict[str, Any]]\n")
            f.write("    hints: List[str] = field(default_factory=list)\n\n\n")
            f.write("QUESTIONS: List[Question] = [\n\n")
            
            for q in questions:
                # Emojis or descriptions can contain double quotes, so we should safely format them
                # Since we write them to python file, triple-quoted strings are great for description and starter_code.
                desc = q.description.replace('"""', '\\"\\"\\"')
                starter = q.starter_code.replace('"""', '\\"\\"\\"')
                
                f.write(f"    Question(\n")
                f.write(f"        id={q.id},\n")
                f.write(f"        title={repr(q.title)},\n")
                f.write(f"        category={repr(q.category)},\n")
                f.write(f"        level={repr(q.level)},\n")
                f.write(f"        description=\"\"\"{desc}\"\"\",\n")
                f.write(f"        starter_code=\"\"\"{starter}\"\"\",\n")
                
                # Format test cases and hints nicely on separate lines using repr
                test_cases_str = "[\n"
                for tc in q.test_cases:
                    test_cases_str += f"            {repr(tc)},\n"
                test_cases_str += "        ]"
                
                hints_str = "[\n"
                for hint in q.hints:
                    hints_str += f"            {repr(hint)},\n"
                hints_str += "        ]"
                
                f.write(f"        test_cases={test_cases_str},\n")
                f.write(f"        hints={hints_str},\n")
                f.write(f"    ),\n\n")
            
            f.write("]\n")
        print(f"✅ {len(questions)} soru {filepath} dosyasına kaydedildi")

    def save_to_python_file(self, questions: List[Question], filepath: str):
        """Mevcut sorularla yeni soruları birleştirip kaydeder"""
        existing_questions = []
        if os.path.exists(filepath):
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("questions_module", filepath)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                existing_questions = list(module.QUESTIONS)
            except Exception as e:
                print(f"⚠️ Mevcut sorular okunurken hata (yeni dosya oluşturuluyor olabilir): {e}")

        # Mevcut ID'leri al, duplicate ekleme
        existing_ids = {q.id for q in existing_questions}
        new_questions = [q for q in questions if q.id not in existing_ids]
    
        # Birleştir ve ID'ye göre sırala
        all_questions = sorted(existing_questions + new_questions, key=lambda q: q.id)

        # Dosyayı yaz
        self._write_to_file(all_questions, filepath)

    def generate_and_save(self, start_day: int = 1, end_day: int = 84):
        """Belirli aralıktaki günleri üret ve kaydet"""
        questions = []
        
        for day in range(start_day, end_day + 1):
            try:
                question = self.generate_question(day)
                questions.append(question)
                print(f"  ✅ Gün {day} tamamlandı")
            except Exception as e:
                print(f"  ❌ Gün {day} başarısız: {e}")
        
        if questions:
            filepath = os.path.join(os.path.dirname(__file__), "..", "data", "QUESTIONS.py")
            self.save_to_python_file(questions, filepath)
        
        return questions

    def generate_creative_question(self, question_id: int) -> Question:
        """AI ile yaratıcı ve yüksek etkileşimli (engagement) başlangıç/orta düzey Python sorusu üretir"""
        prompt = f"""
Sen uzman bir Python eğitmeni ve popüler bir yazılım eğitim platformunun içerik yöneticisisin.
Amacın, başlangıç ve orta seviyedeki (beginner/intermediate) Python öğrencileri için **yaratıcı, eğlenceli ve sosyal medyada etkileşim (engagement) yaratabilecek** bir kodlama sorusu hazırlamaktır.

Soru şu kriterlere sahip olmalıdır:
1. **İlgi Çekici Senaryo**: Kuru matematiksel veya soyut problemler yerine; sosyal medya analizi, oyun mekanikleri, günlük hayattaki eğlenceli durumlar, gizli mesajlar, emojiler veya popüler kültür öğeleri içeren bir senaryo kullan.
2. **Seviye**: Başlangıç ile Orta (beginner veya intermediate) seviyelerinde olmalı, Python temelleri (koşul ifadeleri, döngüler, string manipülasyonu, liste/sözlük işlemleri) üzerinde durmalıdır.
3. **Zorluk**: Çok zor olmamalı, ancak çözmesi keyifli ve tatmin edici olmalıdır.
4. **Format (Python dict)**:
{{
    "id": {question_id},
    "title": "Emoji ile Başlık (örn: 🎮 Karakter İsim Filtresi veya 🕵️ Gizli Ajan Şifresi)",
    "category": "python-basics" veya "strings" veya "list-dict",
    "level": "beginner" veya "intermediate",
    "description": "Senaryoyu ve ne istendiğini açıklayan 3-5 cümlelik Türkçe metin. Örnek girdi ve çıktıları (örnek kullanım) içermelidir.",
    "starter_code": "def fonksiyon_adi(param1: tip, param2: tip) -> donus_tipi:\\n    # Açıklayıcı yorum satırı\\n    pass",
    "test_cases": [
        {{"input": input_deger_1, "expected": beklenen_deger_1}},
        {{"input": input_deger_2, "expected": beklenen_deger_2}},
        ...
    ],
    "hints": [
        "💡 İpucu 1: İlk adım...",
        "💡 İpucu 2: İkinci adım...",
        "💡 İpucu 3: Üçüncü adım..."
    ]
}}

**ÖNEMLİ KURALLAR**:
- Sadece geçerli bir JSON döndür, markdown kod blokları (```json) kullanma, başka hiçbir açıklama metni ekleme.
- `test_cases` listesindeki `input` alanları tek parametre alan fonksiyonlarda direkt değer olmalıdır. Birden fazla parametre varsa dict formatında olmalıdır.
- `test_cases` expected alanında asla tuple kullanma, list kullan.
.
"""
        response = self.model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        
        question_data = json.loads(response.text)
        
        return Question(
            id=question_id,
            title=question_data["title"],
            category=question_data["category"],
            level=question_data["level"],
            description=question_data["description"],
            starter_code=question_data["starter_code"],
            test_cases=question_data["test_cases"],
            hints=question_data["hints"],
        )

    def upload_to_supabase(self, questions: List[Question]) -> bool:
        """Soruları Supabase 'interwiews' tablosuna upsert eder"""
        import sys
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if backend_dir not in sys.path:
            sys.path.append(backend_dir)
            
        try:
            from backend.supabase_client import get_supabase
            supabase = get_supabase()
        except Exception as e:
            print(f"❌ Supabase istemcisi yüklenemedi: {e}")
            return False

        payload = []
        for q in questions:
            payload.append({
                "id": q.id,
                "title": q.title,
                "category": q.category,
                "level": q.level,
                "description": q.description,
                "starter_code": q.starter_code,
                "test_cases": q.test_cases,
                "hints": q.hints
            })

        try:
            result = supabase.table("interwiews").upsert(payload).execute()
            print(f"✅ Supabase 'interwiews' tablosuna {len(payload)} yeni soru yüklendi/güncellendi.")
            return True
        except Exception as e:
            print(f"❌ Supabase yükleme hatası: {e}")
            return False

    def send_email_notification(self, questions: List[Question], to_email: str) -> bool:
        """Üretilen yeni sorular için Resend ile e-posta bildirimi gönderir"""
        import resend
        api_key = os.getenv("RESEND_API_KEY")
        if not api_key:
            print("⚠️ RESEND_API_KEY bulunamadı, e-posta gönderilemedi.")
            return False
        
        resend.api_key = api_key
        
        # Gönderici adresi
        from_email = os.getenv("RESEND_FROM_EMAIL", "pythonmulakat.com")
        if "@" not in from_email:
            from_email = f"noreply@{from_email}"
            
        subject = f"🚀 Yeni Python Soruları Üretildi! ({len(questions)} Yeni Soru)"
        
        # HTML İçeriği
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 8px; }}
                .header {{ background-color: #4F46E5; color: white; padding: 15px; text-align: center; border-radius: 8px 8px 0 0; }}
                .question-card {{ border-left: 4px solid #4F46E5; background-color: #F9FAFB; padding: 15px; margin: 15px 0; border-radius: 0 8px 8px 0; }}
                .title {{ font-size: 18px; font-weight: bold; margin-bottom: 5px; color: #111827; }}
                .meta {{ font-size: 12px; color: #6B7280; margin-bottom: 10px; }}
                .description {{ font-size: 14px; margin-bottom: 10px; white-space: pre-line; }}
                .code {{ background-color: #F1F5F9; font-family: monospace; padding: 10px; border-radius: 4px; overflow-x: auto; font-size: 13px; }}
                .footer {{ font-size: 12px; color: #9CA3AF; text-align: center; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>PythonMulakat.com</h2>
                    <p>Yeni Yaratıcı Sorular Yayında!</p>
                </div>
                <p>Merhaba,</p>
                <p>Eğitim platformumuz için başlangıç seviyesinde, etkileşimi yüksek ve yaratıcı <strong>{len(questions)} yeni soru</strong> başarıyla üretilip <code>QUESTIONS.py</code> dosyasına eklendi ve Supabase veritabanına aktarıldı.</p>
        """
        
        for q in questions:
            html_content += f"""
                <div class="question-card">
                    <div class="title">#{q.id} - {q.title}</div>
                    <div class="meta">Kategori: <strong>{q.category}</strong> | Seviye: <strong>{q.level}</strong></div>
                    <div class="description">{q.description}</div>
                    <div class="code"><pre>{q.starter_code}</pre></div>
                </div>
            """
            
        html_content += """
                <p>Sorular şu anda sisteme entegre edildi ve çözülmeye hazır!</p>
                <div class="footer">
                    <p>Bu e-posta otomatik olarak gönderilmiştir. PythonMulakat © 2026</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            r = resend.Emails.send({
                "from": from_email,
                "to": to_email,
                "subject": subject,
                "html": html_content
            })
            print(f"📧 E-posta başarıyla gönderildi! Alıcı: {to_email}, ID: {r.get('id', 'N/A')}")
            return True
        except Exception as e:
            print(f"❌ E-posta gönderilirken hata oluştu: {e}")
            return False

# ═══════════════════════════════════════════════════════════════
# Manuel çalıştırma
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Soru Üretici")
    parser.add_argument("--day", type=int, help="Tek bir gün üret (örn: --day 1)")
    parser.add_argument("--week", type=int, help="Bir hafta üret (örn: --week 1)")
    parser.add_argument("--range", type=str, help="Aralık üret (örn: --range 1-7)")
    parser.add_argument("--all", action="store_true", help="Tüm 84 günü üret")
    parser.add_argument("--generate-creative", action="store_true", help="Yaratıcı başlangıç/orta düzey soruları toplu üret")
    parser.add_argument("--count", type=int, default=5, help="Üretilecek yaratıcı soru sayısı (varsayılan: 5)")
    parser.add_argument("--email", type=str, help="Üretim sonrası e-posta ile bilgilendirilecek adres")
    
    args = parser.parse_args()
    generator = AIQuestionGenerator()
    
    filepath = os.path.join(os.path.dirname(__file__), "..", "data", "QUESTIONS.py")
    
    if args.generate_creative:
        start_id = generator._get_next_day()
        print(f"🚀 Toplu Yaratıcı Soru Üretimi Başlıyor. Başlangıç ID: {start_id}, Adet: {args.count}")
        
        new_questions = []
        for i in range(args.count):
            q_id = start_id + i
            try:
                question = generator.generate_creative_question(q_id)
                new_questions.append(question)
                print(f"  ✅ Soru {i+1}/{args.count} üretildi (ID: {q_id}): {question.title}")
            except Exception as e:
                print(f"  ❌ Soru {q_id} üretilemedi: {e}")
                
        if new_questions:
            # 1. Dosyaya kaydet
            generator.save_to_python_file(new_questions, filepath)
            
            # 2. Supabase'e yükle
            generator.upload_to_supabase(new_questions)
            
            # 3. Mail gönder
            if args.email:
                generator.send_email_notification(new_questions, args.email)
            else:
                print("ℹ️ E-posta adresi belirtilmediği için bildirim gönderilmedi.")
        else:
            print("❌ Hiçbir soru üretilemedi.")
            
    elif args.day:
        question = generator.generate_question(args.day)
        print(f"\n📝 Üretilen Soru:")
        print(f"  ID: {question.id}")
        print(f"  Başlık: {question.title}")
        print(f"  Kategori: {question.category}")
        print(f"  Seviye: {question.level}")
        
        # Tek soruyu kaydet/yükle
        generator.save_to_python_file([question], filepath)
        generator.upload_to_supabase([question])
        if args.email:
            generator.send_email_notification([question], args.email)
    
    elif args.week:
        questions = generator.generate_week(args.week)
        generator.save_to_python_file(questions, filepath)
        generator.upload_to_supabase(questions)
        if args.email:
            generator.send_email_notification(questions, args.email)
    
    elif args.range:
        start, end = map(int, args.range.split("-"))
        questions = generator.generate_and_save(start, end)
        generator.upload_to_supabase(questions)
        if args.email:
            generator.send_email_notification(questions, args.email)
    
    elif args.all:
        all_questions = generator.generate_full_curriculum()
        generator.save_to_python_file(all_questions, filepath)
        generator.upload_to_supabase(all_questions)
        if args.email:
            generator.send_email_notification(all_questions, args.email)
    
    else:
        print("Kullanım:")
        print("  python ai_question_generator.py --day 1")
        print("  python ai_question_generator.py --week 1")
        print("  python ai_question_generator.py --range 1-7")
        print("  python ai_question_generator.py --all")
        print("  python ai_question_generator.py --generate-creative --count 5 --email alici@gmail.com")