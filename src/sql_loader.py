"""Helpers: open the Chinook database and run named queries from the sql/ folder."""

import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "chinook.sqlite"
SQL_DIR = ROOT / "sql"

_NAME_RE = re.compile(r"^--\s*name:\s*(\w+)\s*$", re.MULTILINE)


def connect(read_only: bool = True) -> sqlite3.Connection:
    """Open the database. Read-only by default so the tests can never change the data."""
    mode = "ro" if read_only else "rw"
    conn = sqlite3.connect(f"file:{DB_PATH}?mode={mode}", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def load_queries() -> dict[str, str]:
    """Return {query_name: sql_text} for every '-- name: xxx' block in sql/*.sql."""
    queries: dict[str, str] = {}
    for path in sorted(SQL_DIR.glob("*.sql")):
        text = path.read_text(encoding="utf-8")
        parts = _NAME_RE.split(text)  # [preamble, name1, body1, name2, body2, ...]
        for name, body in zip(parts[1::2], parts[2::2]):
            if name in queries:
                raise ValueError(f"Duplicate query name '{name}' in {path.name}")
            queries[name] = body.strip()
    return queries


QUERIES = load_queries()


def run(conn: sqlite3.Connection, name: str) -> list[sqlite3.Row]:
    """Execute a named query and return all rows."""
    return conn.execute(QUERIES[name]).fetchall()
