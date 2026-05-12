from nicegui import ui, app
from ..app_controler import AuthController
from .employee_dashboard import EmployeeDashboardUI
from .supervisor_dashboard import SupervisorDashboardUI, UserAdminUI


class DashboardUI:
    def __init__(self, user_id: int):
        self.controller = AuthController()
        self.user_id = user_id

        self.user_info = self.controller.get_user_info(self.user_id)

        if self.user_info is None:
            self.do_logout()
            return

        self.build_ui()

    def build_ui(self):
        with ui.row().classes("items-center justify-between w-full q-pa-md bg-dark shadow-2"):
            with ui.row().classes("items-center q-gutter-md"):
                ui.label(f"Hallo, {self.user_info['first_name']} {self.user_info['last_name']}").classes(
                    "text-h6 text-white")
                ui.label(f"Rolle: {self.user_info['role']}").classes(
                    "text-grey")
            ui.button("Logout", on_click=self.do_logout).props(
                "flat color=primary")

        ui.separator()

        with ui.column().classes("w-full q-pa-md items-center"):
            if self.user_info['role'] == "Vorgesetzter":
                with ui.tabs().classes('w-full bg-dark shadow-2 text-grey-5') \
                        .props('active-color=primary active-bg-color=grey-9 indicator-color=primary') as tabs:

                    t1 = ui.tab('Freigaben', icon='check_circle')
                    t2 = ui.tab('Mitarbeiter', icon='people')

                with ui.tab_panels(tabs, value=t1).classes('w-full bg-transparent'):
                    with ui.tab_panel(t1):
                        SupervisorDashboardUI()
                    with ui.tab_panel(t2):
                        UserAdminUI(self.user_id)
            else:
                EmployeeDashboardUI(self.user_id)

    def do_logout(self):
        app.storage.user.clear()
        ui.open('/')
