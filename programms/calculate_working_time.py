# Funktion zur Berechnung der Arbeitszeit mit eingabe von Arbeitsbeginn, Arbeitsende und Pausenzeit

from datetime import datetime, timedelta
import re
import csv
import os

# Konstanten
LOG_FILE = "work_log.csv"
HEADERS = ["Datum", "Wochentag", "Arbeitsbeginn", "Pause_min",
           "Mittag_beginn", "Mittag_ende", "Arbeitsende", "Kommentar"]

WEEKDAYS = {
    0: "Montag", 1: "Dienstag", 2: "Mittwoch", 3: "Donnerstag",
    4: "Freitag", 5: "Samstag", 6: "Sonntag"
}


def calculate_work_time(start_str, end_str, lunch_start_str, lunch_end_str, short_break_min):
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

        # Prüfen, ob eine Mittagspause eingetragen wurde
        if lunch_start_str and lunch_end_str:
            l_start = datetime.strptime(lunch_start_str, time_fmt)
            l_end = datetime.strptime(lunch_end_str, time_fmt)

            if l_end < l_start:
                l_end += timedelta(days=1)

            lunch_delta = l_end - l_start
            lunch_duration_minutes = lunch_delta.total_seconds() / 60

            # --- REGEL 1: Mittagspause muss mindestens 30 Min sein ---
            if lunch_duration_minutes < 30:
                comment_parts.append(
                    f"Mittag zu kurz ({int(lunch_duration_minutes)} min)")
        else:
            # Falls gar keine Mittagspause eingetragen wurde, aber die Arbeitszeit lang ist
            pass

        # 3. Gesamte Pause (Mittag + Kurzpause)
        total_break_minutes = lunch_duration_minutes + short_break_min

        # 4. Netto-Arbeitszeit berechnen
        net_work_seconds = gross_work_duration.total_seconds() - (total_break_minutes * 60)
        net_work_hours_decimal = net_work_seconds / 3600

        # 5. --- REGEL 2: Arbeitszeit darf nicht > 12 Stunden sein ---
        if net_work_hours_decimal > 12:
            comment_parts.append(f"Überzeit > 12h")

        # TODO Hier noch alle weiteren Regeln erweitern.

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
