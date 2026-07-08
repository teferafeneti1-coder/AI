"""
HMAC-based signature verification on the Agent Node.
"""

import hashlib
import hmac
import json
import time

from config import settings


def verify_signature(signature: str, command_type: str, target_username: str,
                     alert_id: str, service_name: str = "",
                     tolerance_seconds: int = 30) -> bool:
    """
    Verify the HMAC signature sent by HIDS.
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
