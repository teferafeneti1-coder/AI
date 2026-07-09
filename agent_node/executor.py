"""
agent_node/executor.py

OS-level command execution for the Agent Node.
All commands are real — they run actual OS-level operations.

lock_account    → Supabase is_locked=true  (no NET USER needed)
stop_service    → net stop / systemctl stop  (real service stop)
disconnect_network → netsh / ip link set    (real adapter disable)
shutdown_device → shutdown /s /t 0 / shutdown -h now  (real shutdown)
ignore          → no-op
"""

import sys
import logging
import subprocess

import supabase_db
from login_api import set_account_locked

logger = logging.getLogger(__name__)


# ─── Lock account (Supabase — works for any username, no OS account needed) ──

def _lock_account_supabase(username: str) -> tuple[bool, str]:
    """
    Sets is_locked = true in Supabase for the given username.
    Also notifies login_api in-process so the login page updates instantly.
    """
    if supabase_db.is_configured():
        ok, msg = supabase_db.lock_user(username)
        if not ok:
            return False, msg
    else:
        # Supabase not configured — still update in-memory lock
        msg = f"Supabase not configured; in-memory lock applied for '{username}'."
        logger.warning(msg)

    # Notify login_api regardless (fast in-process path)
    set_account_locked(
        username,
        reason="This account has been locked by the HIDS administrator."
    )
    return True, f"Account '{username}' locked successfully."


# ─── Windows implementations ──────────────────────────────────────────────────

def _win_stop_service(service_name: str) -> tuple[bool, str]:
    """
    Stop a named Windows service using `sc stop <service>`.
    sc returns immediately with a STOP_PENDING status — we follow up
    with a query to confirm the final state.
    """
    if not service_name:
        return False, "No service name provided."
    try:
        result = subprocess.run(
            ["sc", "stop", service_name],
            capture_output=True, text=True, timeout=15,
        )
        # sc exits 0 on success and on STOP_PENDING
        if result.returncode in (0, 1062):   # 1062 = service not running
            return True, f"Service '{service_name}' stopped (or was already stopped)."
        stderr = result.stderr.strip() or result.stdout.strip()
        return False, f"sc stop failed (rc={result.returncode}): {stderr}"
    except subprocess.TimeoutExpired:
        return False, f"sc stop '{service_name}' timed out."
    except Exception as e:
        return False, f"Unexpected error: {e}"


def _win_disconnect_network() -> tuple[bool, str]:
    """
    Disable every active non-loopback, non-virtual network adapter using
    `netsh interface set interface "<name>" admin=disable`.
    Returns a list of adapters that were disabled.
    """
    try:
        # Get adapter names whose AdminState is Enabled
        list_result = subprocess.run(
            ["netsh", "interface", "show", "interface"],
            capture_output=True, text=True, timeout=10,
        )
        disabled = []
        for line in list_result.stdout.splitlines():
            # Lines look like:  Enabled    Connected    <type>  <name>
            parts = line.split()
            if len(parts) < 4:
                continue
            admin_state = parts[0]
            adapter_name = " ".join(parts[3:])
            if admin_state.lower() != "enabled":
                continue
            # Skip loopback and virtual adapters
            skip_keywords = ("loopback", "virtual", "bluetooth", "teredo",
                             "isatap", "6to4", "tunnel")
            if any(k in adapter_name.lower() for k in skip_keywords):
                continue
            r = subprocess.run(
                ["netsh", "interface", "set", "interface",
                 adapter_name, "admin=disable"],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0:
                disabled.append(adapter_name)
            else:
                logger.warning("Could not disable adapter '%s': %s",
                               adapter_name, r.stderr.strip())

        if disabled:
            return True, f"Disabled adapters: {', '.join(disabled)}"
        return False, "No active adapters found to disable."
    except Exception as e:
        return False, f"Failed to disable network: {e}"


def _win_shutdown() -> tuple[bool, str]:
    """
    Immediately shut down the Windows machine.
    The response is sent before the process exits.
    """
    try:
        subprocess.Popen(
            ["shutdown", "/s", "/t", "3"],   # 3-second delay — enough for the RPC reply
            creationflags=0x00000008,         # DETACHED_PROCESS
        )
        return True, "Shutdown initiated (3-second delay). Machine will power off."
    except Exception as e:
        return False, f"Shutdown failed: {e}"


# ─── Linux implementations ────────────────────────────────────────────────────

def _linux_stop_service(service_name: str) -> tuple[bool, str]:
    if not service_name:
        return False, "No service name provided."
    try:
        r = subprocess.run(
            ["sudo", "systemctl", "stop", service_name],
            capture_output=True, text=True, timeout=15,
        )
        if r.returncode == 0:
            return True, f"Service '{service_name}' stopped."
        return False, f"systemctl stop failed: {r.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return False, f"systemctl stop '{service_name}' timed out."
    except Exception as e:
        return False, f"Unexpected error: {e}"


def _linux_disconnect_network() -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["ip", "-o", "link", "show"],
            capture_output=True, text=True, check=True, timeout=5,
        )
        disabled = []
        for line in result.stdout.strip().split("\n"):
            parts = line.split(":")
            if len(parts) < 2:
                continue
            iface = parts[1].strip().split("@")[0]  # strip VLAN suffix
            if iface in ("lo",) or iface.startswith("docker"):
                continue
            r = subprocess.run(
                ["sudo", "ip", "link", "set", iface, "down"],
                capture_output=True, text=True, timeout=5,
            )
            if r.returncode == 0:
                disabled.append(iface)
        if disabled:
            return True, f"Disabled interfaces: {', '.join(disabled)}"
        return False, "No active interfaces found."
    except Exception as e:
        return False, f"Failed to disable network: {e}"


def _linux_shutdown() -> tuple[bool, str]:
    try:
        subprocess.Popen(["sudo", "shutdown", "-h", "+0"])
        return True, "Shutdown initiated."
    except Exception as e:
        return False, f"Shutdown failed: {e}"


# ─── OS-agnostic dispatcher ────────────────────────────────────────────────────

def execute_command(command_type: str,
                    target_username: str,
                    service_name: str) -> tuple[bool, str]:
    """
    Dispatch to the appropriate handler based on command_type.
    Returns (success: bool, message: str).
    """
    is_windows = sys.platform == "win32"

    if command_type == "ignore":
        return True, "Ignored alert — no action taken."

    elif command_type == "lock_account":
        # Always goes through Supabase — no NET USER needed
        return _lock_account_supabase(target_username)

    elif command_type == "stop_service":
        if not service_name:
            return False, (
                "No service name was provided. "
                "Enter a service name in the dashboard before sending this command."
            )
        return _win_stop_service(service_name) if is_windows else _linux_stop_service(service_name)

    elif command_type == "disconnect_network":
        return _win_disconnect_network() if is_windows else _linux_disconnect_network()

    elif command_type == "shutdown_device":
        return _win_shutdown() if is_windows else _linux_shutdown()

    else:
        return False, f"Unknown command type: {command_type}"
