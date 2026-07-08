"""
HMAC-based command signing/verification for HIDS → Agent communication.
"""

import hashlib
import hmac
import json
import time

from config import settings


def sign_command(command_type: str, target_username: str, alert_id: str,
                 service_name: str = "") -> str:
    """
    Returns a hex HMAC-SHA256 signature over the command fields.
    Include timestamp in the payload to prevent replay attacks (±30s window).
    """
    payload = json.dumps({
        "command_type": command_type,
        "target_username": target_username,
        "alert_id": alert_id,
        "service_name": service_name,
        "ts": int(time.time()),   # coarse-grained to allow ±30 s drift
    }, sort_keys=True)

    sig = hmac.new(
        settings.hmac_secret.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    # Embed ts inside signature so the agent can re-derive it
    return f"{int(time.time())}:{sig}"


def verify_signature(signature: str, command_type: str, target_username: str,
                     alert_id: str, service_name: str = "",
                     tolerance_seconds: int = 30) -> bool:
    """
    Verify the HMAC signature on the agent side.
    Returns True if valid and within the time window.
    """
    try:
        ts_str, received_sig = signature.split(":", 1)
        ts = int(ts_str)
    except (ValueError, AttributeError):
        return False

    now = int(time.time())
    if abs(now - ts) > tolerance_seconds:
        return False

    payload = json.dumps({
        "command_type": command_type,
        "target_username": target_username,
        "alert_id": alert_id,
        "service_name": service_name,
        "ts": ts,
    }, sort_keys=True)

    expected = hmac.new(
        settings.hmac_secret.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, received_sig)
