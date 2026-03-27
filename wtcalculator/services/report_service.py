from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from ..domain.time_calculator import weekday_de
from ..models import TimeEntry, User


def _hhmm_from_minutes(total_min: int) -> str:
    sign = "-" if total_min < 0 else ""
    total_min = abs(total_min)
    hours, minutes = divmod(total_min, 60)
    return f"{sign}{hours:02d}:{minutes:02d}"


@dataclass(frozen=True)
class MonthlyReport:
    text: str


class ReportService:
    WEEKLY_TARGET_HOURS = 42.0

    def __init__(self, session: Session):
        self._session = session

    def generate_employee_monthly_report(self, *, user_id: int, year: int, month: int) -> MonthlyReport:
        user = self._session.get(User, user_id)
        if user is None:
            return MonthlyReport(text="❌ User nicht gefunden.")

        start = date(year, month, 1)
        end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)

        entries = list(
            self._session.execute(
                select(TimeEntry)
                .where(and_(TimeEntry.user_id == user_id, TimeEntry.work_date >= start, TimeEntry.work_date < end))
                .order_by(TimeEntry.work_date)
            )
            .scalars()
            .all()
        )

        total_min = 0
        week_sums: dict[tuple[int, int], int] = {}
        notes: list[str] = []

        for e in entries:
            mins = int(round(e.net_hours * 60))
            total_min += mins

            iso_year, iso_week, _ = e.work_date.isocalendar()
            week_sums[(iso_year, iso_week)] = week_sums.get((iso_year, iso_week), 0) + mins

            if e.comment:
                notes.append(f"{e.work_date.strftime('%d.%m.%Y')} {e.comment}")

        weekly_overtime_min = 0
        for key, week_min in week_sums.items():
            target_min = int(self.WEEKLY_TARGET_HOURS * 60)
            if week_min > target_min:
                weekly_overtime_min += week_min - target_min

        lines: list[str] = []
        lines.append(f"Mitarbeiter #{user.id:03d} ({user.first_name} {user.last_name})")
        lines.append("------------------------------------------")
        lines.append("Datum        Wochentag   Netto    Kommentar")

        for e in entries:
            d = e.work_date.strftime("%d.%m.%Y").ljust(12)
            w = weekday_de(e.work_date)[:10].ljust(11)
            netto = _hhmm_from_minutes(int(round(e.net_hours * 60))).rjust(7)
            lines.append(f"{d}{w}{netto}   {e.comment or ''}")

        lines.append("")
        lines.append("Hinweise:")
        if notes:
            for n in notes:
                lines.append(f"! {n}")
        else:
            lines.append("keine")

        lines.append("------------------------------------------")
        lines.append("Total Monat:        " + _hhmm_from_minutes(total_min))
        lines.append("Überstunden (Wo):   " + _hhmm_from_minutes(weekly_overtime_min))

        return MonthlyReport(text="\n".join(lines))
