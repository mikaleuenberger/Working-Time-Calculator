# 📊🔢 WTCalculator – Working Time Calculator (Browser App)

> 
## 📝 Application Requirements

### Problem
> Für kleinere Firmen ist das Erfassen der Arbeitszeiten ein essentieller Prozess.  
Kommerzielle Lösungen wie SAP sind jedoch teuer. Mit unserer App bieten wir eine **einfache und kostengünstige Alternative** zur Arbeitszeiterfassung.

### Scenario
In unserer Python Appikation sollen Arbeitszeiten erfasst und ausgewertet werden können. Ein User kann Arbeitsbeginn und Arbeitsende als Uhrzeiten erfassen und die Pausen als Stunden/Minuten Input. Ausgewertet wird die Brutto und die Netto Arbeitszeit. 
Die ausgerechneten Zeiten werden mit bestimmten Rules, die festgelegt sind, abgeglichen. Beispiele sind hier: Maximalarbeitszeiten (Max Überstundenanzahl), Einhaltung der Mittags-Pausenzeit (Keine Pausen unter 30 Minuten).
Der Vorgesetzte kann die Mitarbeiter-Daten pflegen (wie bspw. das Alter), damit die gültigen Regeln (z.B. Jugendschutzgesetz) automatisch angewendet werden.

## 📖 User Stories
1. Als User möchte ich meine Arbeitszeit exakt eingeben (hh:mm) 
2. Ich möchte meine Tages-, Wochen- und Monatsarbeitszeit sehen (Eingabe einzelner Tage und Auswertung der Woche oder des Monats mit bestehenden Daten) 
3. Als User möchte ich eine Fehlermeldung in Form eines Kommentars sehen, wenn ich die gesetzliche mindest Mittagszeit unterschreite
4. Ich möchte als User Mittagspausen eintragen können.
5. Ich möchte als User eine Warnmeldung als Kommentar bekommen, wenn meine maximale Wochenarbeitszeit 45h überschritten ist 
6. Ich möchte mich als User bei der Verwendung des Tools mittels ID, Nachname und Passwort authentifizieren 
7. Als Vorgesetzter will ich einen Rapport erstellen können über die Arbeitszeiten meiner Mitarbeiter 
8. Als minderjähriger Mitarbeiter darf ich nicht über 9h arbeiten und keine Nacht- oder Wochenendarbeit machen, damit die Jugendarbeitsschutzgesetze eingehalten werden. Ausnahmen können begründet vorkommen oder es können nachträglich die Zeiten korrigiert werden

## 🧩 Use Cases
- Authentifizieren mittels ID, Nachnahmen und Kennwort
- Arbeitszeiten und Mittagspausen eingeben  
- Eingaben validieren  
- Zeitrapport auf Wochen- und Monatsbasis ausgeben  
- Kommentare bei Regelverletzungen anzeigen
- Unterschiedliche Menüs für Mitarbeiter und Vorgesetzte


### Main Use Cases
- Zeit erfassen (Mitarbeiter)  
- Zeiterfassung überprüfen (Vorgesetzter)  

-> im Diagramm wird nur die UC-Gruppe der Zeiterfassung beschrieben:

![UC](wtcalculator/docs/ui-images/UC_Zeiterfassung.png)

### Actors
- Mitarbeiter  
- Vorgesetzter

---

### Wireframes / Mockups

#### Mockup: Login
![Wireframes – Home/Transactions](wtcalculator/docs/ui-images/login_rough.png)

#### Mockup: CSV Import
![Wireframes – Home/Transactions](wtcalculator/docs/ui-images/csv_import_rough.png)

#### Mockup: Superior View
![Wireframes – Home/Transactions](wtcalculator/docs/ui-images/entries_rough.png)


---

## 🏛️ Architecture

![UML Klassendiagramm](wtcalculator/docs/ui-images/Klassendiagramm.jpg)
---
### Layers
---
#### UI: NiceGUI
Die Benutzeroberfläche wird mit NiceGUI umgesetzt. Sie dient zur Eingabe und Anzeige von Benutzerdaten, Zeiteinträgen und Auswertungen.

#### Application logic: Services und TimeCalculator
Die Geschäftslogik liegt in den Service-Klassen. AuthService verwaltet die Anmeldung, UserService die Benutzer, TimeEntryService die Zeiteinträge und ReportService die Monatsauswertungen. Der TimeCalculator berechnet die Nettoarbeitszeit und erzeugt Kommentare.

#### Persistence: SQLite, ORM und Datenmodelle
Die Daten werden über ORM-Modelle gespeichert. User und TimeEntry bilden die zentralen Datenobjekte. Ein Benutzer kann mehrere Zeiteinträge besitzen, während jeder Zeiteintrag genau einem Benutzer gehört. 

---
### Design Decisions
---

#### Cleat separation between data and logic
User, TimeEntry, MonthlyReport und WorkTimeResult enthalten Daten. Die Services übernehmen die Verarbeitung und greifen auf diese Klassen zu.

#### Service oriented structure
Jede Service-Klasse hat eine klar abgegrenzte Aufgabe: Authentifizierung, Benutzerverwaltung, Zeiterfassung oder Reporting.

#### Calculation logic outsourced
Die Berechnung der Arbeitszeit ist im TimeCalculator gekapselt. Dadurch bleibt TimeEntryService übersichtlich und delegiert die Berechnung an eine eigene Klasse.

---
### Patterns Used
---

#### Service Pattern
AuthService, UserService, TimeEntryService und ReportService kapseln die Anwendungslogik.

#### Repository / DAO approach via session
Alle Services verwenden eine _session, um Daten zu lesen, zu speichern oder zu verwalten. Dadurch ist der Datenzugriff von der restlichen Logik getrennt.

#### Model Relationship
User und TimeEntry stehen in einer 1:n-Beziehung. Ein Benutzer kann viele Zeiteinträge haben, ein Zeiteintrag gehört zu genau einem Benutzer.

#### DTO / Result Objects
MonthlyReport und WorkTimeResult dienen als einfache Rückgabeobjekte für Reports und Berechnungsergebnisse.

---

## 🗄️ Database and ORM

![ER Diagram](wtcalculator/docs/ui-images/ER_Modell.png)

Die Anwendung nutzt ***SQLAlchemy***, um Domänenobjekte einer SQLite-Datenbank zuzuordnen.

### Entities
- `Mitarbeiter`
- `Vorgesetzte`
- `Arbeitszeiterfassung`

### Relationships
- Ein `Mitarbeiter` → mehrere `Arbeitszeiterfassung`
- Jede `Arbeitszeiterfassung` wird geprüft durch ein `Vorgesetzte`

---

## ✅ Project Requirements

---

Jede Applikation muss die folgenden Kriterien erfüllen, um akzeptiert zu werden (siehe auch die offiziellen Projektvorgaben auf Moodle):

1. Verwendung von NiceGUI für die Entwicklung einer interaktiven Webapplikation
2. Datenvalidierung innerhalb der Anwendung
3. Verwendung eines ORM für das Datenbankmanagement

---

### 1. Browser-based Application (NiceGUI)


Die Applikation interagiert mit dem Benutzer über den Browser. Benutzer können:

- Sich einloggen
- Ihre Arbeitszeiten erfassen
- Kommentare und Hinweise erhalten, wenn Arbeitszeiten gegen Validierungsregeln verstossen
- Arbeitszeitrapporte generieren (z. B. für Vorgesetzte)

**Architektur-Hinweis (gemäss SS26-Richtlinien):**  
Der Browser fungiert als Thin Client. Die Darstellung der Benutzeroberfläche erfolgt clientseitig, während der Applikationszustand sowie die Businesslogik serverseitig innerhalb der NiceGUI-Applikation verarbeitet werden.

Das Projekt verwendet objektorientierte Programmierung in Python, um die Businesslogik in modulare und wiederverwendbare Komponenten zu strukturieren.


---

### 2. Data Validation

- **Benutzervalidierung:**  
  Der Benutzer gibt seine Mitarbeiter-ID und seinen Nachnamen ein. Der Check-In prüft, ob beide Eingaben mit den Mitarbeiterdaten aus dem JSON-Dictionary übereinstimmen. Die ID darf nur aus Zahlen bestehen.

- **Altersvalidierung:**  
  Ist ein Benutzer minderjährig, werden Warnungen ausgegeben bei:
  - mehr als 9 Stunden Arbeitszeit pro Tag
  - Nachtarbeit zwischen 22:00 und 06:00 Uhr
  - Wochenendarbeit

- **Zeitformat-Validierung:**  
  Arbeitszeiten dürfen nur im Format `hh:mm` eingegeben werden.

- **Pausenvalidierung:**  
  Der Benutzer gibt seine Mittagszeiten ein. Wird keine Mittagspause erfasst, wird automatisch die gesetzliche Mindestpause von 30 Minuten abgezogen, ausser es wird Nachtarbeit erkannt oder weniger als 6 Stunden Arbeitszeit erfasst.

- **Arbeitszeitvalidierung:**  
  Die vorgesehene Arbeitszeit beträgt 45 Stunden pro Woche. Alles darüber wird als Überzeit behandelt. Überzeiten über 45 Stunden sind nicht vorgesehen, jedoch nicht verboten.

- **Eingabevalidierung:**  
  Diverse Eingaben im Check-In und Menü werden auf das korrekte Format geprüft, bei Bedarf korrigiert (z. B. Gross-/Kleinschreibung) oder mit einer Fehlermeldung kommentiert und zur erneuten Eingabe aufgefordert.

---

### 3. Database management

- Für das ORM wird SQLAlchemy verwendet.
- Python-Objekte werden innerhalb von Datenbank-Sessions erstellt und verwaltet.
- Datenbankabfragen werden mit ORM-Syntax anstelle von direkten SQL-Befehlen umgesetzt.
- Daten werden über Klassenattribute und Modellbeziehungen gefiltert und ausgelesen.
- Objektattribute wie `xy.approved` werden verwendet, um automatische Updates innerhalb der Services auszulösen.

---

## ⚙️ Implementation

### Technology
- Python 3.x
- Umgebung: GitHub Codespaces
- Benötigte externe Bibliotheken: SQLAlchemy, NiceGUI

### Libraries Used

### External Libraries (Third-Party)

* **[SQLAlchemy](https://www.sqlalchemy.org/):** Wir nutzen es als Object-Relational Mapper (ORM), um objektorientiert mit der SQLite-Datenbank zu interagieren.
* **[NiceGUI](https://nicegui.io/):** Unser Frontend-Framework. Es ermöglicht uns, die gesamte grafische Web-Benutzeroberfläche (Dashboards, Tabellen, Dialoge) direkt und nahtlos in Python zu entwickeln.
* ** `pytest / pytest-cov`: Unser Framework für das automatisierte Unit-Testing und zur Messung der Testabdeckung (Coverage), um die Code-Qualität sicherzustellen.

### Python Standard Libraries (Built-ins)

* **`datetime` / `date, time, timedelta`:** Für Logik der Arbeitszeitberechnung, Pausenabzüge, Nachtschichterkennung sowie die dynamische Altersberechnung anhand des Geburtsdatums.
* **`dataclasses`:** Für schlanke und unveränderliche Datenobjekte (z. B. `WorkTimeResult`, `MonthlyReport`) zur sicheren Datenübergabe zwischen den Schichten.
* **`unittest.mock (patch)`: Wird im Testing verwendet, um externe Abhängigkeiten (wie Datenbank-Sessions) durch kontrollierte Test-Objekte ("Mocks") zu ersetzen, was isolierte Unit-Tests ermöglicht.
* **`contextlib (contextmanager)`: Wir bauen eigene, temporäre Kontexte (wie gemockten session_scope in den Tests) auf und wieder ab.
* **`csv` / `io`:** Für den reibungslosen Import und die Verarbeitung der alten (Legacy) Zeiterfassungsdaten.
* **`json`:** Für das automatische Seeding (initiale Befüllung) der Datenbank mit Benutzerdaten.
* **`pathlib`:** Für moderne, sichere und betriebssystemunabhängige Pfad- und Dateioperationen.

### 📂 Repository Structure

Das Projekt folgt einer sauberen MVC-Architektur (Model-View-Controller) mit einer dedizierten Service- und Domain-Schicht.

```text
WORKING-TIME-CALCULATOR/
├── .devcontainer/         # Konfiguration für Entwicklungscontainer (z.B. GitHub Codespaces)
├── .idea/                 # Lokale IDE-Einstellungen (z.B. PyCharm/WebStorm)
├── .nicegui/              # Lokale NiceGUI-Arbeitsdaten
├── .vscode/               # Lokale Editor-Einstellungen für VS Code
├── data/                  # Speicherort für lokale Daten (time_entries.csv, users.json)
├── scripts/               # Hilfs- und Setup-Skripte (z.B. Start-Skripte, Testdaten generieren)
├── tests/                 # 🧪 Unit- und Integrationstests (conftest.py, diverse test_*.py)
├── wtcalculator/          # 📦 Hauptpaket der Anwendung
│   ├── data_access/       # Datenzugriffsschicht (db.py, seed.py)
│   ├── docs/ui-images/    # Bilder für Dokumentation, Mockups und UML-Diagramme
│   ├── domain/            # Kern-Geschäftslogik (z.B. time_calculator.py)
│   ├── services/          # Service-Schicht (Datenbank-Interaktion & Validierung)
│   │   ├── auth_service.py
│   │   ├── report_service.py
│   │   ├── time_entry_service.py
│   │   └── user_service.py
│   ├── ui/                # UI-Ansichten und Layouts (dashboard, login, etc.)
│   │   ├── dashboard.py
│   │   ├── employee_dashboard.py
│   │   ├── login.py
│   │   └── supervisor_dashboard.py
│   ├── app_controler.py   # Zentraler Controller (verbindet UI mit Services)
│   ├── constants.py       # Globale Konstanten und Konfigurationswerte
│   ├── db.py              # Datenbank-Verbindung (Hinweis: Gibt es auch in data_access/)
│   ├── models.py          # SQLAlchemy ORM-Modelle (Tabellenstrukturen für User & Zeiten)
│   ├── security.py        # Sicherheitsfunktionen (Passwort-Hashing & Policies)
│   └── webapp.py          # Präsentationsschicht / Initialisierung der NiceGUI App
├── .dockerignore          # Docker-spezifische Ausschlüsse
├── .gitignore             # Ignorierte Dateien für die Versionskontrolle
├── main2.py               # Bootstrapper/Einstiegspunkt der Anwendung
├── nixpacks.toml          # Konfiguration für den Nixpacks-Build (Deployment)
├── railway.json           # Konfiguration für das Hosting auf Railway
├── README.md              # Hauptdokumentation des Projekts
└── requirements.txt       # Python-Abhängigkeiten und Bibliotheken
```


### How to Run 

### 1. Launch
https://working-time-calculator.up.railway.app/

Öffne die URL in deinem Browser

### 2. Login

### Authetification as Employee
#### Benutzerübersicht
 | ID  | Nachname      | Rolle       |
 | --- | ------------- | ----------- |
 | 001 | Müller        | Mitarbeiter |
 | 002 | Suter         | Mitarbeiter |
 | 003 | Hübner		(u18) | Mitarbeiter |
 | 004 | Ackermann     | Vorgesetzer |

#### Passwort
Unser Standardpasswort ist zu Testzwecken: Hallo1234!
Wenn die DB neu initialisiert ist, wird man aufgefordert, das Passwort selber zu setzen.


Erfasse Arbeitszeit, lade eine .csv-Datei hoch oder schau dir deine erfassten Arbeitszeiten der Wochen / Monate an

### Possibilities as Superior:
1. Mutiere Mitarbeiter-Daten
2. Prüfe Arbeitszeit der Mitarbeitenden und gebe diese frei
3. Erstelle Rapporte als PDF
--- 

## Screenshots of Webapp:

### Startpage
![UI – Startseite](wtcalculator/docs/ui-images/Login_Page.png)

### Startpage after employee login
![UI – Mitarbeiter-Startseite](wtcalculator/docs/ui-images/startseite_ma1.png)

### Week-overview employee
![UI – Wochenübersicht Mitarbeiter](wtcalculator/docs/ui-images/Wochenübersicht_Mitarbeiter.png)

### Superior View after Login
![UI – Vorgesetzter-Startseite](wtcalculator/docs/ui-images/startseite_vorgesetzter.png)

---

## 🧪 Testing

### Running Tests

```bash
# Install pytest (if not already installed)
pip install pytest
pip install pytest-cov

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=wtcalculator
```

### Test Structure

```
tests/
├── conftest.py                    # Pytest fixtures (test database, sample users)
├── test_time_calculator.py        # Domain logic tests (net hours, minor rules, overtime)
├── test_time_entry_service.py     # Service layer tests (CRUD, weekly/monthly hours)
├── test_app_controler.py          # Controller tests (validation, parsing)
└── test_ui_employee_dashboard.py  # UI import tests, constants validation
```

### Test Coverage

- **Unit tests**: Time calculation logic, date/time parsing, user validation
- **Service tests**: TimeEntry CRUD, weekly/monthly hour calculations, approvals
- **Controller tests**: Input validation, error handling
- **Constants tests**: Verification of rule constants (45h weekly max, 30min break min, etc.)

**Current test count**: 39 passing, 4 skipped (UI imports skipped due to NiceGUI Python 3.14 compatibility)


# Project Test Cases Reference

This document contains the core test cases for the Working Time Calculator (`wtcalculator`) project, categorized by test level (Unit, Database, Integration) and formatted for easy inclusion in the project repository documentation.

---

## 🧪 Unit Tests (Domain Logic & Validation)

### TC_U001: Calculate basic net working hours with a standard lunch break
| Section | Details |
| :--- | :--- |
| **Preconditions** | The time calculator module is accessible. |
| **Test Steps** | 1. Call `calculate_net_hours_and_comment` with valid parameters.<br>2. Pass start time "08:00", end time "17:00", and short break of 60 minutes.<br>3. Evaluate the returned `net_hours_decimal` and `comment` fields. |
| **Test Data / Input** | `start_hhmm`="08:00", `end_hhmm`="17:00", `short_break_min`=60, `work_date`=2026-05-12, `user_birthdate`=2001-01-01 |
| **Expected Result** | The function returns exactly `8.0` net hours and an empty comment string. |
| **Actual Result** | Returns `8.0` net hours with no comment. |
| **Status** | 🟢 Pass |
| **Comments** | Verifies standard 9-hour gross workday minus 1-hour break calculation. |

### TC_U002: Prevent calculation with invalid lunch break chronological order
| Section | Details |
| :--- | :--- |
| **Preconditions** | The time calculator module is accessible. |
| **Test Steps** | 1. Call `calculate_net_hours_and_comment`.<br>2. Input a lunch start time that is chronologically after the lunch end time.<br>3. Check the returned warning comments. |
| **Test Data / Input** | `start_hhmm`="08:00", `end_hhmm`="17:00", `lunch_start_hhmm`="13:00", `lunch_end_hhmm`="12:00" |
| **Expected Result** | The calculation completes but returns a specific warning comment containing `"Ende vor Start"` regarding the invalid lunch timeframe. |
| **Actual Result** | Warning comment `"Ende vor Start"` is successfully generated. |
| **Status** | 🟢 Pass |
| **Comments** | Edge case validation for manual user entry errors. |

### TC_U003: Trigger youth labor protection warning for minors exceeding 9 hours
| Section | Details |
| :--- | :--- |
| **Preconditions** | The time calculator module is accessible. |
| **Test Steps** | 1. Call `calculate_net_hours_and_comment`.<br>2. Provide a birthdate that makes the user under 18 years old at the time of the `work_date`.<br>3. Input work hours that result in a net time greater than 9 hours.<br>4. Assert the contents of the returned comment. |
| **Test Data / Input** | `start_hhmm`="06:00", `end_hhmm`="18:00", `short_break_min`=60, `work_date`=2026-05-12, `user_birthdate`=2010-01-01 |
| **Expected Result** | The system calculates 11 net hours but appends a `"Maximalarbeitszeit Minderjährige"` warning to the comment. |
| **Actual Result** | Net hours calculated correctly, appropriate minor warning appended. |
| **Status** | 🟢 Pass |
| **Comments** | Crucial compliance check for labor laws. |

### TC_U004: Trigger overtime warning for work shifts exceeding 12 net hours
| Section | Details |
| :--- | :--- |
| **Preconditions** | The time calculator module is accessible. |
| **Test Steps** | 1. Call `calculate_net_hours_and_comment` with adult user data.<br>2. Input a start and end time combination totaling more than 12 net hours.<br>3. Inspect the returned comment string. |
| **Test Data / Input** | `start_hhmm`="06:00", `end_hhmm`="20:00", `short_break_min`=30 |
| **Expected Result** | A warning containing `"Überzeit"` and `"12h"` is present in the output comment. |
| **Actual Result** | Warning successfully triggered for 13.5 net hours. |
| **Status** | 🟢 Pass |
| **Comments** | Legal limit verification for standard adult workers. |

### TC_U005: Reject user creation when required name fields are empty
| Section | Details |
| :--- | :--- |
| **Preconditions** | Mocked database session context is active. |
| **Test Steps** | 1. Invoke `AuthController.upsert_user`.<br>2. Provide a payload with empty strings for `first_name` and `last_name`.<br>3. Assert the status and error message of the returned dictionary. |
| **Test Data / Input** | `{'first_name': '', 'last_name': '', 'email': 'test@example.com', 'role': 'Mitarbeiter', 'birthdate': '2001-05-01'}` |
| **Expected Result** | Returns a dictionary with `status='error'` and a message indicating missing `"Vorname und Nachname"`. |
| **Actual Result** | Error triggered with correct validation message. |
| **Status** | 🟢 Pass |
| **Comments** | Ensures data integrity at the business logic layer before hitting persistence. |

### TC_U006: Reject invalid date format strings during parsing
| Section | Details |
| :--- | :--- |
| **Preconditions** | The application controller module is accessible. |
| **Test Steps** | 1. Call the internal helper `_parse_date_yyyy_mm_dd`.<br>2. Pass a date string in DD-MM-YYYY format instead of the expected YYYY-MM-DD.<br>3. Verify that an exception is raised. |
| **Test Data / Input** | `"12-05-2026"` |
| **Expected Result** | An `Exception` is raised due to the format mismatch. |
| **Actual Result** | `Exception` raised successfully. |
| **Status** | 🟢 Pass |
| **Comments** | Input sanitization check before data reaches business logic. |

---

## 🗄️ Database Tests (CRUD & Persistence Logic)

### TC_DB001: Create and persist a new TimeEntry in the database
| Section | Details |
| :--- | :--- |
| **Preconditions** | Active test database session (in-memory SQLite) and an existing sample `User` record. |
| **Test Steps** | 1. Initialize `TimeEntryService` with the test database session.<br>2. Call `upsert_entry` with valid time tracking data for the sample user.<br>3. Query the database or check the returned entity properties. |
| **Test Data / Input** | `user`=sample_user, `work_date`=2026-05-12, `start_hhmm`="08:00", `end_hhmm`="17:00", `short_break_min`=60 |
| **Expected Result** | A new `TimeEntry` record is created, receives a valid database ID, defaults `approved` to `False`, and correctly stores 8.0 net hours. |
| **Actual Result** | Record persists with correct ID and field values. |
| **Status** | 🟢 Pass |
| **Comments** | Foundational data persistence test. |

### TC_DB002: Retrieve all time entries for a specific user within a specific calendar month
| Section | Details |
| :--- | :--- |
| **Preconditions** | Active test database session with a sample user. |
| **Test Steps** | 1. Use `TimeEntryService.upsert_entry` to create two entries in May 2026 and one in June 2026 for the same user.<br>2. Call `list_month_entries` requesting data for May 2026.<br>3. Call `list_month_entries` requesting data for June 2026.<br>4. Count the records returned for both queries. |
| **Test Data / Input** | Entries on `2026-05-11`, `2026-05-12`, and `2026-06-01`. Query Target 1: Month 5, Year 2026. Query Target 2: Month 6, Year 2026. |
| **Expected Result** | The May query returns exactly 2 records. The June query returns exactly 1 record. |
| **Actual Result** | Lists filtered correctly by month. |
| **Status** | 🟢 Pass |
| **Comments** | Verifies correct SQLAlchemy filtering logic based on date ranges. |

### TC_DB003: Update a TimeEntry status to 'approved'
| Section | Details |
| :--- | :--- |
| **Preconditions** | Active test database session with an existing, unapproved `TimeEntry` record. |
| **Test Steps** | 1. Retrieve the unapproved time entry ID.<br>2. Call `TimeEntryService.approve_entry` passing the target ID.<br>3. Reload the entity from the database session.<br>4. Verify the `approved` boolean flag. |
| **Test Data / Input** | `entry_id` of an existing `TimeEntry` where `approved` is initially `False`. |
| **Expected Result** | The function returns `True`, and the database record reflects `approved == True`. |
| **Actual Result** | Status successfully toggled in the database. |
| **Status** | 🟢 Pass |
| **Comments** | Tests the state transition vital for the supervisor workflow. |

---

## 🔗 Integration Tests (Cross-Component Workflows)

### TC_INT001: Calculate aggregate weekly hours across multiple database entries
| Section | Details |
| :--- | :--- |
| **Preconditions** | Active test database session with a sample user. |
| **Test Steps** | 1. Use `TimeEntryService` to create two separate 8-hour shift entries within the same calendar week.<br>2. Call `get_weekly_hours` passing a date falling within that specific week.<br>3. Evaluate the total aggregated hours returned. |
| **Test Data / Input** | Entries on `2026-05-11` (8h net) and `2026-05-13` (8h net). Query parameter `any_day_in_week`=`2026-05-13`. |
| **Expected Result** | The service fetches the correct records from the database, sums the calculated `net_hours`, and returns exactly `16.0`. |
| **Actual Result** | Aggregation logic combines DB queries and math accurately yielding `16.0`. |
| **Status** | 🟢 Pass |
| **Comments** | Integrates time calculation logic, database querying, and grouping by week. |

### TC_INT002: Controller gracefully rejects and formats errors for invalid time inputs before database insertion
| Section | Details |
| :--- | :--- |
| **Preconditions** | Application Controller is instantiated. Mock database can be present but shouldn't be reached. |
| **Test Steps** | 1. Invoke `AuthController.save_time_entry` with a syntactically invalid time string.<br>2. Assert the controller handles the underlying parser exception.<br>3. Verify the formatted response dictionary returned to the UI layer. |
| **Test Data / Input** | `user_id`=999, `date_str`="2026-05-12", `start_s`="99:99" (invalid time format), `end_s`="17:00" |
| **Expected Result** | The underlying parsing error is caught, and the controller returns `{'status': 'error', 'message': '...hh:mm...'}` without attempting a DB write. |
| **Actual Result** | Error handled smoothly, returning specific UI-friendly JSON/Dict payload. |
| **Status** | 🟢 Pass |
| **Comments** | Tests the boundary between the input format parsers, the controller layer, and error handling. |

### TC_INT003: Enforce minimum age policies during new user registration flow
| Section | Details |
| :--- | :--- |
| **Preconditions** | Mocked database session context is active. |
| **Test Steps** | 1. Call `AuthController.upsert_user` with valid profile data, but a birthdate that makes the user too young according to system constants.<br>2. Verify the system logic retrieves the constants, calculates the age based on current date vs birthdate, and blocks the database transaction. |
| **Test Data / Input** | User payload with `birthdate`='2016-01-01' |
| **Expected Result** | Controller logic prevents creation, returning `status='error'` with an "Alter" (Age) specific message, enforcing the `AGE_MIN` constant limits. |
| **Actual Result** | Minimum age limit enforced, user rejected appropriately. |
| **Status** | 🟢 Pass |
| **Comments** | Integrates `constants.py` configurations with controller validation and mocked DB layers. |

---

## 👥 Team & Contributions

| Name               | Contribution                                                                                                                                                                                                                              |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Flavio Waser       | NiceGUI UI, Uhr auf Login Seite, Anpassung des Hauptcodes auf objektorientierte Programmierung, Mockups, CSV-Import                                                                 |
| Kristina Schaffner | NiceGUI UI, Readme-File und diverese Grafiken, Passwort-Design optimieren, Umbau des ersten Entwurfs nach MVC                                                                        |
| Mika Leuenberger   | NiceGUI UI, Programmstart, diverse Validierungen überprüfen und aktualisieren, PDF Generierung |


## 🤝 Contributing

> 🚧 This is a template repository for student projects.  
> 🚧 Do not change this section in your final submission.

- Use this repository as a starting point by importing it into your own GitHub account.  
- Work only within your own copy — do not push to the original template.  
- Commit regularly to track your progress.

## 📝 License

This project is provided for **educational use only** as part of the Programming Foundations module.  
[MIT License](LICENSE)
