from __future__ import annotations

import csv
import io
from datetime import date, datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from ..domain.time_calculator import calculate_net_hours_and_comment
from ..models import TimeEntry, User


class TimeEntryService:
    MAX_WEEKLY_HOURS = 45.0

    def __init__(self, session: Session):
        self._session = session

    def entry_exists(self, *, user_id: int, work_date: date) -> bool:
        existing = self._session.execute(
            select(TimeEntry.id).where(and_(TimeEntry.user_id == user_id, TimeEntry.work_date == work_date)).limit(1)
        ).first()
        return existing is not None

    @staticmethod
    def normalize_user_comment(comment: str | None, *, limit: int = 30) -> str:
        text = (comment or "").strip()
        if len(text) > limit:
            text = text[:limit]
        return text

    def upsert_entry(
        self,
        *,
        user: User,
        work_date: date,
        start_hhmm: str,
        end_hhmm: str,
        lunch_start_hhmm: str | None,
        lunch_end_hhmm: str | None,
        short_break_min: int,
    ) -> TimeEntry:
        base_result = calculate_net_hours_and_comment(
            start_hhmm=start_hhmm,
            end_hhmm=end_hhmm,
            lunch_start_hhmm=lunch_start_hhmm,
            lunch_end_hhmm=lunch_end_hhmm,
            short_break_min=short_break_min,
            user_age=user.age,
            work_date=work_date,
        )

        entry = self._session.execute(
            select(TimeEntry).where(and_(TimeEntry.user_id ==
                                         user.id, TimeEntry.work_date == work_date))
        ).scalar_one_or_none()

        if entry is None:
            entry = TimeEntry(user_id=user.id, work_date=work_date)
            self._session.add(entry)

        entry.start_time = datetime.strptime(start_hhmm, "%H:%M").time()
        entry.end_time = datetime.strptime(end_hhmm, "%H:%M").time()
        entry.lunch_start = (
            datetime.strptime(lunch_start_hhmm, "%H:%M").time(
            ) if lunch_start_hhmm else None
        )
        entry.lunch_end = (
            datetime.strptime(lunch_end_hhmm, "%H:%M").time(
            ) if lunch_end_hhmm else None
        )
        entry.short_break_min = max(0, int(short_break_min))

        entry.net_hours = float(round(base_result.net_hours_decimal, 2))
        entry.comment = base_result.comment

        # dynamic weekly hours check (including this day)
        weekly_sum = self.get_weekly_hours(
            user_id=user.id, any_day_in_week=work_date, exclude_date=None)
        if weekly_sum > self.MAX_WEEKLY_HOURS:
            extra = f"Wochenstunden > {int(self.MAX_WEEKLY_HOURS)}h"
            entry.comment = f"{entry.comment}; {extra}" if entry.comment else extra

        entry.approved = False
        return entry

    def list_month_entries(self, *, user_id: int, year: int, month: int) -> list[TimeEntry]:
        start = date(year, month, 1)
        if month == 12:
            end = date(year + 1, 1, 1)
        else:
            end = date(year, month + 1, 1)

        return list(
            self._session.execute(
                select(TimeEntry)
                .where(and_(TimeEntry.user_id == user_id, TimeEntry.work_date >= start, TimeEntry.work_date < end))
                .order_by(TimeEntry.work_date)
            )
            .scalars()
            .all()
        )

    def list_week_entries(self, *, user_id: int, any_day_in_week: date) -> list[TimeEntry]:
        start_of_week = any_day_in_week - \
            timedelta(days=any_day_in_week.weekday())
        end_of_week = start_of_week + timedelta(days=7)
        return list(
            self._session.execute(
                select(TimeEntry)
                .where(and_(TimeEntry.user_id == user_id, TimeEntry.work_date >= start_of_week, TimeEntry.work_date < end_of_week))
                .order_by(TimeEntry.work_date)
            )
            .scalars()
            .all()
        )

    def import_csv(
        self,
        *,
        user: User,
        csv_bytes: bytes,
        overwrite: bool = True,
    ) -> tuple[int, int, list[str]]:
        """Import legacy CSV (semicolon separated) into DB.

        Returns: (imported_count, skipped_count, error_messages)
        """

        text = csv_bytes.decode('utf-8-sig', errors='replace')
        reader = csv.DictReader(io.StringIO(text), delimiter=';')

        imported = 0
        skipped = 0
        errors = []

        if reader.fieldnames is None:
            return 0, 0, ["CSV hat keine Spalten"]

        for row_idx, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            try:
                datum_str = (row.get('Datum') or '').strip()
                if not datum_str:
                    skipped += 1
                    continue

                work_date = datetime.strptime(datum_str, '%d.%m.%Y').date()
                
                start = (row.get('Arbeitsbeginn') or '').strip()
                end = (row.get('Arbeitsende') or '').strip()
                if not start or not end:
                    skipped += 1
                    continue

                lunch_start = (row.get('Mittag_beginn') or '').strip() or None
                lunch_end = (row.get('Mittag_ende') or '').strip() or None

                short_break_min = int(
                    (row.get('Pause_min') or '0').strip() or 0)

                if not overwrite:
                    existing = self._session.execute(
                        select(TimeEntry).where(and_(TimeEntry.user_id ==
                                                     user.id, TimeEntry.work_date == work_date))
                    ).scalar_one_or_none()
                    if existing is not None:
                        skipped += 1
                        continue

                entry = self.upsert_entry(
                    user=user,
                    work_date=work_date,
                    start_hhmm=start,
                    end_hhmm=end,
                    lunch_start_hhmm=lunch_start,
                    lunch_end_hhmm=lunch_end,
                    short_break_min=short_break_min,
                )

                legacy_comment = (row.get('Kommentar') or '').strip()
                if legacy_comment:
                    if not entry.comment:
                        entry.comment = legacy_comment
                    elif legacy_comment not in entry.comment:
                        entry.comment = f"{entry.comment}; {legacy_comment}"

                imported += 1
            except Exception as e:
                errors.append(f"Zeile {row_idx}: {str(e)}")
                skipped += 1

        return imported, skipped, errors

    def get_weekly_hours(self, *, user_id: int, any_day_in_week: date, exclude_date: date | None) -> float:
        start_of_week = any_day_in_week - \
            timedelta(days=any_day_in_week.weekday())
        end_of_week = start_of_week + timedelta(days=7)

        stmt = select(TimeEntry).where(
            and_(TimeEntry.user_id == user_id, TimeEntry.work_date >=
                 start_of_week, TimeEntry.work_date < end_of_week)
        )
        entries = list(self._session.execute(stmt).scalars().all())
        if exclude_date is not None:
            entries = [e for e in entries if e.work_date != exclude_date]

        return float(sum(e.net_hours for e in entries))

    def list_unapproved_entries(self) -> list[TimeEntry]:
        return list(
            self._session.execute(
                select(TimeEntry).where(TimeEntry.approved.is_(
                    False)).order_by(TimeEntry.work_date.desc())
            )
            .scalars()
            .all()
        )

    def approve_entry(self, *, entry_id: int) -> bool:
        entry = self._session.get(TimeEntry, entry_id)
        if entry is None:
            return False
        entry.approved = True
        return True
