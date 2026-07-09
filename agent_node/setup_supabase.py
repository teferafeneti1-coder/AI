#!/usr/bin/env python3
"""
agent_node/setup_supabase.py

Run once to seed the Supabase 'users' table with the test user.
Requires SUPABASE_URL and SUPABASE_KEY in your .env or environment.

Usage:
    cd agent_node
    py setup_supabase.py

What it does:
  1. Connects to Supabase using your credentials.
  2. Inserts the test user insa / 1234 with is_locked = false.
     (If the row already exists it is left unchanged — safe to re-run.)

Supabase table DDL (run this in the Supabase SQL Editor first):

    CREATE TABLE IF NOT EXISTS users (
        username  TEXT PRIMARY KEY,
        password  TEXT NOT NULL,
        is_locked BOOLEAN NOT NULL DEFAULT FALSE
    );
"""

import sys
import os

# Make sure config.py is importable
sys.path.insert(0, os.path.dirname(__file__))

from config import settings
from supabase_db import _get_client

def main():
    print(f"Connecting to Supabase: {settings.supabase_url}")
    client = _get_client()
    if not client:
        print("ERROR: Supabase client could not be created.")
        print("Check SUPABASE_URL and SUPABASE_KEY in your .env file.")
        sys.exit(1)

    # Upsert the test user — on conflict (username) do nothing
    try:
        resp = (
            client.table("users")
            .upsert(
                {"username": "insa", "password": "1234", "is_locked": False},
                on_conflict="username",
                ignore_duplicates=True,
            )
            .execute()
        )
        print("Test user 'insa' seeded successfully.")
        print("Row:", resp.data)
    except Exception as e:
        print(f"ERROR seeding user: {e}")
        sys.exit(1)

    print()
    print("Done. You can now:")
    print("  - Run 'py login_api.py' to start the login server.")
    print("  - Log in with username=insa, password=1234.")
    print("  - Reset a locked account: set is_locked=false in the Supabase table editor,")
    print("    or run: py unlock.py insa")

if __name__ == "__main__":
    main()
