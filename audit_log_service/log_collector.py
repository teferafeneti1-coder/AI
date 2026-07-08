"""
OS-agnostic log collector interface.
Implementations: WindowsLogCollector, LinuxLogCollector, SimulatedLogCollector.
Auto-selects based on platform if PLATFORM=auto.
"""

import abc
import sys
import time
import uuid
import re
import logging
from dataclasses import dataclass, field
from typing import Iterator

logger = logging.getLogger(__name__)


@dataclass
class AuthEvent:
    username: str
    timestamp: float
    source_ip: str
    status: str   # "success" | "fail"
    attempt_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class BaseLogCollector(abc.ABC):
    """Abstract base — subclasses yield new AuthEvent objects on each poll."""

    @abc.abstractmethod
    def poll(self) -> list[AuthEvent]:
        """Return new events since the last call."""
        ...


# ── Windows collector ─────────────────────────────────────────────────────────

class WindowsLogCollector(BaseLogCollector):
    """
    Reads Windows Security Event Log.
    Event IDs:
      4624 - successful logon
      4625 - failed logon
    """

    def __init__(self):
        import win32evtlog  # type: ignore
        self._win32evtlog = win32evtlog
        self._server = "localhost"
        self._log_type = "Security"
        self._last_record_number: int = 0
        # Seed with current last record so we only pick up NEW events
        self._seed()

    def _seed(self):
        try:
            handle = self._win32evtlog.OpenEventLog(self._server, self._log_type)
            flags = (self._win32evtlog.EVENTLOG_BACKWARDS_READ |
                     self._win32evtlog.EVENTLOG_SEQUENTIAL_READ)
            events = self._win32evtlog.ReadEventLog(handle, flags, 0)
            if events:
                self._last_record_number = events[0].RecordNumber
            self._win32evtlog.CloseEventLog(handle)
        except Exception as e:
            logger.warning("Could not seed Windows event log: %s", e)

    def poll(self) -> list[AuthEvent]:
        import win32evtlog  # type: ignore
        results: list[AuthEvent] = []
        try:
            handle = win32evtlog.OpenEventLog(self._server, self._log_type)
            flags = (win32evtlog.EVENTLOG_FORWARDS_READ |
                     win32evtlog.EVENTLOG_SEQUENTIAL_READ)
            while True:
                events = win32evtlog.ReadEventLog(handle, flags, 0)
                if not events:
                    break
                for ev in events:
                    if ev.RecordNumber <= self._last_record_number:
                        continue
                    self._last_record_number = ev.RecordNumber
                    event_id = ev.EventID & 0xFFFF
                    if event_id not in (4624, 4625):
                        continue
                    status = "success" if event_id == 4624 else "fail"
                    data = ev.StringInserts or []
                    username = data[5] if len(data) > 5 else "unknown"
                    source_ip = data[18] if len(data) > 18 else "0.0.0.0"
                    if username.endswith("$") or username == "-":
                        continue  # skip machine and null accounts
                    results.append(AuthEvent(
                        username=username,
                        timestamp=ev.TimeGenerated.timestamp(),
                        source_ip=source_ip,
                        status=status,
                    ))
            win32evtlog.CloseEventLog(handle)
        except Exception as e:
            logger.error("Windows event log read error: %s", e)
        return results


# ── Linux collector ───────────────────────────────────────────────────────────

class LinuxLogCollector(BaseLogCollector):
    """
    Tails /var/log/auth.log for sshd Accepted/Failed entries.
    """

    AUTH_LOG = "/var/log/auth.log"
    # Patterns for sshd lines
    _FAIL_RE = re.compile(
        r"Failed (?:password|publickey) for (?:invalid user )?(\S+) from ([\d.:]+)"
    )
    _SUCCESS_RE = re.compile(
        r"Accepted (?:password|publickey) for (\S+) from ([\d.:]+)"
    )
    _INVALID_RE = re.compile(
        r"Invalid user (\S+) from ([\d.:]+)"
    )

    def __init__(self):
        self._file_pos: int = 0
        # Seek to end so we only collect new lines
        try:
            with open(self.AUTH_LOG, "r", errors="replace") as f:
                f.seek(0, 2)
                self._file_pos = f.tell()
        except FileNotFoundError:
            logger.warning("%s not found; will retry on next poll", self.AUTH_LOG)

    def poll(self) -> list[AuthEvent]:
        results: list[AuthEvent] = []
        try:
            with open(self.AUTH_LOG, "r", errors="replace") as f:
                f.seek(self._file_pos)
                for line in f:
                    results.extend(self._parse_line(line))
                self._file_pos = f.tell()
        except FileNotFoundError:
            logger.warning("%s not found", self.AUTH_LOG)
        except Exception as e:
            logger.error("Linux auth log read error: %s", e)
        return results

    def _parse_line(self, line: str) -> list[AuthEvent]:
        events = []
        now = time.time()

        m = self._FAIL_RE.search(line)
        if m:
            events.append(AuthEvent(
                username=m.group(1),
                timestamp=now,
                source_ip=m.group(2),
                status="fail",
            ))
            return events

        m = self._INVALID_RE.search(line)
        if m:
            events.append(AuthEvent(
                username=m.group(1),
                timestamp=now,
                source_ip=m.group(2),
                status="fail",
            ))
            return events

        m = self._SUCCESS_RE.search(line)
        if m:
            events.append(AuthEvent(
                username=m.group(1),
                timestamp=now,
                source_ip=m.group(2),
                status="success",
            ))
        return events


# ── Simulated collector (for demo / CI) ───────────────────────────────────────

class SimulatedLogCollector(BaseLogCollector):
    """
    Generates synthetic auth events for demo and testing purposes.
    Uses simple round-robin cycling so the demo always shows activity.
    """

    SCENARIOS = [
        ("alice", "192.168.1.100", "fail"),
        ("alice", "192.168.1.100", "fail"),
        ("alice", "192.168.1.100", "fail"),
        ("alice", "192.168.1.100", "fail"),
        ("alice", "192.168.1.100", "fail"),
        ("bob", "10.0.0.50", "success"),
        ("carol", "172.16.0.1", "fail"),
        ("dave", "172.16.0.1", "fail"),
        ("eve", "172.16.0.1", "fail"),   # triggers credential_stuffing
        ("frank", "10.10.10.10", "fail"),
        ("frank", "10.10.10.10", "fail"),
        ("frank", "10.10.10.10", "fail"),
    ]

    def __init__(self):
        self._idx = 0

    def poll(self) -> list[AuthEvent]:
        username, source_ip, status = self.SCENARIOS[self._idx % len(self.SCENARIOS)]
        self._idx += 1
        return [AuthEvent(
            username=username,
            timestamp=time.time(),
            source_ip=source_ip,
            status=status,
        )]


# ── Factory ───────────────────────────────────────────────────────────────────

def make_collector(platform: str = "auto") -> BaseLogCollector:
    if platform == "auto":
        platform = "windows" if sys.platform == "win32" else "linux"
    if platform == "windows":
        logger.info("Using Windows event log collector")
        return WindowsLogCollector()
    elif platform == "linux":
        logger.info("Using Linux auth.log collector")
        return LinuxLogCollector()
    elif platform == "simulated":
        logger.info("Using simulated log collector")
        return SimulatedLogCollector()
    else:
        raise ValueError(f"Unknown platform: {platform}")
