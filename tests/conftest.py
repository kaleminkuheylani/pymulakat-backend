"""
Test fixtures — Supabase istemcisi mock'lanır, gerçek DB'ye bağlanılmaz.
"""
import os
import sys
from unittest.mock import MagicMock, patch

# Test ortamı ayarla (önce app import'larından önce)
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret-for-pytest-only")

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_supabase():
    """Supabase client mock — tüm DB çağrıları sahte data döner."""
    mock = MagicMock()
    mock.table.return_value.select.return_value.limit.return_value.execute.return_value.data = []
    mock.table.return_value.select.return_value.execute.return_value.data = []
    return mock


@pytest.fixture
def client(mock_supabase):
    """FastAPI TestClient — Supabase mock'lanmış (lru_cache bypass)."""
    import supabase_client
    supabase_client.get_supabase.cache_clear()
    supabase_client.get_supabase_admin.cache_clear()
    with patch.object(supabase_client, "get_supabase", return_value=mock_supabase), \
         patch.object(supabase_client, "get_supabase_admin", return_value=mock_supabase):
        from main import app
        return TestClient(app)


@pytest.fixture
def client_no_auth():
    """SUPABASE_JWT_SECRET olmadan test client (production guard testi için)."""
    env = os.environ.copy()
    env["SUPABASE_JWT_SECRET"] = ""
    env["APP_ENV"] = "production"
    with patch.dict(os.environ, env), \
         patch("supabase_client.get_supabase", return_value=MagicMock()), \
         patch("supabase_client.get_supabase_admin", return_value=MagicMock()):
        # main modülünü fresh import et
        if "main" in sys.modules:
            del sys.modules["main"]
        from main import app
        return TestClient(app)
