import os
import csv
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Eigene Module
import calculate_working_time
from reports import generate_employee_report, generate_supervisor_overview


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
V_BEENDEN = "3"


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

    raw_last = current_user['last_name'].lower()
    raw_first = current_user['surname'][0].lower()

    # Umlaute bereinigen
    clean_name = raw_last.replace("ä", "ae").replace(
        "ö", "oe").replace("ü", "ue").replace("ß", "ss")

    filename = f"{date_part}_{id_part}_{clean_name}{raw_first}.csv"

    # 2. Ordnernamen bestimmen (Nur Nachname)
    user_folder = current_user['last_name']

    # 3. Pfade bauen
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
            f"❌ Ungültiges Format '{val}'. Bitte HH:MM (z.B. 08:00) verwenden.")


# KERNAUFGABEN (Logik)

def process_time_entry(current_user, report_date):
    """
    Die eigentliche Arbeit: Fragt Zeiten ab, berechnet und speichert.
    Wird von 'arbeitszeiterfassung' (Heute) und 'nachtrag_erfassen' (Datum) aufgerufen.
    """
    date_str_display = report_date.strftime("%d.%m.%Y")
    print(f"\n📝 Erfassung für Datum: {date_str_display}")
    print("---------------------------------------")

    # 1. Eingabe der Zeiten
    start_str = input_time_safe("Arbeitsbeginn (HH:MM): ")

    lunch_start = input_time_safe(
        "Mittag Beginn (HH:MM oder Enter falls kein Mittag gemacht): ", allow_empty=True)
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
        start_str, end_str, lunch_start, lunch_end, short_break
    )

    if hours_decimal is not None:
        h = int(hours_decimal)
        m = int((hours_decimal - h) * 60)
        weekday = calculate_working_time.get_german_weekday(report_date)

        print("\n--------------------------------")
        print(f"✅ Ergebnis: {h} Std {m} Min ({weekday})")
        if comment:
            print(f"⚠️  Hinweis: {comment}")
        print("--------------------------------")

        # 3. Daten vorbereiten
        data_to_save = {
            "Datum": date_str_display,
            "Wochentag": weekday,
            "Arbeitsbeginn": start_str,
            "Pause_min": short_break,
            "Mittag_beginn": lunch_start,
            "Mittag_ende": lunch_end,
            "Arbeitsende": end_str,
            "Kommentar": comment
        }

        # 4. Speichern (Pfad holen wir über unsere Helper-Funktion)
        _, user_folder, target_file, _ = get_user_paths(
            current_user, report_date)

        print(f"Speichere in Ordner: {user_folder}...")
        if calculate_working_time.save_to_csv(data_to_save, target_file):
            print("Speichern erfolgreich. ✅")
        else:
            print("Fehler beim Speichern. ❌")
    else:
        print("❌ Fehler bei der Zeitberechnung (Startzeit > Endzeit?).")


# ==========================================
# MENÜFUNKTIONEN FÜR MITARBEITER
# ==========================================

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
            "Datum eingeben (DD.MM.YYYY) oder 'x' abbruch: ").strip()
        if target_date_str.lower() == 'x':
            return

        is_ok, target_date_obj = calculate_working_time.is_date_in_current_month(
            target_date_str)

        if is_ok:
            process_time_entry(current_user, target_date_obj)
            break
        else:
            print(f"❌ {target_date_obj}")  # Zeigt die Fehlermeldung an


def get_files_for_month(current_user, year, month):
    """
    Sammelt alle CSV-Dateien für einen spezifischen Monat (Jahr, Monat).
    """
    # Helper aufrufen um die Basis-Ordner zu bekommen (dummy reicht hier, damit wir die Ordnerstruktur erhalten)
    # TODO Eventuell noch eine bessere Lösung finden
    dummy_date = datetime(year, month, 1)
    _, user_folder, path_ungeprueft_file, path_geprueft_file = get_user_paths(
        current_user, dummy_date)

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
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    entries.append(row)
        except Exception:
            continue

    # Sortieren
    try:
        entries.sort(key=lambda x: datetime.strptime(
            f"{x['Datum']} {x['Arbeitsbeginn']}", "%d.%m.%Y %H:%M"))
    except ValueError:
        pass

    # Anzeige
    print_report_table(entries, f"Monatsübersicht ({date_label})")


def show_employee_weekly_report(current_user):
    print("\n--- Wochenübersicht Auswählen ---")
    print("Drücken Sie [ENTER] für die aktuelle Woche.")
    print("Oder geben Sie 'KW' ein, um eine spezifische Kalenderwoche zu suchen.")

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
                target_year, target_week, 1).date()
        except ValueError:
            print("❌ Ungültige Eingabe. Zeige aktuelle Woche...")
            start_week = today - timedelta(days=today.weekday())
    else:
        # Aktuelle Woche (Montag berechnen)
        start_week = today - timedelta(days=today.weekday())

    # Sonntag berechnen
    end_week = start_week + timedelta(days=6)

    date_label = f"KW {start_week.isocalendar()[1]} ({start_week.strftime('%d.%m.')} bis {end_week.strftime('%d.%m.%Y')})"

    # --- DATEIEN LADEN (Trick für Monatsübergänge) ---
    # Eine Woche kann im Jan anfangen und im Feb aufhören.
    # Wir laden Dateien vom Monat des Montags UND vom Monat des Sonntags.
    files = []

    # 1. Monat (Start der Woche)
    files.extend(get_files_for_month(
        current_user, start_week.year, start_week.month))

    # 2. Monat (Ende der Woche), falls unterschiedlich
    if start_week.month != end_week.month:
        files.extend(get_files_for_month(
            current_user, end_week.year, end_week.month))

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
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    try:
                        rd = datetime.strptime(row['Datum'], "%d.%m.%Y").date()
                        # Liegt der Tag in der berechneten Woche?
                        if start_week <= rd <= end_week:
                            row['_sort_date'] = rd
                            entries.append(row)
                    except ValueError:
                        continue
        except Exception:
            continue

    # Sortieren
    entries.sort(key=lambda x: x.get('_sort_date', datetime.min.date()))

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

    # Header: Wir kombinieren alles Wichtige
    # Breite angepasst für bessere Lesbarkeit
    header = f"{'Datum':<12} | {'Tag':<10} | {'Start':<6} | {'Ende':<6} | {'Pause':<6} | {'Ist-Zeit':<8} | {'Kommentar'}"
    line = "-" * len(header)

    print(line)
    print(header)
    print(line)

    total_minutes_sum = 0

    for row in entries:
        try:
            # --- BERECHNUNG ---
            s = datetime.strptime(row['Arbeitsbeginn'], "%H:%M")
            e = datetime.strptime(row['Arbeitsende'], "%H:%M")

            # Nachtschicht Logik
            if e < s:
                e += timedelta(days=1)

            # Pausen
            pause_total = int(row['Pause_min'])

            # Mittagspause addieren falls vorhanden
            if row.get('Mittag_beginn') and row.get('Mittag_ende'):
                mb = datetime.strptime(row['Mittag_beginn'], "%H:%M")
                me = datetime.strptime(row['Mittag_ende'], "%H:%M")
                if me < mb:
                    me += timedelta(days=1)
                pause_total += (me - mb).total_seconds() / 60

            # Netto Berechnung
            gross_min = (e - s).total_seconds() / 60
            net_min = max(0, gross_min - pause_total)

            total_minutes_sum += net_min

            # Formatierung für die Zeile
            hours = int(net_min // 60)
            mins = int(net_min % 60)
            time_str = f"{hours}h {mins}m"

            # Pause als String (ganzzahlig)
            pause_str = str(int(pause_total))

            # --- AUSGABE ---
            print(f"{row['Datum']:<12} | {row['Wochentag']:<10} | {row['Arbeitsbeginn']:<6} | {row['Arbeitsende']:<6} | {pause_str:<6} | {time_str:<8} | {row['Kommentar']}")

        except (ValueError, TypeError):
            # Falls eine Zeile defekt ist, geben wir sie roh aus oder markieren Fehler
            print(f"{row.get('Datum', '???'):<12} | FEHLER IN DATENZEILE")

    print(line)

    # Gesamtsumme
    sum_h = int(total_minutes_sum // 60)
    sum_m = int(total_minutes_sum % 60)
    print(f"Σ GESAMT: {sum_h} Stunden und {sum_m} Minuten")
    print(line)

    input("\n(Enter für zurück)")

# MENÜFUNKTIONEN FÜR VORGESETZTE


def supervisor_approve_report():
    print("\n🔍 --- Rapport Freigabe (File-basiert) ---")

    src_base = os.path.join(BASE_DIR, "data", "working", "ungeprueft")
    dst_base = os.path.join(BASE_DIR, "data", "working", "geprueft")

    if not os.path.exists(src_base):
        print("Verzeichnis 'ungeprueft' leer.")
        return

    # 1. User Ordner anzeigen
    users = [d for d in os.listdir(
        src_base) if os.path.isdir(os.path.join(src_base, d))]
    users.sort()

    if not users:
        print("✅ Alles erledigt (Keine User-Ordner in ungeprueft).")
        return

    print("Mitarbeiter wählen:")
    for i, u in enumerate(users):
        print(f"  {i+1}) {u}")
    print("  0) Abbrechen")

    try:
        uc = int(input("Auswahl: "))
        if uc == 0:
            return
        selected_user = users[uc-1]

        user_src = os.path.join(src_base, selected_user)
        user_dst = os.path.join(dst_base, selected_user)

        # 2. Dateien anzeigen
        files = [f for f in os.listdir(user_src) if f.endswith(".csv")]
        files.sort()

        if not files:
            print("  -> Ordner ist leer.")
            return

        print(f"\nRapporte von {selected_user}:")
        for i, f in enumerate(files):
            print(f"  {i+1}) {f}")

        fc = int(input("\nWelches File freigeben? "))
        file_to_move = files[fc-1]

        # 3. Verschieben
        if not os.path.exists(user_dst):
            os.makedirs(user_dst)

        src_f = os.path.join(user_src, file_to_move)
        dst_f = os.path.join(user_dst, file_to_move)

        if os.path.exists(dst_f):
            print("⚠️ Datei existiert schon, erstelle Backup-Name...")
            ts = datetime.now().strftime("%Y%m%d%H%M")
            dst_f = os.path.join(
                user_dst, f"{os.path.splitext(file_to_move)[0]}_approved_{ts}.csv")

        shutil.move(src_f, dst_f)
        print(f"✅ Verschieben erfolgreich.")

    except (ValueError, IndexError):
        print("❌ Ungültige Auswahl.")
    except Exception as e:
        print(f"❌ Fehler: {e}")


def monatsrapport():
    """Menü für die Erstellung von Monatsrapporten."""
    print("📊 Monatsrapport")

    # Monatseingabe mit einfacher Validierung
    while True:
        month = input("Monat (YYYY-MM): ").strip()
        # Prüfen: Länge 7, an Stelle 4 ein '-', Jahr und Monat sind Ziffern
        if len(month) == 7 and month[4] == "-" and \
           month[:4].isdigit() and month[5:].isdigit():
            mm = int(month[5:])
            if 1 <= mm <= 12:
                break
        print("❌ Ungültiges Format! Bitte z. B. 2025-10 eingeben.\n")

    # Auswahl, ob Einzelperson oder Vorgesetzten-Übersicht
    print("\n┌───────────────────────────────┐")
    print("│   1) Einzelperson             │")
    print("│   2) Vorgesetzten-Übersicht   │")
    print("└───────────────────────────────┘")

    mode = input("Bitte wählen (1/2): ").strip()

    if mode == "1":
        # Report für eine einzelne Person
        while True:
            print("\n==============================")
            emp = input(
                "Mitarbeiter-ID eingeben (leer = erste passende Datei nehmen): "
            ).strip()
            print("==============================")

            # Falls etwas eingegeben wurde: prüfen, ob es eine Zahl ist
            if emp:
                if not emp.isdigit():
                    print("❌ Mitarbeiter-ID muss eine Zahl sein.\n")
                    continue
                emp_id = int(emp)
            else:
                # Keine ID eingegeben: erste passende Datei des Monats wird benutzt
                emp_id = None

            # Report erzeugen
            result = generate_employee_report(BASE_DIR, month, emp_id=emp_id)

            # generate_employee_report gibt None zurück, wenn keine Datei gefunden wurde
            if result is None:
                print("\n❌ Keine passende Datei gefunden.")
                print("   Bitte Monat und Mitarbeiter-ID prüfen.\n")
                # Schleife erneut laufen lassen, damit der User neue Angaben machen kann
                continue

            # Wenn wir hier sind, wurde ein Report erstellt → Schleife beenden
            break

    elif mode == "2":
        # Übersicht für Vorgesetzte über alle Mitarbeitenden im Monat
        generate_supervisor_overview(BASE_DIR, month)

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


def supervisor_menu_loop(current_user):
    while True:
        print(f"\n🛡️ VORGESETZTER: {current_user['last_name']}")
        print(f"{V_REPORT_GEN}) Monatsrapport generieren (PDF/Excel)")
        print(f"{V_APPROVE}) Rapport freigeben (Verschieben)")
        print(f"{V_BEENDEN}) Beenden")

        c = input("Auswahl: ").strip()

        if c == V_REPORT_GEN:
            monatsrapport()
        elif c == V_APPROVE:
            supervisor_approve_report()
        elif c == V_BEENDEN:
            break
        else:
            print("❌ Ungültig.")


def main(current_user):
    role = current_user.get('business_role', 'Mitarbeiter')
    if role == "Vorgesetzter":
        supervisor_menu_loop(current_user)
    else:
        employee_menu_loop(current_user)


if __name__ == "__main__":
    main()
