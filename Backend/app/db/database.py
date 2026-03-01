"""SQLite database initialization and connection management."""

import sqlite3
import logging
from pathlib import Path
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# SQL for creating all tables
_CREATE_TABLES_SQL = """
    CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    uploaded_by TEXT NOT NULL,
    page_count INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS clauses (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id),
    section_title TEXT,
    text TEXT NOT NULL,
    page INTEGER,
    clause_type TEXT,
    importance TEXT,
    risk_level TEXT,
    risk_reason TEXT
);
"""

def get_db_path() -> str:
    return get_settings().database_path

def init_db() -> None:
    db_path = get_db_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
     
    try:
        conn.executescript(_CREATE_TABLES_SQL)
        conn.commit()
        logger.info("Database initialized at %s", db_path)
    except Exception as e:
        logger.error("Failed to initialize database: %s", str(e))
    finally:
        conn.close()

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn