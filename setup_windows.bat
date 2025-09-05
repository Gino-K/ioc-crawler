@echo off
echo ==========================================================
echo  IOC Webcrawler - Setup
echo ==========================================================
echo.

python --version >nul 2>nul
if %errorlevel% neq 0 (
    echo FEHLER: Python scheint nicht im System-PATH gefunden zu werden.
    echo Bitte installiere Python 3 (https://www.python.org/) und starte das Skript erneut.
    pause
    exit /b 1
)

echo [1/4] Erstelle eine virtuelle Python-Umgebung im Ordner 'venv'...
python -m venv venv
if %errorlevel% neq 0 (
    echo FEHLER beim Erstellen der virtuellen Umgebung.
    pause
    exit /b 1
)
echo      ...Erfolgreich.
echo.

echo [2/4] Aktiviere die virtuelle Umgebung...
call venv\Scripts\activate
echo      ...Erfolgreich.
echo.

echo [3/4] Installiere alle benoetigten Bibliotheken aus requirements.txt...
echo      Dies kann einen Moment dauern.
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo FEHLER beim Installieren der Bibliotheken.
    echo Bitte ueberpruefe die Internetverbindung und die requirements.txt.
    pause
    exit /b 1
)
echo      ...Alle Bibliotheken erfolgreich installiert.
echo.

echo [4/4] Erstelle Desktop-Verknuepfung...
powershell -ExecutionPolicy Bypass -File create_shortcut.ps1
echo      ...Erfolgreich.
echo.

echo ==========================================================
echo  Setup abgeschlossen!
echo ==========================================================
echo Du kannst die Anwendung jetzt ueber die neue Verknuepfung
echo auf deinem Desktop starten.
echo.
pause