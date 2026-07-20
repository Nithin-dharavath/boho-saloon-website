import sqlite3
from app.config import DATABASE_URL


def migrate_schema(conn):
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
    if "google_sub" not in existing:
        conn.execute("ALTER TABLE users ADD COLUMN google_sub TEXT")
    if "phone" not in existing:
        conn.execute("ALTER TABLE users ADD COLUMN phone TEXT")
    conn.commit()


def get_db():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email       TEXT UNIQUE NOT NULL,
            name        TEXT,
            date_of_birth DATE,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS otp_codes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email       TEXT NOT NULL,
            code        TEXT NOT NULL,
            expires_at  TIMESTAMP NOT NULL,
            attempts    INTEGER DEFAULT 0,
            used        INTEGER DEFAULT 0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_otp_lookup
            ON otp_codes(email, used, expires_at);

        CREATE TABLE IF NOT EXISTS automation_logs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER REFERENCES users(id),
            email_type      TEXT NOT NULL,
            recipient       TEXT NOT NULL,
            sent_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status          TEXT NOT NULL DEFAULT 'sent',
            error           TEXT,
            idempotency_key TEXT UNIQUE NOT NULL
        );
    """)
    migrate_schema(conn)
    conn.commit()
    conn.close()
