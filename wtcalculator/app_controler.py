from .db import session_scope
from .services.auth_service import AuthService
from .services.user_service import UserService
from .security import validate_password_policy
from .models import User, TimeEntry
from .services.time_entry_service import TimeEntryService
from datetime import datetime, timedelta
import os

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


class AuthController:
    """Kapselt die reine Geschäftslogik für die Authentifizierung und Benutzerverwaltung."""

    def attempt_login(self, user_id_raw: str, last_name_raw: str, password_raw: str) -> dict:
        # ... (Dein bestehender Code für attempt_login bleibt hier exakt gleich) ...
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

    def save_time_entry(self, user_id: int, date_str: str, start_s: str, end_s: str, ls_s: str, le_s: str):
        try:
            # Das Datum in ein date-Objekt umwandeln
            work_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            with session_scope() as session:
                # 1. Wir brauchen das User-Objekt für den Service
                user = session.get(User, user_id)
                if not user:
                    return {"status": "error", "message": "User nicht gefunden"}

                service = TimeEntryService(session)

                # 2. Aufruf der richtigen Funktion: upsert_entry
                # WICHTIG: Die Parameter müssen exakt so heißen wie im Service!
                service.upsert_entry(
                    user=user,
                    work_date=work_date,
                    start_hhmm=start_s or "00:00",
                    end_hhmm=end_s or "00:00",
                    lunch_start_hhmm=ls_s if ls_s else None,
                    lunch_end_hhmm=le_s if le_s else None,
                    short_break_min=0  # Falls du kein Feld dafür hast, setzen wir 0
                )

                return {"status": "success"}
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
        with session_scope() as session:
            if user_data.get('id'):
                user = session.get(User, user_data['id'])
            else:
                user = User()
                # Standard-Passwort für neue User (z.B. Nachname123)
                user.password = f"{user_data['last_name']}123"
                session.add(user)

            user.first_name = user_data['first_name']
            user.last_name = user_data['last_name']
            user.email = user_data['email']
            user.business_role = user_data['role']
            user.age = int(user_data['age'])
            return True

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
            # Ruft deine bereits existierende Methode im Service auf
            return service.import_csv(user=user, csv_bytes=csv_bytes, overwrite=True)
