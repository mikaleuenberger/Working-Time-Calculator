# Funktion zur Berechnung der Arbeitszeit mit eingabe von Arbeitsbeginn, Arbeitsende und Pausenzeit

from datetime import datetime, timedelta
import re
import csv
import os

# Konstanten
LOG_FILE = "work_log.csv"
HEADERS = ["Datum", "Wochentag", "Arbeitsbeginn", "Pause_min",
           "Mittag_beginn", "Mittag_ende", "Arbeitsende", "Kommentar", "Netto_Stunden"]

WEEKDAYS = {
    0: "Montag", 1: "Dienstag", 2: "Mittwoch", 3: "Donnerstag",
    4: "Freitag", 5: "Samstag", 6: "Sonntag"
}

# Konstanten für Nachtarbeit (zwischen 22:00 und 06:00 für Minderjährige)
NIGHT_START_HOUR = 22
NIGHT_END_HOUR = 6


def calculate_work_time(start_str, end_str, lunch_start_str, lunch_end_str, short_break_min, current_user, work_date_obj):
    """
    Berechnet die Arbeitszeit basierend auf Start, Ende, Mittagspause und Kurzpausen.
    Gibt Arbeitsstunden (dezimal), Arbeitsminuten und einen Kommentar zurück.
    """
    time_fmt = "%H:%M"
    comment_parts = []

    try:
        # 1. Start und Ende parsen
        t_start = datetime.strptime(start_str, time_fmt)
        t_end = datetime.strptime(end_str, time_fmt)

        # Nachtschicht-Korrektur
        if t_end < t_start:
            t_end += timedelta(days=1)

        gross_work_duration = t_end - t_start

        # 2. Mittagspause berechnen
        lunch_duration_minutes = 0
        MINDEST_PAUSE_MIN = 30  # Konstante für die Mindestpausenlänge

        # Prüfen, ob eine Mittagspause eingetragen wurde
        if lunch_start_str and lunch_end_str:
            l_start = datetime.strptime(lunch_start_str, time_fmt)
            l_end = datetime.strptime(lunch_end_str, time_fmt)

            if l_end < l_start:
                l_end += timedelta(days=1)

            lunch_delta = l_end - l_start
            lunch_duration_minutes = lunch_delta.total_seconds() / 60

            # --- REGEL 1: Mittagspause muss mindestens 30 Min sein ---
            if lunch_duration_minutes < MINDEST_PAUSE_MIN:
                comment_parts.append(
                    f"Mittag zu kurz ({int(lunch_duration_minutes)} min)")

        elif gross_work_duration.total_seconds() >= (6 * 3600):  # Nur ab 6h Bruttozeit prüfen

            # NEUE PRÜFUNG: Ist es eine Nachtschicht?
            # <- Prüft, ob über Mitternacht gearbeitet wurde (Nachtschicht-Indikator)
            if t_end < t_start:
                lunch_duration_minutes = 0
                comment_parts.append(
                    "Nachtschicht erkannt: Kein automatischer Mittagsabzug.")
            else:
                lunch_duration_minutes = MINDEST_PAUSE_MIN
                comment_parts.append(
                    f"Keine Mittagszeit erfasst, {MINDEST_PAUSE_MIN} min automatisch abgezogen")

        # 3. Gesamte Pause (Mittag + Kurzpause)
        total_break_minutes = lunch_duration_minutes + short_break_min

        # 4. Netto-Arbeitszeit berechnen
        net_work_seconds = gross_work_duration.total_seconds() - (total_break_minutes * 60)
        net_work_hours_decimal = net_work_seconds / 3600

        # 5. --- REGEL 2: Arbeitszeit darf nicht > 12 Stunden sein ---
        if net_work_hours_decimal > 12:
            comment_parts.append(f"Überzeit > 12h")

        # Minderjähriger darf max. 9h arbeiten
        if current_user["age"] < 18 and net_work_hours_decimal > 9:
            comment_parts.append("Maximalarbeitszeit Minderjährige: 9h")

        # Prüfung auf Nachtarbeit
        # Wir verwenden die Daten der t_start/t_end Objekte (standardmässig 1900-01-01 / 1900-01-02)
        night_start = t_start.replace(
            hour=NIGHT_START_HOUR, minute=0, second=0)
        night_end = t_start.replace(
            hour=NIGHT_END_HOUR, minute=0, second=0) + timedelta(days=1)

        # Überlappung des Arbeitszeitraums mit dem Nachtzeitraum berechnen
        overlap_start = max(t_start, night_start)
        overlap_end = min(t_end, night_end)

        if current_user["age"] < 18 and overlap_start < overlap_end:
            overlap_duration_min = (
                overlap_end - overlap_start).total_seconds() / 60
            if overlap_duration_min > 0:
                comment_parts.append(
                    f"Nachtarbeit ({int(overlap_duration_min)} min) für Minderjährige (verboten 22-6 Uhr)")

        # keine Wochenendarbeit für Minderjährige
        if current_user["age"] < 18 and work_date_obj.weekday() in [5, 6]:
            comment_parts.append(
                "Keine Wochenendarbeit für Minderjährige (Sa/So)")

        # Kommentar zusammenbauen
        final_comment = "; ".join(comment_parts)

        return net_work_hours_decimal, final_comment

    except ValueError:
        return None, "Fehler bei Berechnung"


def is_valid_time_format(time_str):
    """Prüft Format HH:MM oder leeren String (für optionale Mittagspause)"""
    if time_str == "":
        return True  # Leere Eingabe erlauben
    if not re.match(r"^\d{2}:\d{2}$", time_str):
        return False
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False


def save_to_csv(data_row: dict, filepath: str):
    folder_path = os.path.dirname(filepath)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    file_exists = os.path.exists(filepath)

    try:
        with open(filepath, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS, delimiter=';')

            if not file_exists:
                writer.writeheader()

            writer.writerow(data_row)
        return True
    except IOError as e:
        print(f"Fehler beim Speichern: {e}")
        return False


def get_german_weekday(date_obj):
    """Gibt den Wochentag auf Deutsch zurück"""
    return WEEKDAYS[date_obj.weekday()]


def is_date_in_current_month(date_str):
    """
    Prüft, ob der Datums-String (Format DD.MM.YYYY) im aktuellen Monat liegt.
    Gibt (True, date_obj) zurück oder (False, None).
    """
    try:
        # 1. Eingabe in Datum umwandeln
        input_date = datetime.strptime(date_str, "%d.%m.%Y")

        # 2. Aktuelles Datum holen
        now = datetime.now()

        # 3. Vergleichen (Jahr und Monat müssen gleich sein)
        if input_date.year == now.year and input_date.month == now.month:
            if input_date > now:
                return False, "Das Datum liegt in der Zukunft."
            return True, input_date
        else:
            return False, "Das Datum liegt nicht im aktuellen Monat."

    except ValueError:
        return False, "Ungültiges Format. Bitte DD.MM.YYYY benutzen."
