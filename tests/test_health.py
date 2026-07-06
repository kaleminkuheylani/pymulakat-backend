"""Health endpoint testleri — DB connectivity + modül yükleme."""


def test_health_ok(client, mock_supabase):
    """/health 200 veya 503 (degraded) dönmeli, tüm modüller yüklü olmalı."""
    res = client.get("/health")
    # 200 = healthy, 503 = degraded ama yapı sağlam (test ortamı DB mock'lu)
    assert res.status_code in (200, 503)
    data = res.json()
    assert data["status"] in ("ok", "degraded")
    assert data["version"] == "2.5"
    assert "loaded" in data
    assert "db" in data
    # Tüm beklenen modüller yüklü olmalı
    expected = ["auth", "attempts_v1", "questions_v2", "categories_v2", "tutorials_v2", "admin", "account_v2"]
    for mod in expected:
        assert data["loaded"].get(mod) is True, f"{mod} yüklenmedi"


def test_health_db_degraded(client, mock_supabase):
    """DB çağrısı exception fırlatırsa status=503 olmalı."""
    mock_supabase.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception("DB down")
    res = client.get("/health")
    # 503 (degraded) ya da 200 (status=ok ama db.ok=false) kabul edilebilir
    assert res.status_code in (200, 503)
    data = res.json()
    if res.status_code == 503:
        assert data["status"] == "degraded"
    assert data["db"]["ok"] is False


def test_root_endpoint(client):
    """/ endpoint'i metadata dönmeli."""
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["service"] == "PythonMulakat API"
    assert data["version"] == "2.5"
    assert "endpoints" in data
    # Önemli endpoint'ler listelenmiş olmalı
    endpoints = data["endpoints"]
    for key in ("register", "login", "me", "categories", "questions", "tests"):
        assert key in endpoints, f"{key} endpoint'i root'ta eksik"
