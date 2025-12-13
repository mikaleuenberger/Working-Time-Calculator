import os
import csv
import shutil
from datetime import datetime, timedelta
from pathlib import Path


# Eigene Module
import calculate_working_time
from reports import generate_employee_report
from user_admin import benutzerverwaltung_starten


# KONFIGURATION & KONSTANTEN
BASE_DIR = Path(__file__).resolve().parent.parent

# Menü-IDs (als Strings für input Vergleich)
M_ERFASSEN_HEUTE = "1"
M_NACHTRAG = "2"
M_WOCHEN_VIEW = "3"
M_MONATS_VIEW = "4"
M_BEENDEN = "5"

V_REPORT_GEN = "1"
V_APPROVE = "2"
V_USER_JSON = "3"
V_BEENDEN = "4"


# HILFSFUNKTIONEN (Pfad-Logik & Co.)


def get_user_paths(current_user, date_obj):
    """
    Zentrale Funktion, um Dateinamen und Pfade zu generieren.

    Returns:
        filename (str): z.B. "2025-11_001_muellerh.csv"
        user_folder (str): z.B. "Müller"
        path_ungeprueft (str): Vollständiger Pfad zur Datei in 'ungeprueft'
        path_geprueft (str): Vollständiger Pfad zur Datei in 'geprueft'
    """
    # 1. Dateinamen bauen
    date_part = date_obj.strftime("%Y-%m")
    id_part = f"{int(current_user['id']):03d}"

    raw_last = current_user["last_name"].lower()
    raw_first = current_user["surname"][0].lower()

    # Umlaute bereinigen
    clean_name = (
        raw_last.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )

    filename = f"{date_part}_{id_part}_{clean_name}{raw_first}.csv"

    # Ordnernamen bestimmen (Nur Nachname)
    user_folder = current_user["last_name"]

    # Pfade bauen
    base_working = os.path.join(BASE_DIR, "data", "working")

    path_ungeprueft_dir = os.path.join(base_working, "ungeprueft", user_folder)
    path_geprueft_dir = os.path.join(base_working, "geprueft", user_folder)

    file_path_ungeprueft = os.path.join(path_ungeprueft_dir, filename)
    file_path_geprueft = os.path.join(path_geprueft_dir, filename)

    return filename, user_folder, file_path_ungeprueft, file_path_geprueft


def input_time_safe(prompt, allow_empty=False):
    """Fragt eine Uhrzeit ab und validiert sie sofort."""
    while True:
        val = input(prompt)
        if allow_empty and val == "":
            return ""
        if calculate_working_time.is_valid_time_format(val):
            return val
        print(
            f"❌ Ungültiges Format '{val}'. Bitte HH:MM (z.B. 08:00) verwenden."
        )


# KERNAUFGABEN (Logik)


def process_time_entry(current_user, report_date):
    """
    Die eigentliche Arbeit: Fragt Zeiten ab, berechnet und speichert.
    Wird von 'arbeitszeiterfassung' (Heute)
    und 'nachtrag_erfassen' (Datum) aufgerufen.
    """
    date_str_display = report_date.strftime("%d.%m.%Y")
    print(f"\n📝 Erfassung für Datum: {date_str_display}")
    print("---------------------------------------")

    # 1. Eingabe der Zeiten
    start_str = input_time_safe("Arbeitsbeginn (HH:MM): ")

    lunch_start = input_time_safe(
        "Mittag Beginn (HH:MM oder Enter falls kein Mittag gemacht): ",
        allow_empty=True,
    )
    lunch_end = ""
    if lunch_start:
        lunch_end = input_time_safe("Mittag Ende   (HH:MM): ")

    end_str = input_time_safe("Arbeitsende   (HH:MM): ")

    short_break = -1
    while short_break < 0:
        try:
            val = input("Sonstige Pausen (Min, z.B. 15): ")
            short_break = int(val)
        except ValueError:
            print("❌ Bitte eine ganze Zahl eingeben.")

    # 2. Berechnung
    hours_decimal, comment = calculate_working_time.calculate_work_time(
        start_str,
        end_str,
        lunch_start,
        lunch_end,
        short_break,
        current_user,
        report_date,
    )

    if hours_decimal is not None:
        MAX_WEEKLY_HOURS = 45.0

        # Bereits erfasste Stunden der Woche (exklusive heute) lesen
        weekly_hours_so_far = get_weekly_hours_so_far(
            current_user, report_date
        )

        # Gesamtstunden mit dem heutigen Tag berechnen
        total_hours_with_today = weekly_hours_so_far + hours_decimal

        # Ausgabe im Terminal
        print(
            f"\nDynamische Wochensumme bis heute:"
            f" {round(total_hours_with_today, 2)} h"
        )

        if total_hours_with_today > MAX_WEEKLY_HOURS:
            # Hier findet die dynamische Prüfung statt,
            # bevor der Kommentar gesetzt wird
            print("\n" + "=" * 50)
            print(
                f"⚠️  ACHTUNG: Überschreitung der Wochenarbeitszeit"
                + f" (max {MAX_WEEKLY_HOURS} h)!"
            )
            print(f"    Total Woche:     {round(total_hours_with_today, 2)} h")
            print("=" * 50 + "\n")

            # Im ORIGINALEN Kommentarfeld der CSV-Zeile festhalten
            if comment:
                comment += f"; Wochenstunden > {int(MAX_WEEKLY_HOURS)}h"
            else:
                comment = f"Wochenstunden > {int(MAX_WEEKLY_HOURS)}h"
        # --- ENDE WOCHENPRÜFUNG ---

        h = int(hours_decimal)
        m = int((hours_decimal - h) * 60)
        weekday = calculate_working_time.get_german_weekday(report_date)

        print("\n--------------------------------")
        print(f"✅ Ergebnis: {h} Std {m} Min ({weekday})")
        if comment:
            print(f"⚠️  Hinweis: {comment}")
        print("--------------------------------")

        # Daten vorbereiten
        data_to_save = {
            "Datum": date_str_display,
            "Wochentag": weekday,
            "Arbeitsbeginn": start_str,
            "Pause_min": short_break,
            "Mittag_beginn": lunch_start,
            "Mittag_ende": lunch_end,
            "Arbeitsende": end_str,
            "Kommentar": comment,
            "Netto_Stunden": round(hours_decimal, 2),
        }

        # Speichern (Pfad wird über die Helper-Funktion geholt)
        _, user_folder, target_file, _ = get_user_paths(
            current_user, report_date
        )

        print(f"Speichere in Ordner: {user_folder}...")

        success, overwritten = calculate_working_time.save_to_csv(
            data_to_save, target_file
        )

        if success:
            if overwritten:
                print(
                    f"⚠️  Bestehender Eintrag für {date_str_display} "
                    f"wurde aktualisiert/überschrieben! 🔄"
                )
            else:
                print("Speichern erfolgreich (Neuer Eintrag). ✅")
        else:
            print("Fehler beim Speichern. ❌")
    else:
        print("❌ Fehler bei der Zeitberechnung (Startzeit > Endzeit?).")


def get_weekly_hours_so_far(current_user, date_obj):
    """
    Sammelt alle Netto-Arbeitsstunden
    der aktuellen Kalenderwoche für den Benutzer.
    """
    # Start- und Enddatum der aktuellen Woche bestimmen
    start_of_week = date_obj - timedelta(days=date_obj.weekday())
    end_of_week = start_of_week + timedelta(
        days=6, hours=23, minutes=59, seconds=59
    )

    # Relevante Dateien für den Monat(e) dieser Woche finden
    files_to_check = set()
    files_to_check.update(
        get_files_for_month(
            current_user, start_of_week.year, start_of_week.month
        )
    )
    if end_of_week.month != start_of_week.month:
        files_to_check.update(
            get_files_for_month(
                current_user, end_of_week.year, end_of_week.month
            )
        )

    total_weekly_hours = 0.0

    # Stunden aus allen relevanten Dateien lesen und summieren
    for filepath in files_to_check:
        try:
            with open(filepath, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    entry_date = datetime.strptime(row["Datum"], "%d.%m.%Y")

                    # Prüfen, ob der Eintrag in die aktuelle Kalenderwoche
                    # fällt UND nicht der heutige Tag ist (falls schon erfasst)
                    if (
                        start_of_week <= entry_date <= end_of_week
                        and entry_date.date() != date_obj.date()
                    ):
                        try:
                            # Auslesen vom Feld 'Netto_Stunden'
                            hours = float(row.get("Netto_Stunden", 0))
                            total_weekly_hours += hours
                        except ValueError:
                            continue
        except Exception:
            continue

    return total_weekly_hours


# MENÜFUNKTIONEN FÜR MITARBEITER


def arbeitszeiterfassung(current_user):
    """Wrapper für Heute"""
    today = datetime.now()
    process_time_entry(current_user, today)


def nachtrag_erfassen(current_user):
    """Wrapper für Nachtrag"""
    print(f"\n📅 Nachtrag für: {current_user['last_name']}")
    print("Hinweis: Nur Tage im aktuellen Monat möglich.\n")

    while True:
        target_date_str = input(
            "Datum eingeben (DD.MM.YYYY) oder 'x' abbruch: "
        ).strip()
        if target_date_str.lower() == "x":
            return

        is_ok, target_date_obj = (
            calculate_working_time.is_date_in_current_month(target_date_str)
        )

        if is_ok:
            process_time_entry(current_user, target_date_obj)
            break
        else:
            print(f"❌ {target_date_obj}")  # Zeigt die Fehlermeldung an


def get_files_for_month(current_user, year, month):
    """
    Sammelt alle CSV-Dateien für einen spezifischen Monat (Jahr, Monat).
    """
    # Helper aufrufen um die Basis-Ordner zu bekommen
    # (dummy reicht hier, damit wir die Ordnerstruktur erhalten)
    # TODO Eventuell noch eine bessere Lösung finden
    dummy_date = datetime(year, month, 1)
    _, user_folder, path_ungeprueft_file, path_geprueft_file = get_user_paths(
        current_user, dummy_date
    )

    dir_ungeprueft = os.path.dirname(path_ungeprueft_file)
    dir_geprueft = os.path.dirname(path_geprueft_file)

    # Prefix bauen: "2025-10"
    target_prefix = f"{year}-{month:02d}"
    found_files = []

    for d in [dir_ungeprueft, dir_geprueft]:
        if os.path.exists(d):
            for f in os.listdir(d):
                # Wir suchen Dateien, die mit YYYY-MM anfangen
                if f.endswith(".csv") and f.startswith(target_prefix):
                    found_files.append(os.path.join(d, f))

    return found_files


def show_employee_console_report(current_user):
    print("\n--- Monatsübersicht Auswählen ---")
    print("Drücken Sie [ENTER] für den aktuellen Monat.")
    print("Oder geben Sie das Datum ein (Format: YYYY-MM, z.B. 2024-12).")

    choice = input("Auswahl: ").strip()

    # Standardwerte (Aktueller Monat)
    now = datetime.now()
    year = now.year
    month = now.month

    if choice:
        try:
            # Versuch, die Eingabe zu parsen
            parsed_date = datetime.strptime(choice, "%Y-%m")
            year = parsed_date.year
            month = parsed_date.month
        except ValueError:
            print("❌ Ungültiges Format. Zeige aktuellen Monat...")

    # Dateien laden für das gewählte Jahr/Monat
    files = get_files_for_month(current_user, year, month)
    date_label = f"{year}-{month:02d}"

    if not files:
        print(f"\n❌ Keine Daten für {date_label} gefunden.")
        input("(Enter)")
        return

    entries = []
    # Alle Dateien einlesen
    for filepath in files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    entries.append(row)
        except Exception:
            continue

    # Sortieren
    try:
        entries.sort(
            key=lambda x: datetime.strptime(
                f"{x['Datum']} {x['Arbeitsbeginn']}", "%d.%m.%Y %H:%M"
            )
        )
    except ValueError:
        pass

    # Anzeige
    print_report_table(entries, f"Monatsübersicht ({date_label})")


def show_employee_weekly_report(current_user):
    print("\n--- Wochenübersicht Auswählen ---")
    print("Drücken Sie [ENTER] für die aktuelle Woche.")
    print(
        "Oder geben Sie 'KW' ein, um eine spezifische Kalenderwoche zu suchen."
    )

    choice = input("Auswahl: ").strip()

    today = datetime.now().date()

    if choice.lower() == "kw":
        try:
            y_input = input("Welches Jahr? (z.B. 2025): ")
            kw_input = input("Welche Kalenderwoche? (1-53): ")

            target_year = int(y_input)
            target_week = int(kw_input)

            # Magie: Montag der KW berechnen
            # fromisocalendar(Jahr, Woche, Tag 1=Montag)
            start_week = datetime.fromisocalendar(
                target_year, target_week, 1
            ).date()
        except ValueError:
            print("❌ Ungültige Eingabe. Zeige aktuelle Woche...")
            start_week = today - timedelta(days=today.weekday())
    else:
        # Aktuelle Woche (Montag berechnen)
        start_week = today - timedelta(days=today.weekday())

    # Sonntag berechnen
    end_week = start_week + timedelta(days=6)

    date_label = (
        f"KW {start_week.isocalendar()[1]} "
        f"({start_week.strftime('%d.%m.')}"
        f" bis {end_week.strftime('%d.%m.%Y')})"
    )

    # DATEIEN LADEN
    # Eine Woche kann im Januar anfangen und im Februar aufhören.
    # Wir laden Dateien vom Monat des Montags und vom Monat des Sonntags.
    files = []

    # Monat (Start der Woche)
    files.extend(
        get_files_for_month(current_user, start_week.year, start_week.month)
    )

    # Monat (Ende der Woche), falls unterschiedlich
    if start_week.month != end_week.month:
        files.extend(
            get_files_for_month(current_user, end_week.year, end_week.month)
        )

    # Duplikate entfernen (falls Dateien in beiden Listen auftauchen)
    files = list(set(files))

    if not files:
        print(f"\n❌ Keine Dateien im Zeitraum {date_label} gefunden.")
        input("(Enter)")
        return

    entries = []
    # Einlesen und Filtern
    for filepath in files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    try:
                        rd = datetime.strptime(row["Datum"], "%d.%m.%Y").date()
                        # Liegt der Tag in der berechneten Woche?
                        if start_week <= rd <= end_week:
                            row["_sort_date"] = rd
                            entries.append(row)
                    except ValueError:
                        continue
        except Exception:
            continue

    # Sortieren
    entries.sort(key=lambda x: x.get("_sort_date", datetime.min.date()))

    # Anzeige
    print_report_table(entries, f"Wochenübersicht - {date_label}")


def print_report_table(entries, title):
    """
    Zentrale Funktion zur Anzeige der Tabelle.
    Erwartet eine Liste von CSV-Zeilen (dicts) und einen Titel.
    Berechnet die Zeiten live und gibt die Summe aus.
    """
    print(f"\n📊 --- {title} ---")

    if not entries:
        print("❌ Keine Einträge für diesen Zeitraum gefunden.")
        input("\n(Enter für zurück)")
        return

    # Header
    header = (
        f"{'Datum':<12} | {'Tag':<10} | {'Start':<6} | {'Ende':<6} | "
        f"{'Pause':<6} | {'Ist-Zeit':<8} | {'Kommentar'}"
    )

    line = "-" * len(header)
    print(line)
    print(header)
    print(line)

    total_minutes_sum = 0

    for row in entries:
        try:
            net_hours_str = (
                (row.get("Netto_Stunden") or "").strip().replace(",", ".")
            )
            if net_hours_str:
                net_min = float(net_hours_str) * 60
                pause_str = row.get("Pause_min", "N/A")
            else:
                # Berechnung
                s = datetime.strptime(row["Arbeitsbeginn"], "%H:%M")
                e = datetime.strptime(row["Arbeitsende"], "%H:%M")

                # Nachtschicht Logik
                if e < s:
                    e += timedelta(days=1)
                gross_min = (e - s).total_seconds() / 60

                # Mittagspause addieren falls vorhanden
                pause_total_manual = int(row.get("Pause_min", 0))
                if row.get("Mittag_beginn") and row.get("Mittag_ende"):
                    mb = datetime.strptime(row["Mittag_beginn"], "%H:%M")
                    me = datetime.strptime(row["Mittag_ende"], "%H:%M")
                    if me < mb:
                        me += timedelta(days=1)
                    pause_total_manual += (me - mb).total_seconds() / 60

                net_min = max(0, gross_min - pause_total_manual)
                pause_str = str(pause_total_manual)

            total_minutes_sum += net_min

            # Formatierung für die Zeile
            hours = int(net_min // 60)
            mins = int(net_min % 60)
            time_str = f"{hours}h {mins}m"

            if pause_str != "N/A":
                pause_str = str(int(float(pause_str)))

            # --- AUSGABE ---
            print(
                f"{row['Datum']:<12} | {row['Wochentag']:<10} | "
                f"{row['Arbeitsbeginn']:<6} | {row['Arbeitsende']:<6} | "
                f"{pause_str:<6} | {time_str:<8} | {row['Kommentar']}"
            )

        except (ValueError, TypeError, KeyError) as err:
            # Falls eine Zeile unvollständig ist,
            # wird der Fehler markiert
            print(
                f"{row.get('Datum', '???'):<12} | FEHLER IN DATENZEILE ({err})"
            )

    print(line)

    # Gesamtsumme
    sum_h = int(total_minutes_sum // 60)
    sum_m = int(total_minutes_sum % 60)
    print(f"Σ GESAMT: {sum_h} Stunden und {sum_m} Minuten")
    print(line)

    input("\n(Enter für zurück)")


# MENÜFUNKTIONEN FÜR VORGESETZTE


def supervisor_approve_report():
    print("\n🔍 --- Rapport Freigabe (Monats-basiert) ---")

    src_base = os.path.join(BASE_DIR, "data", "working", "ungeprueft")
    dst_base = os.path.join(BASE_DIR, "data", "working", "geprueft")

    if not os.path.exists(src_base):
        print("Verzeichnis 'ungeprueft' existiert nicht oder ist leer.")
        return

    # User Ordner anzeigen
    users = [
        d
        for d in os.listdir(src_base)
        if os.path.isdir(os.path.join(src_base, d))
    ]
    users.sort()

    if not users:
        print("✅ Alles erledigt (Keine offenen Ordner in 'ungeprueft').")
        return

    print("Mitarbeiter wählen:")
    for i, u in enumerate(users):
        print(f"  {i+1}) {u}")
    print("  0) Abbrechen")

    try:
        uc = int(input("Auswahl: "))
        if uc == 0:
            return
        selected_user = users[uc - 1]

        user_src = os.path.join(src_base, selected_user)
        user_dst = os.path.join(dst_base, selected_user)

        # Verfügbare Monate in diesem Ordner finden
        # von allen Dateien werden diese mit yyyy-mm entnommen
        files_in_folder = [
            f
            for f in os.listdir(user_src)
            if os.path.isfile(os.path.join(user_src, f))
        ]

        available_months = set()
        for f in files_in_folder:
            # Erwartetes Format: YYYY-MM_...
            # Hier werden die ersten 7 Zeichen entnommen
            if len(f) >= 7 and f[4] == "-":
                month_prefix = f[:7]  # z.B. "2025-10"
                available_months.add(month_prefix)

        sorted_months = sorted(list(available_months))

        if not sorted_months:
            print("❌ Keine Dateien mit gültigem Datumsformat gefunden.")
            return

        print(f"\nVerfügbare Monate für {selected_user}:")
        for i, m in enumerate(sorted_months):
            # Zähle, wie viele Dateien dazu gehören (CSV + TXT)
            count = sum(1 for f in files_in_folder if f.startswith(m))
            print(f"  {i+1}) {m} ({count} Dateien)")
        print("  0) Abbrechen")

        mc = int(input("Welchen Monat freigeben? "))
        if mc == 0:
            return

        target_month = sorted_months[mc - 1]

        # Zielordner vorbereiten
        if not os.path.exists(user_dst):
            os.makedirs(user_dst)

        # Dateien verschieben, die mit dem gewählten Monat beginnen
        files_to_move = [
            f for f in files_in_folder if f.startswith(target_month)
        ]

        print(f"\nVerschiebe Dateien für {target_month}...")

        moved_count = 0
        for filename in files_to_move:
            src_file = os.path.join(user_src, filename)
            dst_file = os.path.join(user_dst, filename)

            # Namenskollision prüfen
            if os.path.exists(dst_file):
                print(f"  ⚠️ Datei existiert schon: {filename}")
                # Backup-Name generieren
                timestamp = datetime.now().strftime("%Y%m%d%H%M")
                name, ext = os.path.splitext(filename)
                new_name = f"{name}_approved_{timestamp}{ext}"
                dst_file = os.path.join(user_dst, new_name)
                print(f"     -> Umbenannt in: {new_name}")

            try:
                shutil.move(src_file, dst_file)
                print(f"  ✅ Verschoben: {filename}")
                moved_count += 1
            except Exception as e:
                print(f"  ❌ Fehler bei {filename}: {e}")

        print(f"\nFertig. {moved_count} Dateien wurden freigegeben.")

        # Wenn der Quellordner jetzt leer ist, wird er gelöscht
        remaining_files = os.listdir(user_src)
        if not remaining_files:
            try:
                os.rmdir(user_src)
                print(
                    f"Info: Ordner '{selected_user}'"
                    + " in ungeprueft war leer und wurde gelöscht."
                )
            except OSError:
                pass  # Ordner war wohl doch nicht leer oder System-gesperrt

    except (ValueError, IndexError):
        print("❌ Ungültige Eingabe.")
    except Exception as e:
        print(f"❌ Ein unerwarteter Fehler ist aufgetreten: {e}")


def monatsrapport(current_user):
    """Menü für die Erstellung von Monatsrapporten."""
    print("📊 Monatsrapport")

    # 2. Ordnernamen bestimmen (Nur Nachname)
    user_folder = current_user["last_name"]

    # Monatseingabe mit einfacher Validierung
    while True:
        month = input("Monat (YYYY-MM) oder 'x' für Abbruch: ").strip()
        if month.lower() == "x":
            return

        if (
            len(month) == 7
            and month[4] == "-"
            and month[:4].isdigit()
            and month[5:].isdigit()
        ):
            mm = int(month[5:])
            if 1 <= mm <= 12:
                break
        print("❌ Ungültiges Format! Bitte z. B. 2025-10 eingeben.\n")

    # Report für eine einzelne Person
    while True:
        print("\n==============================")
        emp = input(
            "Mitarbeiter-ID eingeben (leer = erste passende Datei nehmen) oder 'x' für Abbruch: "
        ).strip()

        if emp.lower() == "x":
            return
        print("==============================")

        # Falls etwas eingegeben wurde: prüfen, ob es eine Zahl ist
        if emp:
            if not emp.isdigit():
                print("❌ Mitarbeiter-ID muss eine Zahl sein.\n")
                continue
            emp_id = int(emp)
        else:
            # Keine ID eingegeben: erste passende
            # Datei des Monats wird benutzt
            emp_id = None

        # Report erzeugen
        result = generate_employee_report(BASE_DIR, month, emp_id=emp_id)

        # generate_employee_report gibt None zurück,
        # wenn keine Datei gefunden wurde
        if result is None:
            print("\n❌ Keine passende Datei gefunden.")
            print("   Bitte Monat und Mitarbeiter-ID prüfen.\n")
            # Schleife erneut laufen lassen,
            # damit der User neue Angaben machen kann
            continue

        # Report wurde erstellt → Schleife beenden
        break

    else:
        print("❌ Ungültige Auswahl.")


# MAIN LOOPS für das Menu


def employee_menu_loop(current_user):
    while True:
        print(f"\n👤 MITARBEITER: {current_user['last_name']}")
        print(f"{M_ERFASSEN_HEUTE}) Arbeitszeit erfassen (Heute)")
        print(f"{M_NACHTRAG}) Nachtrag erfassen")
        print(f"{M_WOCHEN_VIEW}) Wochenübersicht")
        print(f"{M_MONATS_VIEW}) Monatsübersicht")
        print(f"{M_BEENDEN}) Beenden")

        c = input("Auswahl: ").strip()

        if c == M_ERFASSEN_HEUTE:
            arbeitszeiterfassung(current_user)
        elif c == M_NACHTRAG:
            nachtrag_erfassen(current_user)
        elif c == M_WOCHEN_VIEW:
            show_employee_weekly_report(current_user)
        elif c == M_MONATS_VIEW:
            show_employee_console_report(current_user)
        elif c == M_BEENDEN:
            break
        else:
            print("❌ Ungültig.")


# Schleife für Vorgesetzen Menu


def supervisor_menu_loop(current_user):
    while True:
        print(f"\n🛡️ VORGESETZTER: {current_user['last_name']}")
        print(f"{V_REPORT_GEN}) Monatsrapport generieren (PDF/Excel)")
        print(f"{V_APPROVE}) Rapport freigeben (Verschieben)")
        print(f"{V_USER_JSON}) Benutzerverwaltung")
        print(f"{V_BEENDEN}) Beenden")

        c = input("Auswahl: ").strip()

        if c == V_REPORT_GEN:
            monatsrapport(current_user)
        elif c == V_APPROVE:
            supervisor_approve_report()
        elif c == V_USER_JSON:
            benutzerverwaltung_starten()
        elif c == V_BEENDEN:
            break
        else:
            print("❌ Ungültig.")


def main(current_user):
    role = current_user.get("business_role", "Mitarbeiter")
    if role == "Vorgesetzter":
        supervisor_menu_loop(current_user)
    else:
        employee_menu_loop(current_user)


if __name__ == "__main__":
    main()
