# data/CURRICULUM.py
# 84 günlük Python müfredat planı — AIQuestionGenerator'dan
# Her gün: day, week, topic, category, level, theme, difficulty

from typing import TypedDict

class CurriculumDay(TypedDict):
    day: int
    week: int
    topic: str
    category: str
    level: str
    theme: str
    difficulty: int

CURRICULUM: list[CurriculumDay] = [
    {'day': 1, 'week': 1, 'topic': 'Değişkenler ve Veri Tipleri', 'category': 'python-basics', 'level': 'beginner', 'theme': '🎮 RPG Karakter Oluşturucu', 'difficulty': 1, 'slug': 'degiskenler-ve-veri-tipleri'},
    {'day': 2, 'week': 1, 'topic': 'Operatörler ve İfadeler', 'category': 'python-basics', 'level': 'beginner', 'theme': '💰 Market Kasası Hesaplama', 'difficulty': 1, 'slug': 'operatorler-ve-ifadeler'},
    {'day': 3, 'week': 1, 'topic': 'Koşul İfadeleri (if/elif/else)', 'category': 'python-basics', 'level': 'beginner', 'theme': '🎢 Lunapark Bilet Sistemi', 'difficulty': 1, 'slug': 'kosul-ifadeleri-ifelifelse'},
    {'day': 4, 'week': 1, 'topic': 'Döngüler (for, while)', 'category': 'python-basics', 'level': 'beginner', 'theme': '🏃 Koşu Sayacı ve Hedef', 'difficulty': 2, 'slug': 'donguler-for-while'},
    {'day': 5, 'week': 1, 'topic': 'Fonksiyonlar ve Parametreler', 'category': 'python-basics', 'level': 'beginner', 'theme': '🍳 Tarif Dönüştürücü', 'difficulty': 2, 'slug': 'fonksiyonlar-ve-parametreler'},
    {'day': 6, 'week': 1, 'topic': 'Scope ve Variable Lifetime', 'category': 'python-basics', 'level': 'beginner', 'theme': '🎭 Tiyatro Sahne Yönetimi', 'difficulty': 2, 'slug': 'scope-ve-variable-lifetime'},
    {'day': 7, 'week': 1, 'topic': 'Haftalık Özet ve Pratik', 'category': 'python-basics', 'level': 'beginner', 'theme': '🎲 Zar Atma Simülasyonu', 'difficulty': 2, 'slug': 'haftalik-ozet-ve-pratik'},
    {'day': 8, 'week': 2, 'topic': 'Listeler ve Liste Metodları', 'category': 'list-dict', 'level': 'beginner', 'theme': '🎵 Playlist Yöneticisi', 'difficulty': 2, 'slug': 'listeler-ve-liste-metodlari'},
    {'day': 9, 'week': 2, 'topic': 'Tuple ve Set', 'category': 'list-dict', 'level': 'beginner', 'theme': '🎴 Poker Eli Analizi', 'difficulty': 2, 'slug': 'tuple-ve-set'},
    {'day': 10, 'week': 2, 'topic': 'Sözlükler (Dictionaries)', 'category': 'list-dict', 'level': 'beginner', 'theme': '📞 Telefon Rehberi', 'difficulty': 2, 'slug': 'sozlukler-dictionaries'},
    {'day': 11, 'week': 2, 'topic': 'İç İçe Veri Yapıları', 'category': 'list-dict', 'level': 'beginner', 'theme': '🏨 Otel Rezervasyon Sistemi', 'difficulty': 3, 'slug': 'ic-ice-veri-yapilari'},
    {'day': 12, 'week': 2, 'topic': 'List Comprehension', 'category': 'list-dict', 'level': 'beginner', 'theme': '🎨 Piksel Renk Filtresi', 'difficulty': 3, 'slug': 'list-comprehension'},
    {'day': 13, 'week': 2, 'topic': 'String Manipülasyonu', 'category': 'strings', 'level': 'beginner', 'theme': '🔐 Sezar Şifresi Kırıcı', 'difficulty': 3, 'slug': 'string-manipulasyonu'},
    {'day': 14, 'week': 2, 'topic': 'Haftalık Proje', 'category': 'list-dict', 'level': 'beginner', 'theme': '🛒 Akıllı Alışveriş Sepeti', 'difficulty': 3, 'slug': 'haftalik-proje'},
    {'day': 15, 'week': 3, 'topic': 'İleri Fonksiyon Kavramları', 'category': 'python-basics', 'level': 'beginner', 'theme': '🎯 Hedef Vurma Oyunu', 'difficulty': 2, 'slug': 'ileri-fonksiyon-kavramlari'},
    {'day': 16, 'week': 3, 'topic': 'Lambda Fonksiyonları', 'category': 'python-basics', 'level': 'beginner', 'theme': '🧮 Hesap Makinesi Fabrikası', 'difficulty': 2, 'slug': 'lambda-fonksiyonlari'},
    {'day': 17, 'week': 3, 'topic': 'Higher-Order Functions (map, filter, reduce)', 'category': 'python-basics', 'level': 'intermediate', 'theme': '🏭 Veri İşleme Hattı', 'difficulty': 3, 'slug': 'higher-order-functions-map-filter-reduce'},
    {'day': 18, 'week': 3, 'topic': 'Decorators (Giriş)', 'category': 'python-basics', 'level': 'intermediate', 'theme': '️ Performans Ölçer', 'difficulty': 3, 'slug': 'decorators-giris'},
    {'day': 19, 'week': 3, 'topic': 'Generators ve Iterators', 'category': 'python-basics', 'level': 'intermediate', 'theme': '♾️ Sonsuz Fibonacci Akışı', 'difficulty': 3, 'slug': 'generators-ve-iterators'},
    {'day': 20, 'week': 3, 'topic': 'Modüller ve Paketler', 'category': 'python-basics', 'level': 'beginner', 'theme': '📦 Paket Yönetim Sistemi', 'difficulty': 2, 'slug': 'moduller-ve-paketler'},
    {'day': 21, 'week': 3, 'topic': 'Haftalık Proje', 'category': 'python-basics', 'level': 'intermediate', 'theme': '🎰 Slot Makinesi', 'difficulty': 3, 'slug': 'haftalik-proje'},
    {'day': 22, 'week': 4, 'topic': 'Exception Handling (try/except)', 'category': 'python-basics', 'level': 'beginner', 'theme': '🚨 Acil Durum Yöneticisi', 'difficulty': 2, 'slug': 'exception-handling-tryexcept'},
    {'day': 23, 'week': 4, 'topic': 'Custom Exceptions', 'category': 'python-basics', 'level': 'intermediate', 'theme': '🏦 Banka Hata Sistemi', 'difficulty': 3, 'slug': 'custom-exceptions'},
    {'day': 24, 'week': 4, 'topic': 'Dosya Okuma/Yazma', 'category': 'python-basics', 'level': 'beginner', 'theme': '📔 Günlük Uygulaması', 'difficulty': 2, 'slug': 'dosya-okumayazma'},
    {'day': 25, 'week': 4, 'topic': 'JSON ve CSV İşlemleri', 'category': 'python-basics', 'level': 'intermediate', 'theme': '📊 Veri Dönüştürücü', 'difficulty': 3, 'slug': 'json-ve-csv-islemleri'},
    {'day': 26, 'week': 4, 'topic': 'Context Managers (with statement)', 'category': 'python-basics', 'level': 'intermediate', 'theme': '🔒 Kasa Yöneticisi', 'difficulty': 3, 'slug': 'context-managers-with-statement'},
    {'day': 27, 'week': 4, 'topic': 'Logging ve Debugging', 'category': 'python-basics', 'level': 'intermediate', 'theme': '🕵️ Dedektif Log Sistemi', 'difficulty': 2, 'slug': 'logging-ve-debugging'},
    {'day': 28, 'week': 4, 'topic': 'Haftalık Proje', 'category': 'python-basics', 'level': 'intermediate', 'theme': '📝 Not Defteri Uygulaması', 'difficulty': 3, 'slug': 'haftalik-proje'},
    {'day': 29, 'week': 5, 'topic': 'Classes ve Objects', 'category': 'algorithms', 'level': 'intermediate', 'theme': '🐾 Sanal Evcil Hayvan', 'difficulty': 2, 'slug': 'classes-ve-objects'},
    {'day': 30, 'week': 5, 'topic': '__init__ ve Self', 'category': 'algorithms', 'level': 'intermediate', 'theme': ' Araba Garajı', 'difficulty': 2, 'slug': 'init-ve-self'},
    {'day': 31, 'week': 5, 'topic': 'Inheritance (Kalıtım)', 'category': 'algorithms', 'level': 'intermediate', 'theme': '🦁 Hayvanat Bahçesi', 'difficulty': 3, 'slug': 'inheritance-kalitim'},
    {'day': 32, 'week': 5, 'topic': 'Polymorphism', 'category': 'algorithms', 'level': 'intermediate', 'theme': '🎵 Müzik Çalar', 'difficulty': 3, 'slug': 'polymorphism'},
    {'day': 33, 'week': 5, 'topic': 'Encapsulation', 'category': 'algorithms', 'level': 'intermediate', 'theme': '🏧 ATM Makinesi', 'difficulty': 3, 'slug': 'encapsulation'},
    {'day': 34, 'week': 5, 'topic': 'Magic Methods (__str__, __repr__)', 'category': 'algorithms', 'level': 'intermediate', 'theme': '🃏 Kart Oyunu', 'difficulty': 3, 'slug': 'magic-methods-str-repr'},
    {'day': 35, 'week': 5, 'topic': 'Haftalık Proje: OOP Tasarımı', 'category': 'algorithms', 'level': 'intermediate', 'theme': '🏰 RPG Savaş Sistemi', 'difficulty': 4, 'slug': 'haftalik-proje-oop-tasarimi'},
    {'day': 36, 'week': 6, 'topic': 'Stack ve Queue Implementasyonu', 'category': 'algorithms', 'level': 'intermediate', 'theme': '🥞 Pancake Kulesi', 'difficulty': 3, 'slug': 'stack-ve-queue-implementasyonu'},
    {'day': 37, 'week': 6, 'topic': 'Linked Lists', 'category': 'algorithms', 'level': 'intermediate', 'theme': '🚂 Tren Vagonları', 'difficulty': 3, 'slug': 'linked-lists'},
    {'day': 38, 'week': 6, 'topic': 'Trees ve Binary Search Trees', 'category': 'algorithms', 'level': 'intermediate', 'theme': '🌳 Aile Ağacı', 'difficulty': 4, 'slug': 'trees-ve-binary-search-trees'},
    {'day': 39, 'week': 6, 'topic': 'Sorting Algoritmaları', 'category': 'algorithms', 'level': 'intermediate', 'theme': ' Kart Sıralama Turnuvası', 'difficulty': 3, 'slug': 'sorting-algoritmalari'},
    {'day': 40, 'week': 6, 'topic': 'Searching Algoritmaları', 'category': 'algorithms', 'level': 'intermediate', 'theme': '🗺️ Hazine Avı', 'difficulty': 3, 'slug': 'searching-algoritmalari'},
    {'day': 41, 'week': 6, 'topic': 'Time ve Space Complexity', 'category': 'algorithms', 'level': 'intermediate', 'theme': '⏳ Zaman Yarışı', 'difficulty': 3, 'slug': 'time-ve-space-complexity'},
    {'day': 42, 'week': 6, 'topic': 'Haftalık Proje', 'category': 'algorithms', 'level': 'intermediate', 'theme': ' Tetris Mantığı', 'difficulty': 4, 'slug': 'haftalik-proje'},
    {'day': 43, 'week': 7, 'topic': 'Functional Programming Paradigması', 'category': 'algorithms', 'level': 'intermediate', 'theme': '🧬 DNA Eşleştirme', 'difficulty': 3, 'slug': 'functional-programming-paradigmasi'},
    {'day': 44, 'week': 7, 'topic': 'Closures ve Decorators (İleri)', 'category': 'algorithms', 'level': 'intermediate', 'theme': ' Şifre Üreteci', 'difficulty': 4, 'slug': 'closures-ve-decorators-ileri'},
    {'day': 45, 'week': 7, 'topic': 'Type Hinting ve MyPy', 'category': 'algorithms', 'level': 'intermediate', 'theme': '📋 Tip Denetçisi', 'difficulty': 2, 'slug': 'type-hinting-ve-mypy'},
    {'day': 46, 'week': 7, 'topic': 'Unit Testing (pytest)', 'category': 'algorithms', 'level': 'intermediate', 'theme': '🧪 Laboratuvar Testleri', 'difficulty': 3, 'slug': 'unit-testing-pytest'},
    {'day': 47, 'week': 7, 'topic': 'Test-Driven Development', 'category': 'algorithms', 'level': 'intermediate', 'theme': '🏗️ Bina İnşa Simülasyonu', 'difficulty': 4, 'slug': 'test-driven-development'},
    {'day': 48, 'week': 7, 'topic': 'Code Review Best Practices', 'category': 'algorithms', 'level': 'intermediate', 'theme': '👨\u200d🏫 Kod Mentor', 'difficulty': 3, 'slug': 'code-review-best-practices'},
    {'day': 49, 'week': 7, 'topic': 'Haftalık Proje', 'category': 'algorithms', 'level': 'intermediate', 'theme': '🎲 Sudoku Çözücü', 'difficulty': 4, 'slug': 'haftalik-proje'},
    {'day': 50, 'week': 8, 'topic': 'NumPy Temelleri', 'category': 'pandas', 'level': 'intermediate', 'theme': '📐 Geometri Hesaplayıcı', 'difficulty': 3, 'slug': 'numpy-temelleri'},
    {'day': 51, 'week': 8, 'topic': 'Pandas Series ve DataFrame', 'category': 'pandas', 'level': 'intermediate', 'theme': '📈 Borsa Takibi', 'difficulty': 3, 'slug': 'pandas-series-ve-dataframe'},
    {'day': 52, 'week': 8, 'topic': 'Veri Temizleme ve Dönüştürme', 'category': 'pandas', 'level': 'intermediate', 'theme': ' Kirli Veri Temizleyici', 'difficulty': 3, 'slug': 'veri-temizleme-ve-donusturme'},
    {'day': 53, 'week': 8, 'topic': 'Groupby ve Aggregation', 'category': 'pandas', 'level': 'intermediate', 'theme': '🏆 Spor Ligi İstatistikleri', 'difficulty': 3, 'slug': 'groupby-ve-aggregation'},
    {'day': 54, 'week': 8, 'topic': 'Merge, Join ve Concatenate', 'category': 'pandas', 'level': 'intermediate', 'theme': '🤝 Veri Birleştirme', 'difficulty': 4, 'slug': 'merge-join-ve-concatenate'},
    {'day': 55, 'week': 8, 'topic': 'Time Series Analysis', 'category': 'pandas', 'level': 'intermediate', 'theme': '🌡️ Hava Durumu Analizi', 'difficulty': 4, 'slug': 'time-series-analysis'},
    {'day': 56, 'week': 8, 'topic': 'Haftalık Proje', 'category': 'pandas', 'level': 'intermediate', 'theme': '📊 E-Ticaret Raporu', 'difficulty': 4, 'slug': 'haftalik-proje'},
    {'day': 57, 'week': 9, 'topic': 'HTTP ve REST API Temelleri', 'category': 'algorithms', 'level': 'intermediate', 'theme': '🌐 API Keşif Rehberi', 'difficulty': 3, 'slug': 'http-ve-rest-api-temelleri'},
    {'day': 58, 'week': 9, 'topic': 'Requests Kütüphanesi', 'category': 'algorithms', 'level': 'intermediate', 'theme': ' Hava Durumu Servisi', 'difficulty': 3, 'slug': 'requests-kutuphanesi'},
    {'day': 59, 'week': 9, 'topic': 'BeautifulSoup ile Web Scraping', 'category': 'algorithms', 'level': 'intermediate', 'theme': '🕷️ Haber Toplayıcı', 'difficulty': 4, 'slug': 'beautifulsoup-ile-web-scraping'},
    {'day': 60, 'week': 9, 'topic': 'API Authentication', 'category': 'algorithms', 'level': 'intermediate', 'theme': '🔑 Token Yöneticisi', 'difficulty': 3, 'slug': 'api-authentication'},
    {'day': 61, 'week': 9, 'topic': 'Rate Limiting ve Error Handling', 'category': 'algorithms', 'level': 'intermediate', 'theme': '🚦 Trafik Kontrolü', 'difficulty': 4, 'slug': 'rate-limiting-ve-error-handling'},
    {'day': 62, 'week': 9, 'topic': 'Veri İşleme ve Analiz', 'category': 'algorithms', 'level': 'intermediate', 'theme': '🛡️ Dayanıklı İstemci', 'difficulty': 3, 'slug': 'veri-isleme-ve-analiz'},
    {'day': 63, 'week': 9, 'topic': 'Haftalık Proje', 'category': 'algorithms', 'level': 'intermediate', 'theme': '📰 Haber Aggregator', 'difficulty': 4, 'slug': 'haftalik-proje'},
    {'day': 64, 'week': 10, 'topic': 'SQL Temelleri', 'category': 'algorithms', 'level': 'intermediate', 'theme': '🗄️ Kütüphane Kayıt Sistemi', 'difficulty': 3, 'slug': 'sql-temelleri'},
    {'day': 65, 'week': 10, 'topic': 'SQLite ve Python', 'category': 'algorithms', 'level': 'intermediate', 'theme': '📱 Mobil Uygulama Veritabanı', 'difficulty': 3, 'slug': 'sqlite-ve-python'},
    {'day': 66, 'week': 10, 'topic': 'SQLAlchemy ORM', 'category': 'algorithms', 'level': 'intermediate', 'theme': ' Mağaza Yönetim Sistemi', 'difficulty': 4, 'slug': 'sqlalchemy-orm'},
    {'day': 67, 'week': 10, 'topic': 'CRUD Operasyonları', 'category': 'algorithms', 'level': 'intermediate', 'theme': '👥 Kullanıcı Yönetim Paneli', 'difficulty': 3, 'slug': 'crud-operasyonlari'},
    {'day': 68, 'week': 10, 'topic': 'Relationships ve Joins', 'category': 'algorithms', 'level': 'intermediate', 'theme': ' Öğrenci-Ders İlişkisi', 'difficulty': 4, 'slug': 'relationships-ve-joins'},
    {'day': 69, 'week': 10, 'topic': 'Migration ve Schema Management', 'category': 'algorithms', 'level': 'intermediate', 'theme': '🔄 Veritabanı Versiyonlama', 'difficulty': 3, 'slug': 'migration-ve-schema-management'},
    {'day': 70, 'week': 10, 'topic': 'Haftalık Proje', 'category': 'algorithms', 'level': 'intermediate', 'theme': ' Blog Platformu Backend', 'difficulty': 4, 'slug': 'haftalik-proje'},
    {'day': 71, 'week': 11, 'topic': 'Concurrency vs Parallelism', 'category': 'algorithms', 'level': 'intermediate', 'theme': '🏭 Fabrika Üretim Hattı', 'difficulty': 3, 'slug': 'concurrency-vs-parallelism'},
    {'day': 72, 'week': 11, 'topic': 'Threading', 'category': 'algorithms', 'level': 'intermediate', 'theme': ' Çok Oyunculu Oyun Sunucusu', 'difficulty': 3, 'slug': 'threading'},
    {'day': 73, 'week': 11, 'topic': 'Multiprocessing', 'category': 'algorithms', 'level': 'intermediate', 'theme': "🖼️ Resim İşleme Pipeline'ı", 'difficulty': 4, 'slug': 'multiprocessing'},
    {'day': 74, 'week': 11, 'topic': 'Async/Await Temelleri', 'category': 'algorithms', 'level': 'intermediate', 'theme': ' Web Socket Chat Uygulaması', 'difficulty': 4, 'slug': 'asyncawait-temelleri'},
    {'day': 75, 'week': 11, 'topic': 'Asyncio ve Event Loop', 'category': 'algorithms', 'level': 'intermediate', 'theme': '⚡ Yüksek Performanslı Crawler', 'difficulty': 4, 'slug': 'asyncio-ve-event-loop'},
    {'day': 76, 'week': 11, 'topic': 'Async HTTP Requests', 'category': 'algorithms', 'level': 'intermediate', 'theme': '📡 Gerçek Zamanlı Veri Toplama', 'difficulty': 4, 'slug': 'async-http-requests'},
    {'day': 77, 'week': 11, 'topic': 'Haftalık Proje', 'category': 'algorithms', 'level': 'intermediate', 'theme': '💬 Canlı Mesajlaşma Uygulaması', 'difficulty': 5, 'slug': 'haftalik-proje'},
    {'day': 78, 'week': 12, 'topic': 'Proje Planlama ve Mimari', 'category': 'algorithms', 'level': 'intermediate', 'theme': '📋 Proje Yönetim Aracı', 'difficulty': 2, 'slug': 'proje-planlama-ve-mimari'},
    {'day': 79, 'week': 12, 'topic': 'Code Organization ve Best Practices', 'category': 'algorithms', 'level': 'intermediate', 'theme': '🧹 Kod Temizleme Asistanı', 'difficulty': 3, 'slug': 'code-organization-ve-best-practices'},
    {'day': 80, 'week': 12, 'topic': 'Documentation (Sphinx)', 'category': 'algorithms', 'level': 'intermediate', 'theme': '📖 Otomatik Dokümantasyon', 'difficulty': 3, 'slug': 'documentation-sphinx'},
    {'day': 81, 'week': 12, 'topic': 'Packaging ve Distribution', 'category': 'algorithms', 'level': 'intermediate', 'theme': '📦 Python Paket Yayınlama', 'difficulty': 4, 'slug': 'packaging-ve-distribution'},
    {'day': 82, 'week': 12, 'topic': 'CI/CD Temelleri', 'category': 'algorithms', 'level': 'intermediate', 'theme': "🔄 Otomatik Test Pipeline'ı", 'difficulty': 4, 'slug': 'cicd-temelleri'},
    {'day': 83, 'week': 12, 'topic': 'Docker ve Containerization', 'category': 'algorithms', 'level': 'intermediate', 'theme': '🐳 Container Yönetim Sistemi', 'difficulty': 4, 'slug': 'docker-ve-containerization'},
    {'day': 84, 'week': 12, 'topic': 'Final Proje', 'category': 'algorithms', 'level': 'intermediate', 'theme': '🚀 Full-Stack Uygulama', 'difficulty': 5, 'slug': 'final-proje'},
]

# Haftalık gruplama
WEEKS: dict[int, list[CurriculumDay]] = {}
for _d in CURRICULUM:
    WEEKS.setdefault(_d['week'], []).append(_d)

# Hafta bazlı meta
WEEK_META = {
    1: {'title': 'Python Temelleri', 'icon': '🐍', 'color': '#4ade80'},
    2: {'title': 'Veri Yapıları', 'icon': '📋', 'color': '#60a5fa'},
    3: {'title': 'Fonksiyonlar ve Modüller', 'icon': '⚙️', 'color': '#a78bfa'},
    4: {'title': 'OOP Temelleri', 'icon': '🏗️', 'color': '#f472b6'},
    5: {'title': 'İleri OOP ve Patterns', 'icon': '🎭', 'color': '#fb923c'},
    6: {'title': 'Dosya I/O ve Veri', 'icon': '📁', 'color': '#fbbf24'},
    7: {'title': 'Hata Yönetimi', 'icon': '⚠️', 'color': '#f87171'},
    8: {'title': 'Standart Kütüphane', 'icon': '📚', 'color': '#34d399'},
    9: {'title': 'Veri Analizi (Pandas)', 'icon': '🐼', 'color': '#22d3ee'},
    10: {'title': 'Web Scraping ve API', 'icon': '🌐', 'color': '#818cf8'},
    11: {'title': 'Async ve Concurrency', 'icon': '⚡', 'color': '#c084fc'},
    12: {'title': 'Final Proje ve DevOps', 'icon': '🚀', 'color': '#f43f5e'},
}