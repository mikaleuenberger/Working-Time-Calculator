# reports.py
# Dieses Programm erstellt Monatsrapporte für Mitarbeitende
# und eine Monatsübersicht für Vorgesetzte.

from pathlib import Path
from datetime import datetime
import csv
import json

# So steht das Datum in euren CSV Dateien, z. B. 06.10.2025
DTFMT = "%d.%m.%Y"


# ---------------------------------------------------
# User-Daten aus users.json laden
# ---------------------------------------------------

def load_user_data(base_dir: Path) -> dict:
    """Lädt users.json und gibt dict mit ID → Klarname zurück."""
    # Mögliche Speicherorte der users.json
    candidate_paths = [
        base_dir / "users.json",
        base_dir / "data" / "users.json",
    ]

    user_file = None
    for p in candidate_paths:
        if p.exists():
            user_file = p
            break

    if user_file is None:
        print("⚠️ users.json nicht gefunden (weder im Projektroot noch im data/-Ordner)."
              " Klarname wird auf 'unbekannt' gesetzt.")
        return {}

    # Debug: zeigen, welche Datei verwendet wird
    print(f"ℹ️ users.json geladen von: {user_file}")

    with user_file.open(encoding="utf-8") as fh:
        data = json.load(fh)

    users = {}
    # Struktur deines JSON:
    # { "users": [ { "id": 1, "name": "Müller", "surname": "Hans", ... }, ... ] }
    for u in data.get("users", []):
        try:
            emp_id = int(u["id"])
        except (KeyError, ValueError, TypeError):
            continue

        # In deinem JSON:
        # name    = Nachname (z.B. "Müller")
        # surname = Vorname  (z.B. "Hans")
        vorname = str(u.get("surname", "")).strip()
        nachname = str(u.get("name", "")).strip()
        klarname = f"{vorname} {nachname}".strip()  # "Hans Müller"

        users[emp_id] = klarname or "unbekannt"

    return users


# ---------------------------------------------------
# HILFSFUNKTIONEN
# ---------------------------------------------------

def mm_to_hhmm(total_min: int) -> str:
    """Wandelt Minuten in HH:MM um, Beispiel: 510 → 08:30."""
    sign = "-" if total_min < 0 else ""
    total_min = abs(total_min)
    h, m = divmod(total_min, 60)
    return f"{sign}{h:02d}:{m:02d}"


def row_minutes(row: dict) -> int:
    """Berechnet die Nettoarbeitszeit für eine Zeile im CSV."""

    start_str = (row.get("Arbeitsbeginn") or "").strip()
    end_str = (row.get("Arbeitsende") or "").strip()
    if not start_str or not end_str:
        return 0

    try:
        start = datetime.strptime(start_str, "%H:%M")
        end = datetime.strptime(end_str, "%H:%M")
    except ValueError:
        return 0

    gross = int((end - start).total_seconds() // 60)

    pause_str = (row.get("Pause_min") or "").strip()
    try:
        pause_min = int(pause_str) if pause_str != "" else 0
    except ValueError:
        pause_min = 0

    lunch_min = 0
    lunch_from = (row.get("Mittag_beginn") or "").strip()
    lunch_to = (row.get("Mittag_ende") or "").strip()
    if lunch_from and lunch_to:
        try:
            lf = datetime.strptime(lunch_from, "%H:%M")
            lt = datetime.strptime(lunch_to, "%H:%M")
            lunch_min = int((lt - lf).total_seconds() // 60)
        except ValueError:
            lunch_min = 0

    netto = gross - pause_min - lunch_min
    return max(0, netto)


# ---------------------------------------------------
# HAUPTFUNKTION 1: Report für EINEN Mitarbeiter
# ---------------------------------------------------

def generate_employee_report(base_dir: Path, month: str, emp_id: int | None = None) -> Path | None:
    """Erstellt einen Monatsrapport für eine bestimmte Person (nur über Mitarbeiter-ID)."""

    # Alle Dateien des Monats suchen.
    files: list[Path] = []
    for folder_name in ["geprueft", "ungeprueft"]:
        folder = base_dir / "data" / "working" / folder_name
        if folder.exists():
            files.extend(folder.glob(f"{month}_*.csv"))

    # Passende Datei für den Mitarbeitenden finden.
    # Erwartetes Dateiformat: YYYY-MM_ID_NICKNAME.csv
    target_file: Path | None = None
    for f in files:
        parts = f.stem.split("_")
        if len(parts) < 3:
            continue

        try:
            file_emp_id = int(parts[1])
        except ValueError:
            continue

        if emp_id is None or emp_id == file_emp_id:
            target_file = f
            break

    if target_file is None:
        print("Keine passende Datei gefunden.")
        return None

    # CSV-Datei einlesen
    with target_file.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter=";")
        rows = list(reader)

    total_min = 0
    week_sums: dict[tuple[int, int], int] = {}
    errors: list[str] = []

    for r in rows:
        mins = row_minutes(r)
        total_min += mins

        date_str = (r.get("Datum") or "").strip()
        if date_str:
            try:
                dt = datetime.strptime(date_str, DTFMT)
                year, week_nr, _ = dt.isocalendar()
                key = (year, week_nr)
                week_sums[key] = week_sums.get(key, 0) + mins
            except ValueError:
                pass

        comment = (r.get("Kommentar") or "").strip()
        if comment:
            errors.append(f"{date_str} {comment}")

    weekly_overtime = 0
    for key in week_sums:
        week_min = week_sums[key]
        if week_min > 42 * 60:
            weekly_overtime += week_min - 42 * 60

    parts = target_file.stem.split("_")
    emp_id_from_file = int(parts[1])
    nick_from_file = parts[2]

    lines: list[str] = []
    lines.append(f"Mitarbeiter #{emp_id_from_file:03d} ({nick_from_file})")
    lines.append("------------------------------------------")
    lines.append("Datum        Wochentag   Netto    Kommentar")

    for r in rows:
        d = (r.get("Datum", "")).ljust(12)
        w = (r.get("Wochentag", "")[:10]).ljust(11)
        netto_str = mm_to_hhmm(row_minutes(r)).rjust(7)
        c = (r.get("Kommentar") or "")
        lines.append(f"{d}{w}{netto_str}   {c}")

    lines.append("")
    lines.append("Hinweise:")
    if errors:
        for e in errors:
            lines.append(f"! {e}")
    else:
        lines.append("keine")

    lines.append("------------------------------------------")
    lines.append(f"Total Monat:        {mm_to_hhmm(total_min)}")
    lines.append(f"Überstunden (Wo):   {mm_to_hhmm(weekly_overtime)}")

    out_dir = base_dir / "data" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / \
        f"{month}_report_{emp_id_from_file:03d}_{nick_from_file}.txt"

    with out_path.open("w", encoding="utf-8") as out:
        out.write("\n".join(lines))

    print(f"Report erstellt: {out_path}")
    return out_path


# ---------------------------------------------------
# HAUPTFUNKTION 2: Übersicht für Vorgesetzte
# ---------------------------------------------------

def generate_supervisor_overview(base_dir: Path, month: str) -> Path:
    """Erstellt eine Übersicht über alle Mitarbeitenden des Monats."""

    # Klarname aus users.json laden
    users = load_user_data(base_dir)

    files: list[Path] = []
    for folder_name in ["geprueft", "ungeprueft"]:
        folder = base_dir / "data" / "working" / folder_name
        if folder.exists():
            files.extend(folder.glob(f"{month}_*.csv"))

    # Headerzeile
    out_lines: list[str] = [
        "emp_id;klarname;nickname;status;total_hhmm;overtime_week_hhmm;has_errors;source_file"
    ]

    for f in files:
        with f.open(encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh, delimiter=";")
            rows = list(reader)

        parts = f.stem.split("_")
        if len(parts) < 3:
            continue

        emp_id = int(parts[1])
        nick = parts[2]

        total_min = 0
        week_sums: dict[tuple[int, int], int] = {}
        has_errors = False

        for r in rows:
            mins = row_minutes(r)
            total_min += mins

            if (r.get("Kommentar") or "").strip():
                has_errors = True

            date_str = (r.get("Datum") or "").strip()
            if date_str:
                try:
                    dt = datetime.strptime(date_str, DTFMT)
                    year, week_nr, _ = dt.isocalendar()
                    key = (year, week_nr)
                    week_sums[key] = week_sums.get(key, 0) + mins
                except ValueError:
                    pass

        overtime = 0
        for key in week_sums:
            week_min = week_sums[key]
            if week_min > 42 * 60:
                overtime += week_min - 42 * 60

        status = "geprueft" if f.parent.name == "geprueft" else "ungeprueft"

        klarname = users.get(emp_id, "unbekannt")

        out_lines.append(
            f"{emp_id};{klarname};{nick};{status};"
            f"{mm_to_hhmm(total_min)};{mm_to_hhmm(overtime)};"
            f"{str(has_errors).lower()};{f.name}"
        )

    out_dir = base_dir / "data" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{month}_supervisor_overview.csv"

    with out_path.open("w", encoding="utf-8") as out:
        out.write("\n".join(out_lines))

    print(f"Übersicht erstellt: {out_path}")
    return out_path
