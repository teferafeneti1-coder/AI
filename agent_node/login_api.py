"""
agent_node/login_api.py

Lightweight Flask HTTP API served on the Agent Node machine.
Accepts login attempts from the React login page, validates credentials,
and forwards every event into the Audit Log Service inject endpoint.

  React form  →  POST /api/login  (this file, port 8080)
                     │
                     ▼
              audit_log_service/inject_api.py  (port 8081)
                     │  HTTP POST /inject
                     ▼
              _event_queue  →  gRPC stream  →  grpc_server/rules.py
                     │  alert broadcast
                     ▼
              hids_node dashboard  (port 5000)

When the admin clicks "Lock Account" on the HIDS dashboard, the Agent's
ExecuteCommand RPC runs executor.lock_account() which locks the OS account
AND sets _account_locked = True here so the login page immediately shows
"Account Locked" to anyone trying to log in.
"""

import sys
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

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("login_api")


def log_json(event: str, **kwargs) -> None:
    print(json.dumps({"event": event, "ts": time.time(), **kwargs}), flush=True)


# ── Valid test credentials ────────────────────────────────────────────────────
VALID_USERNAME = "insa"
VALID_PASSWORD = "1234"

# ── Account lock state — set by executor.py when HIDS sends lock_account ─────
_account_locked      = False          # True after admin clicks Lock Account
_locked_username     = ""            # which username was locked
_lock_reason         = ""            # reason message shown on login page
_lock: threading.Lock = threading.Lock()


def set_account_locked(username: str, reason: str = "Locked by HIDS administrator") -> None:
    """Called by executor.py after the OS account lock succeeds."""
    global _account_locked, _locked_username, _lock_reason
    with _lock:
        _account_locked  = True
        _locked_username = username
        _lock_reason     = reason
    log_json("account_locked_by_hids", username=username, reason=reason)


def clear_account_lock() -> None:
    """Called by executor.py if the account is unlocked (unlock_account command)."""
    global _account_locked, _locked_username, _lock_reason
    with _lock:
        _account_locked  = False
        _locked_username = ""
        _lock_reason     = ""
    log_json("account_lock_cleared")


def is_locked(username: str) -> bool:
    with _lock:
        return _account_locked and (
            _locked_username == "" or _locked_username == username
        )


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


# ── Account status endpoint — React page polls this ───────────────────────────
@app.route("/api/account-status")
def account_status():
    """
    GET /api/account-status?username=<user>
    Returns whether the account is currently locked.
    React LoginForm polls this every 2 s so it updates the moment
    the admin clicks Lock Account on the HIDS dashboard.
    """
    username = request.args.get("username", "").strip()
    locked   = is_locked(username) if username else _account_locked
    with _lock:
        reason = _lock_reason
    return jsonify({
        "locked": locked,
        "username": _locked_username,
        "reason": reason,
    })


# ── Login endpoint ────────────────────────────────────────────────────────────
@app.route("/api/login", methods=["POST"])
def login():
    """
    POST /api/login
    Body: { "username": str, "password": str }

    Returns:
      200  { "success": true,  "message": "Login successful" }
      401  { "success": false, "message": "Invalid credentials" }
      423  { "success": false, "message": "Account locked", "locked": true }
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

    # ── Account locked — reject immediately, no event forwarded ──────────────
    if is_locked(username):
        log_json("login_rejected_locked", username=username, source_ip=source_ip)
        with _lock:
            reason = _lock_reason
        return jsonify({
            "success": False,
            "locked":  True,
            "message": reason or "This account has been locked by the administrator.",
        }), 423   # HTTP 423 Locked

    # ── Correct credentials ───────────────────────────────────────────────────
    if username == VALID_USERNAME and password == VALID_PASSWORD:
        log_json("login_success", username=username, source_ip=source_ip)
        _forward_event(username=username, source_ip=source_ip, status="success")
        return jsonify({"success": True, "message": "Login successful"})

    # ── Wrong credentials ─────────────────────────────────────────────────────
    log_json("login_failure", username=username, source_ip=source_ip)
    _forward_event(username=username, source_ip=source_ip, status="fail")
    return jsonify({"success": False, "message": "Invalid credentials"}), 401


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
