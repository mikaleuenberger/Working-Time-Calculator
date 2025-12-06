
# Dieses Programm erstellt Monatsrapporte für Mitarbeitende
# und eine Monatsübersicht für Vorgesetzte.

from pathlib import Path
from datetime import datetime
import csv
import json

DTFMT = "%d.%m.%Y"


# User-Daten aus users.json laden

def load_user_data(base_dir):
    # Lädt users.json und gibt dict mit ID → Klarname zurück
    candidate_paths = [
        base_dir / "users.json",
        base_dir / "data" / "users.json",
        base_dir / "programms" / "users.json",
    ]

    user_file = None
    for p in candidate_paths:
        if p.exists():
            user_file = p
            break

    if user_file is None:
        print("⚠️ users.json nicht gefunden. Klarname wird auf 'unbekannt' gesetzt.")
        return {}

    print("✔ users.json geladen von:", user_file)

    with user_file.open(encoding="utf-8") as fh:
        data = json.load(fh)

    users = {}  # ID → Klarname
    for u in data.get("users", []):
        try:
            emp_id = int(u["id"])
        except:
            continue

        # surname = Vorname
        # name    = Nachname
        vorname = str(u.get("surname", "")).strip()
        nachname = str(u.get("last_name", "")).strip()

        klarname = (vorname + " " + nachname).strip() or "unbekannt"

        users[emp_id] = klarname

    return users


# Hilfsfunktionen

def mm_to_hhmm(total_min):
    # Wandelt Minuten in HH:MM um
    sign = "-" if total_min < 0 else ""
    total_min = abs(total_min)
    h, m = divmod(total_min, 60)
    return "%s%02d:%02d" % (sign, h, m)


def row_minutes(row):
    # NEU: Zuerst versuchen, den bereits berechneten Wert 'Netto_Stunden' zu nutzen
    net_hours_str = (row.get("Netto_Stunden") or "").strip().replace(',', '.')
    try:
        # Konvertiere den String (mit eventuellem Komma oder Punkt) in eine Float-Stundenzahl
        net_hours_decimal = float(net_hours_str)
        # Gib die Stunden als ganze Minuten zurück (wie der Rest der Funktion erwartet)
        return int(net_hours_decimal * 60)
    except ValueError:
        # Wenn das Feld 'Netto_Stunden' leer, nicht vorhanden oder fehlerhaft ist,
        # fallback zur alten Methode der Neuberechnung aus Einzelzeiten.
        pass
    # Berechnet Nettoarbeitszeit für eine CSV-Zeile
    start_str = (row.get("Arbeitsbeginn") or "").strip()
    end_str = (row.get("Arbeitsende") or "").strip()

    if not start_str or not end_str:
        return 0

    try:
        start = datetime.strptime(start_str, "%H:%M")
        end = datetime.strptime(end_str, "%H:%M")
    except:
        return 0

    gross = int((end - start).total_seconds() // 60)

    pause_str = (row.get("Pause_min") or "").strip()
    try:
        pause_min = int(pause_str)
    except:
        pause_min = 0

    lunch_min = 0
    lf = (row.get("Mittag_beginn") or "").strip()
    lt = (row.get("Mittag_ende") or "").strip()

    if lf and lt:
        try:
            lf_dt = datetime.strptime(lf, "%H:%M")
            lt_dt = datetime.strptime(lt, "%H:%M")
            lunch_min = int((lt_dt - lf_dt).total_seconds() // 60)
        except:
            lunch_min = 0

    return max(0, gross - pause_min - lunch_min)


# Mitarbeiter-Report

def generate_employee_report(base_dir, month, emp_id=None):
    # Erstellt Monatsrapport für einen Mitarbeitenden
    users = load_user_data(base_dir)
    files = []
# In programms/reports.py, inside generate_employee_report function:

    full_name = users.get(emp_id)

    if full_name:
        user_folder = full_name.split()[-1]

        print(f"Ordner suchen: {user_folder}")

        for folder_name in ["geprueft", "ungeprueft"]:
            folder = base_dir / "data" / "working" / folder_name / user_folder

            if folder.exists():
                files.extend(folder.glob(month + "_*.csv"))
    else:
        print(f"Error: User ID {emp_id} nicht gefunden.")

    target_file = None
    for f in files:
        parts = f.stem.split("_")
        if len(parts) < 3:
            continue

        try:
            file_emp_id = int(parts[1])
        except:
            continue

        if emp_id is None or emp_id == file_emp_id:
            target_file = f
            break

    if target_file is None:
        print("❌ Keine passende Datei gefunden.")
        return None

    # CSV laden
    with target_file.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter=";")
        rows = list(reader)

    total_min = 0
    week_sums = {}
    errors = []

    for r in rows:
        mins = row_minutes(r)
        total_min += mins

        d = (r.get("Datum") or "").strip()
        if d:
            try:
                dt = datetime.strptime(d, DTFMT)
                year, week_nr, _ = dt.isocalendar()
                key = (year, week_nr)
                week_sums[key] = week_sums.get(key, 0) + mins
            except:
                pass

        comment = (r.get("Kommentar") or "").strip()
        if comment:
            errors.append(d + " " + comment)

    weekly_overtime = 0
    for key in week_sums:
        if week_sums[key] > 42 * 60:
            weekly_overtime += week_sums[key] - 42 * 60

    parts = target_file.stem.split("_")
    emp_id_from_file = int(parts[1])
    nick = parts[2]

    # Report zusammenstellen
    lines = []
    lines.append("Mitarbeiter #%03d (%s)" % (emp_id_from_file, nick))
    lines.append("------------------------------------------")
    lines.append("Datum        Wochentag   Netto    Kommentar")

    for r in rows:
        d = (r.get("Datum") or "").ljust(12)
        w = (r.get("Wochentag") or "")[:10].ljust(11)
        netto = mm_to_hhmm(row_minutes(r)).rjust(7)
        c = r.get("Kommentar") or ""
        lines.append("%s%s%s   %s" % (d, w, netto, c))

    lines.append("")
    lines.append("Hinweise:")
    if errors:
        for e in errors:
            lines.append("! " + e)
    else:
        lines.append("keine")

    lines.append("------------------------------------------")
    lines.append("Total Monat:        " + mm_to_hhmm(total_min))
    lines.append("Überstunden (Wo):   " + mm_to_hhmm(weekly_overtime))

    out_dir = base_dir / "data" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / ("%s_report_%03d_%s.txt" %
                          (month, emp_id_from_file, nick))

    with out_path.open("w", encoding="utf-8") as out:
        out.write("\n".join(lines))

    print("✔ Report erstellt:", out_path)
    return out_path


# Vorgesetzten-Übersicht

def generate_supervisor_overview(base_dir, month):
    # Erstellt eine Übersicht über alle Mitarbeitenden

    users = load_user_data(base_dir)

    files = []

    full_name = users.get(emp_id)

    if full_name:
        user_folder = full_name.split()[-1]

        print(f"Ordner suchen: {user_folder}")

        for folder_name in ["geprueft", "ungeprueft"]:
            folder = base_dir / "data" / "working" / folder_name / user_folder

            if folder.exists():
                files.extend(folder.glob(month + "_*.csv"))
    else:
        print(f"Error: User ID {emp_id} nicht gefunden.")

    out_lines = [
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
        week_sums = {}
        has_errors = False

        for r in rows:
            mins = row_minutes(r)
            total_min += mins

            if (r.get("Kommentar") or "").strip():
                has_errors = True

            d = (r.get("Datum") or "").strip()
            if d:
                try:
                    dt = datetime.strptime(d, DTFMT)
                    year, week_nr, _ = dt.isocalendar()
                    key = (year, week_nr)
                    week_sums[key] = week_sums.get(key, 0) + mins
                except:
                    pass

        overtime = 0
        for key in week_sums:
            if week_sums[key] > 42 * 60:
                overtime += week_sums[key] - 42 * 60

        status = "geprueft" if f.parent.name == "geprueft" else "ungeprueft"
        klarname = users.get(emp_id, "unbekannt")

        out_lines.append(
            "%d;%s;%s;%s;%s;%s;%s;%s"
            % (emp_id, klarname, nick, status,
               mm_to_hhmm(total_min),
               mm_to_hhmm(overtime),
               str(has_errors).lower(),
               f.name)
        )

    out_dir = base_dir / "data" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / (month + "_supervisor_overview.csv")

    with out_path.open("w", encoding="utf-8") as out:
        out.write("\n".join(out_lines))

    print("✔ Übersicht erstellt:", out_path)
    return out_path
