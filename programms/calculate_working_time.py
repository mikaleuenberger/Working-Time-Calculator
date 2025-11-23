# Funktion zur Berechnung der Arbeitszeit mit eingabe von Arbeitsbeginn, Arbeitsende und Pausenzeit

from datetime import datetime, timedelta
import re
import csv
import os

# Konstanten
LOG_FILE = "work_log.csv"
HEADERS = ["date", "start_time", "end_time",
           "break_minutes", "work_hours", "work_minutes"]


def calculate_work_time(start_str: str, end_str: str, break_minutes: int) -> tuple[int, int] | tuple[None, None]:
    """
    Calculates the net working time in hours and minutes from time strings.

    Args:
        start_str: The start time in "HH:MM" format (e.g., "09:00").
        end_str: The end time in "HH:MM" format (e.g., "17:30").
        break_minutes: The total break time in minutes (e.g., 60).

    Returns:
        A tuple of (hours, minutes) of net work time.
        Returns (None, None) if the time format is invalid.
    """
    time_format = "%H:%M"

    try:
        # 1. Parse the time strings into time objects
        start_time = datetime.strptime(start_str, time_format).time()
        end_time = datetime.strptime(end_str, time_format).time()

        # 2. Combine with a dummy date to create datetime objects for subtraction
        # We use a fixed date (like today) to be able to subtract them.
        today = datetime.today().date()
        start_dt = datetime.combine(today, start_time)
        end_dt = datetime.combine(today, end_time)

        # Wenn die Endzeit vor der Startzeit ist, gehen wir von einer Nachtschicht aus..
        # in diesem fall wird mit dem nächsten Tag gerechnet
        # Beispiell 22:00 - 06:00
        if end_dt < start_dt:
            end_dt += timedelta(days=1)

        # 4. Berechnung des Zeit Deltas
        gross_duration: timedelta = end_dt - start_dt

        # 5. Get total duration in minutes and subtract breaks
        gross_minutes = gross_duration.total_seconds() / 60
        net_minutes = gross_minutes - break_minutes

        # 6. Sicherstellen, das minuten nicht negativ ist
        net_minutes = max(0, net_minutes)

        # Wandelt die gesamtanzahl Minuten in Stunden und Minuten um
        # Divmod() gibt ein Tuple von quotient und remainder zurück
        # Beispiel divmod(70, 60) -> (1, 10) -> 1 hour, 10 minutes
        total_net_minutes = int(net_minutes)
        hours, minutes = divmod(total_net_minutes, 60)

        return hours, minutes

    except ValueError:
        # Wenn das Format nicht mit "%H:%M" übereinstimmt, wird dieser ValueError ausgegeben.
        return None, None


def is_valid_time_format(time_str: str) -> bool:
    """
    Checks if a string is a valid time in HH:MM format.

    Args:
        time_str: The string to check (e.g., "09:00" or "25:99").

    Returns:
        True if the format is "HH:MM" AND it's a real time (e.g., "23:59" is ok, "24:00" or "10:60" is not).
    """
    # 1. Schnelle Prüfung des Musters (zwei Ziffern, Doppelpunkt, zwei Ziffern) => Regex
    if not re.match(r"^\d{2}:\d{2}$", time_str):
        return False

    # 2. Tiefere Prüfung: Ist es eine gültige Zeit?
    # datetime.strptime() löst einen ValueError aus, wenn die Zeit ungültig ist
    # (z.B. "25:00" oder "12:60").
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False


def save_to_csv(data_row: dict):
    """
    Fügt eine Reihe von Daten in das LOG_FILE.
    Erstellt das csv File und schreibt neue Headers, falls sie noch nicht existieren..
    """
    # 1. Prüfung, ob das File schon existiert
    file_exists = os.path.exists(LOG_FILE)

    try:
        # 2. Open the file in 'a' (append) mode
        #    newline='' is required by the csv module
        with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:

            # 3. DictWriter wird benutzt um anhand der Headers die Zeilen zu füllen
            writer = csv.DictWriter(f, fieldnames=HEADERS)

            # 4. Falls das File noch nicht vorhanden ist, schreibe neue Headers in ein neues File
            if not file_exists:
                writer.writeheader()

            # 5. Write the actual data
            writer.writerow(data_row)

        return True
    except IOError as e:
        print(f"  -> Error: Could not write to file {LOG_FILE}. {e}")
        return False
