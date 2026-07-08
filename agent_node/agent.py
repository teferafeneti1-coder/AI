"""
Agent Node — gRPC server that receives and executes authenticated commands from HIDS.
"""

import sys
import os
import time
import json
import logging
from concurrent import futures

import grpc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "proto", "generated"))
import hids_pb2
import hids_pb2_grpc

from config import settings
from auth import verify_signature
from executor import execute_command

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
)
logger = logging.getLogger("agent_node")


def log_json(event: str, **kwargs) -> None:
    print(json.dumps({"event": event, "ts": time.time(), **kwargs}), flush=True)


# ── gRPC Servicer ─────────────────────────────────────────────────────────────

class AgentServiceServicer(hids_pb2_grpc.AgentServiceServicer):

    def ExecuteCommand(self, request, context):
        """
        Receive, verify, and execute a signed command from the HIDS node.
        """
        log_json("command_received",
                 command_type=request.command_type,
                 target_username=request.target_username,
                 alert_id=request.alert_id,
                 has_signature=bool(request.signature))

        # ── Auth check ──────────────────────────────────────────────────────
        valid = verify_signature(
            signature=request.signature,
            command_type=request.command_type,
            target_username=request.target_username,
            alert_id=request.alert_id,
            service_name=request.service_name,
        )
        if not valid:
            log_json("command_rejected",
                     reason="invalid_signature",
                     command_type=request.command_type)
            logger.warning("Rejected command with invalid signature: %s",
                           request.command_type)
            return hids_pb2.CommandResult(
                success=False,
                message="Rejected: invalid or expired HMAC signature.",
                alert_id=request.alert_id,
            )

        # ── Execute ─────────────────────────────────────────────────────────
        try:
            success, message = execute_command(
                command_type=request.command_type,
                target_username=request.target_username,
                service_name=request.service_name,
            )
            log_json("command_executed",
                     command_type=request.command_type,
                     success=success,
                     message=message)
            return hids_pb2.CommandResult(
                success=success,
                message=message,
                alert_id=request.alert_id,
            )
        except Exception as e:
            logger.exception("Error executing command: %s", e)
            return hids_pb2.CommandResult(
                success=False,
                message=f"Execution error: {e}",
                alert_id=request.alert_id,
            )


# ── Server bootstrap ──────────────────────────────────────────────────────────

def serve():
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ("grpc.keepalive_time_ms", 30_000),
            ("grpc.keepalive_timeout_ms", 10_000),
        ],
    )
    hids_pb2_grpc.add_AgentServiceServicer_to_server(
        AgentServiceServicer(), server
    )
    bind_address = f"[::]:{settings.agent_port}"
    server.add_insecure_port(bind_address)
    server.start()
    log_json("agent_node_started", address=bind_address)
    logger.info("Agent Node listening on %s", bind_address)
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down Agent…")
        server.stop(grace=5)


if __name__ == "__main__":
    serve()
