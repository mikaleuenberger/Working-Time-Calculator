from __future__ import annotations
from nicegui import ui, app

# Wir sagen Python, dass es in den Ordner "wtcalculator" schauen muss
from wtcalculator.webapp import LoginPageUI, SetPasswordUI, DashboardUI 

import re
from datetime import date, datetime
from pathlib import Path
from urllib.parse import quote
import os

# Auch hier den Ordnernamen davor setzen!
from wtcalculator.db import init_db, session_scope
from wtcalculator.models import TimeEntry, User
from wtcalculator.services.auth_service import AuthService
from wtcalculator.services.report_service import ReportService
from wtcalculator.services.time_entry_service import TimeEntryService
from wtcalculator.services.user_service import UserService
from wtcalculator.security import validate_password_policy

_TIME_RE = re.compile(r"^\d{2}:\d{2}$")
_BRANDING_INJECTED = False
_LOGIN_BG = "#2B2B2B"

def _require_login() -> int | None:
    user_id = app.storage.user.get("user_id")
    return int(user_id) if user_id is not None else None

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


# --- 1. LOGIN ROUTE ---
@ui.page("/")
def render_login_page():
    _inject_branding()
    _fixed_page_background(_LOGIN_BG)
    if _require_login() is not None:
        ui.open("/dashboard")
        return
        
    LoginPageUI() # Startet die ausgelagerte Login-Ansicht


# --- 2. PASSWORT SETZEN ROUTE ---
@ui.page('/set-password')
def render_set_password_page():
    _inject_branding()
    _fixed_page_background(_LOGIN_BG)
    
    # Sicherheitscheck aus dem alten Code
    pending_user_id = app.storage.user.get('pending_user_id')
    if pending_user_id is None:
        ui.open("/")
        return
        
    SetPasswordUI() # Startet die ausgelagerte Passwort-Ansicht


# --- 3. DASHBOARD ROUTE ---
@ui.page('/dashboard')
def render_dashboard_page():
    _inject_branding()
    _fixed_page_background(_LOGIN_BG)
    
    # Sicherheitscheck aus dem alten Code
    user_id = _require_login()
    if user_id is None:
        ui.open("/")
        return
        
    DashboardUI(user_id) # Startet die ausgelagerte Dashboard-Ansicht (übergibt die ID)


if __name__ in {"__main__", "__mp_main__"}:
    # Railway/Container hosting
    # - bind to 0.0.0.0 so the service is reachable from outside the container
    port = int(os.environ.get("PORT", "8080"))

    ui.run(host="0.0.0.0", port=port, storage_secret='wtcalculator_secret')