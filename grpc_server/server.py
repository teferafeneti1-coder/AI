"""
gRPC Analysis Server — receives login streams, fires detection rules,
emits alerts to all subscribed HIDS clients.
"""

import sys
import os
import time
import queue
import logging
import json
import threading
from concurrent import futures

import grpc

# Generated stubs (added to path)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "proto", "generated"))
import hids_pb2
import hids_pb2_grpc

from config import settings
from rules import evaluate, LoginEvent
from database import init_db, save_alert

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
)
logger = logging.getLogger("grpc_server")


def log_json(event: str, **kwargs) -> None:
    print(json.dumps({"event": event, "ts": time.time(), **kwargs}), flush=True)


# ── Alert fan-out (subscribers) ───────────────────────────────────────────────

class AlertBroadcaster:
    """Thread-safe fan-out to all connected HIDS subscribers."""

    def __init__(self):
        self._lock = threading.Lock()
        self._subscribers: list[queue.Queue] = []

    def subscribe(self) -> queue.Queue:
        q: queue.Queue = queue.Queue()
        with self._lock:
            self._subscribers.append(q)
        logger.info("New HIDS subscriber (total=%d)", len(self._subscribers))
        return q

    def unsubscribe(self, q: queue.Queue) -> None:
        with self._lock:
            try:
                self._subscribers.remove(q)
            except ValueError:
                pass
        logger.info("HIDS subscriber disconnected (total=%d)", len(self._subscribers))

    def broadcast(self, alert: dict) -> None:
        with self._lock:
            for q in list(self._subscribers):
                try:
                    q.put_nowait(alert)
                except queue.Full:
                    pass


broadcaster = AlertBroadcaster()


# ── Deduplication window (suppress identical alerts within 30 s) ──────────────

_recent_alert_keys: dict[str, float] = {}
_DEDUP_WINDOW = 30.0


def _is_duplicate(alert: dict) -> bool:
    key = f"{alert['attack_type']}:{alert['username']}:{alert['source_ip']}"
    now = time.time()
    last = _recent_alert_keys.get(key)
    if last and (now - last) < _DEDUP_WINDOW:
        return True
    _recent_alert_keys[key] = now
    return False


# ── gRPC Servicer ─────────────────────────────────────────────────────────────

class AnalysisServiceServicer(hids_pb2_grpc.AnalysisServiceServicer):

    def SendLoginHistory(self, request_iterator, context):
        """
        Audit log node streams LoginRecord messages here.
        Each record is evaluated against all detection rules.
        """
        count = 0
        try:
            for record in request_iterator:
                count += 1
                event = LoginEvent(
                    username=record.username,
                    timestamp=record.timestamp or time.time(),
                    source_ip=record.source_ip,
                    status=record.status,
                    attempt_id=record.attempt_id,
                )
                log_json("login_record_received",
                         username=event.username,
                         source_ip=event.source_ip,
                         status=event.status)

                alerts = evaluate(event)
                for alert in alerts:
                    if _is_duplicate(alert):
                        log_json("alert_deduplicated", attack_type=alert["attack_type"])
                        continue
                    log_json("alert_generated", **alert)
                    save_alert(alert)
                    broadcaster.broadcast(alert)
        except Exception as e:
            logger.exception("Error in SendLoginHistory: %s", e)
        return hids_pb2.Ack(received=True)

    def SubscribeAlerts(self, request, context):
        """
        HIDS nodes call this to receive a live stream of alerts.
        Blocks until the client disconnects.
        """
        q = broadcaster.subscribe()
        try:
            while context.is_active():
                try:
                    alert = q.get(timeout=1.0)
                    yield hids_pb2.Alert(
                        alert_id=alert["alert_id"],
                        severity=alert["severity"],
                        attack_type=alert["attack_type"],
                        username=alert["username"],
                        failed_attempts=alert["failed_attempts"],
                        description=alert["description"],
                        timestamp=alert["timestamp"],
                        source_ip=alert.get("source_ip", ""),
                    )
                except queue.Empty:
                    continue
        finally:
            broadcaster.unsubscribe(q)


# ── Server bootstrap ──────────────────────────────────────────────────────────

def serve():
    init_db()

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=20),
        options=[
            ("grpc.max_send_message_length", 10 * 1024 * 1024),
            ("grpc.max_receive_message_length", 10 * 1024 * 1024),
            ("grpc.keepalive_time_ms", 30_000),
            ("grpc.keepalive_timeout_ms", 10_000),
        ],
    )
    hids_pb2_grpc.add_AnalysisServiceServicer_to_server(
        AnalysisServiceServicer(), server
    )
    bind_address = f"[::]:{settings.grpc_port}"
    server.add_insecure_port(bind_address)
    server.start()
    log_json("grpc_server_started", address=bind_address)
    logger.info("gRPC Analysis Server listening on %s", bind_address)
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server…")
        server.stop(grace=5)


if __name__ == "__main__":
    serve()
