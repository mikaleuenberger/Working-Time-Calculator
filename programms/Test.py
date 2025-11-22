# Dieses Programm erstellt Arbeitszeitrapporte
# 1. Für einzelne Mitarbeiter (TXT-Report)
# 2. Für den Vorgesetzten (CSV-Übersicht)
#
# Der Code liest vorhandene Monatsdateien aus den Ordnern


# --> ""STRUKTUR""??
# data/working/geprueft und data/working/ungeprueft
# und wertet sie aus.
# -------------------------------------------

from pathlib import Path
from datetime import datetime
import csv

# Format, wie das Datum in der CSV steht (z. B. 06.10.2025)
DTFMT = "%d.%m.%Y"


# ------------------------------------------------------------
# HILFSFUNKTIONEN (werden intern verwendet)
# ------------------------------------------------------------

def _mm_to_hhmm(total_min: int) -> str:
    # Wandelt Minuten in das Format HH:MM um (z. B. 510 --> '08:30').
    sign = "-" if total_min < 0 else ""
    total_min = abs(total_min)
    h, m = divmod(total_min, 60)
    return f"{sign}{h:02d}:{m:02d}"


def _parse_hhmm(s: str) -> datetime:
    # Liest eine Uhrzeit im Format HH:MM in ein datetime-Objekt ein.
    return datetime.strptime(s, "%H:%M")


def _safe_int(x, default=0) -> int:
    # Versucht, eine Eingabe in eine ganze Zahl umzuwandeln, sonst default.
    try:
        return int(str(x).strip())
    except Exception:
        return default


def _row_minutes(row: dict) -> int:
    """
    Berechnet die Nettoarbeitszeit (in Minuten) für eine Zeile.
    Erwartete Spalten:
      Arbeitsbeginn, Arbeitsende, Pause_min (optional),
      Mittag_beginn, Mittag_ende (optional)
    """
    beg = (row.get("Arbeitsbeginn") or "").strip()
    end = (row.get("Arbeitsende") or "").strip()

    # Ohne gültige Start- oder Endzeit --> 0 Minuten
    if not beg or not end:
        return 0

    # Umwandeln in datetime-Objekte
    try:
        start = _parse_hhmm(beg)
        finish = _parse_hhmm(end)
    except Exception:
        return 0

    # Bruttoarbeitszeit in Minuten
    gross = int((finish - start).total_seconds() // 60)

    # Pausen in Minuten abziehen
    pause_min = _safe_int(row.get("Pause_min", 0), 0)

    # Mittagspause optional verrechnen
    lf = (row.get("Mittag_beginn") or "").strip()
    lt = (row.get("Mittag_ende") or "").strip()
    lunch = 0
    if lf and lt:
        try:
            lunch = int(
                (_parse_hhmm(lt) - _parse_hhmm(lf)).total_seconds() // 60)
        except Exception:
            lunch = 0

    # Nettozeit (nicht negativ)
    return max(0, gross - pause_min - lunch)


def _collect_files(base: Path, month: str):
    # Sucht alle CSV-Dateien eines Monats in geprueft/ungeprueft.
    files = []
    for bucket in ["geprueft", "ungeprueft"]:
        folder = base / "data" / "working" / bucket
        if folder.exists():
            # Beispiel: 2025-10_001_muellerh.csv
            files.extend(sorted(folder.glob(f"{month}_*.csv")))
    return files


def _emp_from_fname(p: Path):
    # Extrahiert Mitarbeiter-ID und Nickname aus Dateinamen.
    # Erwartet: YYYY-MM_<id>_<nickname>.csv
    parts = p.stem.split("_")
    if len(parts) >= 3:
        try:
            return int(parts[1]), parts[2]
        except Exception:
            return 0, "unknown"
    return 0, "unknown"


def _read_rows(path: Path):
    # Liest eine CSV-Datei in eine Liste von Dictionarys ein.
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter=";"))


# ------------------------------------------------------------
# HAUPTFUNKTIONEN (werden im Hauptprogramm aufgerufen)
# ------------------------------------------------------------

def generate_employee_report(base: Path, month: str, emp_id: int | None = None, nickname: str | None = None) -> Path | None:
    """
    Erstellt einen Monatsrapport (TXT) für einen bestimmten Mitarbeiter.

    - base: Projektverzeichnis (z. B. Path(__file__).resolve().parent)
    - month: Monat im Format YYYY-MM (z. B. "2025-10")
    - emp_id: Mitarbeiter-ID (optional)
    - nickname: Nickname (optional)
    """

    # Suche die passende Datei für den Mitarbeiter
    target = None
    for f in _collect_files(base, month):
        eid, nick = _emp_from_fname(f)
        if (emp_id is None or emp_id == eid) and (nickname is None or nickname == nick):
            target = f
            break

    if not target:
        print("❌ Keine Datei für Mitarbeitenden gefunden (Monat/ID/Nickname prüfen).")
        return None

    # CSV einlesen
    rows = _read_rows(target)
    total_min = 0
    week_sums = {}  # speichert Arbeitsminuten pro Woche (Jahr, KW)
    errors = []  # sammelt alle Fehlertexte aus Kommentar-Spalte

    # Durch alle Zeilen gehen
    for r in rows:
        mins = _row_minutes(r)
        total_min += mins

        # Kalenderwoche berechnen (für Überstunden je KW)
        d = (r.get("Datum") or "").strip()
        if d:
            try:
                dt = datetime.strptime(d, DTFMT)
                y, w, _ = dt.isocalendar()
                week_sums[(y, w)] = week_sums.get((y, w), 0) + mins
            except Exception:
                pass

        # Kommentare speichern
        comment = (r.get("Kommentar") or "").strip()
        if comment:
            errors.append(f"{r.get('Datum','')} {comment}")

    # Überstunden pro Woche berechnen (mehr als 42h)
    weekly_overtime = sum(max(0, m - 42 * 60) for m in week_sums.values())

    # Report als Text zusammensetzen
    eid, nick = _emp_from_fname(target)
    lines = []
    lines.append(f"Mitarbeiter #{eid:03d} ({nick})")
    lines.append("-" * 42)
    lines.append("Datum        Wochentag   Netto    Kommentar")

    for r in rows:
        d = (r.get("Datum", "")).ljust(12)
        w = (r.get("Wochentag", "")[:10]).ljust(11)
        mm = _mm_to_hhmm(_row_minutes(r)).rjust(7)
        c = (r.get("Kommentar") or "")
        lines.append(f"{d}{w}{mm}   {c}")

    # Footer mit Hinweisen und Summen
    lines.append("\nHinweise:")
    if errors:
        for e in errors:
            lines.append(f"! {e}")
    else:
        lines.append("(keine)")

    lines.append("-" * 42)
    lines.append(f"Total Monat:        {_mm_to_hhmm(total_min)}")
    lines.append(
        f"Überstunden (Wo):   {_mm_to_hhmm(weekly_overtime)}  (Basis 42h/Woche)")

    # Ausgabe-Datei anlegen (z. B. data/reports/2025-10_report_001_muellerh.txt)
    out = base / "data" / "reports" / f"{month}_report_{eid:03d}_{nick}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")

    print(f"📄 Report erstellt: {out}")
    return out


def generate_supervisor_overview(base: Path, month: str) -> Path:
    """
    Erstellt eine CSV-Übersicht für den Vorgesetzten über alle Mitarbeiter
    im angegebenen Monat. Enthält:
      - Mitarbeiter-ID / Nickname
      - Status (geprüft/ungeprüft)
      - Total Stunden / Überstunden
      - Ob Fehler (Kommentar) vorhanden sind
    """
    files = _collect_files(base, month)
    out_lines = [
        "emp_id;nickname;status;total_hhmm;overtime_week_hhmm;has_errors;source_file"]

    for f in files:
        rows = _read_rows(f)
        eid, nick = _emp_from_fname(f)
        total_min = sum(_row_minutes(r) for r in rows)

        # Wochenweise Überstunden berechnen
        week_sums = {}
        has_err = False
        for r in rows:
            if (r.get("Kommentar") or "").strip():
                has_err = True
            d = (r.get("Datum") or "").strip()
            if d:
                try:
                    dt = datetime.strptime(d, DTFMT)
                    y, w, _ = dt.isocalendar()
                    week_sums[(y, w)] = week_sums.get(
                        (y, w), 0) + _row_minutes(r)
                except Exception:
                    pass

        overtime = sum(max(0, m - 42 * 60) for m in week_sums.values())
        status = "geprueft" if f.parent.name == "geprueft" else "ungeprueft"

        # Zeile in Übersicht ergänzen
        out_lines.append(
            f"{eid};{nick};{status};{_mm_to_hhmm(total_min)};{_mm_to_hhmm(overtime)};{str(has_err).lower()};{f.name}"
        )

    # CSV speichern im reports-Ordner
    out = base / "data" / "reports" / f"{month}_supervisor_overview.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(out_lines), encoding="utf-8")

    print(f"📊 Übersicht erstellt: {out}")
    return out
