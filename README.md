# Setup

## Erstellen der Desktop-Verknüpfung (Windows)

Um die Anwendung einfach zu starten, kannst du eine Desktop-Verknüpfung erstellen, die das Programm mit den richtigen Einstellungen ausführt.

1.  **PowerShell als Administrator öffnen:**
    * Öffne das Windows-Startmenü, tippe `PowerShell`, mache einen Rechtsklick auf "Windows PowerShell" und wähle "Als Administrator ausführen".

2.  **Ausführungsrichtlinie einmalig anpassen (falls nötig):**
    * Führe den folgenden Befehl in der Admin-PowerShell aus. Dies erlaubt das Ausführen von lokal erstellten Skripten.
      ```powershell
      Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
      ```

3.  **Skript ausführen:**
    * Navigiere in der PowerShell zum Hauptverzeichnis dieses Projekts.
      ```powershell
      cd "C:\Pfad\zum\Webcrawler"
      ```
    * Führe das Setup-Skript aus:
      ```powershell
      .\create_desktop_shortcut_win.ps1
      ```

4.  **Verknüpfung für Admin-Rechte konfigurieren:**
    * Nach dem Ausführen des Skripts hast du eine neue "IOC Crawler"-Verknüpfung auf deinem Desktop.
    * Mache einen Rechtsklick auf diese Verknüpfung -> **Eigenschaften**.
    * Gehe zum Tab "Verknüpfung" -> **Erweitert...** -> Setze den Haken bei **"Als Administrator ausführen"**.

Fertig! Du kannst die Anwendung jetzt immer über diese Verknüpfung starten.

## Erstellen der Desktop-Verknüpfung (Linux)

Um die Anwendung einfach über den Desktop zu starten, kannst du ein Shell-Skript ausführen, das eine `.desktop`-Verknüpfung erstellt.

1.  **Terminal öffnen:**
    * Öffne ein Terminal-Fenster.

2.  **Skript ausführbar machen:**
    * Navigiere zum Hauptverzeichnis dieses Projekts.
      ```bash
      cd /pfad/zu/deinem/Webcrawler
      ```
    * Mache das Setup-Skript mit dem folgenden Befehl ausführbar:
      ```bash
      chmod +x create_shortcut.sh
      ```

3.  **Skript ausführen:**
    * Führe das Skript aus:
      ```bash
      ./create_shortcut.sh
      ```

4.  **Verknüpfung vertrauen (falls nötig):**
    * Nach dem Ausführen des Skripts hast du eine neue "IOC Crawler"-Verknüpfung auf deinem Desktop.
    * Bei den meisten modernen Linux-Desktops musst du diese neue Verknüpfung als vertrauenswürdig markieren. Mache einen **Rechtsklick** darauf und wähle **"Starten erlauben"** (oder eine ähnliche Option).

Fertig! Du kannst die Anwendung jetzt immer über diese Verknüpfung starten. Admin-Rechte werden unter Linux anders gehandhabt; die Anwendung sollte bei Bedarf (z.B. zum Einrichten eines Cron-Jobs) nach deinem Passwort fragen.
