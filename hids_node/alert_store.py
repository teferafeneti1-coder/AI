"""
In-memory + SQLite alert store for the HIDS dashboard.
"""

import sqlite3
import threading
import time
import logging
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger(__name__)
DB_PATH = "./hids_alerts.db"

_lock = threading.Lock()
# In-memory ring buffer for the dashboard live view
_recent_alerts: list[dict] = []
MAX_RECENT = 200


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id        TEXT PRIMARY KEY,
                severity        TEXT NOT NULL,
                attack_type     TEXT NOT NULL,
                username        TEXT NOT NULL,
                source_ip       TEXT NOT NULL DEFAULT '',
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                description     TEXT NOT NULL,
                timestamp       INTEGER NOT NULL
            )
        """)
    logger.info("HIDS alert DB ready at %s", DB_PATH)


def store_alert(alert: dict) -> None:
    global _recent_alerts
    with _lock:
        _recent_alerts.insert(0, alert)
        if len(_recent_alerts) > MAX_RECENT:
            _recent_alerts = _recent_alerts[:MAX_RECENT]
    try:
        with db() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO alerts
                    (alert_id, severity, attack_type, username, source_ip,
                     failed_attempts, description, timestamp)
                VALUES
                    (:alert_id, :severity, :attack_type, :username, :source_ip,
                     :failed_attempts, :description, :timestamp)
            """, alert)
    except Exception as e:
        logger.error("Failed to persist alert: %s", e)


def get_recent(limit: int = 50) -> list[dict]:
    with _lock:
        return list(_recent_alerts[:limit])


def get_history(limit: int = 100,
                severity: Optional[str] = None,
                username: Optional[str] = None,
                since: Optional[int] = None) -> list[dict]:
    clauses = []
    params: list = []
    if severity:
        clauses.append("severity = ?")
        params.append(severity)
    if username:
        clauses.append("username LIKE ?")
        params.append(f"%{username}%")
    if since:
        clauses.append("timestamp >= ?")
        params.append(since)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    params.append(limit)
    with db() as conn:
        rows = conn.execute(f"""
            SELECT * FROM alerts {where}
            ORDER BY timestamp DESC LIMIT ?
        """, params).fetchall()
    return [dict(r) for r in rows]


def get_system_status() -> str:
    """Derive system status from most recent alerts."""
    with _lock:
        if not _recent_alerts:
            return "Normal"
        recent_severity = [a["severity"] for a in _recent_alerts[:5]]
    if "CRITICAL" in recent_severity:
        return "Under Attack"
    if "HIGH" in recent_severity:
        return "Under Attack"
    if "MEDIUM" in recent_severity:
        return "Warning"
    return "Normal"
