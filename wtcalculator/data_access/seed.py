from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple

from sqlalchemy.orm import Session
from sqlalchemy import text

from ..models import User


def _normalize_user_record(raw: dict) -> dict:
    # Support multiple key names from different JSON formats.
    first_name = raw.get("first_name") or raw.get("surname") or raw.get("given_name") or ""
    last_name = raw.get("last_name") or raw.get("family_name") or raw.get("last") or ""
    email = raw.get("email") or ""
    business_role = raw.get("business_role") or raw.get("role") or "Mitarbeiter"
    age = raw.get("age") if raw.get("age") is not None else raw.get("years", 18)
    return {
        "id": raw.get("id"),
        "first_name": str(first_name).strip(),
        "last_name": str(last_name).strip(),
        "email": str(email).strip(),
        "business_role": str(business_role).strip() or "Mitarbeiter",
        "age": int(age) if age is not None else 18,
    }


def seed_users(session: Session, users_json_path: Path) -> Tuple[int, int]:
    """Seed users from a JSON file if the users table is empty.

    Returns a tuple (created_count, skipped_count).
    This function is idempotent: if the DB already has any users, it will do nothing.
    """
    # Quick check: if any user exists, do nothing
    existing = session.execute(text("SELECT 1 FROM users LIMIT 1")).first()
    if existing is not None:
        return 0, 0

    if not users_json_path.exists():
        return 0, 0

    data = json.loads(users_json_path.read_text(encoding="utf-8"))
    created = 0
    skipped = 0
    for raw in data.get("users", []):
        try:
            rec = _normalize_user_record(raw)
            user_id = int(rec.get("id") or 0)
        except Exception:
            skipped += 1
            continue

        if user_id <= 0:
            skipped += 1
            continue

        # If a user with this id already exists, skip (we assume empty DB earlier,
        # but be defensive in case of partial imports).
        if session.get(User, user_id) is not None:
            skipped += 1
            continue

        user = User(
            id=user_id,
            first_name=rec["first_name"],
            last_name=rec["last_name"],
            email=rec["email"],
            business_role=rec["business_role"],
            age=rec["age"],
            password_hash="",
            must_change_password=True,
        )
        session.add(user)
        created += 1

    return created, skipped
