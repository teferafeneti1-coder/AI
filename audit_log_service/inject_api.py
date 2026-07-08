"""
audit_log_service/inject_api.py

Tiny HTTP server that lets external callers (the Agent Node login_api)
inject login events directly into the same _event_queue that service.py
streams to the gRPC Analysis Server.

This means a failed login submitted via the React form enters the pipeline
at exactly the same point as an OS-collected auth event — no new detection
logic is needed. rule_brute_force fires after 5 failures just as normal.

Pipeline after injection:
  HTTP POST /inject  →  _event_queue  →  gRPC stream  →  rules.py  →  Alert
                         (shared with service.py)

Run this alongside service.py:
  py inject_api.py      (port 8081 by default)
  py service.py         (streams the queue to gRPC)
"""

import sys
import os
import time
import json
import uuid
import logging

from flask import Flask, request, jsonify
from flask_cors import CORS

# ── Import the shared queue from service.py ───────────────────────────────────
# We import _event_queue and the proto builder directly so both processes
# share the exact same in-memory queue when run in the same Python process,
# OR when run as separate processes we use a loopback HTTP call (see service.py).
# Here we use the simpler approach: inject_api runs in the SAME process as
# service.py by importing service and calling its public inject function.

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "proto", "generated"))
import hids_pb2

# We'll import the queue reference after service module is available
# (inject_api is started from run.py which imports both)
_queue_ref = None  # set by set_queue() called from run.py


def set_queue(q):
    global _queue_ref
    _queue_ref = q


# ── Settings ──────────────────────────────────────────────────────────────────
try:
    from config import settings as _cfg
    INJECT_PORT = _cfg.__class__.__fields__.get("inject_port") and _cfg.inject_port or 8081
except Exception:
    INJECT_PORT = int(os.environ.get("INJECT_PORT", "8081"))

INJECT_HOST = os.environ.get("INJECT_HOST", "0.0.0.0")
INJECT_PORT = int(os.environ.get("INJECT_PORT", "8081"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("inject_api")


def log_json(event: str, **kwargs) -> None:
    print(json.dumps({"event": event, "ts": time.time(), **kwargs}), flush=True)


# ── Flask ─────────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, resources={r"/inject": {"origins": "*"}})


@app.route("/inject", methods=["POST"])
def inject():
    """
    POST /inject
    Body: {
        "username":   str,
        "source_ip":  str,
        "status":     "success" | "fail",
        "timestamp":  int   (unix, optional — defaults to now),
        "attempt_id": str   (optional — auto-generated if missing)
    }
    Drops the event straight into the audit log queue.
    """
    if _queue_ref is None:
        return jsonify({"ok": False, "error": "queue not initialised"}), 503

    data       = request.get_json(force=True) or {}
    username   = data.get("username", "unknown").strip()
    source_ip  = data.get("source_ip", "0.0.0.0").strip()
    status     = data.get("status", "fail").strip()
    timestamp  = int(data.get("timestamp") or time.time())
    attempt_id = data.get("attempt_id") or str(uuid.uuid4())

    if status not in ("success", "fail"):
        return jsonify({"ok": False, "error": "status must be 'success' or 'fail'"}), 400

    record = hids_pb2.LoginRecord(
        username=username,
        timestamp=timestamp,
        source_ip=source_ip,
        status=status,
        attempt_id=attempt_id,
    )

    try:
        _queue_ref.put_nowait(record)
        log_json("event_injected",
                 username=username, source_ip=source_ip, status=status)
        return jsonify({"ok": True})
    except Exception as exc:
        logger.error("Queue put failed: %s", exc)
        return jsonify({"ok": False, "error": str(exc)}), 500


def run(queue, host: str = "0.0.0.0", port: int = 8081):
    set_queue(queue)
    log_json("inject_api_started", host=host, port=port)
    app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)
