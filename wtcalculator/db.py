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
        Path(__file__).resolve().parent.parent / "data",
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


DB_URL = os.getenv("WTCALC_DB_URL", _default_sqlite_url())

_engine = create_engine(DB_URL, future=True)
_SessionLocal = sessionmaker(
    bind=_engine,
    autoflush=False,
    autocommit=False,
    future=True,
    expire_on_commit=False,
)


def init_db() -> None:
    from .models import Base

    Base.metadata.create_all(_engine)

    # Lightweight schema upgrade for existing SQLite DBs (no migrations framework)
    if DB_URL.startswith('sqlite:///'):
        _ensure_sqlite_columns(
            table='users',
            columns={
                'password_hash': "TEXT NOT NULL DEFAULT ''",
                'must_change_password': "INTEGER NOT NULL DEFAULT 1",
            },
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
