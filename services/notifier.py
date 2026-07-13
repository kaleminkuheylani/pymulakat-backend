"""
services/notifier.py
═══════════════════════════════════════════════════════════════
Next.js ISR revalidation webhook helper.

İçerik güncellendiğinde (yeni soru eklendi, kategori düzenlendi vs.)
backend → Next.js /api/revalidate endpoint'ine POST atar. Next.js
ilgili tag'lere bağlı cache'leri düşürür, sonraki istek taze veriyle
gelir.

Cache stratejisi katmanları (2026-07-13):
  1) Next.js ISR (1 saat revalidate, tags: ...)   ← bu helper tetikler
  2) Backend in-memory 60s (per-filter)             ← question_loader.py
  3) Supabase DB (truth)                            ← değişmez

Güvenlik:
  - REVALIDATE_SECRET env ile korunur (frontend ve backend aynı değer)
  - 3s timeout: Next.js yavaşsa backend'i bloklamaz
  - Hata durumunda warn log, exception raise etmez (best-effort)

Kullanım (admin endpoint'lerden):
    from services.notifier import notify_nextjs_revalidate

    # Yeni soru eklendikten sonra:
    notify_nextjs_revalidate(tags=[
        "questions-list",
        f"category-{category_slug}",
        f"question-{category_slug}-{question_slug}",
    ])
"""

import logging
import os
from typing import Iterable, Optional

import urllib.request
import urllib.error
import json

logger = logging.getLogger("pymulakat.notifier")


def _resolve_endpoint() -> Optional[str]:
    """Frontend Next.js revalidate URL'si (env'den)."""
    return os.getenv("NEXTJS_REVALIDATE_URL") or os.getenv("FRONTEND_REVALIDATE_URL")


def _resolve_secret() -> Optional[str]:
    """Paylaşılan secret — frontend REVALIDATE_SECRET ile aynı değer."""
    return os.getenv("REVALIDATE_SECRET")


def notify_nextjs_revalidate(
    tags: Optional[Iterable[str]] = None,
    paths: Optional[Iterable[str]] = None,
    timeout: float = 3.0,
) -> dict:
    """
    Next.js /api/revalidate endpoint'ine POST at.

    Args:
        tags: revalidateTag() ile düşürülecek tag listesi
              (örn: ["questions-list", "category-heap"])
        paths: revalidatePath() ile düşürülecek path listesi
               (örn: ["/interviews", "/interviews/heap"])
        timeout: HTTP timeout (saniye). Default 3s — Next.js yavaşsa
                 backend'i bloklamamalı.

    Returns:
        dict: {"ok": bool, "status": int | None, "error": str | None,
               "endpoint": str | None, "sent": dict}

    Raises:
        Hiçbir zaman raise etmez. Hata loglanır ve döner.
        Cache invalidation best-effort — kullanıcı isteğini bloklamamalı.
    """
    endpoint = _resolve_endpoint()
    secret = _resolve_secret()

    tags_list = list(tags) if tags else []
    paths_list = list(paths) if paths else []

    # En az bir tag veya path olmalı
    if not tags_list and not paths_list:
        return {
            "ok": False,
            "status": None,
            "error": "no tags or paths provided",
            "endpoint": endpoint,
            "sent": {},
        }

    # Endpoint tanımsızsa sessizce atla (dev ortamı, env ayarlanmamış olabilir)
    if not endpoint:
        logger.debug(
            "[notifier] NEXTJS_REVALIDATE_URL tanimsiz — skip "
            "(tags=%s, paths=%s)",
            tags_list,
            paths_list,
        )
        return {
            "ok": False,
            "status": None,
            "error": "NEXTJS_REVALIDATE_URL not configured",
            "endpoint": None,
            "sent": {"tags": tags_list, "paths": paths_list},
        }

    # Secret tanımsızsa endpoint 401 döner, yine de istek atalım (debug için)
    if not secret:
        logger.warning(
            "[notifier] REVALIDATE_SECRET tanimsiz — Next.js istegi 401 donecek"
        )

    body = {"tags": tags_list, "paths": paths_list}
    body_bytes = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(
        endpoint,
        data=body_bytes,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            **({"Authorization": f"Bearer {secret}"} if secret else {}),
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            try:
                resp_body = json.loads(resp.read().decode("utf-8"))
            except Exception:
                resp_body = None
            ok = 200 <= status < 300
            if ok:
                logger.info(
                    "[notifier] revalidate ok: status=%s tags=%s paths=%s resp=%s",
                    status,
                    tags_list,
                    paths_list,
                    resp_body,
                )
            else:
                logger.warning(
                    "[notifier] revalidate non-2xx: status=%s tags=%s resp=%s",
                    status,
                    tags_list,
                    resp_body,
                )
            return {
                "ok": ok,
                "status": status,
                "error": None if ok else f"HTTP {status}",
                "endpoint": endpoint,
                "sent": {"tags": tags_list, "paths": paths_list},
                "response": resp_body,
            }
    except urllib.error.HTTPError as e:
        # 401/403/503 — secret yanlış, env yok, vb.
        try:
            err_body = e.read().decode("utf-8")
        except Exception:
            err_body = ""
        logger.warning(
            "[notifier] revalidate HTTP error: status=%s body=%s tags=%s",
            e.code,
            err_body[:200],
            tags_list,
        )
        return {
            "ok": False,
            "status": e.code,
            "error": f"HTTP {e.code}: {err_body[:200]}",
            "endpoint": endpoint,
            "sent": {"tags": tags_list, "paths": paths_list},
        }
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        # Network hatası, timeout, DNS — best-effort, logla ve devam
        logger.warning(
            "[notifier] revalidate network error: %s tags=%s",
            str(e)[:200],
            tags_list,
        )
        return {
            "ok": False,
            "status": None,
            "error": f"network: {str(e)[:200]}",
            "endpoint": endpoint,
            "sent": {"tags": tags_list, "paths": paths_list},
        }
    except Exception as e:
        # Beklenmeyen — logla, raise etme
        logger.exception("[notifier] revalidate unexpected error: %s", e)
        return {
            "ok": False,
            "status": None,
            "error": f"unexpected: {str(e)[:200]}",
            "endpoint": endpoint,
            "sent": {"tags": tags_list, "paths": paths_list},
        }


# ═══════════════════════════════════════════════════════════════
# ─── Cache tag registry (frontend CACHE_TAGS ile uyumlu) ─────
# ═══════════════════════════════════════════════════════════════
# Frontend lib/api/questionAPI.ts → CACHE_TAGS ile birebir aynı
# isimlendirme. Değiştirirsen frontend tarafını da güncelle.


def tag_questions_list() -> str:
    return "questions-list"


def tag_categories_list() -> str:
    return "categories-list"


def tag_category(slug: str) -> str:
    return f"category-{slug}"


def tag_question(category_slug: str, question_slug: str) -> str:
    return f"question-{category_slug}-{question_slug}"


def notify_question_upserted(
    category_slug: str,
    question_slug: str,
) -> dict:
    """
    Yeni soru eklendiğinde veya mevcut soru güncellendiğinde çağır.
    Hem liste hem kategori hem soru detay cache'i düşer.
    """
    return notify_nextjs_revalidate(
        tags=[
            tag_questions_list(),
            tag_category(category_slug),
            tag_question(category_slug, question_slug),
        ]
    )


def notify_category_changed(category_slug: str) -> dict:
    """
    Kategori meta güncellendiğinde çağır (label, description, vs.).
    Kategori landing + kategori listesi cache'i düşer.
    """
    return notify_nextjs_revalidate(
        tags=[
            tag_categories_list(),
            tag_category(category_slug),
        ]
    )


def notify_global_invalidate() -> dict:
    """
    Tüm cache'i düşür (acil durum, schema değişikliği, vs.).
    Nadiren kullanılır.
    """
    return notify_nextjs_revalidate(
        tags=[
            tag_questions_list(),
            tag_categories_list(),
        ],
        paths=[
            "/interviews",
            "/",  # landing page question count
        ],
    )
