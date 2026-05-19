from __future__ import annotations

import csv
import io
import json
from datetime import date, datetime
from pathlib import Path
from typing import Tuple

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from ..models import User
from ..services.time_entry_service import TimeEntryService


def _parse_date_yyyy_mm_dd(value: str):
    value = (value or "").strip()
    return datetime.strptime(value, "%Y-%m-%d").date()


def _normalize_user_record(raw: dict) -> dict:
    # Support multiple key names from different JSON formats.
    first_name = raw.get("first_name") or raw.get("surname") or raw.get("given_name") or ""
    last_name = raw.get("last_name") or raw.get("family_name") or raw.get("last") or ""
    email = raw.get("email") or ""
    business_role = raw.get("business_role") or raw.get("role") or "Mitarbeiter"
    age = raw.get("age") if raw.get("age") is not None else raw.get("years", 18)
    # Convert age to birthdate (approximate, assuming 18 years ago as default)
    today = date.today()
    birthdate = raw.get("birthdate")
    if birthdate:
        try:
            birthdate = _parse_date_yyyy_mm_dd(birthdate)
        except Exception:
            birthdate = date(today.year - int(age), today.month, today.day)
    else:
        birthdate = date(today.year - int(age), today.month, today.day)
    return {
        "id": raw.get("id"),
        "first_name": str(first_name).strip(),
        "last_name": str(last_name).strip(),
        "email": str(email).strip(),
        "business_role": str(business_role).strip() or "Mitarbeiter",
        "birthdate": birthdate,
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
            birthdate=rec["birthdate"],
            password_hash="",
            must_change_password=True,
        )
        session.add(user)
        created += 1

    return created, skipped


def seed_time_entries(session: Session, csv_path: Path, *, overwrite: bool = True) -> tuple[int, int, list[str]]:
    
    if not csv_path.exists():
        return 0, 0, [f"CSV file not found: {csv_path}"]

    text = csv_path.read_text(encoding="utf-8-sig")
    reader = csv.DictReader(io.StringIO(text), delimiter=';')

    imported = 0
    skipped = 0
    errors: list[str] = []

    tes = TimeEntryService(session)

    if reader.fieldnames is None:
        return 0, 0, ["CSV hat keine Spalten"]

    for row_idx, row in enumerate(reader, start=2):
        try:
            user_id_raw = (row.get('UserId') or row.get('UserID') or '').strip()
            email_raw = (row.get('Email') or row.get('E-Mail') or '').strip()

            user = None
            if user_id_raw:
                try:
                    uid = int(user_id_raw)
                    user = session.get(User, uid)
                except Exception:
                    user = None

            if user is None and email_raw:
                stmt = select(User).where(User.email == email_raw)
                user = session.execute(stmt).scalar_one_or_none()

            if user is None:
                skipped += 1
                errors.append(f"Zeile {row_idx}: Benutzer nicht gefunden (UserId/Email)")
                continue

            datum_str = (row.get('Datum') or '').strip()
            if not datum_str:
                skipped += 1
                errors.append(f"Zeile {row_idx}: kein Datum")
                continue

            from datetime import datetime
            work_date = datetime.strptime(datum_str, '%d.%m.%Y').date()

            # Only seed entries from the first half of the month (days 1-15)
            if work_date.day > 15:
                skipped += 1
                continue

            start = (row.get('Arbeitsbeginn') or '').strip()
            end = (row.get('Arbeitsende') or '').strip()
            if not start or not end:
                skipped += 1
                errors.append(f"Zeile {row_idx}: Start/End fehlt")
                continue

            lunch_start = (row.get('Mittag_beginn') or '').strip() or None
            lunch_end = (row.get('Mittag_ende') or '').strip() or None
            short_break_min = int((row.get('Pause_min') or '0').strip() or 0)
            legacy_comment = (row.get('Kommentar') or '').strip()

            # check overwrite flag
            if not overwrite:
                if tes.entry_exists(user_id=user.id, work_date=work_date):
                    skipped += 1
                    continue

            entry = tes.upsert_entry(
                user=user,
                work_date=work_date,
                start_hhmm=start,
                end_hhmm=end,
                lunch_start_hhmm=lunch_start,
                lunch_end_hhmm=lunch_end,
                short_break_min=short_break_min,
            )

            if legacy_comment:
                if not entry.comment:
                    entry.comment = legacy_comment
                elif legacy_comment not in entry.comment:
                    entry.comment = f"{entry.comment}; {legacy_comment}"

            imported += 1

        except Exception as e:
            errors.append(f"Zeile {row_idx}: {e}")
            skipped += 1

    return imported, skipped, errors
