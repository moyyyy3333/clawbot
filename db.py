"""SQLite-backed persistence for ClawBot."""
import sqlite3
import json
import os
import time
from contextlib import contextmanager
from typing import Optional

DB_PATH = os.getenv("DB_PATH", "clawbot.db")


def init_db():
    with _conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                tg_username TEXT,
                stage TEXT DEFAULT 'start',
                paid INTEGER DEFAULT 0,
                stripe_session_id TEXT,
                stripe_payment_intent TEXT,
                paid_at INTEGER,
                refunded INTEGER DEFAULT 0,
                created_at INTEGER,
                updated_at INTEGER,
                metadata TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                event_type TEXT,
                payload TEXT,
                created_at INTEGER
            );

            CREATE TABLE IF NOT EXISTS stripe_events (
                event_id TEXT PRIMARY KEY,
                created_at INTEGER
            );
            """
        )


@contextmanager
def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def now() -> int:
    return int(time.time())


def upsert_user(user_id: int, tg_username: Optional[str] = None):
    with _conn() as c:
        c.execute(
            """
            INSERT INTO users (user_id, tg_username, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                tg_username = COALESCE(excluded.tg_username, users.tg_username),
                updated_at = excluded.updated_at
            """,
            (user_id, tg_username, now(), now()),
        )


def get_user(user_id: int) -> Optional[dict]:
    with _conn() as c:
        row = c.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["metadata"] = json.loads(d.get("metadata") or "{}")
        return d


def set_stage(user_id: int, stage: str):
    with _conn() as c:
        c.execute(
            "UPDATE users SET stage = ?, updated_at = ? WHERE user_id = ?",
            (stage, now(), user_id),
        )


def set_metadata(user_id: int, key: str, value):
    user = get_user(user_id) or {"metadata": {}}
    meta = user["metadata"]
    meta[key] = value
    with _conn() as c:
        c.execute(
            "UPDATE users SET metadata = ?, updated_at = ? WHERE user_id = ?",
            (json.dumps(meta), now(), user_id),
        )


def set_stripe_session(user_id: int, session_id: str):
    with _conn() as c:
        c.execute(
            "UPDATE users SET stripe_session_id = ?, updated_at = ? WHERE user_id = ?",
            (session_id, now(), user_id),
        )


def mark_paid(user_id: int, payment_intent: str):
    with _conn() as c:
        c.execute(
            """
            UPDATE users
            SET paid = 1, stripe_payment_intent = ?, paid_at = ?, updated_at = ?
            WHERE user_id = ?
            """,
            (payment_intent, now(), now(), user_id),
        )


def mark_refunded(user_id: int):
    with _conn() as c:
        c.execute(
            "UPDATE users SET refunded = 1, updated_at = ? WHERE user_id = ?",
            (now(), user_id),
        )


def user_by_session(session_id: str) -> Optional[dict]:
    with _conn() as c:
        row = c.execute(
            "SELECT * FROM users WHERE stripe_session_id = ?", (session_id,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["metadata"] = json.loads(d.get("metadata") or "{}")
        return d


def log_event(user_id: Optional[int], event_type: str, payload: dict):
    with _conn() as c:
        c.execute(
            "INSERT INTO events (user_id, event_type, payload, created_at) VALUES (?, ?, ?, ?)",
            (user_id, event_type, json.dumps(payload), now()),
        )


def stripe_event_seen(event_id: str) -> bool:
    """Idempotency check for Stripe webhooks."""
    with _conn() as c:
        existing = c.execute(
            "SELECT 1 FROM stripe_events WHERE event_id = ?", (event_id,)
        ).fetchone()
        if existing:
            return True
        c.execute(
            "INSERT INTO stripe_events (event_id, created_at) VALUES (?, ?)",
            (event_id, now()),
        )
        return False


def stats() -> dict:
    with _conn() as c:
        total = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        paid = c.execute("SELECT COUNT(*) FROM users WHERE paid = 1").fetchone()[0]
        refunded = c.execute("SELECT COUNT(*) FROM users WHERE refunded = 1").fetchone()[0]
        complete = c.execute("SELECT COUNT(*) FROM users WHERE stage = 'complete'").fetchone()[0]
    return {
        "total_users": total,
        "paid": paid,
        "refunded": refunded,
        "completed_setup": complete,
        "net_revenue_usd": (paid - refunded) * 49,
    }
