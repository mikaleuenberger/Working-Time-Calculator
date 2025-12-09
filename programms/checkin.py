import json
import os
import menu1_5

# zeigt den Speicherpfad, wo Python die Datei sucht:
print(os.getcwd())


def load_users(filename="users.json"):
    """Lädt die Benutzerdaten aus der JSON-Datei."""

    # Den absoluten Pfad zur JSON-Datei erstellen
    # os.path.dirname(__file__)
    # gibt den Ordner zurück, in dem das aktuelle Skript liegt
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)

    try:
        # Verwenden Sie jetzt den absoluten Pfad
        with open(file_path, "r", encoding="utf-8") as file:
            users_data = json.load(file)
        return users_data
    except FileNotFoundError:
        print(
            f"Fehler: Die Datei '{file_path}' "
            + "wurde nicht gefunden. Überprüfen Sie den Pfad."
        )
        return []
    except json.JSONDecodeError:
        print(f"Fehler: Die Datei '{filename}' ist keine gültige JSON-Datei.")
        return []


# last_name_input umbenannt zur Klarheit
def check_credentials(user_id, last_name_input, users_list):
    """Überprüft, ob die eingegebenen Daten mit einem Benutzer übereinstimmen.
    und gibt das User Dictionary zurück.
    """
    for user in users_list:
        if (
            int(user["id"]) == int(user_id)
            and user["last_name"].casefold() == last_name_input.casefold()
        ):
            return user
    return None


def next_function(user_data):
    """Die Funktion, die nach einem erfolgreichen Login ausgeführt wird."""
    print(
        f"\nLogin erfolgreich! Willkommen,"
        + " {user_data['surname']} {user_data['last_name']}."
    )

    # Hier starten wir die Anwendung und übergeben den User
    menu1_5.main(user_data)


def main():
    users_data = load_users()
    if not users_data:
        return

    users_list = users_data.get("users", [])
    if not users_list:
        return

    print("\n--- Check-In System ---\n")

    try:
        user_id_input = int(input("Bitte geben Sie Ihre ID ein: "))
        last_name_input = input(
            "Bitte geben Sie Ihren Nachnamen ein: "
        ).strip()
    except ValueError:
        print("\nFehler: Die ID muss eine Zahl sein.")
        return main()

    # Hier fangen wir das User-Objekt ab
    identified_user = check_credentials(
        user_id_input, last_name_input, users_list
    )

    if identified_user:
        next_function(identified_user)
    else:
        print("\nFehler bei der Authentifizierung.")
        while True:
            choice = input("Nochmal? (1=ja, 2=nein, stop): ").lower()
            if choice == "1":
                return main()
            elif choice == "stop" or choice == "2":
                break


if __name__ == "__main__":
    main()
