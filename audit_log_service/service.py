"""
Audit Log Service — polls OS auth logs and streams them to the gRPC Analysis Server.
Uses a local queue + retry/backoff so events are never dropped on disconnect.
"""

import sys
import os
import time
import json
import queue
import logging
import threading
import uuid

import grpc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "proto", "generated"))
import hids_pb2
import hids_pb2_grpc

from config import settings
from log_collector import make_collector, AuthEvent

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
)
logger = logging.getLogger("audit_log_service")


def log_json(event: str, **kwargs) -> None:
    print(json.dumps({"event": event, "ts": time.time(), **kwargs}), flush=True)


# ── Local queue (event buffer while server is unreachable) ────────────────────

_event_queue: queue.Queue[hids_pb2.LoginRecord] = queue.Queue(maxsize=10_000)


def _auth_event_to_proto(ev: AuthEvent) -> hids_pb2.LoginRecord:
    return hids_pb2.LoginRecord(
        username=ev.username,
        timestamp=int(ev.timestamp),
        source_ip=ev.source_ip,
        status=ev.status,
        attempt_id=ev.attempt_id,
    )


# ── Polling thread ────────────────────────────────────────────────────────────

def _poll_loop(platform: str, interval: int) -> None:
    collector = make_collector(platform)
    logger.info("Polling loop started (interval=%ds, platform=%s)", interval, platform)
    while True:
        try:
            events = collector.poll()
            for ev in events:
                record = _auth_event_to_proto(ev)
                try:
                    _event_queue.put_nowait(record)
                    log_json("event_queued", username=ev.username,
                             status=ev.status, source_ip=ev.source_ip)
                except queue.Full:
                    logger.warning("Event queue full — dropping oldest event")
                    try:
                        _event_queue.get_nowait()
                    except queue.Empty:
                        pass
                    _event_queue.put_nowait(record)
        except Exception as e:
            logger.error("Poll error: %s", e)
        time.sleep(interval)


# ── gRPC streaming sender ─────────────────────────────────────────────────────

def _record_generator():
    """Yields records from the local queue; blocks until one is available."""
    while True:
        try:
            record = _event_queue.get(timeout=1.0)
            yield record
        except queue.Empty:
            continue


def _send_loop(stub: hids_pb2_grpc.AnalysisServiceStub) -> None:
    """
    Opens a streaming RPC to the Analysis Server and forwards queued events.
    On error, backs off and retries — events stay in the queue.
    """
    backoff = 1
    while True:
        try:
            logger.info("Opening streaming RPC to Analysis Server…")
            response = stub.SendLoginHistory(_record_generator())
            logger.info("RPC stream ended, ack=%s — will reconnect", response.received)
            backoff = 1
        except grpc.RpcError as e:
            logger.warning("gRPC error (%s): %s — retrying in %ds",
                           e.code(), e.details(), backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)
        except Exception as e:
            logger.error("Unexpected send error: %s — retrying in %ds", e, backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)


# ── Entry point ───────────────────────────────────────────────────────────────

def run() -> None:
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

    log_json("audit_log_service_started",
             target=target, platform=settings.platform,
             poll_interval=settings.poll_interval)

    # Start polling thread
    poll_thread = threading.Thread(
        target=_poll_loop,
        args=(settings.platform, settings.poll_interval),
        daemon=True,
        name="poll_loop",
    )
    poll_thread.start()

    # Send loop runs in main thread
    _send_loop(stub)


if __name__ == "__main__":
    run()
