# Verwaltung der Benutzerdatei (users.json)
# Vom Vorgesetzten-Menü aufgerufen

import json
from pathlib import Path
import re

# Projektverzeichnis bestimmen (eine Ebene über /programms)
BASE_DIR = Path(__file__).resolve().parent.parent

# Hilfsfunktionen für den Zugriff auf users.json


def ermittle_users_json_pfad():
    return Path(__file__).resolve().parent / "users.json"


def lade_users():
    # Lädt die Benutzerinformationen aus der Datei users.json.
    # Falls sie nicht existiert, wird eine neue Datei vorbereitet.

    pfad = ermittle_users_json_pfad()

    if not pfad.exists():
        print(
            "⚠️  users.json existiert noch nicht – "
            "es wird eine neue Datei angelegt."
        )
        return {"users": []}, pfad

    with pfad.open(encoding="utf-8") as f:
        daten = json.load(f)

    if "users" not in daten or not isinstance(daten["users"], list):
        daten["users"] = []

    return daten, pfad


def speichere_users(daten, pfad):
    # Speichert die Benutzerliste (daten)
    # in der Datei users.json am angegebenen Pfad.

    with pfad.open("w", encoding="utf-8") as f:
        json.dump(daten, f, indent=4, ensure_ascii=False)

    print(f"💾 Benutzerdatei gespeichert: {pfad}")


# Funktionen zum Bearbeiten und Anlegen von Benutzern

# Hilfsfunktionen für Validierung

def nur_buchstaben(text):
    # Erlaubt Buchstaben inkl. Umlaute und Bindestrich
    return bool(re.match(r"^[A-Za-zÄÖÜäöüß-]+$", text))


def gueltige_email(text):
    # Simple Prüfung reicht hier
    return "@" in text and "." in text


def gueltige_rolle(text):
    return text in ["Mitarbeiter", "Vorgesetzter"]


def benutzer_bearbeiten(benutzer):
    # Bearbeiten eines einzelnen Benutzers
    # Enter = Wert bleibt unverändert

    print("\n--- Benutzer bearbeiten ---")
    print(
        f"Aktuell: ID={benutzer['id']} | "
        f"{benutzer['surname']} {benutzer['last_name']}"
    )
    print(f"Email:  {benutzer['email']}")
    print(f"Rolle:  {benutzer['business_role']}")
    print(f"Alter:  {benutzer['age']}")

    # Vorname
    while True:
        vor = input(f"Vorname [{benutzer['surname']}]: ").strip()
        if vor == "":
            break
        if not nur_buchstaben(vor):
            print("❌ Vorname darf nur Buchstaben enthalten!")
            continue
        benutzer["surname"] = vor
        break

    # Nachname
    while True:
        nach = input(f"Nachname [{benutzer['last_name']}]: ").strip()
        if nach == "":
            break
        if not nur_buchstaben(nach):
            print("❌ Nachname darf nur Buchstaben enthalten!")
            continue
        benutzer["last_name"] = nach
        break

    # Email
    while True:
        email = input(f"Email [{benutzer['email']}]: ").strip()
        if email == "":
            break
        if not gueltige_email(email):
            print("❌ Ungültige Email-Adresse!")
            continue
        benutzer["email"] = email
        break

    # Rolle
    while True:
        rolle = input(
            f"Rolle (Mitarbeiter/Vorgesetzter) "
            f"[{benutzer['business_role']}]: "
        ).strip()

        if rolle == "":
            break

        rolle = rolle.capitalize()
        if not gueltige_rolle(rolle):
            print("❌ Ungültige Rolle! Erlaubt: Mitarbeiter oder Vorgesetzter")
            continue

        benutzer["business_role"] = rolle
        break

    # Alter
    while True:
        alt = input(f"Alter [{benutzer['age']}]: ").strip()
        if alt == "":
            break
        if not alt.isdigit():
            print("❌ Alter muss eine ganze Zahl sein!")
            continue
        benutzer["age"] = int(alt)
        break


def benutzer_anlegen(daten):
    print("\n--- Neuen Benutzer anlegen ---")

    liste = daten["users"]

    # Neue ID bestimmen: höchste vorhandene ID + 1
    vorhandene_ids = [u.get("id", 0) for u in liste]
    neue_id = max(vorhandene_ids + [0]) + 1

    # Hilfsfunktion nur Buchstaben
    def nur_buchstaben(text):
        return bool(re.match(r"^[A-Za-zÄÖÜäöüß-]+$", text))

    # Vorname (Pflicht)
    while True:
        vor = input("Vorname (Pflicht): ").strip()
        if vor == "":
            print("❌ Vorname darf nicht leer sein!")
            continue
        if not nur_buchstaben(vor):
            print("❌ Vorname darf nicht nur Buchstaben enthalten!")
            continue
        break

    # Nachname (Pflicht)
    while True:
        nach = input("Nachname (Pflicht): ").strip()
        if nach == "":
            print("❌ Nachname darf nicht leer sein!")
            continue
        if not nur_buchstaben(nach):
            print("❌ Nachname darf nichnur Buchstaben enthalten!")
            continue
        break

    # Email (Pflicht)
    while True:
        email = input("Email (Pflicht): ").strip()
        if email != "" and "@" in email and "." in email:
            break
        print("❌ Ungültige Email-Adresse!")

    # Rolle (Pflicht, nur 2 gültige Werte)
    while True:
        rolle = (
            input("Rolle (Mitarbeiter / Vorgesetzter): ").strip().capitalize()
        )

        if rolle in ["Mitarbeiter", "Vorgesetzter"]:
            break

        print("❌ Ungültige Eingabe! Erlaubt: Mitarbeiter oder Vorgesetzter")

    # Alter (Pflicht, nur Zahlen)
    while True:
        alt = input("Alter (Pflicht, nur Zahlen): ").strip()
        if alt.isdigit():
            alter = int(alt)
            break
        print("❌ Alter muss eine ganze Zahl sein!")

    # Benutzer in JSON-Format speichern
    neuer_benutzer = {
        "id": neue_id,
        "last_name": nach,
        "surname": vor,
        "email": email,
        "business_role": rolle,
        "age": alter,
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
            print(
                "Nr  ID   Vorname        Nachname       Rolle            Alter"
            )
            print(
                "-----------------------------"
                + "---------------------------------"
            )
            # Alle Benutzer auflisten
            for i, u in enumerate(liste, start=1):
                print(
                    str(i).ljust(3),
                    str(u["id"]).ljust(5),
                    u["surname"].ljust(15),
                    u["last_name"].ljust(15),
                    u["business_role"].ljust(15),
                    str(u["age"]).ljust(5),
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
