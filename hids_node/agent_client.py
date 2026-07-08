"""
gRPC client to send commands from HIDS to the Agent Node.
"""

import sys
import os
import logging

import grpc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "proto", "generated"))
import hids_pb2
import hids_pb2_grpc

from config import settings
from auth import sign_command

logger = logging.getLogger("agent_client")


def send_command(command_type: str, target_username: str, alert_id: str,
                 service_name: str = "") -> dict:
    """
    Sends an authenticated Command RPC to the Agent Node.
    Returns {"success": bool, "message": str}.
    """
    signature = sign_command(command_type, target_username, alert_id, service_name)
    target = f"{settings.agent_host}:{settings.agent_port}"

    try:
        with grpc.insecure_channel(target) as channel:
            stub = hids_pb2_grpc.AgentServiceStub(channel)
            cmd = hids_pb2.Command(
                command_type=command_type,
                target_username=target_username,
                alert_id=alert_id,
                signature=signature,
                service_name=service_name,
            )
            result = stub.ExecuteCommand(cmd, timeout=10)
            logger.info("Command %s → %s: success=%s, message=%s",
                        command_type, target, result.success, result.message)
            return {"success": result.success, "message": result.message}
    except grpc.RpcError as e:
        logger.error("gRPC error sending command to agent: %s", e.details())
        return {"success": False, "message": f"gRPC error: {e.details()}"}
    except Exception as e:
        logger.error("Unexpected error sending command to agent: %s", e)
        return {"success": False, "message": str(e)}
