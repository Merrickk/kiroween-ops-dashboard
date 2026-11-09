"""SQLite storage for the ops dashboard.

Tables: hosts, deploys, checks. Created automatically on first start.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("ops.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS hosts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'server',
    status TEXT NOT NULL DEFAULT 'unknown',
    last_latency_ms INTEGER,
    last_seen_at TEXT,
    cert_expires_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS deploys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id INTEGER NOT NULL REFERENCES hosts(id),
    summary TEXT NOT NULL,
    actor TEXT NOT NULL DEFAULT '',
    result TEXT NOT NULL DEFAULT 'success',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id INTEGER NOT NULL REFERENCES hosts(id),
    ok INTEGER NOT NULL,
    latency_ms INTEGER,
    detail TEXT NOT NULL DEFAULT '',
    checked_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    if db_path is None:
        db_path = DB_PATH
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | None = None) -> None:
    if db_path is None:
        db_path = DB_PATH
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)


def row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


def list_hosts(conn) -> list[dict]:
    rows = conn.execute("SELECT * FROM hosts ORDER BY id").fetchall()
    return [row_to_dict(r) for r in rows]


def add_host(conn, name: str, address: str, kind: str = "server") -> dict:
    cur = conn.execute(
        "INSERT INTO hosts (name, address, kind) VALUES (?, ?, ?)",
        (name, address, kind),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM hosts WHERE id = ?", (cur.lastrowid,)).fetchone()
    return row_to_dict(row)


def delete_host(conn, host_id: int) -> bool:
    cur = conn.execute("DELETE FROM hosts WHERE id = ?", (host_id,))
    conn.commit()
    return cur.rowcount > 0


def update_host_status(conn, host_id: int, status: str, latency_ms, last_seen_at, cert_expires_at) -> None:
    conn.execute(
        """UPDATE hosts SET status = ?, last_latency_ms = ?, last_seen_at = ?,
           cert_expires_at = ? WHERE id = ?""",
        (status, latency_ms, last_seen_at, cert_expires_at, host_id),
    )
    conn.commit()


def get_host(conn, host_id: int):
    row = conn.execute("SELECT * FROM hosts WHERE id = ?", (host_id,)).fetchone()
    return row_to_dict(row) if row else None


def list_deploys(conn, limit: int = 50) -> list[dict]:
    rows = conn.execute(
        """SELECT d.*, h.name AS host_name FROM deploys d
           LEFT JOIN hosts h ON h.id = d.host_id
           ORDER BY d.id DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    return [row_to_dict(r) for r in rows]


def add_deploy(conn, host_id: int, summary: str, actor: str, result: str) -> dict:
    cur = conn.execute(
        "INSERT INTO deploys (host_id, summary, actor, result) VALUES (?, ?, ?, ?)",
        (host_id, summary, actor, result),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM deploys WHERE id = ?", (cur.lastrowid,)).fetchone()
    return row_to_dict(row)


def list_checks(conn, limit: int = 20) -> list[dict]:
    rows = conn.execute(
        """SELECT c.*, h.name AS host_name FROM checks c
           LEFT JOIN hosts h ON h.id = c.host_id
           ORDER BY c.id DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    return [row_to_dict(r) for r in rows]


def add_check(conn, host_id: int, ok: bool, latency_ms, detail: str) -> None:
    conn.execute(
        "INSERT INTO checks (host_id, ok, latency_ms, detail) VALUES (?, ?, ?, ?)",
        (host_id, 1 if ok else 0, latency_ms, detail),
    )
    conn.commit()
