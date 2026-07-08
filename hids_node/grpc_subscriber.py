"""
gRPC alert subscriber thread for the HIDS node.
Subscribes to the Analysis Server's SubscribeAlerts stream and dispatches:
  - Push alert to dashboard via websocket
  - Show desktop notification for HIGH/CRITICAL
  - Store in local DB + memory
"""

import sys
import os
import time
import json
import logging
import threading

import grpc
from plyer import notification

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "proto", "generated"))
import hids_pb2
import hids_pb2_grpc

from config import settings
from alert_store import store_alert

logger = logging.getLogger("grpc_subscriber")


def log_json(event: str, **kwargs) -> None:
    print(json.dumps({"event": event, "ts": time.time(), **kwargs}), flush=True)


# ── Global callback hook (set by Flask/SocketIO to broadcast alerts) ──────────

_alert_callback = None


def set_alert_callback(func):
    global _alert_callback
    _alert_callback = func


# ── Desktop notification ───────────────────────────────────────────────────────

def _notify(title: str, message: str) -> None:
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="HIDS",
            timeout=10,
        )
    except Exception as e:
        logger.warning("Desktop notification failed: %s", e)


# ── Subscriber loop ────────────────────────────────────────────────────────────

def _subscribe_loop(stub: hids_pb2_grpc.AnalysisServiceStub) -> None:
    backoff = 1
    while True:
        try:
            logger.info("Subscribing to alert stream from Analysis Server…")
            for alert in stub.SubscribeAlerts(hids_pb2.Empty()):
                alert_dict = {
                    "alert_id": alert.alert_id,
                    "severity": alert.severity,
                    "attack_type": alert.attack_type,
                    "username": alert.username,
                    "failed_attempts": alert.failed_attempts,
                    "description": alert.description,
                    "timestamp": alert.timestamp,
                    "source_ip": alert.source_ip,
                }
                log_json("alert_received", **alert_dict)

                # Persist + in-memory
                store_alert(alert_dict)

                # Desktop notification for HIGH/CRITICAL
                if alert.severity in ("HIGH", "CRITICAL"):
                    _notify(
                        title=f"{alert.severity} Alert: {alert.attack_type}",
                        message=f"{alert.username} — {alert.description[:80]}"
                    )

                # Push to dashboard (websocket broadcast)
                if _alert_callback:
                    _alert_callback(alert_dict)

            logger.warning("Alert stream ended — will reconnect")
            backoff = 1
        except grpc.RpcError as e:
            logger.warning("gRPC error (%s): %s — retrying in %ds",
                           e.code(), e.details(), backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)
        except Exception as e:
            logger.error("Unexpected subscriber error: %s — retrying in %ds", e, backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)


def start_subscriber() -> None:
    target = f"{settings.grpc_server_host}:{settings.grpc_server_port}"
    channel = grpc.insecure_channel(
        target,
        options=[
            ("grpc.keepalive_time_ms", 30_000),
            ("grpc.keepalive_timeout_ms", 10_000),
            ("grpc.keepalive_permit_without_calls", True),
        ],
    )
    stub = hids_pb2_grpc.AnalysisServiceStub(channel)
    t = threading.Thread(target=_subscribe_loop, args=(stub,), daemon=True)
    t.start()
    logger.info("Started gRPC alert subscriber thread (target=%s)", target)
