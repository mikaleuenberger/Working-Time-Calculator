# WTCalculator – Hauptmenü (Console Version)
# Dieses Programm gibt dem User ein Einstiegsmenu
# mit der Auswahl von 1–6 Menüpunkten

# Feste Werte für das Menü
ARBEITSZEITERFASSUNG = 1
WOCHENUEBERSICHT = 2
MONATSRAPPORT = 3
BENUTZEREINSTELLUNGEN = 4
ADMIN = 5
BEENDEN = 6

# Platzhalter für die einzelnen Menüoptionen


def arbeitszeiterfassung():
    print("🕑 Funktion: Arbeitszeiterfassung (noch in Entwicklung)")


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
