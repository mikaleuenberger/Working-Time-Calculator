# Arbeitszeiterfassung --> Hauptmenü
# Dieses Programm gibt dem User ein Einstiegsmenu
# mit der Auswahl von 1–6 Menüpunkten

# Frage, macht es sinn hier vorhandene CSV zu prüfen und zu laden? Todo Funktion bauen

from pathlib import Path
from reports import generate_employee_report, generate_supervisor_overview

# BASE_DIR ist der Projektordner (eine Ebene über "programms")
BASE_DIR = Path(__file__).resolve().parent.parent

# Feste Werte für das Menü
ARBEITSZEITERFASSUNG = 1
WOCHENUEBERSICHT = 2
MONATSRAPPORT = 3
BENUTZEREINSTELLUNGEN = 4
ADMIN = 5
BEENDEN = 6


def check_files():
    print("Funktion einbauen für CSV Prüfung (abklären)")

# Platzhalter für die einzelnen Menüoptionen


def arbeitszeiterfassung():
    print("🕑 Funktion: Arbeitszeiterfassung (noch in Entwicklung)")


def wochenuebersicht():
    print("📅 Funktion: Wochenübersicht (noch in Entwicklung)")


def monatsrapport():
    print("📊 Monatsrapport")

    # Monatseingabe mit Validierung
    while True:
        month = input("Monat (YYYY-MM): ").strip()
        if len(month) == 7 and month[4] == "-" and \
           month[:4].isdigit() and month[5:].isdigit():
            mm = int(month[5:])
            if 1 <= mm <= 12:
                break
        print("❌ Ungültiges Format! Bitte z. B. 2025-10 eingeben.\n")

    # Eingabe Report-Auswahl (1 oder 2)
    print("\n┌───────────────────────────────┐")
    print("│   1) Einzelperson             │")
    print("│   2) Vorgesetzten-Übersicht   │")
    print("└───────────────────────────────┘")

    mode = input("Bitte wählen (1/2): ").strip()
    if mode not in ("1", "2"):
        print("❌ Ungültige Auswahl.")
        return

    # -------------------------------
    # Modus 1: Report für eine Person
    # -------------------------------
    if mode == "1":
        while True:
            print("\n==============================")
            emp = input(
                "Mitarbeiter-ID eingeben (leer = erste passende Datei nehmen): "
            ).strip()
            print("==============================")

            # Validierung: Mitarbeiter-ID muss Zahl sein (wenn eingegeben)
            if emp:
                if not emp.isdigit():
                    print("❌ Mitarbeiter-ID muss eine Zahl sein.\n")
                    continue
                emp_id = int(emp)
            else:
                emp_id = None  # nur nach Monat suchen

            # Report erzeugen
            result = generate_employee_report(
                BASE_DIR, month, emp_id=emp_id
            )

            # generate_employee_report gibt None zurück, wenn keine Datei gefunden wurde
            if result is None:
                print("\n❌ Keine passende Datei gefunden für diese Kombination.")
                print("   Bitte Monat und Mitarbeiter-ID prüfen.\n")
                # nochmal fragen
                continue

            # Wenn wir hier sind, hat es geklappt → Schleife beenden
            break

    # -------------------------------
    # Modus 2: Übersicht für Vorgesetzte
    # -------------------------------
    elif mode == "2":
        generate_supervisor_overview(BASE_DIR, month)

    else:
        print("❌ Ungültige Auswahl.")


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
