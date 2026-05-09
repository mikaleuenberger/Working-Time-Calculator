from datetime import datetime
import os

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore
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

                def _now() -> datetime:
                    """Return current time in configured timezone.

                    Railway containers often run in UTC, which shows a 2h offset
                    for Europe/Zurich in summer time.
                    """

                    tz_name = os.environ.get("WTCALC_TZ", "Europe/Zurich")
                    if ZoneInfo is None:
                        return datetime.now()
                    try:
                        return datetime.now(ZoneInfo(tz_name))
                    except Exception:
                        return datetime.now()

                clock_html = ui.html(_clock_svg(_now(), size=260))
                time_label = ui.label(_now().strftime("%H:%M:%S")).classes("text-h5")

                def tick():
                    now = _now()
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
                    ui.input("Passwort", password=True,
                             password_toggle_button=True)
                    .on("keydown.enter", self.do_login)
                )

                ui.button("Login", on_click=self.do_login).props(
                    "color=primary w-full")

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
            ui.notify(
                "Passwort ist noch nicht gesetzt – bitte setzen.", color="warning")
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
                    ui.input('Neues Passwort', password=True,
                             password_toggle_button=True)
                    # Das 'dark' und 'white' ist hier jetzt weg!
                    .props('outlined')
                    .classes('w-full q-mb-sm')
                    .on('keydown.enter', self.do_save)
                )

                self.pw2_input = (
                    ui.input('Passwort bestätigen', password=True,
                             password_toggle_button=True)
                    .props('outlined')
                    .classes('w-full q-mb-sm')
                    .on('keydown.enter', self.do_save)
                )

                ui.label('Policy: mind. 8 Zeichen, 1 Grossbuchstabe, 1 Zahl, 1 Sonderzeichen').classes(
                    'text-grey text-caption q-mb-md')

                # Die Buttons unten rechts anordnen mit etwas Abstand (q-gutter-sm)
                with ui.row().classes('w-full justify-end q-gutter-sm'):
                    # Auch hier das 'text-white' entfernt, damit der Button auf der weißen Karte lesbar ist
                    ui.button('Abbrechen', on_click=self.do_cancel).props(
                        'flat')
                    ui.button('Speichern', on_click=self.do_save).props(
                        'color=primary')

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
            # Zwischenspeicher löschen
            app.storage.user.pop('pending_user_id', None)
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
        # --- HEADER ---
        with ui.row().classes("items-center justify-between w-full q-pa-md bg-dark shadow-2"):
            with ui.row().classes("items-center q-gutter-md"):
                ui.label(f"Hallo, {self.user_info['first_name']} {self.user_info['last_name']}").classes(
                    "text-h6 text-white")
                ui.label(f"Rolle: {self.user_info['role']}").classes(
                    "text-grey")
            ui.button("Logout", on_click=self.do_logout).props(
                "flat color=primary")

        ui.separator()

        # --- HAUPTBEREICH ---
        with ui.column().classes("w-full q-pa-md items-center"):
            if self.user_info['role'] == "Vorgesetzter":
                # Tabs mit Styling-Klassen
                with ui.tabs().classes('w-full bg-dark shadow-2 text-grey-5') \
                        .props('active-color=primary active-bg-color=grey-9 indicator-color=primary') as tabs:

                    t1 = ui.tab('Freigaben', icon='check_circle')
                    t2 = ui.tab('Mitarbeiter', icon='people')

                with ui.tab_panels(tabs, value=t1).classes('w-full bg-transparent'):
                    with ui.tab_panel(t1):
                        SupervisorDashboardUI()
                    with ui.tab_panel(t2):
                        UserAdminUI()
            else:
                # Mitarbeiteransicht
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
        self.current_date = _now().strftime('%Y-%m-%d')
        self.week_offset = 0
        self.build_ui()

    def build_ui(self):
        with ui.tabs().classes('w-full bg-dark shadow-2 text-grey-5') \
                .props('active-color=primary active-bg-color=grey-9 indicator-color=primary expand') as tabs:
            self.tab_entry = ui.tab('Erfassung', icon='edit_calendar')
            self.tab_week = ui.tab('Woche', icon='view_week')
            self.tab_import = ui.tab('CSV Import', icon='file_upload')

        with ui.tab_panels(tabs, value=self.tab_entry).classes('w-full bg-transparent'):
            with ui.tab_panel(self.tab_entry):
                self.render_entry_panel()
            with ui.tab_panel(self.tab_week):
                self.render_week_panel()
            with ui.tab_panel(self.tab_import):
                self.render_import_panel()

    def render_entry_panel(self):
        with ui.column().classes('w-full items-center q-gutter-y-md'):
            # Die Eingabe-Karte
            with ui.card().classes('w-full max-w-4xl q-pa-md shadow-5'):
                ui.label('Neuen Eintrag erfassen').classes('text-h6 q-mb-sm')

                with ui.row().classes('w-full items-start justify-between q-gutter-md'):
                    # Linke Spalte: Datum (Kompakt als Input mit Popup)
                    with ui.column().classes('flex-1'):
                        with ui.input('Datum').bind_value(self, 'current_date') as date_input:
                            self.current_date = _now().strftime('%Y-%m-%d')
                            with ui.menu() as menu:
                                ui.date().bind_value(date_input)

                        self.comment_input = ui.input(
                            'Kommentar (optional)').classes('w-full')

                    # Mittlere Spalte: Arbeitszeit
                    with ui.column().classes('flex-1'):
                        self.start_input = ui.input(
                            'Beginn', value='08:00').props('mask="##:##" outlined')
                        self.end_input = ui.input('Ende', value='17:00').props(
                            'mask="##:##" outlined')

                    # Rechte Spalte: Pause
                    with ui.column().classes('flex-1'):
                        self.l_start_input = ui.input(
                            'Mittag Start', value='12:00').props('mask="##:##" dense')
                        self.l_end_input = ui.input(
                            'Mittag Ende', value='13:00').props('mask="##:##" dense')

                with ui.row().classes('w-full justify-end mt-4'):
                    ui.button('Eintrag Speichern', on_click=self.save_entry).props(
                        'color=primary icon=save')

            # Die Tabelle (Aktueller Monat)
            with ui.card().classes('w-full max-w-4xl q-pa-none'):
                with ui.row().classes('q-pa-md items-center justify-between w-full'):
                    ui.label('Aktueller Monat').classes('text-h6')
                    ui.button(icon='refresh',
                              on_click=self.refresh_month_table).props('flat')

                columns = [
                    {'name': 'date', 'label': 'Datum',
                        'field': 'date', 'align': 'left'},
                    {'name': 'start', 'label': 'Start', 'field': 'start'},
                    {'name': 'end', 'label': 'Ende', 'field': 'end'},
                    {'name': 'net',
                        'label': 'Netto (h)', 'field': 'net', 'classes': 'font-bold'},
                    {'name': 'approved', 'label': 'Status', 'field': 'approved'},
                ]
                self.month_table = ui.table(
                    columns=columns, rows=[]).classes('w-full')
                self.refresh_month_table()

    def refresh_month_table(self):
        now = _now()
        data = self.controller.get_monthly_entries(
            self.user_id, now.year, now.month)
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
                        self.week_total_label = ui.label('Gesamt: 0.00 h').classes(
                            'text-subtitle1 text-primary font-bold')
                    with ui.row().classes('items-center q-gutter-sm'):
                        ui.button(icon='chevron_left',
                                  on_click=self.prev_week).props('flat round')
                        ui.button('Heute', on_click=self.curr_week).props(
                            'outline size=sm')
                        ui.button(icon='chevron_right',
                                  on_click=self.next_week).props('flat round')
                        ui.button(icon='refresh', on_click=self.refresh_week_table).props(
                            'flat round')

                columns = [
                    {'name': 'date', 'label': 'Datum',
                        'field': 'date', 'align': 'left'},
                    {'name': 'start', 'label': 'Beginn', 'field': 'start'},
                    {'name': 'end', 'label': 'Ende', 'field': 'end'},
                    {'name': 'net', 'label': 'Netto', 'field': 'net'},
                    {'name': 'comment', 'label': 'Kommentar',
                        'field': 'comment', 'align': 'left'},
                ]
                self.week_table = ui.table(
                    columns=columns, rows=[]).classes('w-full')
                self.refresh_week_table()

    def render_import_panel(self):
        with ui.column().classes('w-full items-center q-gutter-y-md'):
            with ui.card().classes('w-full max-w-xl q-pa-md shadow-5'):
                with ui.column().classes('items-center w-full q-gutter-y-sm'):
                    ui.icon('file_upload', size='lg').classes('text-primary')
                    ui.label('CSV Zeiterfassung importieren').classes(
                        'text-h6')
                    ui.label('Format: Datum; Arbeitsbeginn; Arbeitsende; Pause_min; ...').classes(
                        'text-caption text-grey-7')

                ui.separator().classes('q-my-md')

                # Das Upload-Element nutzt deinen Handler
                ui.upload(
                    label="CSV-Datei auswählen (Semikolon getrennt)",
                    on_upload=self.handle_upload,
                    auto_upload=True
                ).classes('w-full').props('accept=.csv')

    def prev_week(self):
        self.week_offset -= 1
        self.refresh_week_table()

    def next_week(self):
        self.week_offset += 1
        self.refresh_week_table()

    def curr_week(self):
        self.week_offset = 0
        self.refresh_week_table()

    def refresh_week_table(self):
        # Wir holen die Daten und die Summe vom Controller
        rows, total = self.controller.get_weekly_entries(
            self.user_id, self.week_offset)
        self.week_table.rows = rows
        self.week_total_label.text = f"Gesamt diese Woche: {total:.2f} h"

    async def handle_upload(self, e):
        """Verarbeitet den CSV-Upload über den Controller/Service"""
        try:
            csv_bytes = e.content.read()

            # Hier rufen wir den Controller auf
            imported, skipped, errors = self.controller.run_csv_import(
                self.user_id, csv_bytes)

            if imported > 0:
                ui.notify(
                    f"Erfolg: {imported} Einträge importiert!", color='positive', icon='done')
            if skipped > 0:
                ui.notify(
                    f"Info: {skipped} Einträge übersprungen.", color='warning', icon='info')
            
            if errors:
                for error in errors[:5]:  # Zeige max. 5 Fehler
                    ui.notify(error, color='negative', icon='error')
                if len(errors) > 5:
                    ui.notify(f"... und {len(errors) - 5} weitere Fehler", color='negative', icon='error')

            # Ansichten aktualisieren
            self.refresh_week_table()
            # Falls du ein Monats-Panel hast, auch dieses refreshen:
            # self.refresh_month_table()

        except Exception as ex:
            ui.notify(f"Fehler beim Import: {str(ex)}",
                      color='negative', icon='error')


class SupervisorDashboardUI:
    def __init__(self):
        self.controller = AuthController()
        self.build_ui()

    def build_ui(self):
        with ui.column().classes('w-full max-w-5xl mx-auto q-pa-md'):
            ui.label('Freigabe der Zeiterfassungen').classes(
                'text-h4 text-white q-mb-md')

            # --- Ablehnungs-Dialog ---
            with ui.dialog() as self.reject_dialog, ui.card().classes('q-pa-md'):
                ui.label('Grund für die Ablehnung:').classes('text-h6')
                self.reject_reason = ui.input('Grund').classes('w-full')
                with ui.row().classes('w-full justify-end'):
                    ui.button('Abbrechen', on_click=self.reject_dialog.close).props(
                        'flat')
                    ui.button('Senden', on_click=self.confirm_rejection).props(
                        'color=negative')

            with ui.card().classes('w-full q-pa-none shadow-10'):
                columns = [
                    {'name': 'user', 'label': 'Mitarbeiter',
                        'field': 'user', 'align': 'left'},
                    {'name': 'date', 'label': 'Datum', 'field': 'date'},
                    {'name': 'hours', 'label': 'Zeit', 'field': 'hours'},
                    {'name': 'comment', 'label': 'Hinweis',
                        'field': 'comment', 'align': 'left'},
                    {'name': 'actions', 'label': 'Aktionen', 'field': 'id'}
                ]

                self.table = ui.table(columns=columns, rows=[]).classes(
                    'w-full shadow-10')

                # Jetzt zwei Buttons: Check (Grün) und Ablehnen (Rot)
                self.table.add_slot('body-cell-actions', '''
                    <q-td :props="props">
                        <q-btn size="sm" color="positive" icon="check" @click="$parent.$emit('approve', props.value)" class="q-mr-xs" />
                        <q-btn size="sm" color="negative" icon="close" @click="$parent.$emit('reject', props.value)" />
                    </q-td>
                ''')

                self.table.on('approve', lambda msg: self.do_approve(msg.args))
                self.table.on(
                    'reject', lambda msg: self.open_reject_dialog(msg.args))

            self.refresh_data()

    def refresh_data(self):
        self.table.rows = self.controller.get_unapproved_entries()

    def do_approve(self, entry_id):
        if self.controller.approve_entry(entry_id):
            ui.notify(f"Eintrag freigegeben!", color='positive')
            self.refresh_data()

    def open_reject_dialog(self, entry_id):
        self.current_reject_id = entry_id
        self.reject_reason.value = ""
        self.reject_dialog.open()

    # 'async' hilft bei der UI-Aktualisierung
    async def confirm_rejection(self):
        if self.controller.reject_entry(self.current_reject_id, self.reject_reason.value):
            ui.notify("Eintrag zur Korrektur zurückgewiesen.", color='warning')
            self.reject_dialog.close()
            # Wir warten ganz kurz, damit die DB Zeit zum Speichern hat
            self.refresh_data()


class UserAdminUI:
    def __init__(self):
        self.controller = AuthController()
        self.selected_user_id = None
        self.build_ui()

    def build_ui(self):
        with ui.column().classes('w-full max-w-5xl mx-auto q-pa-md'):
            with ui.row().classes('w-full justify-between items-center'):
                ui.label('Mitarbeiterverwaltung').classes('text-h4 text-white')
                ui.button('Mitarbeiter anlegen', icon='person_add',
                          on_click=self.open_user_dialog).props('color=secondary')

            # --- User Dialog (für Neu & Bearbeiten) ---
            with ui.dialog() as self.user_dialog, ui.card().classes('w-80'):
                ui.label('Mitarbeiterdaten').classes('text-h6')
                self.f_name = ui.input('Vorname').classes('w-full')
                self.l_name = ui.input('Nachname').classes('w-full')
                self.email = ui.input('E-Mail').classes('w-full')
                self.age = ui.number('Alter', format='%.0f').classes('w-full')
                self.role = ui.select(
                    ['Mitarbeiter', 'Vorgesetzter'], label='Rolle').classes('w-full')

                with ui.row().classes('w-full justify-end q-mt-md'):
                    ui.button('Abbrechen', on_click=self.user_dialog.close).props(
                        'flat')
                    ui.button('Speichern', on_click=self.save_user).props(
                        'color=primary')

            # --- Tabelle ---
            columns = [
                {'name': 'name', 'label': 'Name',
                    'field': 'full_name', 'align': 'left'},
                {'name': 'email', 'label': 'E-Mail',
                    'field': 'email', 'align': 'left'},
                {'name': 'role', 'label': 'Rolle', 'field': 'role'},
                # DIESE ZEILE HIER MUSS REIN, DAMIT DIE BUTTONS PLATZ HABEN:
                {'name': 'actions', 'label': 'Aktionen', 'field': 'id'}
            ]
            self.table = ui.table(columns=columns, rows=[]
                                  ).classes('w-full shadow-10')
            self.table.add_slot('body-cell-actions', '''
                <q-td :props="props">
                    <q-btn size="sm" color="primary" icon="edit" @click="$parent.$emit('edit', props.row)" class="q-mr-xs" />
                    <q-btn size="sm" color="warning" icon="lock_reset" @click="$parent.$emit('reset', props.value)" />
                    <q-btn size="sm" color="negative" icon="delete" @click="$parent.$emit('delete', props.value)" />
                </q-td>
            ''')

            self.table.on('edit', lambda msg: self.open_user_dialog(msg.args))
            self.table.on('reset', lambda msg: self.do_reset(msg.args))
            self.table.on('delete', lambda msg: self.do_delete(msg.args))

            self.refresh_data()

    def refresh_data(self):
        users = self.controller.get_all_users()
    # Wir berechnen den vollen Namen hier in Python vor dem Senden an die UI
        for u in users:
            u['full_name'] = f"{u['first_name']} {u['last_name']}"
        self.table.rows = users

    def open_user_dialog(self, user_data=None):
        if isinstance(user_data, dict):  # Bearbeiten
            self.selected_user_id = user_data['id']
            self.f_name.value = user_data['first_name']
            self.l_name.value = user_data['last_name']
            self.email.value = user_data['email']
            self.age.value = user_data['age']
            self.role.value = user_data['role']
        else:  # Neu anlegen
            self.selected_user_id = None
            for field in [self.f_name, self.l_name, self.email, self.age]:
                field.value = None
            self.role.value = 'Mitarbeiter'
        self.user_dialog.open()

    def save_user(self):
        data = {
            'id': self.selected_user_id,
            'first_name': self.f_name.value,
            'last_name': self.l_name.value,
            'email': self.email.value,
            'age': self.age.value,
            'role': self.role.value
        }
        if self.controller.upsert_user(data):
            ui.notify('Benutzer erfolgreich gespeichert!')
            self.user_dialog.close()
            self.refresh_data()

    def do_reset(self, user_id):
        if self.controller.reset_password(user_id):
            ui.notify(
                'Passwort-Reset erfolgreich! Der Mitarbeiter muss beim nächsten Login ein neues Passwort vergeben.',
                color='warning',
                icon='lock_reset'
            )

    async def do_delete(self, user_id):
        # Sicherheitsabfrage
        with ui.dialog() as dialog, ui.card():
            ui.label('Mitarbeiter wirklich unwiderruflich löschen?')
            with ui.row():
                ui.button('Abbrechen', on_click=dialog.close)
                ui.button('Löschen', color='negative',
                          on_click=lambda: dialog.submit(True))

        result = await dialog
        if result is True:
            if self.controller.delete_user(user_id):
                ui.notify('Mitarbeiter gelöscht', color='negative')
                self.refresh_data()
