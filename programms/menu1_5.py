import calculate_working_time
from datetime import datetime, timedelta


# Arbeitszeiterfassung --> Hauptmenü
# Dieses Programm gibt dem User ein Einstiegsmenu
# mit der Auswahl von 1–6 Menüpunkten

# Feste Werte für das Menü3

ARBEITSZEITERFASSUNG = 1
WOCHENUEBERSICHT = 2
MONATSRAPPORT = 3
BENUTZEREINSTELLUNGEN = 4
ADMIN = 5
BEENDEN = 6


# Frage, macht es sinn hier vorhandene CSV zu prüfen und zu laden? Todo Funktion bauen

def check_files():
    print("Funktion einbauen für CSV Prüfung (abklären)")

# Platzhalter für die einzelnen Menüoptionen


def arbeitszeiterfassung():
    print("Bitte benutzen Sie ein 24 Stunden Format HH:MM (Beispiel, 09:00 oder 17:30)\n")
    # Starttime Input und Validierung
    start_str = ""
    while not calculate_working_time.is_valid_time_format(start_str):
        start_str = input("Geben Sie die Startzeit ein (HH:MM): ")
        if not calculate_working_time.is_valid_time_format(start_str):
            print(
                f"  -> Error: Ungültiges Format '{start_str}'. Bitte benutzen sie das Format: HH:MM (Beispiel, 09:00).")

  # Endtime Input und Validierung
    end_str = ""
    while not calculate_working_time.is_valid_time_format(end_str):
        end_str = input("Geben Sie die Endzeit ein (HH:MM): ")
        if not calculate_working_time.is_valid_time_format(end_str):
            print(
                f"  -> Error: Ungültiges format '{end_str}'. Bitte benutzen sie das Format: HH:MM (Beispiel, 17:30).")

    # Get and validate break time
    break_minutes = -1  # Initialize with an invalid value
    while break_minutes < 0:
        break_str = input(
            "Geben sie die gesamte Pausenzeit in Minuten an (Beispiel, 45): ")
        try:
            break_minutes = int(break_str)
            if break_minutes < 0:
                print(
                    "Error: Pausenzeit darf nicht negativ sein. Bitte geben Sie eine gültige Eingabe ein.")
        except ValueError:
            print(
                "Error: Ungültige Zahl. Bitte geben Sie die Pause in ganzen Minuten an.")

    # Berechnung
    hours, minutes = calculate_working_time.calculate_work_time(
        start_str, end_str, break_minutes)
    # Anzeige des Resultats
    if hours is not None:
        print("\n--------------------------------")
        print(
            f"Total Netto Arbeitszeit: {hours} Stunden und {minutes} Minuten.")
        print("--------------------------------")

        # Resultat in File speichern
        print(f"Speichern der Daten ins File...")

        # Heutiges Datum als String
        today_str = datetime.now().strftime("%Y-%m-%d")

        # Vorbereiten der Daten als Dictionary
        data_to_save = {
            "date": today_str,
            "start_time": start_str,
            "end_time": end_str,
            "break_minutes": break_minutes,
            "work_hours": hours,
            "work_minutes": minutes
        }

        # Aufruf der Save_to_csv Funktion
        if calculate_working_time.save_to_csv(data_to_save):
            print("...Erfolgreich gespeichert. ✅")
        else:
            print("...Speichern Fehlgeschlagen. ❌")
    else:
        print("\nError: Ein unbekannter Fehler trat auf während des Speicherns")


def wochenuebersicht():
    print("📅 Funktion: Wochenübersicht (noch in Entwicklung)")


def monatsrapport():
    print("📊 Funktion: Monatsrapport (noch in Entwicklung)")


def benutzereinstellungen():
    print("⚙️ Funktion: Benutzereinstellungen (noch in Entwicklung)")


def adminbereich():
    print("🔐 Funktion: Adminbereich (noch in Entwicklung)")


# !!!   Teil oberhalb der Linie noch anpassen   !!!!!!!!!!!

#   ---------------------------------------------------------

# Die Hauptfunktion (main)
def main():
    # Die choice Variable kontrolliert die Schleife
    # und speichert die Menüauswahl des Benutzers.
    choice = 0

    while choice != BEENDEN:
        # Zeigt das Menü an.
        display_menu()

        # Benutzerauswahl
        try:
            choice = int(input("Bitte deine Auswahl eingeben (1–6): "))
        except ValueError:
            print("❌ Ungültige Eingabe! Bitte eine Zahl zwischen 1 und 6 eingeben.")
            continue

        # Menüauswahl prüfen und Funktionen aufrufen
        if choice == ARBEITSZEITERFASSUNG:
            arbeitszeiterfassung()
        elif choice == WOCHENUEBERSICHT:
            wochenuebersicht()
        elif choice == MONATSRAPPORT:
            monatsrapport()
        elif choice == BENUTZEREINSTELLUNGEN:
            benutzereinstellungen()
        elif choice == ADMIN:
            adminbereich()
        elif choice == BEENDEN:
            print("👋 Programm wird beendet. Bis morgen!")
        else:
            print("❌ Ungültige Auswahl, bitte erneut versuchen.")


# Die display_menu Funktion zeigt das Menü an
def display_menu():
    print("\n==============================")
    print("🕒  Zeiterfassung Hauptmenü")
    print("==============================")
    print("1) Arbeitszeiterfassung")
    print("2) Wochenübersicht")
    print("3) Monatsrapport")
    print("4) Benutzereinstellungen")
    print("5) Administration")
    print("6) Beenden")
    print("==============================\n")


# Ruft das Hauptmenü auf
if __name__ == "__main__":
    main()
