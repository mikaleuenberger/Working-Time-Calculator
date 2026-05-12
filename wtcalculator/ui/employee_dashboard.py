import re
from nicegui import ui, app
from ..app_controler import AuthController
from .login import _now


class EmployeeDashboardUI:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.controller = AuthController()
        self.current_date = _now().strftime('%Y-%m-%d')
        self.week_offset = 0
        self.month_offset = 0
        self.build_ui()

    def build_ui(self):
        with ui.tabs().classes('w-full bg-dark shadow-2 text-grey-5') \
                .props('active-color=primary active-bg-color=grey-9 indicator-color=primary expand') as tabs:
            self.tab_entry = ui.tab('Erfassung', icon='edit_calendar')
            self.tab_week = ui.tab('Woche', icon='view_week')
            self.tab_month = ui.tab('Monat', icon='calendar_month')
            self.tab_import = ui.tab('CSV Import', icon='file_upload')

        with ui.tab_panels(tabs, value=self.tab_entry).classes('w-full bg-transparent'):
            with ui.tab_panel(self.tab_entry):
                self.render_entry_panel()
            with ui.tab_panel(self.tab_week):
                self.render_week_panel()
            with ui.tab_panel(self.tab_month):
                self.render_month_panel()
            with ui.tab_panel(self.tab_import):
                self.render_import_panel()

    def render_entry_panel(self):
        with ui.column().classes('w-full items-center q-gutter-y-md'):
            with ui.card().classes('w-full max-w-4xl q-pa-md shadow-5'):
                ui.label('Neuen Eintrag erfassen').classes('text-h6 q-mb-sm')

                with ui.row().classes('w-full items-start justify-between q-gutter-md'):
                    with ui.column().classes('flex-1'):
                        with ui.input('Datum', placeholder='YYYY-MM-DD').bind_value(self, 'current_date') as date_input:
                            self.current_date = _now().strftime('%Y-%m-%d')
                            with ui.menu():
                                ui.date().bind_value(date_input)

                        self.comment_input = ui.input(
                            'Kommentar (optional)').classes('w-full').props('maxlength=30')

                    with ui.column().classes('flex-1'):
                        self.start_input = ui.input(
                            'Beginn', value='08:00').props('mask="##:##" outlined')
                        self.end_input = ui.input('Ende', value='17:00').props(
                            'mask="##:##" outlined')

                    with ui.column().classes('flex-1'):
                        self.pause_start = ui.input('Pause Start', value='').props('mask="##:##" outlined placeholder="12:00"')
                        self.pause_end = ui.input('Pause Ende', value='').props('mask="##:##" outlined placeholder="13:00"')
                        self.pause_minutes = ui.number(
                            'Zusätzliche Pausen (Min)', value=0, min=0, max=180).classes('w-full')

                with ui.row().classes('w-full justify-end mt-4'):
                    ui.button('Eintrag Speichern', on_click=self.save_entry).props(
                        'color=primary icon=save')

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
        time_re = re.compile(r'^\d{2}:\d{2}$')
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', (self.current_date or '').strip()):
            ui.notify('Bitte geben Sie das Datum im korrekten Format an: YYYY-MM-DD', color='negative')
            return

        for label, val in [
            ('Beginn', self.start_input.value),
            ('Ende', self.end_input.value),
        ]:
            v = (val or '').strip()
            if v and not time_re.match(v):
                ui.notify(f'Bitte geben Sie {label} im korrekten Format an: hh:mm', color='negative')
                return

        pause_min = int(self.pause_minutes.value or 0)
        pause_start = (self.pause_start.value or '').strip()
        pause_end = (self.pause_end.value or '').strip()

        if pause_min < 0:
            ui.notify('Pause darf nicht negativ sein.', color='negative')
            return
        if pause_min > 180:
            ui.notify('Pause darf maximal 180 Minuten (3h) sein.', color='negative')
            return

        if pause_start and not time_re.match(pause_start):
            ui.notify('Bitte geben Sie die Pause Start Zeit im korrekten Format an: hh:mm', color='negative')
            return
        if pause_end and not time_re.match(pause_end):
            ui.notify('Bitte geben Sie die Pause Ende Zeit im korrekten Format an: hh:mm', color='negative')
            return

        if bool(pause_start) != bool(pause_end):
            ui.notify('Bitte geben Sie sowohl Pause Start als auch Pause Ende an, oder lassen Sie beide leer.', color='negative')
            return

        user_comment = (self.comment_input.value or '').strip()[:30]

        try:
            res = self.controller.save_time_entry(
                user_id=self.user_id,
                date_str=self.current_date,
                start_s=self.start_input.value,
                end_s=self.end_input.value,
                pause_minutes=pause_min,
                pause_start=pause_start or None,
                pause_end=pause_end or None,
                comment=user_comment,
            )
        except Exception as e:
            ui.notify(f'Fehler beim Speichern: {str(e)}', color='negative')
            return

        if not isinstance(res, dict):
            ui.notify(f'Unerwarteter Fehler: {type(res)}', color='negative')
            return

        if res.get("status") == "success":
            action = res.get('action')
            if action == 'updated':
                ui.notify("Eintrag existierte bereits und wurde angepasst.", color="warning")
            else:
                ui.notify("Eintrag erfolgreich gespeichert!", color="positive")

            # Show any warnings (45h weekly, insufficient break, etc.)
            notifications = res.get('notifications', [])
            for notif in notifications:
                ui.notify(notif, color='negative', duration=10)

            self.refresh_month_table()
            self.refresh_month_overview_table()
            self.refresh_week_table()
        else:
            message = res.get('message', 'Unbekannter Fehler')
            ui.notify(f"Fehler: {message}", color="negative")

    def render_week_panel(self):
        with ui.column().classes('w-full items-center q-gutter-y-md'):
            with ui.card().classes('w-full max-w-4xl q-pa-none shadow-5'):
                with ui.row().classes('q-pa-md items-center justify-between w-full'):
                    with ui.column():
                        ui.label('Wochenübersicht').classes('text-h6')
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

    def render_month_panel(self):
        with ui.column().classes('w-full items-center q-gutter-y-md'):
            with ui.card().classes('w-full max-w-4xl q-pa-none shadow-5'):
                with ui.row().classes('q-pa-md items-center justify-between w-full'):
                    with ui.column():
                        ui.label('Monatsübersicht').classes('text-h6')
                        self.month_total_label = ui.label('Gesamt: 0.00 h').classes(
                            'text-subtitle1 text-primary font-bold')
                    with ui.row().classes('items-center q-gutter-sm'):
                        ui.button(icon='chevron_left',
                                  on_click=self.prev_month).props('flat round')
                        ui.button('Dieser Monat', on_click=self.curr_month).props(
                            'outline size=sm')
                        ui.button(icon='chevron_right',
                                  on_click=self.next_month).props('flat round')
                        ui.button(icon='refresh', on_click=self.refresh_month_overview_table).props(
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
                self.month_overview_table = ui.table(
                    columns=columns, rows=[]).classes('w-full')
                self.refresh_month_overview_table()

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

    def prev_month(self):
        self.month_offset -= 1
        self.refresh_month_overview_table()

    def next_month(self):
        self.month_offset += 1
        self.refresh_month_overview_table()

    def curr_month(self):
        self.month_offset = 0
        self.refresh_month_overview_table()

    def refresh_week_table(self):
        rows, total = self.controller.get_weekly_entries(
            self.user_id, self.week_offset)
        self.week_table.rows = rows
        self.week_total_label.text = f"Gesamt diese Woche: {total:.2f} h"

    def refresh_month_overview_table(self):
        now = _now()
        year = now.year
        month = now.month + self.month_offset

        while month < 1:
            month += 12
            year -= 1
        while month > 12:
            month -= 12
            year += 1

        rows, total = self.controller.get_monthly_entries_with_total(
            self.user_id, year, month)
        self.month_overview_table.rows = rows

        month_name = f"{month:02d}.{year}"
        self.month_total_label.text = f"Gesamt {month_name}: {total:.2f} h"

    async def handle_upload(self, e):
        try:
            csv_bytes = e.content.read()

            imported, skipped, errors = self.controller.run_csv_import(
                self.user_id, csv_bytes)

            if imported > 0:
                ui.notify(
                    f"Erfolg: {imported} Einträge importiert!", color='positive', icon='done')
            if skipped > 0:
                ui.notify(
                    f"Info: {skipped} Einträge übersprungen.", color='warning', icon='info')

            if errors:
                for error in errors[:5]:
                    ui.notify(error, color='negative', icon='error')
                if len(errors) > 5:
                    ui.notify(f"... und {len(errors) - 5} weitere Fehler", color='negative', icon='error')

            self.refresh_week_table()

        except Exception as ex:
            ui.notify(f"Fehler beim Import: {str(ex)}",
                      color='negative', icon='error')
