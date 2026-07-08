"""
SQLite persistence for alerts on the gRPC Analysis Server.
"""

import sqlite3
import json
import logging
from contextlib import contextmanager
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.db_path)
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
                alert_id    TEXT PRIMARY KEY,
                severity    TEXT NOT NULL,
                attack_type TEXT NOT NULL,
                username    TEXT NOT NULL,
                source_ip   TEXT NOT NULL DEFAULT '',
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                description TEXT NOT NULL,
                timestamp   INTEGER NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)
        """)
    logger.info("Database initialised at %s", settings.db_path)


def save_alert(alert: dict) -> None:
    with db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO alerts
                (alert_id, severity, attack_type, username, source_ip,
                 failed_attempts, description, timestamp)
            VALUES
                (:alert_id, :severity, :attack_type, :username, :source_ip,
                 :failed_attempts, :description, :timestamp)
        """, alert)


def get_alerts(limit: int = 100,
               severity: Optional[str] = None,
               username: Optional[str] = None) -> list[dict]:
    clauses = []
    params: list = []
    if severity:
        clauses.append("severity = ?")
        params.append(severity)
    if username:
        clauses.append("username LIKE ?")
        params.append(f"%{username}%")

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    params.append(limit)

    with db() as conn:
        rows = conn.execute(f"""
            SELECT * FROM alerts {where}
            ORDER BY timestamp DESC
            LIMIT ?
        """, params).fetchall()
    return [dict(r) for r in rows]
