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

AGE_MIN = 14
AGE_MAX = 100


@dataclass(frozen=True)
class WorkTimeResult:
    net_hours_decimal: float
    comment: str


def weekday_de(work_date: date) -> str:
    return WEEKDAYS_DE[work_date.weekday()]


def _parse_hhmm(value: str) -> time:
    return datetime.strptime(value, "%H:%M").time()


def validate_user_age(birthdate: date) -> tuple[bool, str]:
    """Berechnet das Alter und prüft die gesetzlichen Grenzen."""
    today = date.today()
    # Präzise Altersberechnung (berücksichtigt Schaltjahre)
    age = today.year - birthdate.year - \
        ((today.month, today.day) < (birthdate.month, birthdate.day))

    if age < AGE_MIN:
        return False, "Das Alter muss mindestens 14 Jahre betragen."
    if age > AGE_MAX:
        return False, "Das Alter darf maximal 100 Jahre betragen."

    return True, ""


def calculate_net_hours_and_comment(
    *,
    start_hhmm: str,
    end_hhmm: str,
    lunch_start_hhmm: str | None,
    lunch_end_hhmm: str | None,
    short_break_min: int,
    user_birthdate: date | None,
    work_date: date,
) -> WorkTimeResult:
    """Calculate age from birthdate for minor checks."""
    user_age = 18  # default to adult if no birthdate
    if user_birthdate:
        age_delta = work_date - user_birthdate
        user_age = age_delta.days // 365
    """Pure business logic for net working time calculation.

    Mirrors the rules from the previous CLI version:
    - optional lunch break, min 30min
    - auto-deduct 30min for >= 6h gross if no lunch (except night shift)
    - max 12h net warning
    - minors: max 9h warning + no night work (22-06) + no weekend
    """

    user_age = 18  # default to adult if no birthdate
    if user_birthdate:
        # Präzise Altersberechnung passend zur Validierung oben
        user_age = work_date.year - user_birthdate.year - \
            ((work_date.month, work_date.day) <
             (user_birthdate.month, user_birthdate.day))

    comment_parts: list[str] = []

    t_start = datetime.combine(date(1900, 1, 1), _parse_hhmm(start_hhmm))
    t_end = datetime.combine(date(1900, 1, 1), _parse_hhmm(end_hhmm))

    is_night_shift = t_end < t_start
    if is_night_shift:
        t_end += timedelta(days=1)

    gross_work_duration = t_end - t_start

    lunch_minutes = 0.0

    if lunch_start_hhmm and lunch_end_hhmm:
        l_start = datetime.combine(
            date(1900, 1, 1), _parse_hhmm(lunch_start_hhmm))
        l_end = datetime.combine(date(1900, 1, 1), _parse_hhmm(lunch_end_hhmm))

        raw_lunch_minutes = (l_end - l_start).total_seconds() / 60

        if raw_lunch_minutes < 0:
            comment_parts.append(
                "Mittagspause: Ende vor Start – bitte korrigieren.")
            lunch_minutes = 0
        elif raw_lunch_minutes > 180:
            comment_parts.append(
                f"Mittagspause > 3h – unüblich, bitte prüfen.")
            lunch_minutes = raw_lunch_minutes
        else:
            if l_end < l_start:
                l_end += timedelta(days=1)
            lunch_minutes = (l_end - l_start).total_seconds() / 60

            if lunch_minutes < MIN_LUNCH_BREAK_MIN:
                comment_parts.append(
                    f"Mittag zu kurz ({int(lunch_minutes)} min)")

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
    night_end = t_start.replace(
        hour=NIGHT_END_HOUR, minute=0, second=0) + timedelta(days=1)

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
