"""
Chakravyuha Database Layer (SQLite with WAL Mode)
Pure standard library sqlite3 with connection context managers and atomic transactions.
"""

import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

DB_PATH = Path(os.environ.get("DATABASE_PATH", Path(__file__).resolve().parent.parent / "chakravyuha.db"))


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for high concurrency
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_db_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS teams (
            team_id TEXT PRIMARY KEY,
            team_token TEXT UNIQUE,
            banned INTEGER DEFAULT 0,
            lifetime_cap_remaining INTEGER DEFAULT 2000,
            created_at REAL
        );

        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            team_id TEXT NOT NULL,
            session_key TEXT NOT NULL,
            seq INTEGER DEFAULT 0,
            current_nonce TEXT NOT NULL,
            next_nonce TEXT NOT NULL,
            created_at REAL,
            last_active_at REAL,
            last_heartbeat_at REAL,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (team_id) REFERENCES teams(team_id)
        );

        CREATE TABLE IF NOT EXISTS machine_state (
            session_id TEXT PRIMARY KEY,
            team_id TEXT NOT NULL,
            mode TEXT DEFAULT 'replica',
            is_sealed INTEGER DEFAULT 0,
            walzenlage TEXT NOT NULL,
            ringstellung TEXT NOT NULL,
            grundstellung TEXT NOT NULL,
            plugboard TEXT NOT NULL,
            current_positions TEXT NOT NULL,
            updated_at REAL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        );

        CREATE TABLE IF NOT EXISTS token_buckets (
            team_id TEXT PRIMARY KEY,
            tokens REAL DEFAULT 400.0,
            last_refill_at REAL,
            FOREIGN KEY (team_id) REFERENCES teams(team_id)
        );

        CREATE TABLE IF NOT EXISTS strikes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id TEXT NOT NULL,
            strike_count INTEGER NOT NULL,
            detector TEXT NOT NULL,
            evidence TEXT,
            ua_hash TEXT,
            timestamp REAL,
            FOREIGN KEY (team_id) REFERENCES teams(team_id)
        );

        CREATE TABLE IF NOT EXISTS soft_violations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id TEXT NOT NULL,
            violation_type TEXT NOT NULL,
            timestamp REAL,
            FOREIGN KEY (team_id) REFERENCES teams(team_id)
        );

        CREATE TABLE IF NOT EXISTS lockouts (
            team_id TEXT PRIMARY KEY,
            locked_until REAL DEFAULT 0.0,
            reason TEXT,
            wrong_flag_count INTEGER DEFAULT 0,
            FOREIGN KEY (team_id) REFERENCES teams(team_id)
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            team_id TEXT,
            event_type TEXT NOT NULL,
            details TEXT,
            timestamp REAL
        );

        CREATE TABLE IF NOT EXISTS team_gates (
            team_id TEXT NOT NULL,
            gate_id TEXT NOT NULL,
            unlocked_at REAL,
            wrong_attempts INTEGER DEFAULT 0,
            locked_until REAL DEFAULT 0.0,
            PRIMARY KEY (team_id, gate_id),
            FOREIGN KEY (team_id) REFERENCES teams(team_id)
        );

        CREATE INDEX IF NOT EXISTS idx_sessions_team ON sessions(team_id);
        CREATE INDEX IF NOT EXISTS idx_soft_violations_time ON soft_violations(team_id, timestamp);
        CREATE INDEX IF NOT EXISTS idx_strikes_team ON strikes(team_id);
        CREATE INDEX IF NOT EXISTS idx_team_gates ON team_gates(team_id);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_team ON audit_logs(team_id, timestamp);
        """)

        # Run safe migrations for existing tables
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(machine_state)")
        cols = [col[1] for col in cursor.fetchall()]
        if "mode" not in cols:
            cursor.execute("ALTER TABLE machine_state ADD COLUMN mode TEXT DEFAULT 'replica'")

        conn.commit()



# Database helper methods
def log_audit(session_id: Optional[str], team_id: Optional[str], event_type: str, details: Any):
    now = time.time()
    details_json = json.dumps(details) if not isinstance(details, str) else details
    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO audit_logs (session_id, team_id, event_type, details, timestamp) VALUES (?, ?, ?, ?, ?)",
            (session_id, team_id, event_type, details_json, now)
        )
        conn.commit()
