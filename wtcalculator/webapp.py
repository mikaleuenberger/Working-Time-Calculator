from datetime import datetime
from nicegui import ui, app
from .app_controler import AuthController

class LoginPageUI:
    def __init__(self):
        # Wir laden den Controller ein, der die harte Arbeit macht
        self.controller = AuthController()
        
        # UI-Elemente als Eigenschaften (Attribute) der Klasse anlegen
        self.user_id_input = None
        self.last_name_input = None
        self.password_input = None
        
        # Die Seite direkt aufbauen
        self.build_ui()

    def build_ui(self):
        ui.label("WTCalculator – Login").classes("text-h5 text-white")

        with ui.row().classes("w-full justify-center items-stretch q-gutter-xl"):
            
            # --- 1. DIE UHR FUNKTION ---
            def _clock_svg(now: datetime, *, size: int = 260) -> str:
                """Simple inline SVG analog clock (no external assets)."""
                s = int(size)
                c = s / 2
                r = s * 0.42
                hour = now.hour % 12
                minute = now.minute
                second = now.second
                hour_angle = (hour + minute / 60.0) * 30.0 - 90.0
                minute_angle = (minute + second / 60.0) * 6.0 - 90.0
                second_angle = second * 6.0 - 90.0
                
                def hand(angle_deg: float, length: float, width: float) -> str:
                    return (
                        f'<line x1="{c}" y1="{c}" '
                        f'x2="{c + length}" y2="{c}" '
                        f'stroke="rgba(0,0,0,0.65)" stroke-width="{width}" stroke-linecap="round" '
                        f'transform="rotate({angle_deg} {c} {c})" />'
                    )
                
                tick_lines = []
                for i in range(12):
                    ang = i * 30.0 - 90.0
                    x1 = c + (r * 0.88)
                    x2 = c + (r * 0.98)
                    tick_lines.append(
                        f'<line x1="{x1}" y1="{c}" x2="{x2}" y2="{c}" '
                        f'stroke="rgba(0,0,0,0.55)" stroke-width="4" stroke-linecap="round" '
                        f'transform="rotate({ang} {c} {c})" />'
                    )
                return (
                    f'<svg width="{s}" height="{s}" viewBox="0 0 {s} {s}" xmlns="http://www.w3.org/2000/svg">'
                    f'<circle cx="{c}" cy="{c}" r="{r}" fill="rgba(255,255,255,0.55)" stroke="rgba(0,0,0,0.25)" stroke-width="6" />'
                    + "".join(tick_lines)
                    + hand(hour_angle, r * 0.50, 7)
                    + hand(minute_angle, r * 0.72, 5)
                    + f'<line x1="{c}" y1="{c}" x2="{c + r * 0.78}" y2="{c}" '
                    f'stroke="rgba(220,0,0,0.65)" stroke-width="2.5" stroke-linecap="round" '
                    f'transform="rotate({second_angle} {c} {c})" />'
                    + f'<circle cx="{c}" cy="{c}" r="7" fill="rgba(0,0,0,0.55)" />'
                    + '</svg>'
                )

            # --- 2. DIE UHR KARTE (Anzeige & Timer) ---
            with ui.card().classes("w-80 items-center justify-center"):
                ui.label("Uhr").classes("text-h6")
                clock_html = ui.html(_clock_svg(datetime.now(), size=260))
                time_label = ui.label(datetime.now().strftime("%H:%M:%S")).classes("text-h5")
                
                def tick():
                    now = datetime.now()
                    time_label.text = now.strftime("%H:%M:%S")
                    clock_html.content = _clock_svg(now, size=260)
                    clock_html.update()
                    
                ui.timer(1.0, tick)
            
            # --- 3. DIE LOGIN KARTE ---
            with ui.card().classes("w-96"):
                self.user_id_input = (
                    ui.input("ID", placeholder="z.B. 1")
                    .props("type=number").on("keydown.enter", self.do_login)
                )
                self.last_name_input = (
                    ui.input("Nachname", placeholder="z.B. Müller")
                    .on("keydown.enter", self.do_login)
                )
                self.password_input = (
                    ui.input("Passwort", password=True, password_toggle_button=True)
                    .on("keydown.enter", self.do_login)
                )

                ui.button("Login", on_click=self.do_login).props("color=primary w-full")

    def do_login(self):
        # 1. Daten aus der UI lesen
        uid_val = self.user_id_input.value or ""
        lname_val = self.last_name_input.value or ""
        pw_val = self.password_input.value or ""

        # 2. Den Controller (die Business Logik) fragen! Kein Datenbank-Code hier!
        result = self.controller.attempt_login(uid_val, lname_val, pw_val)

        # 3. Auf das Ergebnis reagieren (Die View macht nur noch Darstellung)
        if result["status"] == "error":
            ui.notify(result["message"], color="negative")
            
        elif result["status"] == "requires_setup":
            app.storage.user["pending_user_id"] = result["pending_user_id"]
            ui.notify("Passwort ist noch nicht gesetzt – bitte setzen.", color="warning")
            ui.open("/set-password")
            
        elif result["status"] == "success":
            app.storage.user["user_id"] = result["user_id"]
            ui.open("/dashboard")

class SetPasswordUI:
    def __init__(self):
        self.controller = AuthController()
        
        # UI-Elemente
        self.pw1_input = None
        self.pw2_input = None
        
        self.build_ui()

    def build_ui(self):
        # Wir packen alles in eine Spalte und zentrieren es schön mittig
        with ui.column().classes("w-full items-center mt-12"):
            ui.label('Passwort setzen').classes('text-h5 text-white q-mb-md')
            
            # Etwas mehr "Padding" (q-pa-md) für eine luftigere Karte
            with ui.card().classes("w-96 q-pa-md"):
                self.pw1_input = (
                    ui.input('Neues Passwort', password=True, password_toggle_button=True)
                    .props('outlined') # Das 'dark' und 'white' ist hier jetzt weg!
                    .classes('w-full q-mb-sm')
                    .on('keydown.enter', self.do_save)
                )
                
                self.pw2_input = (
                    ui.input('Passwort bestätigen', password=True, password_toggle_button=True)
                    .props('outlined') 
                    .classes('w-full q-mb-sm')
                    .on('keydown.enter', self.do_save)
                )
                
                ui.label('Policy: mind. 8 Zeichen, 1 Grossbuchstabe, 1 Zahl, 1 Sonderzeichen').classes('text-grey text-caption q-mb-md')
                
                # Die Buttons unten rechts anordnen mit etwas Abstand (q-gutter-sm)
                with ui.row().classes('w-full justify-end q-gutter-sm'):
                    # Auch hier das 'text-white' entfernt, damit der Button auf der weißen Karte lesbar ist
                    ui.button('Abbrechen', on_click=self.do_cancel).props('flat')
                    ui.button('Speichern', on_click=self.do_save).props('color=primary')

    def do_save(self):
        # 1. Daten aus der View holen
        pw1 = self.pw1_input.value or ""
        pw2 = self.pw2_input.value or ""
        
        # 2. Die User-ID aus dem Zwischenspeicher holen (wurde beim Login dort abgelegt)
        pending_user_id = app.storage.user.get('pending_user_id')
        if pending_user_id is None:
            ui.open("/")
            return

        # 3. Den Controller die Arbeit machen lassen!
        result = self.controller.set_new_password(pending_user_id, pw1, pw2)

        # 4. Auf das Ergebnis reagieren
        if result["status"] == "error":
            ui.notify(result["message"], color="negative")
        elif result["status"] == "success":
            app.storage.user.pop('pending_user_id', None) # Zwischenspeicher löschen
            ui.notify('Passwort gesetzt. Bitte einloggen.', color='positive')
            ui.open('/')

    def do_cancel(self):
        # Wenn der User abbricht, löschen wir die ID und werfen ihn zum Login zurück
        app.storage.user.pop('pending_user_id', None)
        ui.open('/')

class DashboardUI:
    def __init__(self, user_id: int):
        self.controller = AuthController()
        self.user_id = user_id
        
        # 1. Daten über den Controller abfragen
        self.user_info = self.controller.get_user_info(self.user_id)
        
        # Sicherheitscheck: Falls der User in der DB nicht (mehr) existiert
        if self.user_info is None:
            self.do_logout()
            return
            
        # 2. UI aufbauen
        self.build_ui()

    def build_ui(self):
        # Den dunklen Hintergrund auch hier setzen (falls gewünscht, ansonsten text-white unten entfernen)
               
        # --- HEADER (Kopfzeile) ---
        with ui.row().classes("items-center justify-between w-full q-pa-md bg-dark shadow-2"):
            with ui.row().classes("items-center q-gutter-md"):
                ui.label(f"Hallo, {self.user_info['first_name']} {self.user_info['last_name']}").classes("text-h6 text-white")
                ui.label(f"Rolle: {self.user_info['role']}").classes("text-grey")
                
            ui.button("Logout", on_click=self.do_logout).props("flat color=primary")

        # --- HAUPTBEREICH (Je nach Rolle) ---
        ui.separator()
        
        with ui.column().classes("w-full q-pa-md items-center"):
            if self.user_info['role'] == "Vorgesetzter":
                # Hier rufen wir später die ausgelagerte Vorgesetzten-Ansicht auf
                ui.label("👷 Vorgesetzten-Ansicht im Bau 👷").classes("text-h5 text-white mt-8")
            else:
                EmployeeDashboardUI(self.user_id)

    def do_logout(self):
        # User-Daten aus dem Browser-Speicher löschen
        app.storage.user.clear()
        # Zurück zum Login werfen
        ui.open('/')

class EmployeeDashboardUI:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.controller = AuthController()
        self.current_date = datetime.now().strftime('%Y-%m-%d')
        self.build_ui()

    def build_ui(self):
        with ui.tabs().classes('w-full') as tabs:
            self.tab_entry = ui.tab('Erfassung')
            self.tab_week = ui.tab('Woche')
            self.tab_import = ui.tab('CSV Import')

        with ui.tab_panels(tabs, value=self.tab_entry).classes('w-full bg-transparent'):
            with ui.tab_panel(self.tab_entry):
                self.render_entry_panel()
            with ui.tab_panel(self.tab_week):
                self.render_week_panel()
            with ui.tab_panel(self.tab_import):
                ui.label("Import (folgt)").classes("text-white")

    def render_entry_panel(self):
        with ui.column().classes('w-full items-center q-gutter-y-md'):
            # Die Eingabe-Karte
            with ui.card().classes('w-full max-w-4xl q-pa-md shadow-5'):
                ui.label('Neuen Eintrag erfassen').classes('text-h6 q-mb-sm')
                
                with ui.row().classes('w-full items-start justify-between q-gutter-md'):
                    # Linke Spalte: Datum (Kompakt als Input mit Popup)
                    with ui.column().classes('flex-1'):
                        with ui.input('Datum').bind_value(self, 'current_date') as date_input:
                            self.current_date = datetime.now().strftime('%Y-%m-%d')
                            with ui.menu() as menu:
                                ui.date().bind_value(date_input)
                        
                        self.comment_input = ui.input('Kommentar (optional)').classes('w-full')

                    # Mittlere Spalte: Arbeitszeit
                    with ui.column().classes('flex-1'):
                        self.start_input = ui.input('Beginn', value='08:00').props('mask="##:##" outlined')
                        self.end_input = ui.input('Ende', value='17:00').props('mask="##:##" outlined')

                    # Rechte Spalte: Pause
                    with ui.column().classes('flex-1'):
                        self.l_start_input = ui.input('Mittag Start', value='12:00').props('mask="##:##" dense')
                        self.l_end_input = ui.input('Mittag Ende', value='13:00').props('mask="##:##" dense')

                with ui.row().classes('w-full justify-end mt-4'):
                    ui.button('Eintrag Speichern', on_click=self.save_entry).props('color=primary icon=save')

            # Die Tabelle (Aktueller Monat)
            with ui.card().classes('w-full max-w-4xl q-pa-none'):
                with ui.row().classes('q-pa-md items-center justify-between w-full'):
                    ui.label('Aktueller Monat').classes('text-h6')
                    ui.button(icon='refresh', on_click=self.refresh_month_table).props('flat')
                
                columns = [
                    {'name': 'date', 'label': 'Datum', 'field': 'date', 'align': 'left'},
                    {'name': 'start', 'label': 'Start', 'field': 'start'},
                    {'name': 'end', 'label': 'Ende', 'field': 'end'},
                    {'name': 'net', 'label': 'Netto (h)', 'field': 'net', 'classes': 'font-bold'},
                    {'name': 'approved', 'label': 'Status', 'field': 'approved'},
                ]
                self.month_table = ui.table(columns=columns, rows=[]).classes('w-full')
                self.refresh_month_table()

    def refresh_month_table(self):
        now = datetime.now()
        data = self.controller.get_monthly_entries(self.user_id, now.year, now.month)
        self.month_table.rows = data

    def save_entry(self):
        # Wir holen die Werte jetzt direkt aus den Attributen, die wir in build_ui definiert haben
        res = self.controller.save_time_entry(
            user_id=self.user_id, 
            date_str=self.current_date,      # Hier liegt jetzt das Datum
            start_s=self.start_input.value, 
            end_s=self.end_input.value,
            ls_s=self.l_start_input.value,
            le_s=self.l_end_input.value
        )
        
        if res["status"] == "success":
            ui.notify("Eintrag erfolgreich gespeichert!", color="positive")
            self.refresh_month_table()
            self.refresh_week_table()
        else:
            ui.notify(f"Fehler: {res['message']}", color="negative")
    def render_week_panel(self):
        with ui.column().classes('w-full items-center q-gutter-y-md'):
            with ui.card().classes('w-full max-w-4xl q-pa-none shadow-5'):
                with ui.row().classes('q-pa-md items-center justify-between w-full'):
                    with ui.column():
                        ui.label('Wochenübersicht').classes('text-h6')
                        # Hier speichern wir das Label für die Summe, um es später zu aktualisieren
                        self.week_total_label = ui.label('Gesamt: 0.00 h').classes('text-subtitle1 text-primary font-bold')
                    ui.button(icon='refresh', on_click=self.refresh_week_table).props('flat')

                columns = [
                    {'name': 'date', 'label': 'Datum', 'field': 'date', 'align': 'left'},
                    {'name': 'start', 'label': 'Beginn', 'field': 'start'},
                    {'name': 'end', 'label': 'Ende', 'field': 'end'},
                    {'name': 'net', 'label': 'Netto', 'field': 'net'},
                    {'name': 'comment', 'label': 'Kommentar', 'field': 'comment', 'align': 'left'},
                ]
                self.week_table = ui.table(columns=columns, rows=[]).classes('w-full')
                self.refresh_week_table()

    def refresh_week_table(self):
        # Wir holen die Daten und die Summe vom Controller
        rows, total = self.controller.get_weekly_entries(self.user_id)
        self.week_table.rows = rows
        self.week_total_label.text = f"Gesamt diese Woche: {total:.2f} h"