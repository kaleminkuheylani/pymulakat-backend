from dotenv import load_dotenv
from supabase import create_client, Client
from functools import lru_cache
import os

load_dotenv()


@lru_cache()
def get_supabase() -> Client:
    """Anon key client — user-facing işlemler için (RLS aktif)."""
    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_ANON_KEY"],
    )

@lru_cache()
def get_supabase_admin() -> Client:
    """Service role client — backend-only, RLS bypass (güvenli!)."""
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not service_key:
        raise RuntimeError(
            "SUPABASE_SERVICE_ROLE_KEY tanımlı değil! "
            "Supabase Dashboard → Settings → API → service_role key'i .env'e ekleyin."
        )
    return create_client(
        os.environ["SUPABASE_URL"],
        service_key,
    )