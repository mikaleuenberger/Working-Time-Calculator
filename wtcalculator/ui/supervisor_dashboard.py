from datetime import date
from io import BytesIO
from nicegui import ui
from ..app_controler import AuthController


class SupervisorDashboardUI:
    def __init__(self):
        self.controller = AuthController()
        self.current_year = date.today().year
        self.current_month = date.today().month
        self.selected_user_id = None
        self.build_ui()

    def build_ui(self):
        with ui.column().classes('w-full max-w-5xl mx-auto q-pa-md'):
            ui.label('Freigabe der Zeiterfassungen').classes(
                'text-h4 text-white q-mb-md')

            # Filter row
            with ui.card().classes('w-full q-pa-md'):
                with ui.row().classes('w-full items-center justify-between'):
                    with ui.row().classes('items-center q-gutter-md'):
                        ui.label('Filter:').classes('text-white')

                        # Employee filter - build options before creating select
                        emp_options = {'all': 'Alle Mitarbeiter'}
                        employees = self.controller.get_all_employees()
                        for emp in employees:
                            emp_options[str(emp['id'])] = emp['name']
                        self.employee_select = ui.select(
                            emp_options, label='Mitarbeiter', value='all'
                        ).classes('w-48')

                        # Year filter
                        years = list(range(date.today().year - 2, date.today().year + 1))
                        self.year_select = ui.select(
                            years, label='Jahr', value=self.current_year
                        ).classes('w-24').on_value_change(self.on_filter_change)

                        # Month filter - use string values for display
                        month_options = {str(i): f"{i:02d}" for i in range(1, 13)}
                        self.month_select = ui.select(
                            month_options, label='Monat', value=str(self.current_month)
                        ).classes('w-24').on_value_change(self.on_filter_change)

                    with ui.row().classes('items-center q-gutter-sm'):
                        ui.button('Alle freigeben', icon='done_all',
                                  on_click=self.approve_all_filtered).props('color=positive')
                        ui.button('PDF herunterladen', icon='download',
                                  on_click=self.download_pdf).props('color=secondary')
                        ui.button('Aktualisieren', icon='refresh',
                                  on_click=self.refresh_data).props('flat')

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
                    {'name': 'approved', 'label': 'Status',
                        'field': 'approved', 'align': 'center'},
                    {'name': 'actions', 'label': 'Aktionen', 'field': 'id'}
                ]

                self.table = ui.table(columns=columns, rows=[]).classes(
                    'w-full shadow-10')

                self.table.add_slot('body-cell-actions', '''
                    <q-td :props="props">
                        <q-btn size="sm" color="positive" icon="check" @click="$parent.$emit('approve', props.value)" class="q-mr-xs" />
                        <q-btn size="sm" color="negative" icon="close" @click="$parent.$emit('reject', props.value)" />
                    </q-td>
                ''')

                self.table.add_slot('body-cell-approved', '''
                    <q-td :props="props">
                        <q-badge :color="props.value ? 'positive' : 'warning'" :label="props.value ? '✓' : '⏳'" />
                    </q-td>
                ''')

                self.table.on('approve', lambda msg: self.do_approve(msg.args))
                self.table.on(
                    'reject', lambda msg: self.open_reject_dialog(msg.args))

            self.refresh_data()

    def load_employees(self):
        employees = self.controller.get_all_employees()
        # Clear existing options and update in-place to trigger UI update
        self.employee_select.options.clear()
        self.employee_select.options['all'] = 'Alle Mitarbeiter'
        for emp in employees:
            self.employee_select.options[str(emp['id'])] = emp['name']
        self.employee_select.update()

    def on_filter_change(self):
        if not hasattr(self, 'month_select') or not hasattr(self, 'employee_select'):
            return
        self.current_year = int(self.year_select.value)
        self.current_month = int(self.month_select.value)
        self.refresh_data()

    def refresh_data(self):
        # 'all' means show all employees, otherwise use the selected user_id
        emp_value = self.employee_select.value
        user_id = None if emp_value == 'all' else int(emp_value)
        entries = self.controller.get_entries_for_approval(
            user_id=user_id,
            year=self.current_year,
            month=self.current_month
        )
        self.table.rows = entries

    def approve_all_filtered(self):
        rows = self.table.rows
        if not rows:
            ui.notify('Keine Einträge zum Freigeben vorhanden.', color='warning')
            return

        unapproved = [r for r in rows if not r.get('approved', False)]
        if not unapproved:
            ui.notify('Alle angezeigten Einträge sind bereits freigegeben.', color='positive')
            return

        entry_ids = [r['id'] for r in unapproved]
        count = self.controller.approve_entries_batch(entry_ids)
        ui.notify(f'{count} Einträge freigegeben!', color='positive')
        self.refresh_data()

    def download_pdf(self):
        """Generate and download a PDF report of the filtered entries."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import cm
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        except ImportError:
            ui.notify('PDF-Bibliothek nicht installiert', color='negative')
            return

        emp_value = self.employee_select.value
        user_id = None if emp_value == 'all' else int(emp_value)
        entries = self.controller.get_entries_for_approval(
            user_id=user_id,
            year=self.current_year,
            month=self.current_month
        )

        if not entries:
            ui.notify('Keine Einträge für den gewählten Filter vorhanden.', color='warning')
            return

        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        # Title
        month_name = f"{self.current_month:02d}/{self.current_year}"
        title = Paragraph(f"Zeiterfassungs-Report {month_name}", styles['Heading1'])
        elements.append(title)
        elements.append(Spacer(1, 0.5 * cm))

        # Summary info
        emp_name = "Alle Mitarbeiter" if emp_value == 'all' else self.employee_select.options.get(str(emp_value), 'Unbekannt')
        info = Paragraph(f"Mitarbeiter: {emp_name}<br/>Monat: {month_name}<br/>Einträge: {len(entries)}", styles['Normal'])
        elements.append(info)
        elements.append(Spacer(1, 0.5 * cm))

        # Table data
        table_data = [['Datum', 'Mitarbeiter', 'Netto (h)', 'Status', 'Kommentar']]
        total_hours = 0.0
        for entry in entries:
            hours = entry.get('net_hours', 0)
            total_hours += hours
            status = 'Genehmigt' if entry.get('approved') else 'Ausstehend'
            table_data.append([
                entry.get('date', ''),
                entry.get('user', ''),
                f"{hours:.2f}",
                status,
                entry.get('comment', '')[:30]
            ])

        # Add total row
        table_data.append(['TOTAL', '', f"{total_hours:.2f}", '', ''])

        # Create table
        table = Table(table_data, colWidths=[3*cm, 4*cm, 2.5*cm, 2.5*cm, 5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (4, 1), (4, -1), 'LEFT'),  # Kommentar left aligned
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -2), 1, colors.black),
        ]))
        elements.append(table)

        # Build PDF
        doc.build(elements)
        buffer.seek(0)

        # Send to browser
        pdf_bytes = buffer.getvalue()
        filename = f"Zeiterfassung_{month_name.replace('/', '_')}.pdf"

        ui.notify(f'PDF wird heruntergeladen: {filename}', color='positive')
        ui.download(pdf_bytes, filename)

    def do_approve(self, entry_id):
        if self.controller.approve_entry(entry_id):
            ui.notify(f"Eintrag freigegeben!", color='positive')
            self.refresh_data()

    def open_reject_dialog(self, entry_id):
        self.current_reject_id = entry_id
        self.reject_reason.value = ""
        self.reject_dialog.open()

    async def confirm_rejection(self):
        if self.controller.reject_entry(self.current_reject_id, self.reject_reason.value):
            ui.notify("Eintrag zur Korrektur zurückgewiesen.", color='warning')
            self.reject_dialog.close()
            self.refresh_data()


class UserAdminUI:
    def __init__(self, current_user_id: int, supervisor_dashboard=None):
        self.controller = AuthController()
        self.current_user_id = current_user_id
        self.supervisor_dashboard = supervisor_dashboard
        self.selected_user_id = None
        self.build_ui()

    def build_ui(self):
        with ui.column().classes('w-full max-w-5xl mx-auto q-pa-md'):
            with ui.row().classes('w-full justify-between items-center'):
                ui.label('Mitarbeiterverwaltung').classes('text-h4 text-white')
                ui.button('Mitarbeiter anlegen', icon='person_add',
                          on_click=self.open_user_dialog).props('color=secondary')

            with ui.dialog() as self.user_dialog, ui.card().classes('w-80'):
                ui.label('Mitarbeiterdaten').classes('text-h6')
                self.user_id_input = ui.number('ID', format='%.0f', min=1).classes('w-full')
                self.f_name = ui.input('Vorname').classes('w-full').props('maxlength=50')
                self.l_name = ui.input('Nachname').classes('w-full').props('maxlength=50')
                self.email = ui.input('E-Mail').classes('w-full').props('maxlength=254')
                self.age = ui.number('Alter', format='%.0f', min=14, max=100).classes('w-full')
                self.role = ui.select(
                    ['Mitarbeiter', 'Vorgesetzter'], label='Rolle').classes('w-full')

                with ui.row().classes('w-full justify-end q-mt-md'):
                    ui.button('Abbrechen', on_click=self.user_dialog.close).props(
                        'flat')
                    ui.button('Speichern', on_click=self.save_user).props(
                        'color=primary')

            columns = [
                {'name': 'name', 'label': 'Name',
                    'field': 'full_name', 'align': 'left'},
                {'name': 'email', 'label': 'E-Mail',
                    'field': 'email', 'align': 'left'},
                {'name': 'role', 'label': 'Rolle', 'field': 'role'},
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
        for u in users:
            u['full_name'] = f"{u['first_name']} {u['last_name']}"
        self.table.rows = users

    def open_user_dialog(self, user_data=None):
        if isinstance(user_data, dict):
            self.selected_user_id = user_data['id']
            self.user_id_input.value = user_data['id']
            self.user_id_input.props(add='readonly')
            self.user_id_input.update()
            self.f_name.value = user_data['first_name']
            self.f_name.update()
            self.l_name.value = user_data['last_name']
            self.l_name.update()
            self.email.value = user_data['email']
            self.email.update()
            self.age.value = user_data['age']
            self.age.update()
            self.role.value = user_data['role']
            self.role.update()
        else:
            self.selected_user_id = None
            self.user_id_input.value = None
            self.user_id_input.props(remove='readonly')
            self.user_id_input.update()
            self.f_name.value = ''
            self.f_name.update()
            self.l_name.value = ''
            self.l_name.update()
            self.email.value = ''
            self.email.update()
            self.age.value = 14
            self.age.update()
            self.role.value = 'Mitarbeiter'
            self.role.update()
        self.user_dialog.open()

    def save_user(self):
        # For new users, require an ID to be specified
        if self.selected_user_id is None:
            user_id = self.user_id_input.value
            if user_id is None or not isinstance(user_id, (int, float)) or user_id < 1 or not float(user_id).is_integer():
                ui.notify('Bitte geben Sie eine gültige ID ein (positive ganze Zahl)', color='negative')
                return
            user_id = int(user_id)
            # Check if ID is already taken
            existing_user = self.controller.get_all_users()
            if any(u['id'] == user_id for u in existing_user):
                ui.notify(f'Die ID {user_id} ist bereits vergeben', color='negative')
                return
        else:
            user_id = self.selected_user_id

        # Validate age
        age = self.age.value
        if not isinstance(age, (int, float)) or not float(age).is_integer() or age < 14 or age > 100:
            ui.notify('Ungültiges Alter (14-100 erlaubt)', color='negative')
            return

        data = {
            'id': user_id,
            'first_name': self.f_name.value,
            'last_name': self.l_name.value,
            'email': self.email.value,
            'age': int(age),
            'role': self.role.value
        }
        res = self.controller.upsert_user(data)
        if isinstance(res, dict) and res.get('status') == 'success':
            ui.notify('Benutzer erfolgreich gespeichert!', color='positive')
            self.user_dialog.close()
            self.refresh_data()
            # Refresh the employee filter in supervisor dashboard if available
            if self.supervisor_dashboard:
                self.supervisor_dashboard.load_employees()
        else:
            msg = res.get('message') if isinstance(res, dict) else 'Ungültige Eingabe'
            ui.notify(msg, color='negative')

    def do_reset(self, user_id):
        if self.controller.reset_password(user_id):
            ui.notify(
                'Passwort-Reset erfolgreich! Der Mitarbeiter muss beim nächsten Login ein neues Passwort vergeben.',
                color='warning',
                icon='lock_reset'
            )

    async def do_delete(self, user_id):
        if user_id == self.current_user_id:
            ui.notify('Sie können sich nicht selbst löschen!', color='negative')
            return

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
                # Refresh the employee filter in supervisor dashboard if available
                if self.supervisor_dashboard:
                    self.supervisor_dashboard.load_employees()


class ApprovedEntriesUI:
    def __init__(self):
        self.controller = AuthController()
        self.current_year = date.today().year
        self.current_month = date.today().month
        self.build_ui()

    def build_ui(self):
        with ui.column().classes('w-full max-w-5xl mx-auto q-pa-md'):
            ui.label('Genehmigte Zeiterfassungen').classes(
                'text-h4 text-white q-mb-md')

            # Filter row
            with ui.card().classes('w-full q-pa-md'):
                with ui.row().classes('w-full items-center justify-between'):
                    with ui.row().classes('items-center q-gutter-md'):
                        ui.label('Filter:').classes('text-white')

                        # Employee filter - build options before creating select
                        emp_options = {'all': 'Alle Mitarbeiter'}
                        employees = self.controller.get_all_employees()
                        for emp in employees:
                            emp_options[str(emp['id'])] = emp['name']
                        self.employee_select = ui.select(
                            emp_options, label='Mitarbeiter', value='all'
                        ).classes('w-48')

                        # Year filter
                        years = list(range(date.today().year - 2, date.today().year + 1))
                        self.year_select = ui.select(
                            years, label='Jahr', value=self.current_year
                        ).classes('w-24').on_value_change(self.on_filter_change)

                        # Month filter - use string values for display
                        month_options = {str(i): f"{i:02d}" for i in range(1, 13)}
                        self.month_select = ui.select(
                            month_options, label='Monat', value=str(self.current_month)
                        ).classes('w-24').on_value_change(self.on_filter_change)

                    with ui.row().classes('items-center q-gutter-sm'):
                        ui.button('PDF herunterladen', icon='download',
                                  on_click=self.download_pdf).props('color=secondary')
                        ui.button('Aktualisieren', icon='refresh',
                                  on_click=self.refresh_data).props('flat')

            with ui.card().classes('w-full q-pa-none shadow-10'):
                columns = [
                    {'name': 'user', 'label': 'Mitarbeiter',
                        'field': 'user', 'align': 'left'},
                    {'name': 'date', 'label': 'Datum', 'field': 'date'},
                    {'name': 'hours', 'label': 'Zeit', 'field': 'hours'},
                    {'name': 'comment', 'label': 'Hinweis',
                        'field': 'comment', 'align': 'left'},
                    {'name': 'approved', 'label': 'Status',
                        'field': 'approved', 'align': 'center'},
                ]

                self.table = ui.table(columns=columns, rows=[]).classes(
                    'w-full shadow-10')

                self.table.add_slot('body-cell-approved', '''
                    <q-td :props="props">
                        <q-badge color="positive" label="Genehmigt" />
                    </q-td>
                ''')

            self.refresh_data()

    def load_employees(self):
        employees = self.controller.get_all_employees()
        self.employee_select.options.clear()
        self.employee_select.options['all'] = 'Alle Mitarbeiter'
        for emp in employees:
            self.employee_select.options[str(emp['id'])] = emp['name']
        self.employee_select.update()

    def on_filter_change(self):
        self.current_year = int(self.year_select.value)
        self.current_month = int(self.month_select.value)
        self.refresh_data()

    def refresh_data(self):
        emp_value = self.employee_select.value
        user_id = None if emp_value == 'all' else int(emp_value)
        entries = self.controller.get_approved_entries(
            user_id=user_id,
            year=self.current_year,
            month=self.current_month
        )
        self.table.rows = entries

    def download_pdf(self):
        """Generate and download a PDF report of approved entries."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import cm
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        except ImportError:
            ui.notify('PDF-Bibliothek nicht installiert', color='negative')
            return

        emp_value = self.employee_select.value
        user_id = None if emp_value == 'all' else int(emp_value)
        entries = self.controller.get_approved_entries(
            user_id=user_id,
            year=self.current_year,
            month=self.current_month
        )

        if not entries:
            ui.notify('Keine genehmigten Einträge für den gewählten Filter vorhanden.', color='warning')
            return

        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        # Title
        month_name = f"{self.current_month:02d}/{self.current_year}"
        title = Paragraph(f"Genehmigte Zeiterfassung {month_name}", styles['Heading1'])
        elements.append(title)
        elements.append(Spacer(1, 0.5 * cm))

        # Summary info
        emp_name = "Alle Mitarbeiter" if emp_value == 'all' else self.employee_select.options.get(str(emp_value), 'Unbekannt')
        info = Paragraph(f"Mitarbeiter: {emp_name}<br/>Monat: {month_name}<br/>Einträge: {len(entries)}", styles['Normal'])
        elements.append(info)
        elements.append(Spacer(1, 0.5 * cm))

        # Table data
        table_data = [['Datum', 'Mitarbeiter', 'Netto (h)', 'Kommentar']]
        total_hours = 0.0
        for entry in entries:
            hours = entry.get('net_hours', 0)
            total_hours += hours
            table_data.append([
                entry.get('date', ''),
                entry.get('user', ''),
                f"{hours:.2f}",
                entry.get('comment', '')[:30]
            ])

        # Add total row
        table_data.append(['TOTAL', '', f"{total_hours:.2f}", ''])

        # Create table
        table = Table(table_data, colWidths=[3*cm, 4*cm, 2.5*cm, 7.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (3, 1), (3, -1), 'LEFT'),  # Kommentar left aligned
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -2), 1, colors.black),
        ]))
        elements.append(table)

        # Build PDF
        doc.build(elements)
        buffer.seek(0)

        # Send to browser
        pdf_bytes = buffer.getvalue()
        filename = f"Genehmigte_Zeiterfassung_{month_name.replace('/', '_')}.pdf"

        ui.notify(f'PDF wird heruntergeladen: {filename}', color='positive')
        ui.download(pdf_bytes, filename)
