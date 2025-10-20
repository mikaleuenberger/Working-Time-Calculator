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

        # Ausgewählte Funktion ausführen
        if choice == ARBEITSZEITERFASSUNG:
            print("🔹 Gib deine Arbeitszeiten ein...")
            #Todo: Programm noch schreiben
        elif choice == WOCHENUEBERSICHT:
            print("📅 Wochenübersicht wird angezeigt...")
            #Todo: Programm noch schreiben
        elif choice == MONATSRAPPORT:
            print("📊 Monatsrapport wird erstellt...")
            #Todo: Programm noch schreiben
        elif choice == BENUTZEREINSTELLUNGEN:
            print("⚙️ Öffne Benutzereinstellungen...")
            #Todo: Programm noch schreiben
        elif choice == ADMIN:
            print("🔐 Adminbereich wird geöffnet...")
            #Todo: Programm noch schreiben
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
main()

