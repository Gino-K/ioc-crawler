#!/bin/bash
cd "$(dirname "$0")" || exit

YEAR=$(date +%Y)
MONTH=$(date +%m)
LOG_DIR="crawler_log/lin/$YEAR/$MONTH"

mkdir -p "$LOG_DIR"

TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
LOGFILE="$LOG_DIR/crawler_log_$TIMESTAMP.txt"

echo "[SHELL] Versuche, in folgende Log-Datei zu schreiben: $LOGFILE"

PROJECT_ROOT=$(pwd)
PYTHON_EXE="$PROJECT_ROOT/venv/bin/python"
CRAWLER_MODULE="crawler.crawler_orch"

if [ ! -f "$PYTHON_EXE" ]; then
    echo "[SHELL] FEHLER: Python Executable nicht gefunden unter: $PYTHON_EXE"
    echo "[SHELL] Stelle sicher, dass das Virtual Environment existiert und korrekt eingerichtet ist."
    read -p "Drücke eine beliebige Taste zum Beenden..."
    exit 1
fi

{
    echo "[SHELL] Log-Sitzung gestartet am $(date)"
    echo ""
    echo "[SHELL] Projekt-Root: $PROJECT_ROOT"
    echo "[SHELL] Python Executable: $PYTHON_EXE"
    echo "[SHELL] Crawler Modul: $CRAWLER_MODULE"
    echo ""

    export PYTHONPATH="$PROJECT_ROOT"
    echo "[SHELL] PYTHONPATH gesetzt auf: $PYTHONPATH"
    echo ""

    echo "[SHELL] Starte Crawler-Skript..."

    "$PYTHON_EXE" -m "$CRAWLER_MODULE"

    echo ""
    echo "[SHELL] Crawler-Skript beendet."

} >> "$LOGFILE" 2>&1

echo "[SHELL] Skriptausführung beendet. Prüfe die Log-Datei: $LOGFILE"
exit 0