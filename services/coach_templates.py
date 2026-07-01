# services/coach_templates.py
# Rule-based email templates — AI YOK.
# Her kural için hazır HTML/metin şablonu.

from typing import Dict, Any, List, Optional

BRAND = {
    "site_name": "PythonMulakat",
    "site_url": "https://www.pythonmulakat.com",
    "from_email": "mkemal@pythonmulakat.com",
    "logo_url": "https://www.pythonmulakat.com/logo.png",
    "accent": "#f59e0b",  # amber-500
}

# ── Yardımcılar ─────────────────────────────────────────
def _cta(url: str, label: str) -> str:
    return f'''
    <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin: 24px 0;">
      <tr>
        <td style="background: {BRAND['accent']}; border-radius: 8px;">
          <a href="{url}" target="_blank"
             style="display: inline-block; padding: 12px 28px;
                    color: #050816; font-weight: 700; text-decoration: none;
                    font-size: 14px; font-family: -apple-system, sans-serif;">
            {label}
          </a>
        </td>
      </tr>
    </table>
    '''

def _shell(title: str, body_html: str, preheader: str = "") -> str:
    """Tüm emaillerin ortak HTML kabuğu."""
    return f'''<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; background: #050816; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
  <span style="display: none; max-height: 0; overflow: hidden;">{preheader}</span>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background: #050816;">
    <tr>
      <td align="center" style="padding: 32px 16px;">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"
               style="background: #0a0e1a; border: 1px solid rgba(255,255,255,0.08);
                      border-radius: 16px; max-width: 600px;">
          <tr>
            <td style="padding: 32px 40px; border-bottom: 1px solid rgba(255,255,255,0.06);">
              <div style="font-size: 20px; font-weight: 800; color: white;">
                🐍 {BRAND['site_name']}
              </div>
              <div style="font-size: 12px; color: rgba(255,255,255,0.4); margin-top: 4px;">
                Kişisel Python Mülakat Koçun
              </div>
            </td>
          </tr>
          <tr>
            <td style="padding: 32px 40px; color: rgba(255,255,255,0.85); font-size: 15px; line-height: 1.6;">
              {body_html}
            </td>
          </tr>
          <tr>
            <td style="padding: 20px 40px; border-top: 1px solid rgba(255,255,255,0.06);
                       font-size: 11px; color: rgba(255,255,255,0.3); text-align: center;">
              Bu maili almak istemiyorsan
              <a href="{BRAND['site_url']}/profile" style="color: rgba(255,255,255,0.5);">ayarlardan bildirim tercihlerini değiştirebilirsin</a>.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>'''


def _question_card(q: Dict[str, Any]) -> str:
    cat = q.get("category", "")
    lvl = (q.get("level") or "beginner").title()
    cat_label = cat.replace("-", " ").title()
    return f'''
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
           style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
                  border-radius: 12px; margin: 12px 0;">
      <tr>
        <td style="padding: 16px 20px;">
          <div style="font-size: 14px; font-weight: 700; color: white;">
            {q.get("title", "Soru")}
          </div>
          <div style="font-size: 11px; color: rgba(255,255,255,0.4); margin-top: 6px;">
            <span style="background: rgba(245,158,11,0.15); color: {BRAND['accent']};
                         padding: 2px 8px; border-radius: 4px; font-weight: 600;">
              {lvl}
            </span>
            <span style="margin-left: 8px;">{cat_label}</span>
          </div>
        </td>
      </tr>
    </table>
    '''


def _tutorial_card(t: Dict[str, Any]) -> str:
    diff = (t.get("difficulty") or "beginner").title()
    mins = t.get("reading_time_minutes") or 5
    return f'''
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
           style="background: rgba(99,102,241,0.05); border: 1px solid rgba(99,102,241,0.25);
                  border-radius: 12px; margin: 16px 0;">
      <tr>
        <td style="padding: 16px 20px;">
          <div style="font-size: 14px; font-weight: 700; color: white;">
            📘 {t.get("title", "Rehber")}
          </div>
          <div style="font-size: 12px; color: rgba(255,255,255,0.6); margin-top: 6px;">
            {t.get("description", "")[:140]}
          </div>
          <div style="font-size: 10px; color: rgba(255,255,255,0.3); margin-top: 8px;">
            {diff} · ⏱ {mins} dakika okuma
          </div>
        </td>
      </tr>
    </table>
    '''


# ─────────────────────────────────────────────────────────
# KURAL 1: İlk çözüm kutlaması
# ─────────────────────────────────────────────────────────
def first_solve(user: Dict, question: Dict) -> Dict[str, Any]:
    url = f"{BRAND['site_url']}/interviews/{question.get('category')}/{question.get('slug') or question.get('id')}"
    body = f'''
    <p style="margin: 0 0 16px 0;">Selam <strong>{user.get("username","mülakatçı")}</strong>,</p>
    <p style="margin: 0 0 16px 0;">
      İlk sorunu başarıyla çözdün — <strong>{question.get("title","bu soru")}</strong>. 🎉
      Bu sadece bir başlangıç; doğru pratik temposuyla devam edersen 50+ soru seviyesine rahat çıkarsın.
    </p>
    {_question_card(question)}
    <p style="margin: 16px 0;">Bir sonraki soruna geçmeye ne dersin?</p>
    {_cta(url, "Bir Sonraki Soruya Geç →")}
    '''
    return {
        "subject": f"🎉 Tebrikler! İlk sorunu çözdün — {question.get('title','')}",
        "html": _shell("İlk başarın!", body, "İlk sorunu çözdün, devam et!"),
    }


# ─────────────────────────────────────────────────────────
# KURAL 2: Milestone (10 / 25 / 50 / 100 çözüm)
# ─────────────────────────────────────────────────────────
def milestone(user: Dict, total_solved: int, milestone_count: int) -> Dict[str, Any]:
    body = f'''
    <p style="margin: 0 0 16px 0;">Selam <strong>{user.get("username","mülakatçı")}</strong>,</p>
    <p style="margin: 0 0 16px 0;">
      Bugün Python mülakat pratiğinde bir milestone'a ulaştın:
    </p>
    <div style="text-align: center; padding: 24px; background: rgba(245,158,11,0.08); border: 1px solid rgba(245,158,11,0.3); border-radius: 12px; margin: 16px 0;">
      <div style="font-size: 48px; font-weight: 800; color: {BRAND['accent']}; line-height: 1;">{total_solved}</div>
      <div style="font-size: 13px; color: rgba(255,255,255,0.7); margin-top: 8px;">
        Soru başarıyla çözüldü
      </div>
    </div>
    <p style="margin: 16px 0;">
      Bu tempoyla devam edersen <strong>{milestone_count}</strong> soruya ulaşman tahminen
      birkaç hafta sürer. Hangi kategorilerde daha çok pratik yapmak istersin?
    </p>
    {_cta(f"{BRAND['site_url']}/interviews", "Sıradaki Problemi Seç →")}
    '''
    return {
        "subject": f"🏆 {total_solved} soru çözdün — yeni milestone!",
        "html": _shell(f"{total_solved} çözüm!", body, f"Milestone: {total_solved} soru çözüldü"),
    }


# ─────────────────────────────────────────────────────────
# KURAL 3: Streak (ardışık gün aktivitesi)
# ─────────────────────────────────────────────────────────
def streak(user: Dict, streak_days: int) -> Dict[str, Any]:
    body = f'''
    <p style="margin: 0 0 16px 0;">Selam <strong>{user.get("username","mülakatçı")}</strong>,</p>
    <p style="margin: 0 0 16px 0;">
      Harika bir streak yakaladın:
    </p>
    <div style="text-align: center; padding: 24px; background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.3); border-radius: 12px; margin: 16px 0;">
      <div style="font-size: 64px; line-height: 1;">🔥</div>
      <div style="font-size: 32px; font-weight: 800; color: white;">{streak_days} gün</div>
      <div style="font-size: 13px; color: rgba(255,255,255,0.6); margin-top: 4px;">Üst üste aktif gün</div>
    </div>
    <p style="margin: 16px 0;">
      Bir sonraki güne taşımak için bugün sadece 1 soru daha çözmen yeterli.
    </p>
    {_cta(f"{BRAND['site_url']}/interviews", "Bugünkü Soruyu Çöz →")}
    '''
    return {
        "subject": f"🔥 {streak_days} günlük streak — devam!",
        "html": _shell(f"{streak_days} günlük streak!", body, f"Streak: {streak_days} gün"),
    }


# ─────────────────────────────────────────────────────────
# KURAL 4: Inactive re-engagement (7 / 30 gün)
# ─────────────────────────────────────────────────────────
def inactive(user: Dict, days_inactive: int, suggested_question: Optional[Dict]) -> Dict[str, Any]:
    suggested_html = _question_card(suggested_question) if suggested_question else ""
    cta_url = (
        f"{BRAND['site_url']}/interviews/{suggested_question.get('category')}/{suggested_question.get('slug') or suggested_question.get('id')}"
        if suggested_question else f"{BRAND['site_url']}/interviews"
    )
    body = f'''
    <p style="margin: 0 0 16px 0;">Selam <strong>{user.get("username","mülakatçı")}</strong>,</p>
    <p style="margin: 0 0 16px 0;">
      <strong>{days_inactive} gündür</strong> ortalarda yoktun. Pratik yapmak istersen
      burada sana özel bir öneri var:
    </p>
    {suggested_html}
    <p style="margin: 16px 0;">
      Sadece 10 dakika ayırıp bu soruyu çözmen streak'ini canlı tutar.
    </p>
    {_cta(cta_url, "Pratiğe Devam Et →")}
    '''
    return {
        "subject": f"👋 {days_inactive} gündür yoktun — bir soru önerisi",
        "html": _shell("Seni özledik!", body, f"{days_inactive} gündür pratik yapılmadı"),
    }


# ─────────────────────────────────────────────────────────
# KURAL 5: Difficulty progression (beginner→intermediate)
# ─────────────────────────────────────────────────────────
def difficulty_progression(user: Dict, beginner_solved: int, beginner_total: int) -> Dict[str, Any]:
    pct = round(100 * beginner_solved / beginner_total) if beginner_total else 0
    body = f'''
    <p style="margin: 0 0 16px 0;">Selam <strong>{user.get("username","mülakatçı")}</strong>,</p>
    <p style="margin: 0 0 16px 0;">
      Beginner soruların <strong>%{pct}</strong>'ini tamamladın ({beginner_solved}/{beginner_total}).
      Intermediate seviyeye geçmeye hazırsın — yeni zorluklar seni bekliyor.
    </p>
    <div style="background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.3); border-radius: 12px; padding: 16px; margin: 16px 0;">
      <div style="font-size: 13px; color: rgba(255,255,255,0.6); margin-bottom: 8px;">Beginner ilerlemen</div>
      <div style="background: rgba(255,255,255,0.1); border-radius: 999px; height: 10px; overflow: hidden;">
        <div style="background: linear-gradient(90deg, #6366f1, {BRAND['accent']}); height: 100%; width: {pct}%;"></div>
      </div>
    </div>
    {_cta(f"{BRAND['site_url']}/interviews?level=intermediate", "Intermediate'a Geç →")}
    '''
    return {
        "subject": "📈 Beginner'ı bitirdin — sırada Intermediate var",
        "html": _shell("Seviye atlamaya hazır mısın?", body, f"Beginner %{pct} tamamlandı"),
    }


# ─────────────────────────────────────────────────────────
# KURAL 6: Yeni kategori önerisi (hiç denenmemiş)
# ─────────────────────────────────────────────────────────
def new_category(user: Dict, category_slug: str, category_label: str,
                 suggested_questions: List[Dict]) -> Dict[str, Any]:
    cards = "".join(_question_card(q) for q in suggested_questions[:2])
    body = f'''
    <p style="margin: 0 0 16px 0;">Selam <strong>{user.get("username","mülakatçı")}</strong>,</p>
    <p style="margin: 0 0 16px 0;">
      <strong>{category_label}</strong> kategorisini henüz denememişsin. Geniş bir yelpaze
      mülakatlarda daha avantajlı — bu kategoriyle başla:
    </p>
    {cards}
    {_cta(f"{BRAND['site_url']}/interviews/{category_slug}", "{category_label} kategorisine git →".format(category_label=category_label))}
    '''
    return {
        "subject": f"🆕 {category_label} kategorisini denemelisin",
        "html": _shell(f"Yeni kategori önerisi", body, f"{category_label} kategorisi"),
    }


# ─────────────────────────────────────────────────────────
# KURAL 7: Category struggle (aynı kategoride 3+ fail)
# ─────────────────────────────────────────────────────────
def category_struggle(user: Dict, category_slug: str, category_label: str,
                      failed_count: int, tutorial: Optional[Dict]) -> Dict[str, Any]:
    tut_html = _tutorial_card(tutorial) if tutorial else ""
    cta_url = f"{BRAND['site_url']}/interviews/{category_slug}"
    body = f'''
    <p style="margin: 0 0 16px 0;">Selam <strong>{user.get("username","mülakatçı")}</strong>,</p>
    <p style="margin: 0 0 16px 0;">
      Son zamanlarda <strong>{category_label}</strong> kategorisinde
      <strong>{failed_count}</strong> kez başarısız oldun. Endişelenme, bu kategoride
      birçok kişi zorlanıyor — özel bir rehber hazırladık:
    </p>
    {tut_html}
    <p style="margin: 16px 0;">
      Rehberi okuyup sonra pratik yaparsan başarı oranın belirgin şekilde artar.
    </p>
    {_cta(cta_url, f"{category_label} pratiğine dön →")}
    '''
    return {
        "subject": f"😓 {category_label} zorluyor — özel rehber",
        "html": _shell(f"{category_label} desteği", body, "Struggle pattern tespit edildi"),
    }


# ─────────────────────────────────────────────────────────
# KURAL 8: ID-chain (çözülen Q1 → öner Q2)
# ─────────────────────────────────────────────────────────
def id_chain_recommendation(user: Dict, solved_q: Dict,
                            recommended_q: Dict) -> Dict[str, Any]:
    url = f"{BRAND['site_url']}/interviews/{recommended_q.get('category')}/{recommended_q.get('slug') or recommended_q.get('id')}"
    body = f'''
    <p style="margin: 0 0 16px 0;">Selam <strong>{user.get("username","mülakatçı")}</strong>,</p>
    <p style="margin: 0 0 16px 0;">
      <strong>{solved_q.get("title","son sorunu")}</strong> çözdün — harika! Bir sonraki
      adım için en uygun soru bu:
    </p>
    {_question_card(recommended_q)}
    {_cta(url, "Önerilen Soruya Geç →")}
    '''
    return {
        "subject": f"🔗 {solved_q.get('title','')} çözdün — sıradaki hazır",
        "html": _shell("Sıradaki önerin", body, "ID-chain recommendation"),
    }


# ─────────────────────────────────────────────────────────
# KURAL 9: Related concepts gap (recursion var, DP yok)
# ─────────────────────────────────────────────────────────
def concept_gap(user: Dict, mastered_concept: str,
                missing_concept: str, tutorial: Optional[Dict]) -> Dict[str, Any]:
    tut_html = _tutorial_card(tutorial) if tutorial else ""
    body = f'''
    <p style="margin: 0 0 16px 0;">Selam <strong>{user.get("username","mülakatçı")}</strong>,</p>
    <p style="margin: 0 0 16px 0;">
      <strong>{mastered_concept}</strong> konusunda sağlam bir temelin var. Mülakatlarda sıkça
      birlikte sorulan <strong>{missing_concept}</strong> konusuna da göz atman iyi olur —
      bu tamamlayıcı beceri seni bir üst seviyeye taşır.
    </p>
    {tut_html}
    {_cta(f"{BRAND['site_url']}/interviews?concept={missing_concept}", f"{missing_concept} konusuna başla →")}
    '''
    return {
        "subject": f"🧩 {mastered_concept} biliyorsun — {missing_concept} de tamamla",
        "html": _shell("Beceri tamamlama önerisi", body, "Concept gap"),
    }


# ─────────────────────────────────────────────────────────
# KURAL 10: Time-of-day (opsiyonel)
# ─────────────────────────────────────────────────────────
def gentle_nudge(user: Dict, hours_active_avg: float) -> Dict[str, Any]:
    body = f'''
    <p style="margin: 0 0 16px 0;">Selam <strong>{user.get("username","mülakatçı")}</strong>,</p>
    <p style="margin: 0 0 16px 0;">
      Genelde bu saatlerde ({int(hours_active_avg):02d}:00 civarı) pratiğe başlıyorsun —
      bugün de 5 dakikalık bir tur atmak ister misin?
    </p>
    {_cta(f"{BRAND['site_url']}/interviews", "Hızlı Bir Tur Yap →")}
    '''
    return {
        "subject": "🐍 Günün sorusu — 5 dakika yeter",
        "html": _shell("Günün önerisi", body, "Time-of-day nudge"),
    }


# ═══════════════════════════════════════════════════════════
# Hata-tabanlı template'ler
# ═══════════════════════════════════════════════════════════

def _error_intro(user: Dict, category_label: str, count: int) -> str:
    return f'''
    <p style="margin: 0 0 16px 0;">Selam <strong>{user.get("username","mülakatçı")}</strong>,</p>
    <p style="margin: 0 0 16px 0;">
      Son 14 günde <strong>{count} kez</strong> <strong style="color: {BRAND['accent']};">{category_label}</strong> ile karşılaştın.
      Spesifik bir hata, spesifik bir çözüm demek — spam değil, hedefe yönelik bir rehber.
    </p>
    '''


def error_index_bounds(user: Dict, count: int, tutorial: Optional[Dict] = None) -> Dict[str, Any]:
    body = _error_intro(user, "Liste/Metin Sınır Hatası", count)
    body += '''
    <h3 style="margin: 16px 0 8px 0; color: #ffffff;">📐 Neden olur?</h3>
    <ul style="margin: 0 0 16px 0; padding-left: 20px; color: rgba(255,255,255,0.85);">
      <li><code style="background: rgba(255,255,255,0.05); padding: 2px 6px; border-radius: 4px;">for i in range(len(arr))</code> döngüsünde <code style="background: rgba(255,255,255,0.05); padding: 2px 6px; border-radius: 4px;">arr[i+1]</code> kullanmak (off-by-one)</li>
      <li><code style="background: rgba(255,255,255,0.05); padding: 2px 6px; border-radius: 4px;">arr[len(arr)]</code> yazmak (son indeks <code>len-1</code>)</li>
    </ul>
    <h3 style="margin: 16px 0 8px 0; color: #ffffff;">✅ Çözüm</h3>
    <pre style="background: rgba(99,102,241,0.08); border-left: 3px solid #6366f1; padding: 12px; border-radius: 6px; color: rgba(255,255,255,0.9); font-size: 13px; overflow-x: auto;">for i in range(len(arr) - 1):
    if arr[i] == arr[i + 1]:
        # ...</pre>
    '''
    if tutorial:
        body += _tutorial_card(tutorial)
    body += _cta(f"{BRAND['site_url']}/interviews?category=list-dict", "Liste Sorularını Çöz →")
    return {
        "subject": "🐛 Sınır hatası mı? 3 kez yapmışsın — hızlı çözüm",
        "html": _shell("Liste Sınırı Hatası", body, "Liste/Metin index problemi"),
    }


def error_type_check(user: Dict, count: int, tutorial: Optional[Dict] = None) -> Dict[str, Any]:
    body = _error_intro(user, "Tip Hatası", count)
    body += '''
    <h3 style="margin: 16px 0 8px 0; color: #ffffff;">🎯 Yaygın nedenler</h3>
    <ul style="margin: 0 0 16px 0; padding-left: 20px; color: rgba(255,255,255,0.85);">
      <li><code style="background: rgba(255,255,255,0.05); padding: 2px 6px; border-radius: 4px;">None</code> değerini matematiksel işleme sokmak</li>
      <li><code style="background: rgba(255,255,255,0.05); padding: 2px 6px; border-radius: 4px;">str + int</code> veya <code style="background: rgba(255,255,255,0.05); padding: 2px 6px; border-radius: 4px;">int + str</code> birleştirme</li>
    </ul>
    <h3 style="margin: 16px 0 8px 0; color: #ffffff;">✅ İki kalıp</h3>
    <pre style="background: rgba(99,102,241,0.08); border-left: 3px solid #6366f1; padding: 12px; border-radius: 6px; color: rgba(255,255,255,0.9); font-size: 13px; overflow-x: auto;"># 1. None kontrolü
if value is not None:
    total = value + 1

# 2. Tip dönüşümü
msg = "count: " + str(n)</pre>
    '''
    if tutorial:
        body += _tutorial_card(tutorial)
    body += _cta(f"{BRAND['site_url']}/interviews?category=python-basics", "Tip Sorularını Çöz →")
    return {
        "subject": "🎯 Tip hatasını 3 kez yaptın — bu 2 kalıbı öğren",
        "html": _shell("Tip Kontrolü", body, "Type mismatch problemi"),
    }


def error_recursion_base(user: Dict, count: int, tutorial: Optional[Dict] = None) -> Dict[str, Any]:
    body = _error_intro(user, "Özyineleme Hatası (Recursion)", count)
    body += '''
    <h3 style="margin: 16px 0 8px 0; color: #ffffff;">🔁 Belirtisi</h3>
    <p style="margin: 0 0 16px 0;">
      <code style="background: rgba(255,255,255,0.05); padding: 2px 6px; border-radius: 4px;">RecursionError</code> veya <code style="background: rgba(255,255,255,0.05); padding: 2px 6px; border-radius: 4px;">MemoryError</code> —
      fonksiyon kendini sonsuz kez çağırıyor.
    </p>
    <h3 style="margin: 16px 0 8px 0; color: #ffffff;">✅ Base case formülü</h3>
    <p style="margin: 0 0 8px 0; color: rgba(255,255,255,0.85);">
      Her recursive fonksiyon şu 3 parçayı içermeli:
    </p>
    <ol style="margin: 0 0 16px 0; padding-left: 20px; color: rgba(255,255,255,0.85);">
      <li><strong>Base case:</strong> ne zaman duracağını söyle</li>
      <li><strong>Recursive case:</strong> problemi küçült ve kendini çağır</li>
      <li><strong>İlerleme:</strong> her adımda base case'e yaklaş</li>
    </ol>
    <pre style="background: rgba(99,102,241,0.08); border-left: 3px solid #6366f1; padding: 12px; border-radius: 6px; color: rgba(255,255,255,0.9); font-size: 13px; overflow-x: auto;">def factorial(n):
    if n <= 1:           # ← base case
        return 1
    return n * factorial(n - 1)  # ← recursive case</pre>
    '''
    if tutorial:
        body += _tutorial_card(tutorial)
    body += _cta(f"{BRAND['site_url']}/interviews?category=algorithms", "Recursion Sorularını Çöz →")
    return {
        "subject": "🔁 Recursion patladı mı? Base case'i unutma",
        "html": _shell("Özyineleme Base Case", body, "Recursion base case rehberi"),
    }


def error_name(user: Dict, count: int, tutorial: Optional[Dict] = None) -> Dict[str, Any]:
    body = _error_intro(user, "Tanımsız Değişken", count)
    body += '''
    <h3 style="margin: 16px 0 8px 0; color: #ffffff;">🔤 Yaygın nedenler</h3>
    <ul style="margin: 0 0 16px 0; padding-left: 20px; color: rgba(255,255,255,0.85);">
      <li>Değişken kullanılmadan önce tanımlanmamış</li>
      <li>Tip adı yanlış (örn. <code style="background: rgba(255,255,255,0.05); padding: 2px 6px; border-radius: 4px;">leng</code> yerine <code style="background: rgba(255,255,255,0.05); padding: 2px 6px; border-radius: 4px;">len</code>)</li>
      <li>Scope dışı kullanım (for içinde tanımlayıp dışarıda kullanmak)</li>
    </ul>
    <p style="margin: 0 0 16px 0; color: rgba(255,255,255,0.7); font-size: 13px;">
      💡 İpucu: IDE'de <strong>Python</strong> eklentisi kullanırsan değişken tanımsızsa anında kırmızı çizer.
    </p>
    '''
    if tutorial:
        body += _tutorial_card(tutorial)
    body += _cta(f"{BRAND['site_url']}/interviews?category=python-basics", "Değişken Sorularını Çöz →")
    return {
        "subject": "🔤 Tanımsız değişken hatası mı? 3 kez",
        "html": _shell("Değişken Tanımı", body, "NameError rehberi"),
    }


def error_attribute(user: Dict, count: int, tutorial: Optional[Dict] = None) -> Dict[str, Any]:
    body = _error_intro(user, "Nesne Özelliği Yok", count)
    body += '''
    <h3 style="margin: 16px 0 8px 0; color: #ffffff;">🧩 Neden olur?</h3>
    <ul style="margin: 0 0 16px 0; padding-left: 20px; color: rgba(255,255,255,0.85);">
      <li><code style="background: rgba(255,255,255,0.05); padding: 2px 6px; border-radius: 4px;">.push()</code> (JS/Java alışkanlığı — Python'da <code style="background: rgba(255,255,255,0.05); padding: 2px 6px; border-radius: 4px;">.append()</code>)</li>
      <li><code style="background: rgba(255,255,255,0.05); padding: 2px 6px; border-radius: 4px;">.length</code> (JS — Python'da <code style="background: rgba(255,255,255,0.05); padding: 2px 6px; border-radius: 4px;">len(x)</code> fonksiyon)</li>
      <li><code style="background: rgba(255,255,255,0.05); padding: 2px 6px; border-radius: 4px;">dict.sort()</code> (dict sıralanamaz — key'leri alıp sırala)</li>
    </ul>
    <h3 style="margin: 16px 0 8px 0; color: #ffffff;">✅ Python yolu</h3>
    <pre style="background: rgba(99,102,241,0.08); border-left: 3px solid #6366f1; padding: 12px; border-radius: 6px; color: rgba(255,255,255,0.9); font-size: 13px; overflow-x: auto;">lst = [3, 1, 2]
lst.append(4)        # ekle
print(len(lst))      # uzunluk
lst.sort()           # sırala</pre>
    '''
    if tutorial:
        body += _tutorial_card(tutorial)
    body += _cta(f"{BRAND['site_url']}/interviews?category=oop", "OOP Sorularını Çöz →")
    return {
        "subject": "🧩 .push() mı yazıyorsun? Python'da yok",
        "html": _shell("Nesne Metotları", body, "AttributeError rehberi"),
    }


def error_key(user: Dict, count: int, tutorial: Optional[Dict] = None) -> Dict[str, Any]:
    body = _error_intro(user, "Sözlük Anahtarı Yok", count)
    body += '''
    <h3 style="margin: 16px 0 8px 0; color: #ffffff;">🔑 Neden olur?</h3>
    <p style="margin: 0 0 16px 0;">
      <code style="background: rgba(255,255,255,0.05); padding: 2px 6px; border-radius: 4px;">d['key']</code> anahtar yoksa patlar.
    </p>
    <h3 style="margin: 16px 0 8px 0; color: #ffffff;">✅ Güvenli erişim</h3>
    <pre style="background: rgba(99,102,241,0.08); border-left: 3px solid #6366f1; padding: 12px; border-radius: 6px; color: rgba(255,255,255,0.9); font-size: 13px; overflow-x: auto;"># 1. .get() ile None döner
val = d.get('key')

# 2. .get() ile varsayılan
val = d.get('key', 0)

# 3. defaultdict (sık kullanım için)
from collections import defaultdict
d = defaultdict(int)
d['count'] += 1   # yoksa 0'dan başlar</pre>
    '''
    if tutorial:
        body += _tutorial_card(tutorial)
    body += _cta(f"{BRAND['site_url']}/interviews?category=list-dict", "Sözlük Sorularını Çöz →")
    return {
        "subject": "🔑 KeyError mı? Güvenli erişim kalıbını öğren",
        "html": _shell("Sözlük Erişimi", body, "KeyError rehberi"),
    }


ERROR_TEMPLATES = {
    "error_index_bounds": error_index_bounds,
    "error_type_check": error_type_check,
    "error_recursion_base": error_recursion_base,
    "error_name": error_name,
    "error_attribute": error_attribute,
    "error_key": error_key,
}