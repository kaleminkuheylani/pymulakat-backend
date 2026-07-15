"""
services/email.py — Resend API wrapper (admin magic link).

SMTP yok, Resend HTTP API kullanir (basit, guvenilir, KVKK uyumlu — ABD/EU
veri merkezleri).
"""

import os
import logging
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx

log = logging.getLogger("pymulakat.email")

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "mkemal@pythonmulakat.com")
RESEND_MAGIC_LINK_TTL_MIN = int(os.getenv("RESEND_MAGIC_LINK_TTL_MIN", "15"))


def generate_magic_token() -> tuple[str, str]:
    """(raw_token, hash) doner. raw token URL'de, hash DB'de saklanir."""
    raw = secrets.token_urlsafe(32)
    h = hashlib.sha256(raw.encode()).hexdigest()
    return raw, h


def send_magic_link_email(to_email: str, magic_link: str) -> bool:
    """
    Resend API ile admin magic link gonder.

    Returns:
        True: email basariyla gonderildi
        False: RESEND_API_KEY yok veya hata (dev mode'da link log'a yazilir)
    """
    if not RESEND_API_KEY:
        log.warning(f"[email] dev mode (RESEND_API_KEY yok). Magic link: {magic_link}")
        return False

    try:
        res = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": RESEND_FROM_EMAIL,
                "to": [to_email],
                "subject": "PythonMulakat Admin Giris",
                "html": (
                    f'<div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:20px">'
                    f'<h2 style="color:#0a0e1a">Admin Giris</h2>'
                    f'<p>PythonMulakat admin paneline giris yapmak icin asagidaki butona tiklayin:</p>'
                    f'<a href="{magic_link}" style="display:inline-block;padding:12px 24px;background:#f59e0b;color:#0a0e1a;text-decoration:none;border-radius:8px;font-weight:bold">'
                    f'Giris Yap</a>'
                    f'<p style="color:#6b7280;font-size:12px;margin-top:20px">Bu link {RESEND_MAGIC_LINK_TTL_MIN} dakika gecerlidir ve sadece bir kez kullanilabilir.</p>'
                    f'<p style="color:#6b7280;font-size:12px">Bu emaili siz talep etmediyseniz dikkate almayin.</p>'
                    f'</div>'
                ),
            },
            timeout=10.0,
        )
        if res.status_code in (200, 201):
            log.info(f"[email] magic link sent to {to_email}")
            return True
        else:
            log.error(f"[email] Resend error {res.status_code}: {res.text[:200]}")
            return False
    except Exception as e:
        log.error(f"[email] Resend exception: {type(e).__name__}: {str(e)[:200]}")
        return False
