from .db import session_scope
from .services.auth_service import AuthService
from .services.user_service import UserService
from .security import validate_password_policy
from .models import User
from .services.time_entry_service import TimeEntryService
from datetime import datetime

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
            tmp_user = auth_service.requires_password_setup(user_id=user_id, last_name=last_name)
            if tmp_user is not None:
                return {"status": "requires_setup", "pending_user_id": tmp_user.id}

            if not password:
                return {"status": "error", "message": "Passwort ist erforderlich"}

            user = auth_service.authenticate(user_id=user_id, last_name=last_name, password=password)
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
            entries = service.list_month_entries(user_id=user_id, year=year, month=month)
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
                    short_break_min=0 # Falls du kein Feld dafür hast, setzen wir 0
                )
                
                return {"status": "success"}
        except Exception as e:
            # Falls z.B. calculate_net_hours_and_comment einen Fehler wirft
            return {"status": "error", "message": f"Fehler bei der Berechnung: {str(e)}"}
    def get_weekly_entries(self, user_id: int):
        with session_scope() as session:
            service = TimeEntryService(session)
            # Wir nehmen das heutige Datum als Referenz für "diese Woche"
            today = datetime.now().date()
            entries = service.list_week_entries(user_id=user_id, any_day_in_week=today)
            
            # Summe der Woche berechnen
            total_week = sum(e.net_hours for e in entries)
            
            rows = [{
                'date': e.work_date.strftime('%a, %d.%m.'),
                'start': e.start_time.strftime('%H:%M') if e.start_time else '-',
                'end': e.end_time.strftime('%H:%M') if e.end_time else '-',
                'net': f"{e.net_hours:.2f} h",
                'comment': e.comment or ''
            } for e in entries]
            
            return rows, total_week