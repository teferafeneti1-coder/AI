"""
agent_node/supabase_db.py

Thin wrapper around the Supabase REST API for user credential
and account-lock management.

Supabase table required:
    CREATE TABLE users (
        username   TEXT PRIMARY KEY,
        password   TEXT NOT NULL,
        is_locked  BOOLEAN NOT NULL DEFAULT FALSE
    );
    -- seed test user:
    INSERT INTO users (username, password) VALUES ('insa', '1234');

All functions return (success: bool, data/message).
Falls back gracefully when SUPABASE_URL / SUPABASE_KEY are not set
so the service still starts without Supabase configured.
"""

import logging
from typing import Optional

from config import settings

logger = logging.getLogger("supabase_db")

# ── Lazy client — only instantiated when credentials are present ─────────────
_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    if not settings.supabase_url or not settings.supabase_key:
        logger.warning("SUPABASE_URL / SUPABASE_KEY not set — Supabase disabled")
        return None
    try:
        from supabase import create_client
        _client = create_client(settings.supabase_url, settings.supabase_key)
        logger.info("Supabase client created (%s)", settings.supabase_url)
        return _client
    except Exception as e:
        logger.error("Could not create Supabase client: %s", e)
        return None


def is_configured() -> bool:
    return bool(settings.supabase_url and settings.supabase_key)


# ── User lookup ───────────────────────────────────────────────────────────────

def get_user(username: str) -> Optional[dict]:
    """
    Returns the row for `username` or None if not found / Supabase unavailable.
    Row shape: { username, password, is_locked }
    """
    client = _get_client()
    if not client:
        return None
    try:
        resp = (
            client.table("users")
            .select("username, password, is_locked")
            .eq("username", username)
            .single()
            .execute()
        )
        return resp.data
    except Exception as e:
        logger.error("get_user(%s) failed: %s", username, e)
        return None


# ── Lock / unlock ─────────────────────────────────────────────────────────────

def lock_user(username: str) -> tuple[bool, str]:
    """Set is_locked = true for `username`."""
    client = _get_client()
    if not client:
        return False, "Supabase not configured"
    try:
        client.table("users").update({"is_locked": True}).eq("username", username).execute()
        logger.info("User '%s' locked in Supabase", username)
        return True, f"Account '{username}' locked in Supabase."
    except Exception as e:
        logger.error("lock_user(%s) failed: %s", username, e)
        return False, f"Supabase lock failed: {e}"


def unlock_user(username: str) -> tuple[bool, str]:
    """Set is_locked = false for `username` (admin reset path)."""
    client = _get_client()
    if not client:
        return False, "Supabase not configured"
    try:
        client.table("users").update({"is_locked": False}).eq("username", username).execute()
        logger.info("User '%s' unlocked in Supabase", username)
        return True, f"Account '{username}' unlocked in Supabase."
    except Exception as e:
        logger.error("unlock_user(%s) failed: %s", username, e)
        return False, f"Supabase unlock failed: {e}"
