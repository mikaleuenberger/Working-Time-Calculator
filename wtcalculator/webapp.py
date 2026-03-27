from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from urllib.parse import quote

import os

from nicegui import app, ui

from .db import init_db, session_scope
from .models import TimeEntry, User
from .services.auth_service import AuthService
from .services.report_service import ReportService
from .services.time_entry_service import TimeEntryService
from .services.user_service import UserService
from .security import validate_password_policy


_TIME_RE = re.compile(r"^\d{2}:\d{2}$")

_BRANDING_INJECTED = False

_LOGIN_BG = "#2B2B2B"


def _inject_branding() -> None:
    global _BRANDING_INJECTED
    if _BRANDING_INJECTED:
        return
    ui.add_css(
        """
        html, body { height: 100%; }
        #app { background: transparent !important; }
        .nicegui-layout, .q-layout, .q-page-container { background: transparent !important; }
        .q-page, .nicegui-content { background: transparent !important; }
        """
    )
    _BRANDING_INJECTED = True


def _fixed_page_background(color: str) -> None:
    bg = _forest_lake_background_data_uri()
    ui.html(
        (
            '<!-- page background -->'
            f'<div style="position:fixed; inset:0; z-index:-1; '
            f'background-color:{color}; '
            f"background-image:url('{bg}'); "
            'background-size:cover; background-position:center; background-repeat:no-repeat; '
            '"></div>'
        )
    )


def _forest_lake_background_data_uri() -> str:
    """Return a data URI for a simple forest + mountain lake background SVG."""

    svg = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1600 900'>
    <defs>
        <linearGradient id='sky' x1='0' y1='0' x2='0' y2='1'>
            <stop offset='0' stop-color='#1f2a3a'/>
            <stop offset='1' stop-color='#2b2b2b'/>
        </linearGradient>
        <linearGradient id='mist' x1='0' y1='0' x2='0' y2='1'>
            <stop offset='0' stop-color='rgba(255,255,255,0.35)'/>
            <stop offset='1' stop-color='rgba(255,255,255,0)'/>
        </linearGradient>
        <linearGradient id='lake' x1='0' y1='0' x2='0' y2='1'>
            <stop offset='0' stop-color='#1c4f66'/>
            <stop offset='1' stop-color='#0d2d3b'/>
        </linearGradient>
        <filter id='soft' x='-10%' y='-10%' width='120%' height='120%'>
            <feGaussianBlur stdDeviation='3'/>
        </filter>
    </defs>

    <!-- sky -->
    <rect width='1600' height='900' fill='url(#sky)'/>

    <!-- distant mountains -->
    <path d='M0 520 L260 360 L430 460 L620 300 L820 460 L1020 320 L1240 450 L1420 360 L1600 470 L1600 900 L0 900 Z'
                fill='#2b3b4a' opacity='0.75'/>
    <path d='M0 560 L220 420 L420 520 L650 360 L880 540 L1120 380 L1340 520 L1600 420 L1600 900 L0 900 Z'
                fill='#263240' opacity='0.85'/>

    <!-- mist band -->
    <rect x='0' y='500' width='1600' height='160' fill='url(#mist)' filter='url(#soft)'/>

    <!-- forest silhouettes -->
    <g opacity='0.92'>
        <path d='M-40 680 C120 610, 220 650, 320 600 C420 555, 560 610, 660 570 C760 530, 900 590, 1040 550 C1180 510, 1340 600, 1500 540 C1600 500, 1700 560, 1660 700 L1660 920 L-40 920 Z'
                    fill='#14201b'/>
        <path d='M-40 720 C140 650, 260 700, 380 650 C520 590, 700 700, 860 630 C1000 570, 1160 690, 1320 620 C1460 560, 1600 640, 1660 620 L1660 920 L-40 920 Z'
                    fill='#0e1713' opacity='0.9'/>
    </g>

    <!-- lake -->
    <path d='M0 690 C260 760, 520 730, 760 780 C1000 830, 1280 800, 1600 860 L1600 900 L0 900 Z'
                fill='url(#lake)' opacity='0.95'/>

    <!-- lake highlights -->
    <path d='M140 760 C320 730, 520 760, 700 735' stroke='rgba(255,255,255,0.18)' stroke-width='6' fill='none' filter='url(#soft)'/>
    <path d='M820 805 C1020 770, 1220 815, 1420 785' stroke='rgba(255,255,255,0.14)' stroke-width='6' fill='none' filter='url(#soft)'/>
</svg>"""

    return "data:image/svg+xml," + quote(svg)


def _clock_svg(now: datetime, *, size: int = 260) -> str:
    """Simple inline SVG analog clock (no external assets)."""
    s = int(size)
    c = s / 2
    r = s * 0.42

    # angles: 12 o'clock = -90deg
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


def _is_valid_hhmm(value: str) -> bool:
    if not _TIME_RE.match(value.strip()):
        return False
    try:
        datetime.strptime(value.strip(), "%H:%M")
        return True
    except ValueError:
        return False


def _require_login() -> int | None:
    user_id = app.storage.user.get("user_id")
    return int(user_id) if user_id is not None else None


def _logout() -> None:
    app.storage.user.clear()
    ui.open("/")


@ui.page("/")
def login_page() -> None:
    _inject_branding()
    _fixed_page_background(_LOGIN_BG)
    if _require_login() is not None:
        ui.open("/dashboard")
        return

    ui.label("WTCalculator – Login").classes("text-h5 text-white")

    with ui.row().classes("w-full justify-center items-stretch q-gutter-xl"):
        with ui.card().classes("w-80 items-center justify-center"):
            ui.label("Uhr").classes("text-h6")
            clock_html = ui.html(_clock_svg(datetime.now(), size=260))
            time_label = ui.label(datetime.now().strftime(
                "%H:%M:%S")).classes("text-h5")

            def tick() -> None:
                now = datetime.now()
                time_label.text = now.strftime("%H:%M:%S")
                clock_html.content = _clock_svg(now, size=260)
                clock_html.update()

            ui.timer(1.0, tick)

        with ui.card().classes("w-96"):
            user_id_input = ui.input(
                "ID", placeholder="z.B. 1").props("type=number")
            last_name_input = ui.input("Nachname", placeholder="z.B. Müller")
            password_input = ui.input("Passwort").props("type=password")

    def do_login() -> None:
        try:
            user_id = int(user_id_input.value)
        except Exception:
            ui.notify("ID muss eine Zahl sein", color="negative")
            return

        last_name = (last_name_input.value or "").strip()
        if not last_name:
            ui.notify("Nachname ist erforderlich", color="negative")
            return

        password = (password_input.value or "").strip()

        with session_scope() as session:
            # If user must set/change password (seeded user or after reset), guide to setup.
            tmp_user = AuthService(session).requires_password_setup(
                user_id=user_id, last_name=last_name)
            if tmp_user is not None:
                app.storage.user["pending_user_id"] = tmp_user.id
                ui.notify(
                    "Passwort ist noch nicht gesetzt – bitte setzen.", color="warning")
                ui.open("/set-password")
                return

            if not password:
                ui.notify("Passwort ist erforderlich", color="negative")
                return

            user = AuthService(session).authenticate(
                user_id=user_id, last_name=last_name, password=password)
            if user is None:
                ui.notify("Login fehlgeschlagen", color="negative")
                return

            app.storage.user["user_id"] = user.id

        ui.open("/dashboard")

    ui.button("Login", on_click=do_login).props("color=primary")


@ui.page('/set-password')
def set_password_page() -> None:
    _inject_branding()
    _fixed_page_background(_LOGIN_BG)
    pending_user_id = app.storage.user.get('pending_user_id')
    if pending_user_id is None:
        ui.open('/')
        return

    ui.label('Passwort setzen').classes('text-h5 text-white')
    p1 = ui.input('Neues Passwort').props('type=password')
    p2 = ui.input('Passwort bestätigen').props('type=password')

    ui.label('Policy: mind. 8 Zeichen, 1 Grossbuchstabe, 1 Zahl, 1 Sonderzeichen').classes(
        'text-grey')

    def save() -> None:
        pw1 = (p1.value or '').strip()
        pw2 = (p2.value or '').strip()

        if pw1 != pw2:
            ui.notify('Passwörter stimmen nicht überein', color='negative')
            return
        if not validate_password_policy(pw1):
            ui.notify('Passwort erfüllt die Policy nicht', color='negative')
            return

        with session_scope() as session:
            ok = UserService(session).set_password(
                user_id=int(pending_user_id), password=pw1)
            if not ok:
                ui.notify('Konnte Passwort nicht setzen', color='negative')
                return

        app.storage.user.pop('pending_user_id', None)
        ui.notify('Passwort gesetzt. Bitte einloggen.', color='positive')
        ui.open('/')

    ui.row()
    ui.button('Speichern', on_click=save).props('color=primary')
    ui.button('Abbrechen', on_click=lambda: (app.storage.user.pop(
        'pending_user_id', None), ui.open('/'))).props('flat')


@ui.page("/dashboard")
def dashboard_page() -> None:
    _inject_branding()
    user_id = _require_login()
    if user_id is None:
        ui.open("/")
        return

    with session_scope() as session:
        current_user = session.get(User, user_id)
        if current_user is None:
            _logout()
            return
        first_name = current_user.first_name
        last_name = current_user.last_name
        role = current_user.business_role

    ui.row().classes("items-center justify-between w-full")
    with ui.row().classes("items-center"):
        ui.label(f"Hallo, {first_name} {last_name}").classes("text-h6")
        ui.label(f"Rolle: {role}").classes("text-grey")
    ui.button("Logout", on_click=_logout).props("flat color=primary")

    if role == "Vorgesetzter":
        _supervisor_view()
    else:
        _employee_view(user_id)


def _employee_view(user_id: int) -> None:

    with ui.tabs().classes('w-full') as tabs:
        tab_entry = ui.tab('Erfassung')
        tab_week = ui.tab('Woche')
        tab_import = ui.tab('CSV Import')

    with ui.tab_panels(tabs, value=tab_entry).classes('w-full'):
        with ui.tab_panel(tab_entry):
            _employee_entry_panel(user_id)
        with ui.tab_panel(tab_week):
            _employee_week_panel(user_id)
        with ui.tab_panel(tab_import):
            _employee_import_panel(user_id)


def _employee_entry_panel(user_id: int) -> None:

    ui.separator()
    ui.label("Zeiterfassung").classes("text-h6")

    work_date = ui.date(value=date.today().isoformat())

    start_in = ui.input("Arbeitsbeginn (HH:MM)", value="08:00")
    end_in = ui.input("Arbeitsende (HH:MM)", value="17:00")
    short_break = ui.number("Kurzpausen (Min)", value=0, min=0, step=1)

    lunch_start = ui.input("Mittag Beginn (optional, HH:MM)", placeholder="")
    lunch_end = ui.input("Mittag Ende (optional, HH:MM)", placeholder="")

    month_table = ui.table(
        columns=[
            {"name": "date", "label": "Datum", "field": "date", "sortable": True},
            {"name": "start", "label": "Start", "field": "start"},
            {"name": "end", "label": "Ende", "field": "end"},
            {"name": "net", "label": "Netto (h)",
             "field": "net", "sortable": True},
            {"name": "comment", "label": "Kommentar", "field": "comment"},
            {"name": "approved", "label": "Geprüft", "field": "approved"},
        ],
        rows=[],
        row_key="id",
    ).classes("w-full")

    def refresh_month() -> None:
        today = date.today()
        with session_scope() as session:
            service = TimeEntryService(session)
            entries = service.list_month_entries(
                user_id=user_id, year=today.year, month=today.month)
            month_table.rows = [
                {
                    "id": e.id,
                    "date": e.work_date.strftime("%d.%m.%Y"),
                    "start": e.start_time.strftime("%H:%M"),
                    "end": e.end_time.strftime("%H:%M"),
                    "net": f"{e.net_hours:.2f}",
                    "comment": e.comment,
                    "approved": "✅" if e.approved else "⏳",
                }
                for e in entries
            ]
        month_table.update()

    def submit() -> None:
        wd_raw = work_date.value
        if not wd_raw:
            ui.notify("Datum fehlt", color="negative")
            return
        wd = datetime.strptime(wd_raw, "%Y-%m-%d").date()

        start = (start_in.value or "").strip()
        end = (end_in.value or "").strip()
        if not _is_valid_hhmm(start) or not _is_valid_hhmm(end):
            ui.notify("Start/Ende muss HH:MM sein", color="negative")
            return

        ls = (lunch_start.value or "").strip() or None
        le = (lunch_end.value or "").strip() or None
        if (ls and not le) or (le and not ls):
            ui.notify(
                "Mittag braucht Start und Ende (oder leer lassen)", color="negative")
            return
        if ls and (not _is_valid_hhmm(ls) or not _is_valid_hhmm(le or "")):
            ui.notify("Mittag muss HH:MM sein", color="negative")
            return

        with session_scope() as session:
            current_user = session.get(User, user_id)
            if current_user is None:
                ui.notify("Session abgelaufen – bitte neu einloggen",
                          color="negative")
                _logout()
                return

            service = TimeEntryService(session)
            entry = service.upsert_entry(
                user=current_user,
                work_date=wd,
                start_hhmm=start,
                end_hhmm=end,
                lunch_start_hhmm=ls,
                lunch_end_hhmm=le,
                short_break_min=int(short_break.value or 0),
            )

        ui.notify(f"Gespeichert: {entry.net_hours:.2f} h", color="positive")
        refresh_month()

    ui.button("Speichern", on_click=submit).props("color=primary")

    ui.separator()
    ui.label("Aktueller Monat").classes("text-h6")
    refresh_month()


def _employee_week_panel(user_id: int) -> None:
    ui.label('Wochenübersicht').classes('text-h6')

    any_day = ui.date(value=date.today().isoformat())
    week_table = ui.table(
        columns=[
            {"name": "date", "label": "Datum", "field": "date", "sortable": True},
            {"name": "start", "label": "Start", "field": "start"},
            {"name": "end", "label": "Ende", "field": "end"},
            {"name": "net", "label": "Netto (h)", "field": "net"},
            {"name": "comment", "label": "Kommentar", "field": "comment"},
        ],
        rows=[],
        row_key='id',
    ).classes('w-full')

    total_label = ui.label('')

    def refresh_week() -> None:
        raw = any_day.value
        if not raw:
            return
        d = datetime.strptime(raw, '%Y-%m-%d').date()
        with session_scope() as session:
            service = TimeEntryService(session)
            entries = service.list_week_entries(
                user_id=user_id, any_day_in_week=d)
        week_table.rows = [
            {
                'id': e.id,
                'date': e.work_date.strftime('%d.%m.%Y'),
                'start': e.start_time.strftime('%H:%M'),
                'end': e.end_time.strftime('%H:%M'),
                'net': f"{e.net_hours:.2f}",
                'comment': e.comment,
            }
            for e in entries
        ]
        week_table.update()
        total = sum(e.net_hours for e in entries)
        total_label.text = f"Σ Woche: {total:.2f} h"

    ui.button('Aktualisieren', on_click=refresh_week).props('outline')
    refresh_week()


def _employee_import_panel(user_id: int) -> None:
    ui.label('CSV Import').classes('text-h6')
    ui.label('Importiert das Legacy-CSV Format (Delimiter ;, Spalten wie Datum/Arbeitsbeginn/Arbeitsende, ...).').classes('text-grey')

    overwrite = ui.checkbox('Vorhandene Tage überschreiben', value=True)
    result_label = ui.label('')

    def handle_upload(e) -> None:
        csv_bytes = e.content.read()
        with session_scope() as session:
            current_user = session.get(User, user_id)
            if current_user is None:
                ui.notify("Session abgelaufen – bitte neu einloggen",
                          color="negative")
                _logout()
                return
            service = TimeEntryService(session)
            imported, skipped = service.import_csv(
                user=current_user,
                csv_bytes=csv_bytes,
                overwrite=bool(overwrite.value),
            )
        result_label.text = f"Importiert: {imported}, Übersprungen: {skipped}"
        ui.notify('Import abgeschlossen', color='positive')

    ui.upload(label='CSV Datei hochladen',
              auto_upload=True, on_upload=handle_upload)
    ui.separator()
    ui.label('Hinweis: Nach Import bitte in "Monat" oder "Woche" aktualisieren.').classes(
        'text-grey')


def _supervisor_view() -> None:

    ui.separator()

    with ui.tabs().classes("w-full") as tabs:
        unapproved_tab = ui.tab("Offen")
        users_tab = ui.tab("Users")
        report_tab = ui.tab("Report")

    with ui.tab_panels(tabs, value=unapproved_tab).classes("w-full"):
        with ui.tab_panel(unapproved_tab):
            ui.label("Offene Einträge (ungeprüft)").classes("text-h6")

            container = ui.column().classes("w-full")

            def refresh_unapproved() -> None:
                container.clear()
                with session_scope() as session:
                    entry_service = TimeEntryService(session)
                    entries = entry_service.list_unapproved_entries()

                    user_map: dict[int, User] = {}
                    for e in entries:
                        if e.user_id not in user_map:
                            u = session.get(User, e.user_id)
                            if u is not None:
                                user_map[e.user_id] = u
                if not entries:
                    ui.label("Keine offenen Einträge.")
                    return

                for e in entries:
                    user = user_map.get(e.user_id)
                    with container:
                        with ui.row().classes("items-center justify-between w-full"):
                            who = f"#{e.user_id:03d} {user.last_name if user else ''}"
                            ui.label(
                                f"{e.work_date.strftime('%d.%m.%Y')} – {who} – {e.net_hours:.2f} h")
                            with ui.row():
                                ui.label(e.comment).classes("text-grey")
                                ui.button(
                                    "Freigeben",
                                    on_click=lambda entry_id=e.id: (
                                        _approve_entry(entry_id),
                                        ui.notify("Freigegeben",
                                                  color="positive"),
                                        refresh_unapproved(),
                                    ),
                                ).props("outline color=primary")

            refresh_unapproved()
            ui.button("Aktualisieren",
                      on_click=refresh_unapproved).props("flat")

        with ui.tab_panel(users_tab):
            ui.label("Mitarbeiterverwaltung").classes("text-h6")

            role_options = ["Mitarbeiter", "Vorgesetzter"]

            users_table = ui.table(
                columns=[
                    {"name": "id", "label": "ID", "field": "id", "sortable": True},
                    {"name": "name", "label": "Name", "field": "name"},
                    {"name": "email", "label": "E-Mail", "field": "email"},
                    {"name": "role", "label": "Rolle", "field": "role"},
                    {"name": "age", "label": "Alter", "field": "age"},
                ],
                rows=[],
                row_key="id",
                selection="single",
            ).classes("w-full")

            users_by_id: dict[int, User] = {}
            selected_label = ui.label(
                "Bitte Mitarbeiter in der Tabelle auswählen").classes("text-grey")
            selected_user_id: int | None = None

            edit_first = ui.input("Vorname")
            edit_last = ui.input("Nachname")
            edit_email = ui.input("E-Mail")
            edit_role = ui.select(options=role_options, label="Rolle")
            edit_age = ui.number("Alter", value=18, min=0, step=1)

            def load_user_into_form(user_id: int) -> None:
                u = users_by_id.get(user_id)
                if u is None:
                    return
                edit_first.value = u.first_name
                edit_last.value = u.last_name
                edit_email.value = u.email
                edit_role.value = u.business_role
                edit_age.value = u.age

            def refresh_users(*, selected_user_id_override: int | None = None) -> None:
                nonlocal users_by_id
                nonlocal selected_user_id
                if selected_user_id_override is not None:
                    selected_user_id = selected_user_id_override
                with session_scope() as session:
                    users = UserService(session).list_users()
                users_by_id = {u.id: u for u in users}
                users_table.rows = [
                    {
                        "id": u.id,
                        "name": f"{u.first_name} {u.last_name}",
                        "email": u.email,
                        "role": u.business_role,
                        "age": u.age,
                    }
                    for u in users
                ]

                # re-select previously selected user (if any)
                if selected_user_id is not None:
                    for row in users_table.rows:
                        if int(row.get("id")) == int(selected_user_id):
                            users_table.selected = [row]
                            selected_label.text = f"Ausgewählt: #{int(selected_user_id):03d}"
                            load_user_into_form(int(selected_user_id))
                            break
                users_table.update()

            def on_table_select(e) -> None:
                nonlocal selected_user_id
                selection = getattr(e, "selection", None) or []
                if not selection:
                    selected_user_id = None
                    selected_label.text = "Bitte Mitarbeiter in der Tabelle auswählen"
                    return
                row = selection[0]
                try:
                    selected_user_id = int(row.get("id"))
                except Exception:
                    selected_user_id = None
                    selected_label.text = "Bitte Mitarbeiter in der Tabelle auswählen"
                    return
                selected_label.text = f"Ausgewählt: #{selected_user_id:03d}"
                load_user_into_form(selected_user_id)

            users_table.on_select(on_table_select)

            def on_row_click(e) -> None:
                # Quasar emits row click events; depending on the version the event name can differ.
                row = getattr(e, "args", {}).get(
                    "row") if hasattr(e, "args") else None
                if not isinstance(row, dict):
                    return
                try:
                    users_table.selected = [row]
                except Exception:
                    return
                users_table.update()
                on_table_select(type("E", (), {"selection": [row]})())

            users_table.on('row-click', on_row_click, ['row'])
            users_table.on('rowClick', on_row_click, ['row'])

            def save_edit() -> None:
                if not selected_user_id:
                    ui.notify("Bitte Mitarbeiter wählen", color="negative")
                    return
                uid = int(selected_user_id)
                with session_scope() as session:
                    ok = UserService(session).update_user(
                        user_id=uid,
                        first_name=str(edit_first.value or ""),
                        last_name=str(edit_last.value or ""),
                        email=str(edit_email.value or ""),
                        business_role=str(edit_role.value or "Mitarbeiter"),
                        age=int(edit_age.value or 0),
                    )
                if not ok:
                    ui.notify(
                        "Konnte Mitarbeiter nicht speichern (Daten prüfen)", color="negative")
                    return
                ui.notify("Mitarbeiter gespeichert", color="positive")
                refresh_users(selected_user_id_override=uid)

            def reset_pw() -> None:
                if not selected_user_id:
                    ui.notify("Bitte Mitarbeiter wählen", color="negative")
                    return
                uid = int(selected_user_id)
                with session_scope() as session:
                    ok = UserService(session).reset_password(user_id=uid)
                if not ok:
                    ui.notify(
                        "Passwort konnte nicht zurückgesetzt werden", color="negative")
                    return
                ui.notify(
                    "Passwort zurückgesetzt: Benutzer muss neues Passwort setzen", color="positive")

            with ui.row().classes("items-center q-gutter-sm"):
                ui.button("Änderungen speichern",
                          on_click=save_edit).props("color=primary")
                ui.button("Passwort zurücksetzen", on_click=reset_pw).props(
                    "outline color=primary")
                ui.button(
                    "Aktualisieren",
                    on_click=lambda: refresh_users(
                        selected_user_id_override=int(selected_user_id))
                    if selected_user_id
                    else refresh_users(),
                ).props("flat")

            ui.separator()
            ui.label("Neuer Mitarbeiter").classes("text-h6")

            new_id = ui.input("ID").props("type=number")
            new_first = ui.input("Vorname")
            new_last = ui.input("Nachname")
            new_email = ui.input("E-Mail")
            new_role = ui.select(options=role_options,
                                 label="Rolle", value="Mitarbeiter")
            new_age = ui.number("Alter", value=18, min=0, step=1)

            def create_new() -> None:
                try:
                    uid = int(new_id.value)
                except Exception:
                    ui.notify("ID muss eine Zahl sein", color="negative")
                    return
                with session_scope() as session:
                    ok = UserService(session).create_user(
                        user_id=uid,
                        first_name=str(new_first.value or ""),
                        last_name=str(new_last.value or ""),
                        email=str(new_email.value or ""),
                        business_role=str(new_role.value or "Mitarbeiter"),
                        age=int(new_age.value or 0),
                    )
                if not ok:
                    ui.notify(
                        "Konnte Mitarbeiter nicht anlegen (ID frei? Daten korrekt?)", color="negative")
                    return
                ui.notify(
                    "Mitarbeiter angelegt (Passwort muss gesetzt werden)", color="positive")
                new_id.value = ""
                new_first.value = ""
                new_last.value = ""
                new_email.value = ""
                new_role.value = "Mitarbeiter"
                new_age.value = 18
                refresh_users(selected_user_id_override=uid)

            ui.button("Anlegen", on_click=create_new).props("color=primary")

            ui.separator()
            seeded_label = ui.label("")

            def seed_users() -> None:
                users_json = Path(__file__).resolve(
                ).parent.parent / "programms" / "users.json"
                with session_scope() as session:
                    user_service = UserService(session)
                    created = user_service.seed_from_users_json_if_empty(
                        users_json)
                seeded_label.text = f"Seeded: {created} user(s)" if created else "Keine Änderungen"
                refresh_users(selected_user_id_override=int(
                    selected_user_id) if selected_user_id else None)

            ui.button("Seed aus users.json (falls DB leer)",
                      on_click=seed_users).props("outline")

            refresh_users()

        with ui.tab_panel(report_tab):
            ui.label("Monatsreport")

            with session_scope() as session:
                users = UserService(session).list_users()
            options = {f"#{u.id:03d} {u.last_name}": u.id for u in users}
            user_select = ui.select(options=options, label="Mitarbeiter")
            month_in = ui.input("Monat (YYYY-MM)",
                                value=date.today().strftime("%Y-%m"))
            out = ui.textarea("Report", value="").props(
                "readonly").classes("w-full")

            def gen() -> None:
                if not user_select.value:
                    ui.notify("Mitarbeiter wählen", color="negative")
                    return
                try:
                    y, m = (month_in.value or "").split("-")
                    year = int(y)
                    month = int(m)
                except Exception:
                    ui.notify("Monat muss YYYY-MM sein", color="negative")
                    return

                with session_scope() as session:
                    report_service = ReportService(session)
                    report = report_service.generate_employee_monthly_report(
                        user_id=int(user_select.value),
                        year=year,
                        month=month,
                    )
                out.value = report.text

            ui.button("Report erstellen", on_click=gen).props("color=primary")


def _approve_entry(entry_id: int) -> None:
    with session_scope() as session:
        TimeEntryService(session).approve_entry(entry_id=entry_id)


def main() -> None:
    init_db()

    # Ensure global branding is injected before the server starts
    _inject_branding()

    # auto seed users once (idempotent)
    with session_scope() as session:
        user_service = UserService(session)
        users_json = Path(__file__).resolve().parent.parent / \
            "programms" / "users.json"
        user_service.seed_from_users_json_if_empty(users_json)

    ui.run(
        title="WTCalculator",
        reload=False,
        storage_secret=os.getenv(
            "WTCALC_STORAGE_SECRET", "dev-storage-secret"),
        port=int(os.getenv("WTCALC_PORT", "8081")),
    )


if __name__ == "__main__":
    main()
