from .db import session_scope
from .services.auth_service import AuthService
from .services.user_service import UserService
from .security import validate_password_policy
from .models import User, TimeEntry
from .services.time_entry_service import TimeEntryService
from datetime import datetime, timedelta
from datetime import time as dtime
import os
import re

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore


def _today_local_date():
    tz_name = os.environ.get('WTCALC_TZ', 'Europe/Zurich')
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


class AuthController:
    """Kapselt die reine Geschäftslogik für die Authentifizierung und Benutzerverwaltung."""

    def attempt_login(self, user_id_raw: str, last_name_raw: str, password_raw: str) -> dict:
        try:
            user_id = int(user_id_raw)
        except ValueError:
            return {"status": "error", "message": "ID muss eine Zahl sein"}

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
            return [{
                'id': e.id,
                'date': e.work_date.strftime('%d.%m.%y'),
                'start': e.start_time.strftime('%H:%M') if e.start_time else '',
                'end': e.end_time.strftime('%H:%M') if e.end_time else '',
                'net': f"{e.net_hours:.2f}",
                'comment': e.comment or '',
                'approved': '✅' if e.approved else '⏳'
            } for e in entries]

    def get_monthly_entries_with_total(self, user_id: int, year: int, month: int):
        """Like get_monthly_entries, but also returns the summed net hours."""
        with session_scope() as session:
            service = TimeEntryService(session)
            entries = service.list_month_entries(
                user_id=user_id, year=year, month=month)

            total_month = float(sum(e.net_hours for e in entries))
            rows = [{
                'id': e.id,
                'date': e.work_date.strftime('%d.%m.%y'),
                'start': e.start_time.strftime('%H:%M') if e.start_time else '',
                'end': e.end_time.strftime('%H:%M') if e.end_time else '',
                'net': f"{e.net_hours:.2f}",
                'comment': e.comment or '',
                'approved': '✅' if e.approved else '⏳'
            } for e in entries]

            return rows, total_month

    def save_time_entry(self, user_id: int, date_str: str, start_s: str, end_s: str, ls_s: str, le_s: str, comment: str = ""):
        try:
            try:
                work_date = _parse_date_yyyy_mm_dd(date_str)
            except Exception:
                return {"status": "error", "message": "Bitte geben Sie das Datum im korrekten Format an: YYYY-MM-DD"}

            # Nur aktueller Monat darf erfasst werden (lokale Zeitzone)
            today = _today_local_date()
            if work_date.year != today.year or work_date.month != today.month:
                return {"status": "error", "message": "Du kannst nur Arbeitszeiten im aktuellen Monat erfassen."}

            # Input trim + Kommentar limit (30 Zeichen)
            start_s = (start_s or "").strip()
            end_s = (end_s or "").strip()
            ls_s = (ls_s or "").strip()
            le_s = (le_s or "").strip()
            comment = (comment or "").strip()[:30]

            # Validate basic time parsing so we can do pause checks
            try:
                start_t = _parse_time_hh_mm(start_s or "00:00")
                end_t = _parse_time_hh_mm(end_s or "00:00")
            except Exception:
                return {"status": "error", "message": "Bitte geben Sie die Zeit im korrekten Format an: hh:mm"}

            try:
                lunch_start_t = _parse_time_hh_mm(ls_s) if ls_s else None
                lunch_end_t = _parse_time_hh_mm(le_s) if le_s else None
            except Exception:
                return {"status": "error", "message": "Bitte geben Sie die Zeit im korrekten Format an: hh:mm"}

            # Pause muss innerhalb Arbeitszeit sein
            if (lunch_start_t is None) ^ (lunch_end_t is None):
                return {"status": "error", "message": "Bitte Mittag Start und Ende vollständig ausfüllen (oder beide leer lassen)."}

            if lunch_start_t is not None and lunch_end_t is not None:
                if not _is_time_in_interval(t=lunch_start_t, start=start_t, end=end_t):
                    return {"status": "error", "message": "Mittag Start muss innerhalb der Arbeitszeit liegen."}
                if not _is_time_in_interval(t=lunch_end_t, start=start_t, end=end_t):
                    return {"status": "error", "message": "Mittag Ende muss innerhalb der Arbeitszeit liegen."}

                # for sanity: lunch must not be longer than work interval
                if _work_interval_minutes(start=start_t, end=end_t) <= 0:
                    return {"status": "error", "message": "Arbeitszeit ist ungültig."}

            with session_scope() as session:
                # 1. Wir brauchen das User-Objekt für den Service
                user = session.get(User, user_id)
                if not user:
                    return {"status": "error", "message": "User nicht gefunden"}

                service = TimeEntryService(session)

                existed = service.entry_exists(user_id=user.id, work_date=work_date)

                # 2. Aufruf der richtigen Funktion: upsert_entry
                # WICHTIG: Die Parameter müssen exakt so heißen wie im Service!
                entry = service.upsert_entry(
                    user=user,
                    work_date=work_date,
                    start_hhmm=start_s or "00:00",
                    end_hhmm=end_s or "00:00",
                    lunch_start_hhmm=ls_s if ls_s else None,
                    lunch_end_hhmm=le_s if le_s else None,
                    short_break_min=0  # Falls du kein Feld dafür hast, setzen wir 0
                )

                # User-Kommentar speichern (bei Anpassung ebenfalls)
                if comment:
                    # kombiniere Regel-Kommentar (vom Calculator) + User-Notiz
                    if entry.comment and comment not in entry.comment:
                        entry.comment = f"{comment}; {entry.comment}"
                    else:
                        entry.comment = comment

                return {"status": "success", "action": "updated" if existed else "created"}
        except Exception as e:
            # Falls z.B. calculate_net_hours_and_comment einen Fehler wirft
            return {"status": "error", "message": f"Fehler bei der Berechnung: {str(e)}"}

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
                'start': e.start_time.strftime('%H:%M') if e.start_time else '-',
                'end': e.end_time.strftime('%H:%M') if e.end_time else '-',
                'net': f"{e.net_hours:.2f} h",
                'comment': e.comment or ''
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
                'hours': f"{e.net_hours:.2f} h",
                'comment': e.comment or ''
            } for e in entries if "❌ ABGELEHNT" not in (e.comment or "")]

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
                'age': u.age
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

        if len(first_name) > 20:
            return {"status": "error", "message": "Vorname ist zu lang (max. 50 Zeichen)."}
        if len(last_name) > 20:
            return {"status": "error", "message": "Nachname ist zu lang (max. 50 Zeichen)."}

        if not email:
            return {"status": "error", "message": "E-Mail ist erforderlich."}

        if not _EMAIL_RE.match(email):
            return {"status": "error", "message": "Bitte geben Sie eine gültige E-Mail-Adresse ein."}

        if len(email) > 30:
            return {"status": "error", "message": "E-Mail ist zu lang (max. 255 Zeichen)."}

        allowed_roles = {"Mitarbeiter", "Vorgesetzter"}
        if role not in allowed_roles:
            return {"status": "error", "message": "Ungültige Rolle."}

        try:
            age = int(user_data.get('age'))
        except Exception:
            return {"status": "error", "message": "Alter muss eine ganze Zahl sein."}

        if age < 14 or age > 100:
            return {"status": "error", "message": "Alter muss zwischen 14 und 100 liegen."}

        with session_scope() as session:
            # Unique-Check (case-insensitive) - allow keeping own email on update
            current_id = user_data.get('id')
            for u in session.query(User).filter(User.email.ilike(email)).all():
                if current_id is None or u.id != current_id:
                    return {"status": "error", "message": "Diese E-Mail ist bereits vergeben."}

            if user_data.get('id'):
                user = session.get(User, user_data['id'])
            else:
                user = User()
                # Standard-Passwort für neue User (z.B. Nachname123)
                user.password = f"{user_data['last_name']}123"
                session.add(user)

            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.business_role = role
            user.age = age
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
