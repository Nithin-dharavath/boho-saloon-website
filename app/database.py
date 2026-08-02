import logging

import psycopg
from psycopg.rows import dict_row

from app.config import DATABASE_URL

logger = logging.getLogger(__name__)


class _DictRow(dict):
    """psycopg dict_row is already a dict, but a thin subclass keeps callers
    using attribute-style access (`row["col"]`) consistent across the codebase."""

    __getattr__ = dict.get


def _connect():
    """Open a psycopg connection with dict_row so all fetches return dicts
    compatible with the previous sqlite3.Row usage across the app."""
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    conn.autocommit = False
    return conn


class _ConnectionProxy:
    """Adapter so existing call sites that use sqlite-style
    `conn.execute(...)` followed by `conn.fetchone()` keep working with psycopg.

    psycopg returns rows from the cursor, not the connection. Each call opens
    a fresh cursor, runs the statement, and (for fetchone/fetchall) reuses the
    cursor that the previous execute created.
    """

    def __init__(self, conn):
        self._conn = conn
        self._cursor = None

    def execute(self, sql, params=None):
        self._cursor = self._conn.cursor()
        self._cursor.execute(sql, params) if params is not None else self._cursor.execute(sql)
        return self._cursor

    def executemany(self, sql, seq):
        self._cursor = self._conn.cursor()
        self._cursor.executemany(sql, seq)
        return self._cursor

    def executescript(self, sql):
        self._cursor = self._conn.cursor()
        self._cursor.execute(sql)
        return self._cursor

    def fetchone(self):
        if self._cursor is None:
            raise RuntimeError("No active cursor; call execute() first")
        return self._cursor.fetchone()

    def fetchall(self):
        if self._cursor is None:
            raise RuntimeError("No active cursor; call execute() first")
        return self._cursor.fetchall()

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        try:
            if self._cursor is not None:
                self._cursor.close()
        finally:
            self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self._conn.commit()
        else:
            self._conn.rollback()
        self.close()


def get_db():
    """Return a connection proxy with sqlite-style fetchone/fetchall helpers
    on top of psycopg. Callers close it (same contract as the old sqlite3 path).
    Dict-row cursor means `row["col"]` still works."""
    return _ConnectionProxy(_connect())


def init_db():
    """Schema already lives in Supabase. This function is kept for backwards
    compatibility with `lifespan` in main.py — it now just verifies
    connectivity and logs a warning if anything is missing."""
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT to_regclass('public.profiles')")
                profiles = cur.fetchone()["to_regclass"]
                cur.execute("SELECT to_regclass('public.otp_codes')")
                otp = cur.fetchone()["to_regclass"]
                cur.execute("SELECT to_regclass('public.automation_logs')")
                logs = cur.fetchone()["to_regclass"]
                cur.execute("SELECT to_regclass('public.bookings')")
                bookings = cur.fetchone()["to_regclass"]
                cur.execute("SELECT to_regclass('public.contact_submissions')")
                contacts = cur.fetchone()["to_regclass"]
        missing = [
            name
            for name, present in (
                ("profiles", profiles),
                ("otp_codes", otp),
                ("automation_logs", logs),
                ("bookings", bookings),
                ("contact_submissions", contacts),
            )
            if not present
        ]
        if missing:
            logger.warning(
                "Supabase schema check — missing tables: %s", ", ".join(missing)
            )
        else:
            logger.info("Supabase schema check — all tables present")
    except Exception as exc:  # pragma: no cover - startup safety net
        logger.error("Supabase connectivity check failed: %s", exc)