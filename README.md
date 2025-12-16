# 📊🔢 WTCalculator – Working Time Calculator (Console)

> 
## 📝 Analyse

**Problem**
> Für kleinere Firmen ist das Erfassen der Arbeitszeiten ein essentieller Prozess.  
Kommerzielle Lösungen wie SAP sind jedoch teuer. Mit unserer App bieten wir eine **einfache und kostengünstige Alternative** zur Arbeitszeiterfassung.

**Scenario**
In unserer Python Appikation sollen Arbeitszeiten erfasst und ausgewertet werden können. Ein User kann Arbeitsbeginn und Arbeitsende als Uhrzeiten erfassen und die Pausen als Stunden/Minuten Input. Ausgewertet wird die Brutto und die Netto Arbeitszeit. 
Die ausgerechneten Zeiten werden mit bestimmten Rules, die festgelegt sind, abgeglichen. Beispiele sind hier: Maximalarbeitszeiten (Max Überstundenanzahl), Einhaltung der Mittags-Pausenzeit (Keine Pausen unter 30 Minuten).
Der Vorgesetzte kann die Mitarbeiter-Daten pflegen (wie bspw. das Alter), damit die gültigen Regeln (z.B. Jugendschutzgesetz) automatisch angewendet werden.

**User stories:**
1. Als User möchte ich meine Arbeitszeit exakt eingeben (hh:mm) 
2. Ich möchte meine Tages-, Wochen- und Monatsarbeitszeit auf dem Blatt sehen (Eingabe einzelner Tage und Auswertung der Woche oder des Monats mit bestehenden Daten) 
3. Als User möchte ich eine Fehlermeldung in Form eines Kommentars sehen, wenn ich die gesetzliche mindest Mittagszeit unterschreite
4. Ich möchte als User Pausen in mm eintragen können.
5. Ich möchte als User eine Warnmeldung als Kommentar bekommen, wenn meine maximale Wochenarbeitszeit 45h überschritten ist 
6. Ich möchte mich als User bei der Verwendung des Tools mittels ID und Nachname authentifizieren 
7. Als Vorgesetzter will ich Ende des Monats oder der Woche einen Repport erstellen können über die Arbeitszeiten meiner Mitarbeiter 
8. Als minderjähriger Mitarbeiter darf ich nicht über 9h arbeiten und keine Nacht- oder Wochenendarbeit machen, damit die Jugendarbeitsschutzgesetze eingehalten werden. Ausnahmen können begründet vorkommen oder es können nachträglich die Zeiten korrigiert werden

**Use cases:**
- Authentifizieren mittels ID und Nachnahmen
- Arbeitszeiten und Pausen eingeben  
- Eingaben validieren  
- Zeitrapport auf Wochen- und Monatsbasis ausgeben  
- Kommentare bei Regelverletzungen anzeigen
- Unterschiedliche Menüs für Mitarbeiter und Vorgesetzte


---

## ✅ Projekt Anforderungen

Jede Applikation muss die folgenden 3 Kriterien erfüllen, um akzeptiert zu werden (gemäss Guidelines auf Moodle):

1. Interaktive Applikation (console input)
2. Datenvalidierung (input checking)
3. Dateiverarbeitung (read/write)

---

### 1. Interaktive Applikation

---
Die Applikation interagiert mit dem User in der Konsole. Der User kann in der App:
- Nachname und ID des Users eingeben
- Zeiteingabe
- Eingabe von Pausen
- Input Überprüfung: gemäss Data Validation
- Ausgabe meines Zeitrapports auf Monatsbasis
- Kommentare bei Verletzungen der Vorgaben

---


### 2. Daten Überprüfung

- **user validation:** Der user gibt seine ID und Nachnamen ein. Das Check-In prüft, ob beide Eingaben gemäss jscon-Dictionary (Mitarbeiterdaten) übereinstimmen. ID muss aus Zahlen bestehen, Name aus Buchstaben

- **age validation:** Ist der User minderjährig, erhält er Kommentare bei Tagesarbeitszeit über 9h, bei Nachtarbeit (22:00-06:00) und bei Wochenendarbeit

- **time input validation:** Die Arbeitszeit darf nur im Format hh:mm erfasst werden

- **break validation:** Der user gibt seine Pausenzeiten in mm ein. Ohne Mittagspause wird das gesetzliche Minimum von 30min abgezogen, ausser es wird Nachtarbeit erkannt

- **work time validation:** Die vorgesehene Arbeitszeit ist 42h. Alles darüber gilt als Überstunden. Nicht vorgesehen aber nicht verboten sind Überstunden ab 45h

- **input validation:** Diverse Eingaben im Check-In und im Menü werden auf das Format geprüft, bei Bedarf korrigiert (Gross-/Kleinschreibung) oder bei falscher Eingabe kommentiert und zur neuen Eingabe aufgefordert

### 3. File Processing

Die Applikation liest und schreibt Daten mit bestehenden .csv-Dateien als Grundlage für die letzten Zeiterfassungen:

- **Input file:** `arbeitszeiterfassung.csv` — Enthält die Zeiteingaben des Benutzers, ein Tag pro Zeile im Format `Wochentag;Arbeitsbeginn;Pause;Arbeitsende;Zeitsaldo`.
	- Beispiel:
		```
		06.10.2025;Montag;08:20;20;12:00;12:45;17:30
		07.10.2025;Dienstag;07:35;20;11:45;13:00;17:00
		08.10.2025;Mittwoch;07:35;20;11:45;13:00;17:00
		```
	- Die Applikation liest die Daten zu Beginn, um die Validierunug sowie den Rapport auszuführen.

- **Output file:** `arbeitszeitrapport.csv` — Enthält die Zeiteingabe des Benutzers des Monats inkl. Kommentare gemäss Validierung (Über-, Minusstunden und der Berücksichtigung der gesetztlichen Vorschriften).

	- Beispiel:
		```
		Mitarbeiter #001
		----------------------
		Datum:			Wochentag:				Arbeitszeit		Kommentar					Kummulierter Saldo
		06.10.2025		Montag					08:24										08:24
		07.10.2025		Dienstag				08:24			Mittagszeit unterschritten	16:48
		08.10.2025		Mittwoch				09:24			Arbeitszeit über 9h			26:12


		!Achtung: 07.10.2025 Mittagszeit unterschritten!
		!Achtung: 08.10.2025 Arbeitszeit Minderjährige überschritten!
		----------------------
		Total:                  26:12
		Monats-Soll:            168:00
		Gleitzeit-Saldo:        -142.28
		```
		- Der Output dient dem Vorgesetzen als Übersicht über die geleistete Arbeitsstunden, den Gleitzeitssaldo sowie der Einhaltung gesetzlicher Vorgaben. 
		- Der Mitarbeiter bekommt kein Output-File, sondern die Wochen- und Monatsübersicht direkt in der Konsole

## ⚙️ Implementation

### Technology
- Python 3.x
- Umgebung: GitHub Codespaces
- Keine externen libraries

### 📂 Repository Structure
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
### How to Run
1. Öffne das repository in **GitHub Codespaces**
2. Öffne **Terminal**
3. Starte Programm:	python3 checkin.py
4. Authentifizieren als Benutzer
	#### Benutzerübersicht
 | ID  | Nachname      | Rolle       |
 | --- | ------------- | ----------- |
 | 001 | Müller        | Mitarbeiter |
 | 002 | Suter         | Mitarbeiter |
 | 003 | Hübner		(u18) | Mitarbeiter |
 | 004 | Ackermann     | Vorgesetzer |

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


## 👥 Team & Contributions

| Name               | Contribution                                                                                                                                                                                                                              |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Flavio Waser       | Menü für Mitarbeiter und Vorgesetzte, Erstellen der Monatsrapports als .csv-File oder Ausgabe in Konsole je nach Rolle, Mutation der Mitarbeiter-Daten durch Vorgesetzten                                                                 |
| Kristina Schaffner | User-File, Check-In, Validierung Minderjährige, automatischer Abzug Mittagszeit, Validierung Wochenarbeitszeit über 45h, Überprüfung und Überarbeitung Readme-File                                                                        |
| Mika Leuenberger   | Zeiterfassung, Verschieben der Dateien nach Prüfung durch Vorgesetzten, diverse Validierungen bei Eingabe der Daten (Datum, Wochentage, Erkennung ob Woche über Monatsende geht, maximale Tagesarbeitszeit 12h, Mittagspause mind. 30min) |


## 🤝 Contributing

> 🚧 This is a template repository for student projects.  
> 🚧 Do not change this section in your final submission.

- Use this repository as a starting point by importing it into your own GitHub account.  
- Work only within your own copy — do not push to the original template.  
- Commit regularly to track your progress.

## 📝 License

This project is provided for **educational use only** as part of the Programming Foundations module.  
[MIT License](LICENSE)
