"""
agent_node/login_api.py

Lightweight Flask HTTP API served on the Agent Node machine.
Accepts login attempts from the React login page, validates credentials,
and forwards every event into the Audit Log Service inject endpoint so it
travels through the normal pipeline:

  React form  →  POST /api/login  (this file, port 8080)
                     │
                     ▼
              audit_log_service/inject_api.py  (port 8081)
                     │  HTTP POST /inject
                     ▼
              _event_queue  (same queue service.py reads)
                     │  gRPC stream
                     ▼
              grpc_server/server.py  →  rules.py  →  Alert
                     │  SubscribeAlerts stream
                     ▼
              hids_node dashboard  (port 5000)
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

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder="login_ui/dist", static_url_path="")
CORS(app, resources={r"/api/*": {"origins": "*"}})


# ── Serve React build at root ─────────────────────────────────────────────────
@app.route("/")
@app.route("/<path:path>")
def serve_frontend(path=""):
    """Serve the React build. Falls back to index.html for client-side routing."""
    dist = os.path.join(os.path.dirname(__file__), "login_ui", "dist")
    target = os.path.join(dist, path)
    if path and os.path.exists(target):
        return app.send_static_file(path)
    return app.send_static_file("index.html")


# ── Login endpoint ────────────────────────────────────────────────────────────
@app.route("/api/login", methods=["POST"])
def login():
    """
    POST /api/login
    Body: { "username": str, "password": str }

    Returns:
      200  { "success": true,  "message": "Login successful" }
      401  { "success": false, "message": "Invalid credentials" }

    Side-effect on failure: forwards a LoginRecord to the Audit Log
    inject endpoint so rule_brute_force can detect repeated failures.
    """
    data     = request.get_json(force=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    # Capture submitter's IP (X-Forwarded-For if behind proxy, else direct)
    source_ip = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.remote_addr
        or "0.0.0.0"
    )

    if not username:
        return jsonify({"success": False, "message": "Username is required"}), 400

    # ── Correct credentials ───────────────────────────────────────────────────
    if username == VALID_USERNAME and password == VALID_PASSWORD:
        log_json("login_success", username=username, source_ip=source_ip)
        _forward_event(username=username, source_ip=source_ip, status="success")
        return jsonify({"success": True, "message": "Login successful"})

    # ── Wrong credentials — forward a failure event ───────────────────────────
    log_json("login_failure", username=username, source_ip=source_ip)
    _forward_event(username=username, source_ip=source_ip, status="fail")
    return jsonify({"success": False, "message": "Invalid credentials"}), 401


# ── Forward event to Audit Log inject endpoint ────────────────────────────────

def _forward_event(username: str, source_ip: str, status: str) -> None:
    """
    Sends a login event to audit_log_service/inject_api.py via HTTP.
    Non-blocking (fire-and-forget in a daemon thread) so the login
    response is never delayed by network issues.
    """
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
            log_json("event_forwarded", url=url, status_code=resp.status_code,
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
