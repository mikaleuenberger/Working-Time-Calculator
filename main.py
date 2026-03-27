from __future__ import annotations

import sys


def _print_venv_hint() -> None:
    print("\nWTCalculator Webapp konnte nicht gestartet werden: Python-Dependencies fehlen.\n")
    print("Ursache: Du verwendest sehr wahrscheinlich den System-Python (z.B. /usr/bin/python3) statt .venv.\n")
    print("So startest du korrekt im Projektroot:\n")
    print("  python3 -m venv .venv")
    print("  source .venv/bin/activate")
    print("  python -m pip install -r requirements.txt")
    print("  python main.py\n")
    print("Windows (PowerShell):\n")
    print("  py -m venv .venv")
    print("  .venv\\Scripts\\Activate.ps1")
    print("  python -m pip install -r requirements.txt")
    print("  python main.py\n")


if __name__ == "__main__":
    try:
        from wtcalculator.webapp import main
    except ModuleNotFoundError as exc:
        if exc.name in {"nicegui", "sqlalchemy"}:
            _print_venv_hint()
            raise SystemExit(1)
        raise

    sys.exit(main() or 0)
