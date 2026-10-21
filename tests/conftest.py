import sqlite3

import pytest

from src.sql_loader import connect


@pytest.fixture(scope="session")
def db() -> sqlite3.Connection:
    """Read-only connection to the real Chinook database."""
    conn = connect(read_only=True)
    yield conn
    conn.close()


@pytest.fixture
def broken_db(db) -> sqlite3.Connection:
    """
    An in-memory COPY of the database that we are free to damage.
    Used to prove that the data-quality checks really detect defects.
    """
    mem = sqlite3.connect(":memory:")
    mem.row_factory = sqlite3.Row
    db.backup(mem)
    yield mem
    mem.close()
