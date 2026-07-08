"""
Detection rules for the HIDS Analysis Server.
Each rule is a standalone function that can be tested independently.
Add new rules here without touching transport or server code.
"""

import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Optional

# ──────────────────────────────────────────────────────────────────────────────
# Shared event state (in-memory sliding windows)
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class LoginEvent:
    username: str
    timestamp: float
    source_ip: str
    status: str  # "success" or "fail"
    attempt_id: str


class EventStore:
    """Lightweight in-memory store with configurable sliding-window retention."""

    def __init__(self, window_seconds: int = 300):
        self.window = window_seconds
        # All recent events in a deque ordered by arrival time
        self._events: deque[LoginEvent] = deque()

    def add(self, event: LoginEvent) -> None:
        self._events.append(event)
        self._prune()

    def recent(self) -> list[LoginEvent]:
        self._prune()
        return list(self._events)

    def _prune(self) -> None:
        cutoff = time.time() - self.window
        while self._events and self._events[0].timestamp < cutoff:
            self._events.popleft()


# Module-level shared store used by all rules
_store = EventStore(window_seconds=300)


def ingest(event: LoginEvent) -> None:
    """Feed a new event into the shared store before running rules."""
    _store.add(event)


# ──────────────────────────────────────────────────────────────────────────────
# Rule helpers
# ──────────────────────────────────────────────────────────────────────────────

def _make_alert(severity: str, attack_type: str, username: str,
                failed_attempts: int, description: str,
                source_ip: str = "") -> dict:
    return {
        "alert_id": str(uuid.uuid4()),
        "severity": severity,
        "attack_type": attack_type,
        "username": username,
        "failed_attempts": failed_attempts,
        "description": description,
        "timestamp": int(time.time()),
        "source_ip": source_ip,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Individual detection rules
# ──────────────────────────────────────────────────────────────────────────────

def rule_brute_force(events: list[LoginEvent],
                     threshold: int = 5,
                     window_seconds: int = 120) -> Optional[dict]:
    """
    Rule 1: ≥ threshold failed logins for the same username within window_seconds.
    Severity: HIGH
    """
    now = time.time()
    cutoff = now - window_seconds

    # Group failures by username
    by_user: dict[str, list[LoginEvent]] = defaultdict(list)
    for e in events:
        if e.status == "fail" and e.timestamp >= cutoff:
            by_user[e.username].append(e)

    for username, fails in by_user.items():
        if len(fails) >= threshold:
            ips = {e.source_ip for e in fails}
            return _make_alert(
                severity="HIGH",
                attack_type="brute_force",
                username=username,
                failed_attempts=len(fails),
                description=(
                    f"{len(fails)} failed login attempts for user '{username}' "
                    f"within {window_seconds}s from {len(ips)} IP(s)."
                ),
                source_ip=next(iter(ips)),
            )
    return None


def rule_ip_sweep(events: list[LoginEvent],
                  threshold: int = 10,
                  window_seconds: int = 120) -> Optional[dict]:
    """
    Rule 2: Repeated failures from the same source IP regardless of username.
    Severity: MEDIUM (threshold) → HIGH (2×threshold)
    """
    now = time.time()
    cutoff = now - window_seconds

    by_ip: dict[str, list[LoginEvent]] = defaultdict(list)
    for e in events:
        if e.status == "fail" and e.timestamp >= cutoff:
            by_ip[e.source_ip].append(e)

    for ip, fails in by_ip.items():
        if len(fails) >= threshold:
            severity = "HIGH" if len(fails) >= threshold * 2 else "MEDIUM"
            usernames = {e.username for e in fails}
            return _make_alert(
                severity=severity,
                attack_type="ip_sweep",
                username=",".join(sorted(usernames)),
                failed_attempts=len(fails),
                description=(
                    f"{len(fails)} failed logins from IP {ip} "
                    f"targeting {len(usernames)} account(s) within {window_seconds}s."
                ),
                source_ip=ip,
            )
    return None


def rule_credential_stuffing(events: list[LoginEvent],
                              min_users: int = 3,
                              threshold: int = 5,
                              window_seconds: int = 120) -> Optional[dict]:
    """
    Rule 3: Failures spread across ≥ min_users distinct usernames from the same IP
             → credential stuffing / password-spray pattern.
    Severity: CRITICAL
    """
    now = time.time()
    cutoff = now - window_seconds

    by_ip: dict[str, set[str]] = defaultdict(set)
    by_ip_count: dict[str, int] = defaultdict(int)
    for e in events:
        if e.status == "fail" and e.timestamp >= cutoff:
            by_ip[e.source_ip].add(e.username)
            by_ip_count[e.source_ip] += 1

    for ip, users in by_ip.items():
        if len(users) >= min_users and by_ip_count[ip] >= threshold:
            return _make_alert(
                severity="CRITICAL",
                attack_type="credential_stuffing",
                username=",".join(sorted(users)),
                failed_attempts=by_ip_count[ip],
                description=(
                    f"Credential stuffing detected from IP {ip}: "
                    f"{by_ip_count[ip]} failures across {len(users)} distinct accounts "
                    f"within {window_seconds}s."
                ),
                source_ip=ip,
            )
    return None


def rule_after_hours_login(events: list[LoginEvent],
                            start_hour: int = 22,
                            end_hour: int = 6) -> Optional[dict]:
    """
    Rule 4: Successful login during off-hours (after start_hour or before end_hour).
    Severity: LOW
    """
    import datetime
    for e in events:
        if e.status == "success":
            hour = datetime.datetime.fromtimestamp(e.timestamp).hour
            if hour >= start_hour or hour < end_hour:
                return _make_alert(
                    severity="LOW",
                    attack_type="after_hours_login",
                    username=e.username,
                    failed_attempts=0,
                    description=(
                        f"Successful login by '{e.username}' from {e.source_ip} "
                        f"at off-hours (hour={hour})."
                    ),
                    source_ip=e.source_ip,
                )
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Rule registry — add new rules here
# ──────────────────────────────────────────────────────────────────────────────

ALL_RULES = [
    rule_credential_stuffing,   # Most severe first
    rule_brute_force,
    rule_ip_sweep,
    rule_after_hours_login,
]


def evaluate(event: LoginEvent) -> list[dict]:
    """
    Ingest one event and evaluate all rules.
    Returns a (possibly empty) list of alert dicts.
    """
    ingest(event)
    events = _store.recent()
    alerts = []
    for rule in ALL_RULES:
        result = rule(events)
        if result:
            alerts.append(result)
    return alerts
