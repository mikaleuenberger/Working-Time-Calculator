from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker


def _default_sqlite_url() -> str:
    # In containers (e.g. Railway) the application directory may be read-only.
    # Prefer an attached volume at /data when available; otherwise fall back
    # to /tmp (ephemeral).
    preferred_dirs = [
        Path(os.environ.get("WTCALC_DATA_DIR", "")) if os.environ.get("WTCALC_DATA_DIR") else None,
        Path("/data"),
        Path("/tmp"),
        Path(__file__).resolve().parent.parent.parent / "data",
    ]

    for candidate in preferred_dirs:
        if candidate is None:
            continue
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            test_file = candidate / ".write_test"
            test_file.write_text("ok")
            test_file.unlink(missing_ok=True)
        except Exception:
            continue
        else:
            db_path = candidate / "wtcalculator.db"
            return f"sqlite:///{db_path}"

    # Fallback: last resort in current working directory
    return "sqlite:///wtcalculator.db"


DATABASE_URL = (
    os.environ.get("WTCALC_DATABASE_URL")
    or os.environ.get("DATABASE_URL")
    or os.environ.get("WTCALC_DB_URL")
)

if DATABASE_URL:
    DB_URL = DATABASE_URL
else:
    DB_URL = _default_sqlite_url()


# Create engine with sensible defaults depending on the backend.
if DB_URL.startswith("sqlite:"):
    # SQLite: allow use from multiple threads in the same process where needed
    _engine = create_engine(DB_URL, future=True, connect_args={"check_same_thread": False})
else:
    # Assume a networked DB like Postgres. Enable pool_pre_ping to avoid stale
    # connection errors in long-running processes.
    _engine = create_engine(DB_URL, future=True, echo=False, pool_pre_ping=True)


_SessionLocal = sessionmaker(bind=_engine, autoflush=False, future=True, expire_on_commit=False)


def init_db() -> None:
    from ..models import Base

    Base.metadata.create_all(_engine)

    # Lightweight schema upgrade for existing SQLite DBs (no migrations framework)
    # only run the SQLite-specific helpers when the active DB is sqlite.
    if DB_URL.startswith('sqlite:'):
        _ensure_sqlite_columns(
            table='users',
            columns={
                'password_hash': "TEXT NOT NULL DEFAULT ''",
                'must_change_password': "INTEGER NOT NULL DEFAULT 1",
            },
        )
        _ensure_sqlite_unique_index(
            table='users',
            index_name='ux_users_email',
            columns=['email'],
        )


def _ensure_sqlite_columns(*, table: str, columns: dict[str, str]) -> None:
    with _engine.begin() as conn:
        existing_cols = {
            row[1]
            for row in conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
        }
        for col_name, ddl in columns.items():
            if col_name in existing_cols:
                continue
            conn.execute(
                text(f"ALTER TABLE {table} ADD COLUMN {col_name} {ddl}"))


def _ensure_sqlite_unique_index(*, table: str, index_name: str, columns: list[str]) -> None:
    cols = ", ".join(columns)
    with _engine.begin() as conn:
        indexes = {row[1] for row in conn.execute(text(f"PRAGMA index_list({table})")).fetchall()}
        if index_name in indexes:
            return
        conn.execute(text(f"CREATE UNIQUE INDEX {index_name} ON {table} ({cols})"))


@contextmanager
def session_scope() -> Session:
    session: Session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
