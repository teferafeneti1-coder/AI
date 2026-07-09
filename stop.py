#!/usr/bin/env python3
"""
stop.py — kills all HIDS Python processes.

Run from the project root:
    py stop.py
"""

import subprocess
import sys

SCRIPTS = [
    "server.py",
    "agent.py",
    "login_api.py",
    "service.py",
    "app.py",
]

def main():
    print("Stopping HIDS services...")
    for script in SCRIPTS:
        result = subprocess.run(
            ["taskkill", "/F", "/FI", f"WINDOWTITLE eq HIDS*",
             "/FI", f"IMAGENAME eq python.exe"],
            capture_output=True, text=True,
        )
    # Also kill by script name pattern
    result = subprocess.run(
        ["wmic", "process", "where",
         "name='python.exe'", "get", "processid,commandline"],
        capture_output=True, text=True,
    )
    killed = []
    for line in result.stdout.splitlines():
        for script in SCRIPTS:
            if script in line:
                parts = line.strip().split()
                pid = parts[-1]
                if pid.isdigit():
                    subprocess.run(["taskkill", "/F", "/PID", pid],
                                   capture_output=True)
                    killed.append(f"{script} (PID {pid})")
                    break

    if killed:
        for k in killed:
            print(f"  Stopped: {k}")
    else:
        print("  No running HIDS processes found.")
    print("Done.")


if __name__ == "__main__":
    main()
