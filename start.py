#!/usr/bin/env python3
"""
start.py — starts all HIDS services in separate cmd windows (Windows).

Run from the project root:
    py start.py

Each service gets its own window so logs stay separate.
Close a window to stop that service.
"""

import subprocess
import os
import time

ROOT = os.path.dirname(os.path.abspath(__file__))


def open_terminal(title: str, cwd: str, command: str) -> None:
    """Open a new cmd window, cd into cwd, and run command."""
    subprocess.Popen(
        ['cmd', '/c', 'start', title, 'cmd', '/k',
         f'cd /d "{cwd}" && {command}'],
    )


def main():
    print("Starting HIDS — opening service windows...\n")

    # ── 1. gRPC Analysis Server ─────────────────────────────────────────────
    open_terminal(
        "HIDS [1] gRPC Analysis Server",
        os.path.join(ROOT, "grpc_server"),
        "py server.py"
    )
    print("[1/5]  gRPC Analysis Server   port 50051")
    time.sleep(2)          # must be up before audit log connects

    # ── 2. Agent Node — gRPC command receiver ───────────────────────────────
    open_terminal(
        "HIDS [2] Agent Node",
        os.path.join(ROOT, "agent_node"),
        "py agent.py"
    )
    print("[2/5]  Agent Node             port 50052")
    time.sleep(1)

    # ── 3. Login Page — Flask + React UI ────────────────────────────────────
    open_terminal(
        "HIDS [3] Login Page",
        os.path.join(ROOT, "agent_node"),
        "py login_api.py"
    )
    print("[3/5]  Login Page             http://localhost:8080")
    time.sleep(1)

    # ── 4. Audit Log Service ─────────────────────────────────────────────────
    open_terminal(
        "HIDS [4] Audit Log Service",
        os.path.join(ROOT, "audit_log_service"),
        "py service.py"
    )
    print("[4/5]  Audit Log Service      inject port 8081")
    time.sleep(1)

    # ── 5. HIDS Node — Dashboard ─────────────────────────────────────────────
    open_terminal(
        "HIDS [5] Dashboard",
        os.path.join(ROOT, "hids_node"),
        "py app.py"
    )
    print("[5/5]  HIDS Dashboard         http://localhost:5000")

    print()
    print("=" * 54)
    print("  All services started in separate windows.")
    print()
    print("  Login page   ->  http://localhost:8080")
    print("  Dashboard    ->  http://localhost:5000")
    print()
    print("  To stop: close the individual cmd windows.")
    print("=" * 54)


if __name__ == "__main__":
    main()
