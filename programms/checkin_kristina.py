import json
import os

# zeigt den Speicherpfad, wo Python die Datei sucht:
print(os.getcwd())


def load_users(filename="users.json"):
    """Lädt die Benutzerdaten aus der JSON-Datei."""

    # Den absoluten Pfad zur JSON-Datei erstellen
    # os.path.dirname(__file__) gibt den Ordner zurück, in dem das aktuelle Skript liegt
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)

    try:
        # Verwenden Sie jetzt den absoluten Pfad
        with open(file_path, 'r', encoding='utf-8') as file:
            users_data = json.load(file)
        return users_data
    except FileNotFoundError:
        print(
            f"Fehler: Die Datei '{file_path}' wurde nicht gefunden. Überprüfen Sie den Pfad.")
        return []
    except json.JSONDecodeError:
        print(f"Fehler: Die Datei '{filename}' ist keine gültige JSON-Datei.")
        return []


# last_name_input umbenannt zur Klarheit
def check_credentials(user_id, last_name_input, users_list):
    """Überprüft, ob die eingegebenen Daten mit einem Benutzer übereinstimmen."""
    for user in users_list:
        # Achten Sie auf die exakte Schreibweise: "last_name"
        if int(user["id"]) == int(user_id) and user["last_name"].casefold() == last_name_input.casefold():
            return True
    return False


def next_function(user_id):
    """Die Funktion, die nach einem erfolgreichen Login ausgeführt wird."""
    print(
        f"\nLogin erfolgreich! Willkommen, User ID: {user_id}. Hier geht es zur nächsten Funktion.")
    # Hier kommt Ihr weiterer Code für die Anwendung hin
    # zum Beispiel: show_user_dashboard(user_id)


def main():
    # users_data enthält jetzt das volle Dictionary: {"users": [...]}
    users_data = load_users()

    if not users_data:
        return

    # Extrahieren Sie hier die tatsächliche Benutzerliste aus dem Dictionary
    users_list = users_data.get("users", [])

    if not users_list:
        print("Keine Benutzerliste unter dem Schlüssel 'users' in der JSON-Datei gefunden.")
        return

    print("\n--- Check-In System ---\n")

    # Benutzereingaben abfragen
    # ACHTUNG: Die Umwandlung zu int() hier kann fehlschlagen, siehe unten!
    try:
        user_id_input = int(input("Bitte geben Sie Ihre ID ein: "))
        last_name_input = input(
            "Bitte geben Sie Ihren Nachnamen ein: ").strip()
    except ValueError:
        print("\nFehler: Die ID muss eine Zahl sein.")
        return main()

    # Daten validieren, übergeben Sie die extrahierte Liste
    if check_credentials(user_id_input, last_name_input, users_list):
        next_function(user_id_input)
    else:
        print("\nFehler bei der Authentifizierung. ID oder Nachname sind falsch.")
        while True:
            choice = input("Wollen Sie es nochmals versuchen?\n"
                           'ja (1), nein (2) oder stop zum Beenden: ').strip().lower()
            if choice == "1":
                return main()
            elif choice == "2":
                print("Dann schreiben Sie heute die Zeit von Hand auf...")
                return main()
            elif choice == "stop":
                print("Programm wird beendet")
                break
            else:
                print(
                    "\nBitte nur 1 oder 2 als Zahlen eingeben oder stop zum Beenden. Beginnen wir von vorn.")
                return main()


if __name__ == "__main__":
    main()
