#!/usr/bin/env python3
"""
stop.py — kills all HIDS Python processes on Windows.

Run from the project root:
    py stop.py
"""

import subprocess
import sys

# Script filenames that identify HIDS processes
HIDS_SCRIPTS = ["server.py", "agent.py", "login_api.py", "service.py", "app.py"]


def get_python_processes() -> list[dict]:
    """
    Use 'tasklist /V /FO CSV' to get all running processes with window titles,
    then filter for python.exe entries.
    """
    result = subprocess.run(
        ["tasklist", "/FO", "CSV", "/V"],
        capture_output=True, text=True, errors="replace"
    )
    processes = []
    for line in result.stdout.splitlines():
        if '"python.exe"' in line.lower() or '"py.exe"' in line.lower():
            parts = [p.strip('"') for p in line.split('","')]
            if len(parts) >= 2:
                pid = parts[1]
                title = parts[-1] if len(parts) > 1 else ""
                if pid.isdigit():
                    processes.append({"pid": pid, "title": title})
    return processes


def kill_pid(pid: str) -> bool:
    result = subprocess.run(
        ["taskkill", "/F", "/PID", pid],
        capture_output=True, text=True
    )
    return result.returncode == 0


def main():
    print("Stopping HIDS services...\n")

    # Strategy 1: kill by window title prefix "HIDS"
    r = subprocess.run(
        ["taskkill", "/F", "/FI", "WINDOWTITLE eq HIDS*"],
        capture_output=True, text=True
    )
    if "SUCCESS" in r.stdout:
        for line in r.stdout.splitlines():
            if "SUCCESS" in line:
                print(f"  Stopped: {line.strip()}")

    # Strategy 2: kill python.exe processes whose window title contains HIDS script names
    procs = get_python_processes()
    killed = []
    for proc in procs:
        title = proc["title"].lower()
        for script in HIDS_SCRIPTS:
            if script.lower() in title or "hids" in title:
                if kill_pid(proc["pid"]):
                    killed.append(f"PID {proc['pid']} ({proc['title']})")
                break

    if killed:
        for k in killed:
            print(f"  Stopped: {k}")

    # Strategy 3: forcibly close all HIDS-titled cmd windows
    subprocess.run(
        ['cmd', '/c',
         'taskkill /F /FI "WINDOWTITLE eq HIDS*" /T'],
        capture_output=True
    )

    if not killed and "SUCCESS" not in r.stdout:
        print("  No HIDS processes found running.")
        print("  If services are still open, close the cmd windows manually.")

    print("\nDone.")


if __name__ == "__main__":
    main()
