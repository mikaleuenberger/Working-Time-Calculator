from datetime import datetime
import os
import re

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore
from nicegui import ui, app
from ..app_controler import AuthController


def _now() -> datetime:
    tz_name = os.environ.get("WTCALC_TZ", "Europe/Zurich")
    if ZoneInfo is None:
        return datetime.now()
    try:
        return datetime.now(ZoneInfo(tz_name))
    except Exception:
        return datetime.now()


class LoginPageUI:
    def __init__(self):
        self.controller = AuthController()
        self.user_id_input = None
        self.last_name_input = None
        self.password_input = None
        self.build_ui()

    def build_ui(self):
        ui.label("WTCalculator – Login").classes("text-h5 text-white")

        with ui.row().classes("w-full justify-center items-stretch q-gutter-xl"):

            def _clock_svg(now: datetime, *, size: int = 260) -> str:
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

            with ui.card().classes("w-80 items-center justify-center"):
                ui.label("Uhr").classes("text-h6")
                clock_html = ui.html(_clock_svg(_now(), size=260))
                time_label = ui.label(_now().strftime("%H:%M:%S")).classes("text-h5")

                def tick():
                    now = _now()
                    time_label.text = now.strftime("%H:%M:%S")
                    clock_html.content = _clock_svg(now, size=260)
                    clock_html.update()

                ui.timer(1.0, tick)

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
        uid_val = self.user_id_input.value or ""
        lname_val = self.last_name_input.value or ""
        pw_val = self.password_input.value or ""

        result = self.controller.attempt_login(uid_val, lname_val, pw_val)

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
        self.pw1_input = None
        self.pw2_input = None
        self.build_ui()

    def build_ui(self):
        with ui.column().classes("w-full items-center mt-12"):
            ui.label('Passwort setzen').classes('text-h5 text-white q-mb-md')

            with ui.card().classes("w-96 q-pa-md"):
                self.pw1_input = (
                    ui.input('Neues Passwort', password=True,
                             password_toggle_button=True)
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

                with ui.row().classes('w-full justify-end q-gutter-sm'):
                    ui.button('Abbrechen', on_click=self.do_cancel).props('flat')
                    ui.button('Speichern', on_click=self.do_save).props('color=primary')

    def do_save(self):
        pw1 = self.pw1_input.value or ""
        pw2 = self.pw2_input.value or ""

        pending_user_id = app.storage.user.get('pending_user_id')
        if pending_user_id is None:
            ui.open("/")
            return

        result = self.controller.set_new_password(pending_user_id, pw1, pw2)

        if result["status"] == "error":
            ui.notify(result["message"], color="negative")
        elif result["status"] == "success":
            app.storage.user.pop('pending_user_id', None)
            ui.notify('Passwort gesetzt. Bitte einloggen.', color='positive')
            ui.open('/')

    def do_cancel(self):
        app.storage.user.pop('pending_user_id', None)
        ui.open('/')
