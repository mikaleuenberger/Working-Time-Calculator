# 📊🔢 WTCalculator – Working Time Calculator (Console)

> 
## 📝 Analyse

**Problem**
> Für kleinere Firmen ist das Erfassen der Arbeitszeiten ein essentieller Prozess.  
Kommerzielle Lösungen wie SAP sind jedoch teuer. Mit unserer App bieten wir eine **einfache und kostengünstige Alternative** zur Arbeitszeiterfassung.

**Scenario**
In unserer Python Appikation sollen Arbeitszeiten erfasst und ausgewertet werden können. Ein User kann Arbeitsbeginn und Arbeitsende als Uhrzeiten erfassen und die Pausen als Stunden/Minuten Input.
Ausgewertet wird die Brutto und die Netto Arbeitszeit. Und die Monatliche Übersicht kann als Liste in der Konsole ausgegeben werden. 
Die ausgerechneten Zeiten werden mit bestimmten Rules, die festgelegt sind, abgeglichen. Beispiele sind hier: Maximalarbeitszeiten (Max Überstundenanzahl), Einhaltung der Mittags-Pausenzeit (Keine Pausen unter 30 Minuten)
Der Mitarbeiter soll ich die Möglichkeit haben, sein Alter einmalig zu hinterlegen, damit die für ihn gültigen Regeln automatisch angewendet werden.

**User stories:**
1. Als User möchte ich meine Arbeitszeit exakt eingeben (stempeln) (hh:mm:ss) 
2. Ich möchte meine Tages-, Wochen- und Monatsarbeitszeit auf dem Blatt sehen (entweder Stand jetzt inkl. verbleibende Soll-Arbeitszeit oder Eingabe einzelner Tage und Auswertung des ganzen Monats mit bestehenden Daten) 
3. Als User möchte ich eine Fehlermeldung, wenn ich die gesetzliche mindest Mittagszeit unterschreitet 
4. Ich möchte als User Pausen in mm eintragen können, diese Eingabe ist jedoch optional 
5. Ich möchte als User sehen, wie viele Überstunden ich habe (ab Wochenarbeitszeit 42h) 
6. Ich möchte als User eine Warnmeldung bekommen, wenn meine maximale Wochenarbeitszeit 45h überschritten ist 
7. Ich möchte mich als User Authentifizieren (als Nickname) können bei der Verwendung des Tools, mit Personalnummer oder ähnl. 
8. Als Vorgesetzter will ich Ende des Monats oder der Woche einen Repport erstellen können über die Arbeitszeiten meiner Mitarbeiter.  
9. Als minderjähriger Mitarbeiter möchte ich nicht über 9h arbeiten und keine Nacht- oder Wochenendarbeit erfassen können, damit die Jugendarbeitsschutzgesetze automatisch eingehalten werden.

**Use cases:**
- Benutzernamen und Alter erfassen  
- Arbeitszeiten und Pausen eingeben  
- Eingaben validieren  
- Zeitrapport auf Monatsbasis ausgeben  
- Kommentare bei Regelverletzungen anzeigen


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
- Name des Users eingeben
- Zeiteingabe
- Eingabe von Pausen
- Eingabe des Alters
- Input Überprüfung: gemäss Data Validation
- Ausgabe meines Zeitrapports auf Monatsbasis
- Kommentare bei Verletzungen der Vorgaben

---


### 2. Daten Überprüfung

Die Applikation prüft den Upload der user-Datei und Dateneingabe.

- **file selection:** Der user muss ein .csv file eingeben, alle anderen Datei-Typen werden nicht unterstützt und mit einer Fehlermeldung abgeblockt.

- **day validation:** Der user muss als Wochentage "Montag, Dienstag, Mittwoch, Donnerstag, Freitag, Samstag oder Sonntag" eingeben, alle anderen Eingaben werden nicht unterstützt und mit einer Fehlermeldung abgeblockt.

- **user validation:** Der user gibt seinen nickname ein, welcher nur aus Buchstaben bestehen darf

- **age validation:** Der user gibt sein Alter ein, welche nur ganze Zahlen sein können und für <=18 spezielle Bedingungen gelten: Arbeitszeit pro Tag max. 9h, keine Arbeit an Wochenenden, keine Arbeit nach 21:00 Uhr

- **time input validation:** Die Arbeitszeit darf nur im Format hh:mm erfasst werden

- **break validation:** Der user gibt seine Pausenzeiten in mm ein, wobei diese nicht zu Arbeitsbeginn oder Ende sein dürfen. Weiter muss die Mittagspause >=30min sein.

- **work time validation:** Die vorgesehene Arbeitszeit ist 42h. Alles darüber gilt als Überstunden, vorgesehen aber nicht verboten sind Überstunden ab 45h.

### 3. File Processing

Die Applikation liest und schreibt Daten mit dem Input file:

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
		- Der Output dient dem Mitarbeiter wie auch dem Vorgesetzen als Übersicht über die geleistete Arbeitsstunden, den Gleitzeitssaldo sowie der Einhaltung gesetzlicher Vorgaben. 

## ⚙️ Implementation
> ⚠️ Dieser Abschnitt ist noch in Bearbeitung und folgt in der finalen Version des Dokuments.

### Technology
- Python 3.x
- Environment: GitHub Codespaces
- No external libraries

### 📂 Repository Structure
> 🚧 Beschreibung folgt noch..

```text
Working Time Calculator/
├── main.py             # main program logic (console application)
├── wtc.csv	            # working time (input data file)
├── oct2025_001.csv     # example of monthly report (output file)
├── docs/               # optional screenshots or project documentation
└── README.md           # project description and milestones
```

### How to Run
> 🚧 Beschreibung folgt noch..
1. Open the repository in **GitHub Codespaces**
2. Open the **Terminal**
3. Run:
	```bash
	python3 main.py
	```

### Libraries Used
> 🚧 Beschreibung folgt noch..
- `os`: Used for file and path operations, such as checking if the menu file exists and creating new files.
- `glob`: Used to find all invoice files matching a pattern (e.g., `invoice_*.txt`) to determine the next invoice number.

These libraries are part of the Python standard library, so no external installation is required. They were chosen for their simplicity and effectiveness in handling file management tasks in a console application.


## 👥 Team & Contributions
> 🚧 Die genauen Beteiligungen der einzelnen Mitglieder folgt noch..

| Name               | Contribution |
| ------------------ | ------------ |
| Flavio Waser       | ..           |
| Kristina Schaffner | ..           |
| Mika Leuenberger   | ..           |


## 🤝 Contributing

> 🚧 This is a template repository for student projects.  
> 🚧 Do not change this section in your final submission.

- Use this repository as a starting point by importing it into your own GitHub account.  
- Work only within your own copy — do not push to the original template.  
- Commit regularly to track your progress.

## 📝 License

This project is provided for **educational use only** as part of the Programming Foundations module.  
[MIT License](LICENSE)
