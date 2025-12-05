# Verwaltung der Benutzerdatei (users.json)
# Wird vom Vorgesetzten-Menü aufgerufen, um Mitarbeitende zu verwalten.

import json
from pathlib import Path

# Projektverzeichnis bestimmen (eine Ebene über /programms)
BASE_DIR = Path(__file__).resolve().parent.parent

# Hilfsfunktionen für den Zugriff auf users.json


def ermittle_users_json_pfad():
    # Sucht nach der Datei 'users.json' an üblichen Orten.
    # Rückgabewert: Pfadobjekt (kann existieren oder noch nicht existieren)

    # Ordner, in dem user_admin.py liegt (also /programms)
    script_dir = Path(__file__).resolve().parent

    moegliche_pfade = [
        # -> /.../programms/users.json  (gleiche wie checkin.py)
        script_dir / "users.json",
        BASE_DIR / "users.json",          # Fallback: Projekt-Root
        BASE_DIR / "data" / "users.json"  # weiterer Fallback: /data/users.json
    ]

    for p in moegliche_pfade:
        if p.exists():
            return p

    # Falls keine Datei gefunden wurde, wird standardmässig
    # im /programms-Ordner eine neue users.json erwartet/angelegt.
    return script_dir / "users.json"


def lade_users():
    # Lädt die Benutzerinformationen aus der Datei users.json.
    # Rückgabe:
    #   daten -> Dictionary mit dem Schlüssel "users"
    #   pfad  -> tatsächlicher Speicherort der Datei

    pfad = ermittle_users_json_pfad()

    # Wenn die Datei noch nicht existiert, leere Struktur zurückgeben
    if not pfad.exists():
        print("⚠️  Die Datei 'users.json' existiert noch nicht. Es wird eine neue Datei angelegt.")
        return {"users": []}, pfad

    # Datei öffnen und JSON-Daten einlesen
    with pfad.open(encoding="utf-8") as f:
        daten = json.load(f)

    # Sicherstellen, dass der Schlüssel "users" vorhanden ist
    if "users" not in daten or not isinstance(daten["users"], list):
        daten["users"] = []

    return daten, pfad


def speichere_users(daten, pfad):
    # Speichert die Benutzerliste (daten) in der Datei users.json am angegebenen Pfad.

    with pfad.open("w", encoding="utf-8") as f:
        json.dump(daten, f, indent=4, ensure_ascii=False)

    print(f"💾 Benutzerdatei gespeichert: {pfad}")

# Funktionen zum Bearbeiten und Anlegen von Benutzern


def benutzer_bearbeiten(benutzer):
    # Ermöglicht das Bearbeiten eines einzelnen Benutzers.
    # Alle Eingaben sind optional (Enter = Wert bleibt unverändert).

    print("\n--- Benutzer bearbeiten ---")
    print(
        f"Aktuell: ID={benutzer['id']} | {benutzer['surname']} {benutzer['last_name']}")
    print(f"Email:  {benutzer['email']}")
    print(f"Rolle:  {benutzer['business_role']}")
    print(f"Alter:  {benutzer['age']}")

    # Vorname (surname im JSON)
    vor = input(f"Vorname [{benutzer['surname']}]: ").strip()
    if vor:
        benutzer["surname"] = vor

    # Nachname (name im JSON)
    nach = input(f"Nachname [{benutzer['last_name']}]: ").strip()
    if nach:
        benutzer["last_name"] = nach

    # E-Mail-Adresse
    email = input(f"Email [{benutzer['email']}]: ").strip()
    if email:
        benutzer["email"] = email

    # Rolle (Mitarbeiter oder Vorgesetzter)
    rolle = input(
        f"Rolle (Mitarbeiter/Vorgesetzter) [{benutzer['business_role']}]: ").strip()
    if rolle:
        benutzer["business_role"] = rolle

    # Alter
    alt = input(f"Alter [{benutzer['age']}]: ").strip()
    if alt:
        try:
            benutzer["age"] = int(alt)
        except:
            print("⚠️  Ungültige Eingabe – Alter wurde nicht geändert.")


def benutzer_anlegen(daten):
    # Legt einen neuen Benutzer in der Benutzerliste an.

    print("\n--- Neuen Benutzer anlegen ---")

    liste = daten["users"]

    # Neue ID bestimmen: höchste vorhandene ID + 1
    vorhandene_ids = [u.get("id", 0) for u in liste]
    neue_id = max(vorhandene_ids + [0]) + 1

    vor = input("Vorname: ").strip()
    nach = input("Nachname: ").strip()
    email = input("Email: ").strip()
    rolle = input("Rolle (Mitarbeiter/Vorgesetzter): ").strip()
    if rolle == "":
        rolle = "Mitarbeiter"

    alt = input("Alter: ").strip()
    try:
        alter = int(alt)
    except:
        alter = 0

    # Achtung: In users.json ist:
    #   "last_name"    = Nachname
    #   "surname" = Vorname
    neuer_benutzer = {
        "id": neue_id,
        "last_name": nach,
        "surname": vor,
        "email": email,
        "business_role": rolle,
        "age": alter
    }

    liste.append(neuer_benutzer)
    print(f"✅ Benutzer angelegt: ID={neue_id} | {vor} {nach}")

# Hauptmenü der Benutzerverwaltung


def benutzerverwaltung_starten():
    # Startpunkt für die Benutzerverwaltung
    # Hier kann der Vorgesetzte:
    #   - alle Benutzer ansehen
    #   - einen Benutzer bearbeiten
    #   - einen neuen Benutzer anlegen

    daten, pfad = lade_users()

    while True:
        liste = daten["users"]

        print("\n======== Benutzerverwaltung ========")
        if not liste:
            print("Keine Benutzer vorhanden.")
        else:
            print("Nr  ID   Vorname        Nachname       Rolle            Alter")
            print("--------------------------------------------------------------")
            # Alle Benutzer auflisten
            for i, u in enumerate(liste, start=1):
                print(
                    str(i).ljust(3),
                    str(u["id"]).ljust(5),
                    u["surname"].ljust(15),
                    u["last_name"].ljust(15),
                    u["business_role"].ljust(15),
                    str(u["age"]).ljust(5)
                )

        print("\nOptionen:")
        print("  [Nummer]  -> Benutzer bearbeiten")
        print("  a         -> Neuen Benutzer anlegen")
        print("  x         -> Zurück zum Hauptmenü")

        auswahl = input("Auswahl: ").strip().lower()

        if auswahl == "x":
            # Zurück ins Vorgesetzten-Menü
            return

        elif auswahl == "a":
            # Neuen Benutzer anlegen
            benutzer_anlegen(daten)
            speichere_users(daten, pfad)

        elif auswahl.isdigit():
            # Benutzer anhand der Nummer bearbeiten
            index = int(auswahl)
            if 1 <= index <= len(liste):
                benutzer_bearbeiten(liste[index - 1])
                speichere_users(daten, pfad)
            else:
                print("❌ Ungültige Auswahl (Nummer existiert nicht).")

        else:
            print("❌ Ungültige Eingabe.")
