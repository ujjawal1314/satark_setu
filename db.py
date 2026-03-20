import os
from functools import lru_cache
from typing import Optional

try:
    from supabase import Client, create_client
except ImportError:  # pragma: no cover
    Client = object  # type: ignore[assignment]
    create_client = None  # type: ignore[assignment]


@lru_cache(maxsize=1)
def get_supabase() -> Optional["Client"]:
    """Singleton Supabase client. Returns None when env/dependency is missing."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key or create_client is None:
        return None
    return create_client(url, key)
