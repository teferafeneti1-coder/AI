"""
OS-level command execution for the Agent Node.
Lock accounts, kill processes, disable network adapters, shutdown, etc.
"""

import sys
import logging
import subprocess

logger = logging.getLogger(__name__)


def _notify_login_api_locked(username: str) -> None:
    """
    Tell login_api.py that this account is now OS-locked so the
    login page immediately shows 'Account Locked' without needing
    a page refresh. Uses a direct in-process call if running together,
    or falls back silently if running separately.
    """
    try:
        from login_api import set_account_locked
        set_account_locked(
            username,
            reason="This account has been locked by the HIDS administrator."
        )
    except Exception as e:
        logger.warning("Could not notify login_api of lock: %s", e)


# ─── Windows implementations ─────────────────────────────────────────────────

def _win_lock_account(username: str) -> tuple[bool, str]:
    """
    Lock/disable a Windows user account via `net user <user> /active:no`.
    Also notifies login_api so the login page shows "Account Locked".
    """
    try:
        subprocess.run(
            ["net", "user", username, "/active:no"],
            check=True,
            capture_output=True,
            text=True,
        )
        _notify_login_api_locked(username)
        return True, f"Account '{username}' locked successfully."
    except subprocess.CalledProcessError as e:
        return False, f"Failed to lock account: {e.stderr.strip()}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def _win_stop_service(service_name: str) -> tuple[bool, str]:
    """
    Stop a Windows service by name using `net stop <service>`.
    """
    if not service_name:
        return False, "No service name provided."
    try:
        subprocess.run(
            ["net", "stop", service_name],
            check=True,
            capture_output=True,
            text=True,
        )
        return True, f"Service '{service_name}' stopped."
    except subprocess.CalledProcessError as e:
        return False, f"Failed to stop service: {e.stderr.strip()}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def _win_disconnect_network() -> tuple[bool, str]:
    """
    Disable all network adapters (non-loopback).
    Uses PowerShell: Get-NetAdapter | Where-Object { $_.Name -notlike '*Loopback*' } | Disable-NetAdapter -Confirm:$false
    """
    try:
        ps_script = (
            "Get-NetAdapter | Where-Object { $_.Status -eq 'Up' -and $_.Name -notlike '*Loopback*' } "
            "| Disable-NetAdapter -Confirm:$false"
        )
        subprocess.run(
            ["powershell", "-Command", ps_script],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return True, "Network adapters disabled successfully."
    except subprocess.CalledProcessError as e:
        return False, f"Failed to disable network: {e.stderr.strip()}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def _win_shutdown() -> tuple[bool, str]:
    """
    Shutdown the Windows machine immediately.
    """
    try:
        subprocess.run(
            ["shutdown", "/s", "/t", "0"],
            check=True,
            capture_output=True,
            text=True,
        )
        return True, "Shutdown command issued."
    except Exception as e:
        return False, f"Shutdown failed: {e}"


# ─── Linux implementations ────────────────────────────────────────────────────

def _linux_lock_account(username: str) -> tuple[bool, str]:
    """
    Lock a Linux user account using `passwd -l <user>`.
    Also notifies login_api so the login page shows "Account Locked".
    """
    try:
        subprocess.run(
            ["sudo", "passwd", "-l", username],
            check=True,
            capture_output=True,
            text=True,
        )
        _notify_login_api_locked(username)
        return True, f"Account '{username}' locked."
    except subprocess.CalledProcessError as e:
        return False, f"Failed to lock account: {e.stderr.strip()}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def _linux_stop_service(service_name: str) -> tuple[bool, str]:
    """
    Stop a systemd service: `systemctl stop <service>`.
    """
    if not service_name:
        return False, "No service name provided."
    try:
        subprocess.run(
            ["sudo", "systemctl", "stop", service_name],
            check=True,
            capture_output=True,
            text=True,
        )
        return True, f"Service '{service_name}' stopped."
    except subprocess.CalledProcessError as e:
        return False, f"Failed to stop service: {e.stderr.strip()}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def _linux_disconnect_network() -> tuple[bool, str]:
    """
    Disable all non-loopback network interfaces via `ip link set <iface> down`.
    """
    try:
        # List all interfaces
        result = subprocess.run(
            ["ip", "-o", "link", "show"],
            capture_output=True,
            text=True,
            check=True,
        )
        lines = result.stdout.strip().split("\n")
        disabled = []
        for line in lines:
            parts = line.split(":")
            if len(parts) < 2:
                continue
            iface = parts[1].strip()
            if iface == "lo":
                continue
            subprocess.run(
                ["sudo", "ip", "link", "set", iface, "down"],
                check=True,
                capture_output=True,
                text=True,
            )
            disabled.append(iface)
        return True, f"Disabled interfaces: {', '.join(disabled)}"
    except Exception as e:
        return False, f"Failed to disable network: {e}"


def _linux_shutdown() -> tuple[bool, str]:
    """
    Shutdown the Linux machine immediately: `shutdown -h now`.
    """
    try:
        subprocess.run(
            ["sudo", "shutdown", "-h", "now"],
            check=True,
            capture_output=True,
            text=True,
        )
        return True, "Shutdown command issued."
    except Exception as e:
        return False, f"Shutdown failed: {e}"


# ─── OS-agnostic dispatcher ────────────────────────────────────────────────────

def execute_command(command_type: str, target_username: str, service_name: str) -> tuple[bool, str]:
    """
    Dispatch to the appropriate OS-level function based on command_type.
    Returns (success: bool, message: str).
    """
    is_windows = sys.platform == "win32"

    if command_type == "ignore":
        return True, "Ignored alert — no action taken."

    elif command_type == "lock_account":
        if is_windows:
            return _win_lock_account(target_username)
        else:
            return _linux_lock_account(target_username)

    elif command_type == "stop_service":
        if is_windows:
            return _win_stop_service(service_name)
        else:
            return _linux_stop_service(service_name)

    elif command_type == "disconnect_network":
        if is_windows:
            return _win_disconnect_network()
        else:
            return _linux_disconnect_network()

    elif command_type == "shutdown_device":
        if is_windows:
            return _win_shutdown()
        else:
            return _linux_shutdown()

    else:
        return False, f"Unknown command type: {command_type}"
