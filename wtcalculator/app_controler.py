from .constants import DEFAULT_TIMEZONE, NAME_MAX_LENGTH, EMAIL_MAX_LENGTH, AGE_MIN, AGE_MAX, VALID_ROLES, COMMENT_MAX_LENGTH, MIN_LUNCH_BREAK_MINUTES, MAX_WEEKLY_HOURS, MIN_BREAK_FOR_AUTO_DEDUCT_HOURS
from .data_access.db import session_scope
from .services.auth_service import AuthService
from .services.user_service import UserService
from .security import validate_password_policy
from .models import User, TimeEntry
from .services.time_entry_service import TimeEntryService
from datetime import datetime, timedelta, date
from datetime import time as dtime
import os
import re
from wtcalculator.domain.time_calculator import validate_user_age

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore


def _today_local_date():
    tz_name = os.environ.get('WTCALC_TZ', DEFAULT_TIMEZONE)
    if ZoneInfo is not None:
        try:
            return datetime.now(ZoneInfo(tz_name)).date()
        except Exception:
            return datetime.now().date()
    return datetime.now().date()


def _minutes_since_midnight(t: dtime) -> int:
    return int(t.hour) * 60 + int(t.minute)


def _is_time_in_interval(*, t: dtime, start: dtime, end: dtime) -> bool:
    """Return True if t is within the work interval [start, end] with night-shift support."""

    tm = _minutes_since_midnight(t)
    sm = _minutes_since_midnight(start)
    em = _minutes_since_midnight(end)

    # normal shift
    if em >= sm:
        return sm <= tm <= em

    # night shift (end is next day)
    return tm >= sm or tm <= em


def _work_interval_minutes(*, start: dtime, end: dtime) -> int:
    sm = _minutes_since_midnight(start)
    em = _minutes_since_midnight(end)
    if em >= sm:
        return em - sm
    return (24 * 60 - sm) + em


def _parse_date_yyyy_mm_dd(value: str):
    value = (value or "").strip()
    # strict ISO date
    return datetime.strptime(value, "%Y-%m-%d").date()


def _parse_time_hh_mm(value: str):
    value = (value or "").strip()
    # strict 24h time (rejects 01:99 etc.)
    return datetime.strptime(value, "%H:%M").time()


_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _entry_dict(e) -> dict:
    """Convert TimeEntry to display dict."""
    return {
        'id': e.id,
        'date': e.work_date.strftime('%d.%m.%y'),
        'date_sort': e.work_date.isoformat(),
        'start': e.start_time.strftime('%H:%M') if e.start_time else '',
        'end': e.end_time.strftime('%H:%M') if e.end_time else '',
        'net': f"{e.net_hours:.2f}",
        'comment': e.comment or '',
        'approved': e.approved,
        'is_rejected': '❌ ABGELEHNT' in (e.comment or '')
    }


class AuthController:
    """Kapselt die reine Geschäftslogik für die Authentifizierung und Benutzerverwaltung."""

    def attempt_login(self, user_id_raw: str, last_name_raw: str, password_raw: str) -> dict:
        try:
            user_id = int(user_id_raw)
        except ValueError:
            return {"status": "error", "message": "ID muss eine Zahl sein"}

        if user_id < 0:
            return {"status": "error", "message": "ID darf nicht negativ sein"}

        last_name = last_name_raw.strip()
        if not last_name:
            return {"status": "error", "message": "Nachname ist erforderlich"}

        password = password_raw.strip()

        with session_scope() as session:
            auth_service = AuthService(session)
            tmp_user = auth_service.requires_password_setup(
                user_id=user_id, last_name=last_name)
            if tmp_user is not None:
                return {"status": "requires_setup", "pending_user_id": tmp_user.id}

            if not password:
                return {"status": "error", "message": "Passwort ist erforderlich"}

            user = auth_service.authenticate(
                user_id=user_id, last_name=last_name, password=password)
            if user is None:
                return {"status": "error", "message": "Login fehlgeschlagen"}

            return {"status": "success", "user_id": user.id}

    # --- NEU: Hier kommt die Logik für das Passwort-Setzen hin ---
    def set_new_password(self, user_id: int, pw1: str, pw2: str) -> dict:
        pw1 = pw1.strip()
        pw2 = pw2.strip()

        # 1. Prüfen ob sie gleich sind
        if pw1 != pw2:
            return {"status": "error", "message": "Passwörter stimmen nicht überein."}

        # 2. Policy prüfen
        if not validate_password_policy(pw1):
            return {"status": "error", "message": "Passwort erfüllt die Policy nicht."}

        # 3. In die Datenbank schreiben
        with session_scope() as session:
            user_service = UserService(session)
            ok = user_service.set_password(user_id=user_id, password=pw1)
            if not ok:
                return {"status": "error", "message": "Konnte Passwort nicht in DB setzen."}

        return {"status": "success"}

    def get_user_info(self, user_id: int) -> dict | None:
        """Holt die grundlegenden Infos für das Dashboard."""
        with session_scope() as session:
            # Wir holen den User anhand der ID
            user = session.get(User, user_id)
            if user is None:
                return None

            # Wir geben nur ein Dictionary zurück, kein Datenbank-Objekt!
            return {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.business_role
            }

    def get_monthly_entries(self, user_id: int, year: int, month: int):
        with session_scope() as session:
            service = TimeEntryService(session)
            entries = service.list_month_entries(
                user_id=user_id, year=year, month=month)
            return [_entry_dict(e) for e in entries]

    def get_monthly_entries_with_total(self, user_id: int, year: int, month: int):
        """Like get_monthly_entries, but also returns the summed net hours."""
        with session_scope() as session:
            service = TimeEntryService(session)
            entries = service.list_month_entries(
                user_id=user_id, year=year, month=month)
            rows = [_entry_dict(e) for e in entries]
            total_month = float(sum(e.net_hours for e in entries))
            return rows, total_month

    def save_time_entry(self, user_id: int, date_str: str, start_s: str, end_s: str, pause_minutes: int, comment: str = "", pause_start: str | None = None, pause_end: str | None = None):
        work_date, error = self._parse_and_validate_date(date_str)
        if error:
            return error

        today = _today_local_date()
        if work_date.year != today.year or work_date.month != today.month:
            return {"status": "error", "message": "Du kannst nur Arbeitszeiten im aktuellen Monat erfassen."}

        start_s = (start_s or "").strip()
        end_s = (end_s or "").strip()
        comment = (comment or "").strip()[:COMMENT_MAX_LENGTH]

        start_t, end_t, error = self._parse_times(start_s, end_s)
        if error:
            return error

        # Parse lunch times if provided
        lunch_start_t = None
        lunch_end_t = None
        if pause_start and pause_end:
            lunch_start_t, lunch_end_t, error = self._parse_lunch_times(
                pause_start, pause_end)
            if error:
                return error
            # Validate lunch interval
            error = self._validate_lunch_interval(
                start_t, end_t, lunch_start_t, lunch_end_t)
            if error:
                return error

        # Pre-calculate gross hours for this entry (before break deduction)
        t_start_dt = datetime.combine(date(1900, 1, 1), start_t)
        t_end_dt = datetime.combine(date(1900, 1, 1), end_t)
        if t_end_dt <= t_start_dt:
            t_end_dt += timedelta(days=1)
        gross_hours = (t_end_dt - t_start_dt).total_seconds() / 3600

        # Calculate lunch break duration if times provided
        lunch_minutes = 0
        if lunch_start_t and lunch_end_t:
            ls_dt = datetime.combine(date(1900, 1, 1), lunch_start_t)
            le_dt = datetime.combine(date(1900, 1, 1), lunch_end_t)
            if le_dt <= ls_dt:
                le_dt += timedelta(days=1)
            lunch_minutes = (le_dt - ls_dt).total_seconds() / 60

        # Total break = lunch break + additional pause_minutes
        total_break_minutes = lunch_minutes + pause_minutes

        # Check minimum break requirement (>= 6h work → >= 30min break) and auto-add if needed
        notifications = []
        missing_break = 0
        if gross_hours >= MIN_BREAK_FOR_AUTO_DEDUCT_HOURS and total_break_minutes < MIN_LUNCH_BREAK_MINUTES:
            # Auto-add missing break time
            missing_break = MIN_LUNCH_BREAK_MINUTES - total_break_minutes
            total_break_minutes = MIN_LUNCH_BREAK_MINUTES
            notifications.append(
                f"Mindestpause von {MIN_LUNCH_BREAK_MINUTES} min automatisch ergänzt ({int(missing_break)} min fehlten).")

        try:
            with session_scope() as session:
                user = session.get(User, user_id)
                if not user:
                    return {"status": "error", "message": "User nicht gefunden"}

                service = TimeEntryService(session)
                existed = service.entry_exists(
                    user_id=user.id, work_date=work_date)

                # Calculate net hours for weekly check (using total break)
                net_hours_for_check = max(
                    0, gross_hours - total_break_minutes / 60)

                # Check weekly hours BEFORE saving (exclude current date to get existing total)
                weekly_before = service.get_weekly_hours(
                    user_id=user.id, any_day_in_week=work_date, exclude_date=work_date)
                projected_weekly = weekly_before + net_hours_for_check

                if projected_weekly > MAX_WEEKLY_HOURS:
                    notifications.append(
                        f"Warnung: Wochenstunden {projected_weekly:.1f}h > {int(MAX_WEEKLY_HOURS)}h!")

                entry = service.upsert_entry(
                    user=user,
                    work_date=work_date,
                    start_hhmm=start_s or "00:00",
                    end_hhmm=end_s or "00:00",
                    lunch_start_hhmm=pause_start if lunch_start_t else None,
                    lunch_end_hhmm=pause_end if lunch_end_t else None,
                    short_break_min=pause_minutes + missing_break,
                )

                if comment:
                    if entry.comment and comment not in entry.comment:
                        entry.comment = f"{comment}; {entry.comment}"
                    else:
                        entry.comment = comment

                # Check for warnings and add notifications
                if entry.comment:
                    if "Überzeit > 12h" in entry.comment:
                        notifications.append(
                            "Warnung: Überzeit > 12h – bitte prüfen.")
                    if "Maximalarbeitszeit Minderjährige: 9h" in entry.comment:
                        notifications.append(
                            "Warnung: Maximalarbeitszeit für Minderjährige überschritten (9h).")
                    if "Nachtarbeit" in entry.comment and "Minderjährige" in entry.comment:
                        notifications.append(
                            "Warnung: Nachtarbeit für Minderjährige (verboten 22-6 Uhr).")

                return {"status": "success", "action": "updated" if existed else "created", "notifications": notifications}
        except Exception as e:
            return {"status": "error", "message": f"Fehler bei der Berechnung: {str(e)}"}

    @staticmethod
    def _parse_and_validate_date(date_str: str) -> tuple:
        try:
            return _parse_date_yyyy_mm_dd(date_str), None
        except Exception:
            return None, {"status": "error", "message": "Bitte geben Sie das Datum im korrekten Format an: YYYY-MM-DD"}

    @staticmethod
    def _parse_times(start_s: str, end_s: str) -> tuple:
        try:
            start_t = _parse_time_hh_mm(start_s or "00:00")
            end_t = _parse_time_hh_mm(end_s or "00:00")
            return start_t, end_t, None
        except Exception:
            return None, None, {"status": "error", "message": "Bitte geben Sie die Zeit im korrekten Format an: hh:mm"}

    @staticmethod
    def _parse_lunch_times(ls_s: str, le_s: str) -> tuple:
        try:
            lunch_start_t = _parse_time_hh_mm(ls_s) if ls_s else None
            lunch_end_t = _parse_time_hh_mm(le_s) if le_s else None
            return lunch_start_t, lunch_end_t, None
        except Exception:
            return None, None, {"status": "error", "message": "Bitte geben Sie die Zeit im korrekten Format an: hh:mm"}

    @staticmethod
    def _validate_lunch_interval(start_t, end_t, lunch_start_t, lunch_end_t) -> dict | None:
        if (lunch_start_t is None) ^ (lunch_end_t is None):
            return {"status": "error", "message": "Bitte Mittag Start und Ende vollständig ausfüllen (oder beide leer lassen)."}

        if lunch_start_t is not None and lunch_end_t is not None:
            if not _is_time_in_interval(t=lunch_start_t, start=start_t, end=end_t):
                return {"status": "error", "message": "Mittag Start muss innerhalb der Arbeitszeit liegen."}
            if not _is_time_in_interval(t=lunch_end_t, start=start_t, end=end_t):
                return {"status": "error", "message": "Mittag Ende muss innerhalb der Arbeitszeit liegen."}
            if _work_interval_minutes(start=start_t, end=end_t) <= 0:
                return {"status": "error", "message": "Arbeitszeit ist ungültig."}
        return None

    def _calc_break_display(self, entry) -> str:
        """Calculate total break duration from lunch break and short break."""
        total_min = entry.short_break_min or 0

        # Calculate lunch break duration if both times are set
        if entry.lunch_start and entry.lunch_end:
            lunch_start_dt = datetime.combine(
                datetime(1900, 1, 1), entry.lunch_start)
            lunch_end_dt = datetime.combine(
                datetime(1900, 1, 1), entry.lunch_end)
            if lunch_end_dt <= lunch_start_dt:
                lunch_end_dt += timedelta(days=1)
            lunch_min = (lunch_end_dt - lunch_start_dt).total_seconds() / 60
            total_min += int(lunch_min)

        if total_min == 0:
            return '-'
        hours, mins = divmod(total_min, 60)
        return f"{hours:02d}:{mins:02d}"

    def get_weekly_entries(self, user_id: int, week_offset: int = 0):
        with session_scope() as session:
            service = TimeEntryService(session)
            # Berechne den Referenz-Tag basierend auf dem Offset
            target_date = _today_local_date() + timedelta(weeks=week_offset)

            entries = service.list_week_entries(
                user_id=user_id, any_day_in_week=target_date)

            # Wichtig: Sortierung umkehren, damit das aktuellste Datum oben steht
            entries.sort(key=lambda e: e.work_date, reverse=True)

            total_week = sum(e.net_hours for e in entries)
            rows = [{
                'date': e.work_date.strftime('%a, %d.%m.'),
                'date_sort': e.work_date.isoformat(),
                'start': e.start_time.strftime('%H:%M') if e.start_time else '-',
                'end': e.end_time.strftime('%H:%M') if e.end_time else '-',
                'net': f"{e.net_hours:.2f} h",
                'comment': e.comment or '',
                'approved': e.approved,
                'is_rejected': '❌ ABGELEHNT' in (e.comment or '')
            } for e in entries]

            return rows, total_week

    def get_unapproved_entries(self):
        with session_scope() as session:
            service = TimeEntryService(session)
            entries = service.list_unapproved_entries()

            return [{
                'id': e.id,
                'user': f"{e.user.first_name} {e.user.last_name}",
                'date': e.work_date.strftime('%d.%m.%Y'),
                'date_sort': e.work_date.isoformat(),
                'hours': f"{e.net_hours:.2f} h",
                'comment': e.comment or ''
            } for e in entries if "❌ ABGELEHNT" not in (e.comment or "")]

    def get_entries_for_approval(self, user_id: int | None = None, year: int | None = None, month: int | None = None):
        """Holt Einträge für die Freigabe mit optionalen Filtern."""
        with session_scope() as session:
            service = TimeEntryService(session)
            entries = service.list_entries_for_approval(
                user_id=user_id, year=year, month=month, approved_only=False
            )

            return [{
                'id': e.id,
                'user_id': e.user_id,
                'user': f"{e.user.first_name} {e.user.last_name}",
                'date': e.work_date.strftime('%d.%m.%Y'),
                'date_sort': e.work_date.isoformat(),
                'start': e.start_time.strftime('%H:%M') if e.start_time else '',
                'end': e.end_time.strftime('%H:%M') if e.end_time else '',
                'break': self._calc_break_display(e),
                'hours': f"{e.net_hours:.2f} h",
                'net_hours': e.net_hours,
                'comment': e.comment or '',
                'approved': e.approved
            } for e in entries if "❌ ABGELEHNT" not in (e.comment or "")]

    def get_approved_entries(self, user_id: int | None = None, year: int | None = None, month: int | None = None):
        """Holt genehmigte Einträge mit optionalen Filtern."""
        with session_scope() as session:
            service = TimeEntryService(session)
            entries = service.list_entries_for_approval(
                user_id=user_id, year=year, month=month, approved_only=True
            )

            return [{
                'id': e.id,
                'user_id': e.user_id,
                'user': f"{e.user.first_name} {e.user.last_name}",
                'date': e.work_date.strftime('%d.%m.%Y'),
                'date_sort': e.work_date.isoformat(),
                'start': e.start_time.strftime('%H:%M') if e.start_time else '',
                'end': e.end_time.strftime('%H:%M') if e.end_time else '',
                'break': self._calc_break_display(e),
                'hours': f"{e.net_hours:.2f} h",
                'net_hours': e.net_hours,
                'comment': e.comment or '',
                'approved': e.approved
            } for e in entries if "❌ ABGELEHNT" not in (e.comment or "")]

    def get_all_employees(self):
        """Holt alle Mitarbeiter für die Filter-Liste."""
        with session_scope() as session:
            users = session.query(User).all()
            return [{
                'id': u.id,
                'name': f"{u.first_name} {u.last_name}"
            } for u in users]

    def approve_entries_batch(self, entry_ids: list[int]):
        """Genehmigt mehrere Einträge auf einmal."""
        if not entry_ids:
            return 0
        with session_scope() as session:
            service = TimeEntryService(session)
            count = service.approve_entries_batch(entry_ids)
            return count

    def approve_entry(self, entry_id: int):
        """Gibt einen spezifischen Eintrag frei"""
        with session_scope() as session:
            service = TimeEntryService(session)
            success = service.approve_entry(entry_id=entry_id)
            return success

    def reject_entry(self, entry_id: int, reason: str):
        with session_scope() as session:
            # Eintrag laden
            entry = session.get(TimeEntry, entry_id)
            if entry:
                # Wir hängen die Ablehnung an den Kommentar an
                original_comment = entry.comment or ""
                entry.comment = f"{original_comment} | ❌ ABGELEHNT: {reason}".strip(
                    " | ")
                # Status bleibt auf approved=False
                return True
            return False

    def get_all_users(self):
        """Holt alle Benutzer für die Verwaltungs-Liste"""
        with session_scope() as session:
            users = session.query(User).all()
            return [{
                'id': u.id,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'email': u.email,
                'role': u.business_role,
                'birthdate': u.birthdate
            } for u in users]

    def upsert_user(self, user_data: dict):
        """Erstellt einen neuen User oder aktualisiert einen bestehenden"""
        # --- Validierung ---
        first_name = str(user_data.get('first_name') or '').strip()
        last_name = str(user_data.get('last_name') or '').strip()
        email = str(user_data.get('email') or '').strip()
        role = str(user_data.get('role') or '').strip()

        if not first_name or not last_name:
            return {"status": "error", "message": "Vorname und Nachname sind erforderlich."}

        if len(first_name) > NAME_MAX_LENGTH:
            return {"status": "error", "message": f"Vorname ist zu lang (max. {NAME_MAX_LENGTH} Zeichen)."}
        if len(last_name) > NAME_MAX_LENGTH:
            return {"status": "error", "message": f"Nachname ist zu lang (max. {NAME_MAX_LENGTH} Zeichen)."}

        if not email:
            return {"status": "error", "message": "E-Mail ist erforderlich."}

        if not _EMAIL_RE.match(email):
            return {"status": "error", "message": "Bitte geben Sie eine gültige E-Mail-Adresse ein."}

        if len(email) > EMAIL_MAX_LENGTH:
            return {"status": "error", "message": f"E-Mail ist zu lang (max. {EMAIL_MAX_LENGTH} Zeichen)."}

        if role not in VALID_ROLES:
            return {"status": "error", "message": "Ungültige Rolle."}

        # Parse birthdate
        birthdate = None
        birthdate_str = user_data.get('birthdate')
        if birthdate_str:
            try:
                birthdate = _parse_date_yyyy_mm_dd(birthdate_str)
            except Exception:
                return {"status": "error", "message": "Geburtsdatum muss im Format YYYY-MM-DD sein."}

            is_valid_age, error_message = validate_user_age(birthdate)
            if not is_valid_age:
                return {"status": "error", "message": error_message}

        provided_id = user_data.get('id')

        with session_scope() as session:
            # Check if we're updating an existing user
            is_update = False
            if provided_id is not None:
                existing_user = session.get(User, provided_id)
                is_update = existing_user is not None

            # Check if the provided ID is already taken by another user
            if not is_update and provided_id is not None:
                existing_with_id = session.query(User).filter(
                    User.id == provided_id).first()
                if existing_with_id:
                    return {"status": "error", "message": f"Diese ID {provided_id} ist bereits vergeben."}

            # Unique-Check (case-insensitive) - allow keeping own email on update
            for u in session.query(User).filter(User.email.ilike(email)).all():
                if not is_update or u.id != provided_id:
                    return {"status": "error", "message": "Diese E-Mail ist bereits vergeben."}

            if is_update:
                user = session.get(User, provided_id)
            elif provided_id is not None:
                # New user with custom ID
                user = User()
                user.id = provided_id
                user.password_hash = ""
                user.must_change_password = True
                session.add(user)
            else:
                user = User()
                user.password_hash = ""
                user.must_change_password = True
                session.add(user)

            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.business_role = role
            user.birthdate = birthdate
            return {"status": "success"}

    def reset_password(self, user_id: int):
        """Setzt das Passwort auf ein Standard-Passwort zurück"""
        with session_scope() as session:
            user = session.get(User, user_id)
            if user:
                user.password_hash = ""
                return True
            return False

    def delete_user(self, user_id: int):
        """Löscht den Mitarbeiter komplett aus der Datenbank"""
        with session_scope() as session:
            user = session.get(User, user_id)
            if user:
                session.delete(user)
                return True
            return False

    def run_csv_import(self, user_id, csv_bytes):
        with session_scope() as session:
            service = TimeEntryService(session)
            user = session.get(User, user_id)
            if not user:
                return 0, 0, ["User nicht gefunden"]
            return service.import_csv(user=user, csv_bytes=csv_bytes, overwrite=True)
