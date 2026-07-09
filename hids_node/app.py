"""
HIDS Node — Flask + SocketIO dashboard with live alert streaming.
"""

import sys
import os
import time
import json
import logging

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

from config import settings
from alert_store import init_db, get_recent, get_history, get_system_status
from grpc_subscriber import start_subscriber, set_alert_callback
from agent_client import send_command

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
)
logger = logging.getLogger("hids_node")


def log_json(event: str, **kwargs) -> None:
    print(json.dumps({"event": event, "ts": time.time(), **kwargs}), flush=True)


# ── Flask + SocketIO ──────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = settings.hmac_secret
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")


def push_alert_to_clients(alert: dict) -> None:
    """Called by the subscriber thread when a new alert arrives."""
    socketio.emit("new_alert", alert, namespace="/")


# Wire up the callback before starting
set_alert_callback(push_alert_to_clients)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    status = get_system_status()
    recent = get_recent(limit=20)
    current_alert = recent[0] if recent else None
    return render_template(
        "dashboard.html",
        status=status,
        current_alert=current_alert,
        recent_alerts=recent,
    )


@app.route("/api/alerts")
def api_alerts():
    severity = request.args.get("severity")
    username = request.args.get("username")
    since = request.args.get("since", type=int)
    alerts = get_history(limit=200, severity=severity,
                         username=username, since=since)
    return jsonify(alerts)


@app.route("/api/status")
def api_status():
    return jsonify({"status": get_system_status()})


@app.route("/api/test/login-event", methods=["POST"])
def api_test_login_event():
    """
    Accepts synthetic login events from the React test dashboard and
    forwards them into the HIDS pipeline by inserting directly into the
    alert evaluation path via the analysis server.

    POST body: { "username": str, "source_ip": str, "status": "success"|"fail" }
    """
    import sys
    import os
    import time
    import uuid as uuid_mod

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "proto", "generated"))
    import hids_pb2
    import hids_pb2_grpc
    import grpc

    data = request.get_json(force=True) or {}
    username = data.get("username", "unknown").strip()
    source_ip = data.get("source_ip", "127.0.0.1").strip()
    status = data.get("status", "fail").strip()

    if status not in ("success", "fail"):
        return jsonify({"ok": False, "error": "status must be success or fail"}), 400

    log_json("test_event_received", username=username,
             source_ip=source_ip, status=status)

    # Forward to analysis server as a real LoginRecord stream
    target = f"{settings.grpc_server_host}:{settings.grpc_server_port}"
    try:
        channel = grpc.insecure_channel(target)
        stub = hids_pb2_grpc.AnalysisServiceStub(channel)
        record = hids_pb2.LoginRecord(
            username=username,
            timestamp=int(time.time()),
            source_ip=source_ip,
            status=status,
            attempt_id=str(uuid_mod.uuid4()),
        )
        stub.SendLoginHistory(iter([record]), timeout=5)
        channel.close()
        return jsonify({"ok": True})
    except Exception as e:
        # Non-fatal — test dashboard works standalone even if backend is down
        log_json("test_event_forward_failed", error=str(e))
        return jsonify({"ok": False, "error": str(e)}), 503


@app.route("/api/command", methods=["POST"])
def api_command():
    """
    POST body: {
        "command_type": str,
        "target_username": str,
        "alert_id": str,
        "service_name": str   (optional)
    }
    """
    data = request.get_json(force=True) or {}
    command_type = data.get("command_type", "").strip()
    target_username = data.get("target_username", "").strip()
    alert_id = data.get("alert_id", "").strip()
    service_name = data.get("service_name", "").strip()

    allowed = {"ignore", "lock_account", "unlock_account", "stop_service",
                "disconnect_network", "shutdown_device"}
    if command_type not in allowed:
        return jsonify({"success": False, "message": "Unknown command type"}), 400

    log_json("command_dispatched",
             command_type=command_type,
             target_username=target_username,
             alert_id=alert_id)

    result = send_command(command_type, target_username, alert_id, service_name)
    return jsonify(result)


# ── SocketIO events ───────────────────────────────────────────────────────────

@socketio.on("connect")
def on_connect():
    logger.info("Dashboard client connected")
    # Send recent alerts to newly connected client
    recent = get_recent(limit=20)
    for alert in reversed(recent):
        emit("new_alert", alert)


# ── Bootstrap ─────────────────────────────────────────────────────────────────

def main():
    init_db()
    start_subscriber()
    log_json("hids_node_started",
             web_host=settings.web_host,
             web_port=settings.web_port)
    socketio.run(
        app,
        host=settings.web_host,
        port=settings.web_port,
        debug=False,
        use_reloader=False,
        allow_unsafe_werkzeug=True,
    )


if __name__ == "__main__":
    main()
