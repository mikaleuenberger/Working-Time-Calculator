from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta


WEEKDAYS_DE = {
    0: "Montag",
    1: "Dienstag",
    2: "Mittwoch",
    3: "Donnerstag",
    4: "Freitag",
    5: "Samstag",
    6: "Sonntag",
}

NIGHT_START_HOUR = 22
NIGHT_END_HOUR = 6
MIN_LUNCH_BREAK_MIN = 30


@dataclass(frozen=True)
class WorkTimeResult:
    net_hours_decimal: float
    comment: str


def weekday_de(work_date: date) -> str:
    return WEEKDAYS_DE[work_date.weekday()]


def _parse_hhmm(value: str) -> time:
    return datetime.strptime(value, "%H:%M").time()


def calculate_net_hours_and_comment(
    *,
    start_hhmm: str,
    end_hhmm: str,
    lunch_start_hhmm: str | None,
    lunch_end_hhmm: str | None,
    short_break_min: int,
    user_age: int,
    work_date: date,
) -> WorkTimeResult:
    """Pure business logic for net working time calculation.

    Mirrors the rules from the previous CLI version:
    - optional lunch break, min 30min
    - auto-deduct 30min for >= 6h gross if no lunch (except night shift)
    - max 12h net warning
    - minors: max 9h warning + no night work (22-06) + no weekend
    """

    comment_parts: list[str] = []

    t_start = datetime.combine(date(1900, 1, 1), _parse_hhmm(start_hhmm))
    t_end = datetime.combine(date(1900, 1, 1), _parse_hhmm(end_hhmm))

    is_night_shift = t_end < t_start
    if is_night_shift:
        t_end += timedelta(days=1)

    gross_work_duration = t_end - t_start

    lunch_minutes = 0.0

    if lunch_start_hhmm and lunch_end_hhmm:
        l_start = datetime.combine(date(1900, 1, 1), _parse_hhmm(lunch_start_hhmm))
        l_end = datetime.combine(date(1900, 1, 1), _parse_hhmm(lunch_end_hhmm))
        if l_end < l_start:
            l_end += timedelta(days=1)
        lunch_minutes = (l_end - l_start).total_seconds() / 60

        if lunch_minutes < MIN_LUNCH_BREAK_MIN:
            comment_parts.append(f"Mittag zu kurz ({int(lunch_minutes)} min)")

    elif gross_work_duration.total_seconds() >= 6 * 3600:
        if is_night_shift:
            comment_parts.append("Nachtschicht erkannt: Kein automatischer Mittagsabzug.")
        else:
            lunch_minutes = MIN_LUNCH_BREAK_MIN
            comment_parts.append(
                f"Keine Mittagszeit erfasst, {MIN_LUNCH_BREAK_MIN} min automatisch abgezogen"
            )

    total_break_minutes = float(max(0, short_break_min)) + lunch_minutes
    net_seconds = gross_work_duration.total_seconds() - total_break_minutes * 60
    net_seconds = max(0.0, net_seconds)
    net_hours_decimal = net_seconds / 3600

    if net_hours_decimal > 12:
        comment_parts.append("Überzeit > 12h")

    if user_age < 18 and net_hours_decimal > 9:
        comment_parts.append("Maximalarbeitszeit Minderjährige: 9h")

    # night-work overlap (22:00 - 06:00)
    night_start = t_start.replace(hour=NIGHT_START_HOUR, minute=0, second=0)
    night_end = t_start.replace(hour=NIGHT_END_HOUR, minute=0, second=0) + timedelta(days=1)

    overlap_start = max(t_start, night_start)
    overlap_end = min(t_end, night_end)

    if user_age < 18 and overlap_start < overlap_end:
        overlap_min = (overlap_end - overlap_start).total_seconds() / 60
        if overlap_min > 0:
            comment_parts.append(
                f"Nachtarbeit ({int(overlap_min)} min) für Minderjährige (verboten 22-6 Uhr)"
            )

    if user_age < 18 and work_date.weekday() in (5, 6):
        comment_parts.append("Keine Wochenendarbeit für Minderjährige (Sa/So)")

    return WorkTimeResult(net_hours_decimal=net_hours_decimal, comment="; ".join(comment_parts))
