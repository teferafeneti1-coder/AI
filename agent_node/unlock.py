#!/usr/bin/env python3
"""
agent_node/unlock.py  <username>

Reset a locked account by setting is_locked = false in Supabase.
Use this after a test to re-enable the 'insa' account.

Usage:
    py unlock.py insa
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from supabase_db import unlock_user

def main():
    if len(sys.argv) < 2:
        print("Usage: py unlock.py <username>")
        sys.exit(1)
    username = sys.argv[1].strip()
    ok, msg = unlock_user(username)
    print(msg)
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
