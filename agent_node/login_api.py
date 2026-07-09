"""
agent_node/login_api.py

Lightweight Flask HTTP API served on the Agent Node machine.
Accepts login attempts from the React login page, validates credentials
against Supabase, and forwards every event into the Audit Log pipeline.

  React form  →  POST /api/login  (this file, port 8080)
                     │
                     ├── Supabase users table (credential + lock check)
                     │
                     └── audit_log_service/inject_api.py  (port 8081)
                              │  HTTP POST /inject
                              ▼
                         _event_queue  →  gRPC  →  rules.py  →  Alert
                              │
                              ▼
                         hids_node dashboard (port 5000)

Lock path:
  HIDS dashboard  →  ExecuteCommand(lock_account)
                  →  executor.py  →  supabase_db.lock_user()
                  →  sets is_locked=true in Supabase
                  →  /api/account-status polls picks it up → LockedScreen
"""

import os
import time
import json
import uuid
import logging
import threading

import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

from config import settings
import supabase_db

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("login_api")


def log_json(event: str, **kwargs) -> None:
    print(json.dumps({"event": event, "ts": time.time(), **kwargs}), flush=True)


# ── Fallback in-memory credentials (used when Supabase is not configured) ────
_FALLBACK_USER = "insa"
_FALLBACK_PASS = "1234"

# ── In-memory lock state (mirrors Supabase; also catches lock within same process) ──
_mem_locked: dict[str, bool]   = {}
_mem_reason: dict[str, str]    = {}
_mem_lock = threading.Lock()


def set_account_locked(username: str,
                       reason: str = "Locked by HIDS administrator") -> None:
    """
    Called by executor.py immediately after the Supabase lock succeeds.
    Updates the in-memory mirror so /api/account-status returns locked
    instantly without waiting for the next Supabase poll.
    """
    with _mem_lock:
        _mem_locked[username] = True
        _mem_reason[username] = reason
    log_json("account_locked_by_hids", username=username, reason=reason)


def clear_account_lock(username: str) -> None:
    """Called by executor.py after an unlock_account command."""
    with _mem_lock:
        _mem_locked.pop(username, None)
        _mem_reason.pop(username, None)
    log_json("account_lock_cleared", username=username)


def _is_locked_mem(username: str) -> tuple[bool, str]:
    """Check the fast in-memory mirror."""
    with _mem_lock:
        return _mem_locked.get(username, False), _mem_reason.get(username, "")


def _is_locked_supabase(username: str) -> tuple[bool, str]:
    """
    Check Supabase directly (authoritative source).
    Falls back to False when Supabase is not configured.
    """
    if not supabase_db.is_configured():
        return False, ""
    user = supabase_db.get_user(username)
    if user and user.get("is_locked"):
        return True, "This account has been locked by the HIDS administrator."
    return False, ""


def is_locked(username: str) -> tuple[bool, str]:
    """
    Check in-memory first (fast path, set within same process),
    then fall through to Supabase (catches locks applied from outside).
    """
    mem, reason = _is_locked_mem(username)
    if mem:
        return True, reason
    return _is_locked_supabase(username)


# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder="login_ui/dist", static_url_path="")
CORS(app, resources={r"/api/*": {"origins": "*"}})


# ── Serve React build at root ─────────────────────────────────────────────────
@app.route("/")
@app.route("/<path:path>")
def serve_frontend(path=""):
    dist   = os.path.join(os.path.dirname(__file__), "login_ui", "dist")
    target = os.path.join(dist, path)
    if path and os.path.exists(target):
        return app.send_static_file(path)
    return app.send_static_file("index.html")


# ── Account status endpoint ───────────────────────────────────────────────────
@app.route("/api/account-status")
def account_status():
    """
    GET /api/account-status?username=<user>
    Polled every 2 s by the React LoginForm.
    Returns locked=true as soon as executor sets is_locked in Supabase.
    """
    username = request.args.get("username", "").strip()
    if not username:
        return jsonify({"locked": False, "username": "", "reason": ""})

    locked, reason = is_locked(username)
    return jsonify({"locked": locked, "username": username, "reason": reason})


# ── Login endpoint ────────────────────────────────────────────────────────────
@app.route("/api/login", methods=["POST"])
def login():
    """
    POST /api/login
    Body: { "username": str, "password": str }

    Returns:
      200  { "success": true,  "message": "Login successful" }
      401  { "success": false, "message": "Invalid credentials" }
      423  { "success": false, "message": "...", "locked": true }
    """
    data      = request.get_json(force=True) or {}
    username  = data.get("username", "").strip()
    password  = data.get("password", "").strip()
    source_ip = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.remote_addr
        or "0.0.0.0"
    )

    if not username:
        return jsonify({"success": False, "message": "Username is required"}), 400

    # ── 1. Check lock state (Supabase is_locked OR in-memory mirror) ──────────
    locked, lock_reason = is_locked(username)
    if locked:
        log_json("login_rejected_locked", username=username, source_ip=source_ip)
        return jsonify({
            "success": False,
            "locked":  True,
            "message": lock_reason or "This account has been locked by the administrator.",
        }), 423

    # ── 2. Validate credentials ────────────────────────────────────────────────
    auth_ok = _check_credentials(username, password)

    if auth_ok:
        log_json("login_success", username=username, source_ip=source_ip)
        _forward_event(username=username, source_ip=source_ip, status="success")
        return jsonify({"success": True, "message": "Login successful"})

    # ── 3. Wrong password ──────────────────────────────────────────────────────
    log_json("login_failure", username=username, source_ip=source_ip)
    _forward_event(username=username, source_ip=source_ip, status="fail")
    return jsonify({"success": False, "message": "Invalid credentials"}), 401


def _check_credentials(username: str, password: str) -> bool:
    """
    Returns True if username/password match.
    Uses Supabase when configured, falls back to hardcoded test credentials.
    """
    if supabase_db.is_configured():
        user = supabase_db.get_user(username)
        if user is None:
            return False
        return user.get("password") == password
    # Fallback for local dev without Supabase
    return username == _FALLBACK_USER and password == _FALLBACK_PASS


# ── Forward event to Audit Log inject endpoint ────────────────────────────────
def _forward_event(username: str, source_ip: str, status: str) -> None:
    payload = {
        "username":   username,
        "source_ip":  source_ip,
        "status":     status,
        "timestamp":  int(time.time()),
        "attempt_id": str(uuid.uuid4()),
    }
    url = f"http://{settings.audit_host}:{settings.audit_inject_port}/inject"

    def _send():
        try:
            resp = requests.post(url, json=payload, timeout=3)
            log_json("event_forwarded", url=url,
                     status_code=resp.status_code,
                     username=username, event_status=status)
        except Exception as exc:
            logger.warning("Could not forward login event to audit service: %s", exc)

    threading.Thread(target=_send, daemon=True).start()


# ── Entry point ───────────────────────────────────────────────────────────────
def run():
    if supabase_db.is_configured():
        log_json("supabase_enabled", url=settings.supabase_url)
    else:
        log_json("supabase_disabled",
                 note="Using fallback credentials insa/1234. Set SUPABASE_URL + SUPABASE_KEY to enable.")
    log_json("login_api_started",
             host=settings.login_api_host,
             port=settings.login_api_port)
    app.run(
        host=settings.login_api_host,
        port=settings.login_api_port,
        debug=False,
        use_reloader=False,
        threaded=True,
    )


if __name__ == "__main__":
    run()
