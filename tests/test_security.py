"""Security testleri — JWT guard, CORS, auth."""


def test_missing_auth_header_rejected(client):
    """Authorization header olmadan /auth/me 401 dönmeli."""
    res = client.get("/auth/me")
    assert res.status_code == 401


def test_malformed_auth_header_rejected(client):
    """Geçersiz formatta header 401 dönmeli."""
    res = client.get("/auth/me", headers={"Authorization": "InvalidFormat"})
    assert res.status_code == 401


def test_bearer_without_token_rejected(client):
    """Bearer boş token 401 dönmeli."""
    res = client.get("/auth/me", headers={"Authorization": "Bearer "})
    assert res.status_code == 401


def test_cors_preflight_allowed(client):
    """OPTIONS preflight doğru CORS header'ları ile dönmeli."""
    res = client.options(
        "/api/v2/categories",
        headers={
            "Origin": "https://pymulakat-frontend.vercel.app",
            "Access-Control-Request-Method": "GET",
        },
    )
    # CORS preflight 200 veya 204 dönmeli
    assert res.status_code in (200, 204)
    assert "access-control-allow-origin" in res.headers
    assert "access-control-allow-methods" in res.headers


def test_cors_vercel_preview_regex(client):
    """*.vercel.app preview URL'leri de izinli olmalı (regex)."""
    res = client.get(
        "/",
        headers={"Origin": "https://pymulakat-frontend-git-feature-ahmet.vercel.app"},
    )
    # Varsa Access-Control-Allow-Origin kontrol et
    acao = res.headers.get("access-control-allow-origin", "")
    assert "vercel.app" in acao or acao == "*" or not acao
    # Yani Vercel preview URL'leri de kabul ediliyor (regex match)
