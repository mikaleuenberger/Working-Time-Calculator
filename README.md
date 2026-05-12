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
2. Ich möchte meine Tages-, Wochen- und Monatsarbeitszeit auf dem Blatt sehen (Eingabe einzelner Tage und Auswertung der Woche oder des Monats mit bestehenden Daten) 
3. Als User möchte ich eine Fehlermeldung in Form eines Kommentars sehen, wenn ich die gesetzliche mindest Mittagszeit unterschreite
4. Ich möchte als User Pausen in mm eintragen können.
5. Ich möchte als User eine Warnmeldung als Kommentar bekommen, wenn meine maximale Wochenarbeitszeit 45h überschritten ist 
6. Ich möchte mich als User bei der Verwendung des Tools mittels ID und Nachname authentifizieren 
7. Als Vorgesetzter will ich Ende des Monats oder der Woche einen Repport erstellen können über die Arbeitszeiten meiner Mitarbeiter 
8. Als minderjähriger Mitarbeiter darf ich nicht über 9h arbeiten und keine Nacht- oder Wochenendarbeit machen, damit die Jugendarbeitsschutzgesetze eingehalten werden. Ausnahmen können begründet vorkommen oder es können nachträglich die Zeiten korrigiert werden

## 🧩 Use Cases
- Authentifizieren mittels ID und Nachnahmen
- Arbeitszeiten und Pausen eingeben  
- Eingaben validieren  
- Zeitrapport auf Wochen- und Monatsbasis ausgeben  
- Kommentare bei Regelverletzungen anzeigen
- Unterschiedliche Menüs für Mitarbeiter und Vorgesetzte

### Main Use Cases
- Zeit erfassen (Mitarbeiter)  
- Zeiterfassung überprüfen (Vorgesetzter)  

### Actors
- Mitarbeiter  
- Vorgesetzter

---

### Wireframes / Mockups

#### Mockup: Login
![Wireframes – Home/Transactions](wtcalculator/docs/ui-images/login_rough.png)

#### Mockup: CSV Import
![Wireframes – Home/Transactions](wtcalculator/docs/ui-images/csv_import_rough.png)

#### Mockup: Ansicht Vorgesetzter
![Wireframes – Home/Transactions](wtcalculator/docs/ui-images/entries_rough.png)


---

## 🏛️ Architecture *in progress*

![UML Class Diagram](wtcalculator/docs/ui-images/UML-diagram.png)

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

#### Klare Trennung zwischen Daten und Logik
User, TimeEntry, MonthlyReport und WorkTimeResult enthalten Daten. Die Services übernehmen die Verarbeitung und greifen auf diese Klassen zu.

#### Service-orientierte Struktur
Jede Service-Klasse hat eine klar abgegrenzte Aufgabe: Authentifizierung, Benutzerverwaltung, Zeiterfassung oder Reporting.

#### Berechnungslogik ausgelagert
Die Berechnung der Arbeitszeit ist im TimeCalculator gekapselt. Dadurch bleibt TimeEntryService übersichtlich und delegiert die Berechnung an eine eigene Klasse.

---
### Patterns Used
---

#### Service Pattern
AuthService, UserService, TimeEntryService und ReportService kapseln die Anwendungslogik.

#### Repository / DAO Ansatz über Session
Alle Services verwenden eine _session, um Daten zu lesen, zu speichern oder zu verwalten. Dadurch ist der Datenzugriff von der restlichen Logik getrennt.

#### Model Relationship
User und TimeEntry stehen in einer 1:n-Beziehung. Ein Benutzer kann viele Zeiteinträge haben, ein Zeiteintrag gehört zu genau einem Benutzer.

#### DTO / Result Objects
MonthlyReport und WorkTimeResult dienen als einfache Rückgabeobjekte für Reports und Berechnungsergebnisse.

---

## 🗄️ Database and ORM

![ER Diagram](wtcalculator/docs/ui-images/ER_Modell.png)

The application uses **SQLModel** to map domain objects to a SQLite database.

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

> 🚧 Requirements act as a contract: implement and demonstrate each point below.

Each app must meet the following criteria in order to be accepted (see also the official project guidelines PDF on Moodle):

1. Using NiceGUI for building an interactive web app
2. Data validation in the app
3. Using an ORM for database management

---

### 1. Browser-based App (NiceGUI)

> 🚧 In this section, document how your project fulfills each criterion.

Die Applikation interagiert mit dem User via browser. Users können:

- Sich einloggen
- Ihre Arbeitszeit erfassen
- Kommentare erhalten, wenn die Arbeitszeit der Validierung widerspricht
- Arbeitszeitrapporte generieren (bspw. für Vorgesetzte)

**Architecture note (per SS26 guidelines):** the browser is a thin client; UI state + business logic live on the server-side NiceGUI app.

---

### 2. Daten Überprüfung

- **user validation:** Der user gibt seine ID und Nachnamen ein. Das Check-In prüft, ob beide Eingaben gemäss jscon-Dictionary (Mitarbeiterdaten) übereinstimmen. ID muss aus Zahlen bestehen, Name aus Buchstaben

- **age validation:** Ist der User minderjährig, erhält er Kommentare bei Tagesarbeitszeit über 9h, bei Nachtarbeit (22:00-06:00) und bei Wochenendarbeit

- **time input validation:** Die Arbeitszeit darf nur im Format hh:mm erfasst werden

- **break validation:** Der user gibt seine Pausenzeiten in mm ein. Ohne Mittagspause wird das gesetzliche Minimum von 30min abgezogen, ausser es wird Nachtarbeit erkannt

- **work time validation:** Die vorgesehene Arbeitszeit ist 42h. Alles darüber gilt als Überstunden. Nicht vorgesehen aber nicht verboten sind Überstunden ab 45h

- **input validation:** Diverse Eingaben im Check-In und im Menü werden auf das Format geprüft, bei Bedarf korrigiert (Gross-/Kleinschreibung) oder bei falscher Eingabe kommentiert und zur neuen Eingabe aufgefordert

---

### 3. Database Management *in progress*

All relevant data is managed via an ORM (e.g. SQLModel or SQLAlchemy). For the pizza example this includes users, pizzas, and orders.

---

## ⚙️ Implementation

### Technology
- Python 3.x
- Umgebung: GitHub Codespaces
- Keine externen libraries

### Libraries Used
- `datetime: datetime, timedelta`: benutzt für Datums- und Zeiteingaben und für berechnen des Deltas
- `re`: benutzt für die Input Validierung
- `csv`: benutzt um .csv files zu lesen oder zu schreiben
- `json`: benutzt um users.json file zu lesen
- `shutil`: benutzt um Dateien zwischen Ordner "geprüft" und "ungeprüft" zu verschieben
- `pathlib: path`: benutzt um zu prüfen, ob ein file existiert und den Dateipfad zu verwalten
- `os`: benutzt um json-file zu finden, auch wenn es in in einem anderen Pfad ist

Diese libraries sind Teil der Python Standard Library, es müssen keine externen installiert werden.
Sie wurden gewählt, um die spezifischen Anforderungen des Programms zu ermöglichen und es stabil zu machen.

### 📂 Repository Structure *in progress*
```Working-Time-Calculator/
data folder
reports/
├── working / ungeprüft 			 # Ordner für ungeprüfte .csv reports
	/Hübner
	├── 2025_10_003_huebnerm.csv     # Beispiel eines Monatsreports (output file)
	├── 2025_11_003_huebnerm.csv     # Beispiel eines Monatsreports (output file)
	├── 2025_12_003_huebnerm.csv     # Beispiel eines Monatsreports (output file)
	/Müller
	├── 2025_10_001_muellerh.csv     # Beispiel eines Monatsreports (output file)
	├── 2025_11_001_muellerh.csv     # Beispiel eines Monatsreports (output file)
	├── 2025_12_001_muellerh.csv     # Beispiel eines Monatsreports (output file)
	/Suter
	├── 2025_10_002_suterp.csv		# Beispiel eines Monatsreports (output file)
	├── 2025_11_002_suterp.csv     	# Beispiel eines Monatsreports (output file)
	├── 2025_12_002_suterp.csv     	# Beispiel eines Monatsreports (output file)
├── working / geprüft				# Ordner für geprüfte .csv reports
programms
├── calculate_working_time.py 		# Berechnet die Zeit, meiste Validierungen
├── checkin.py            			# User Authentifizierung mit ID und Nachname
├── menu1_5.py             			# Menu für die Auswahl der Interkation
├── reports.py						# Generierung der Reports 
├── user_admin.py					# Administration der Benutzerdaten
├── users.json						# Dictionary mit den Benutzerdaten
└── README.md           			# Projektbeschreibung
```
### How to Run *in progress*

### 1. Project Setup
- Python 3.13 (or the course version) is required
- Create and activate a virtual environment:
   - **macOS/Linux:**
      ```bash
      python3 -m venv .venv
      source .venv/bin/activate
      ```
   - **Windows:**
      ```bash
      python -m venv .venv
      .venv\Scripts\Activate
      ```
- Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 2. Configuration
- E.g., setup of parameters or environment variables

### 3. Launch
- Start the NiceGUI app (example):
   ```bash
   py -m pizza_app
   ```
- Open the URL printed in the console.

### 4. Usage

Zeiterfassung als Mitarbeiter:
1. Öffne **Visual Studio Code**
2. Öffne **Terminal**
3. Starte Programm:	source .venv/bin/activate python main.py
4. Authentifizieren als Benutzer
	#### Benutzerübersicht
 | ID  | Nachname      | Rolle       |
 | --- | ------------- | ----------- |
 | 001 | Müller        | Mitarbeiter |
 | 002 | Suter         | Mitarbeiter |
 | 003 | Hübner		(u18) | Mitarbeiter |
 | 004 | Ackermann     | Vorgesetzer |
5. Erfasse Arbeitszeit, lade eine .csv-Datei hoch oder schau dir deinen Rapport an

Einstieg als Vorgesetzter (nach Schritt 4):
1. Mutiere Mitarbeiter-Daten
2. Prüfe Arbeitszeit der Mitarbeitenden

> 🚧 Add UI screenshots of the main screens (or a short video link):

![UI – Mitarbeiter-Startseite](wtcalculator/docs/ui-images/startseite_ma1.png)
![UI – Zeiterfassung](wtcalculator/docs/ui-images/zeiterfassung.png)

---

## 🧪 Testing

### Running Tests

```bash
# Install pytest (if not already installed)
pip install pytest

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=wtcalculator
```

### Test Structure

```
tests/
├── conftest.py                 # Pytest fixtures (test database, sample users)
├── test_time_calculator.py     # Domain logic tests (net hours, minor rules, overtime)
├── test_time_entry_service.py  # Service layer tests (CRUD, weekly/monthly hours)
├── test_app_controler.py      # Controller tests (validation, parsing)
└── test_ui_employee_dashboard.py  # UI import tests, constants validation
```

### Test Coverage

- **Unit tests**: Time calculation logic, date/time parsing, user validation
- **Service tests**: TimeEntry CRUD, weekly/monthly hour calculations, approvals
- **Controller tests**: Input validation, error handling
- **Constants tests**: Verification of rule constants (45h weekly max, 30min break min, etc.)

**Current test count**: 39 passing, 4 skipped (UI imports skipped due to NiceGUI Python 3.14 compatibility)

---

## 👥 Team & Contributions

| Name               | Contribution                                                                                                                                                                                                                              |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Flavio Waser       | NiceGUI UI, Anpassung des Hauptcodes auf objektorientierte Programmierung                                                                 |
| Kristina Schaffner | Readme-File inkl. Grafiken, Passwort-Design, optimieren, Code review agent                                                                        |
| Mika Leuenberger   | Ausführung für Mac optimieren, Programmstart |


## 🤝 Contributing

> 🚧 This is a template repository for student projects.  
> 🚧 Do not change this section in your final submission.

- Use this repository as a starting point by importing it into your own GitHub account.  
- Work only within your own copy — do not push to the original template.  
- Commit regularly to track your progress.

## 📝 License

This project is provided for **educational use only** as part of the Programming Foundations module.  
[MIT License](LICENSE)
