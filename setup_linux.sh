#!/bin/bash

echo "=========================================================="
echo " IOC Webcrawler - Setup fuer Linux"
echo "=========================================================="
echo ""

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR" || exit

if ! command -v python3 &> /dev/null
then
    echo "FEHLER: python3 konnte nicht gefunden werden."
    echo "Bitte installiere Python 3 (z.B. mit 'sudo apt install python3 python3-venv') und starte das Skript erneut."
    exit 1
fi
echo "[1/8] Python 3 gefunden."
echo ""

echo "[2/8] ueberpruefe auf venv-Abhaengigkeit..."
if ! python3 -m venv --help &> /dev/null; then
    echo "     ...python3-venv nicht gefunden. Versuche automatische Installation."
    sudo apt update
    sudo apt install -y python3-venv
    if [ $? -ne 0 ]; then
        echo "     FEHLER: Konnte python3-venv nicht automatisch installieren."
        echo "     Bitte installiere es manuell (z.B. mit 'sudo apt install python3-venv') und starte das Skript erneut."
        exit 1
    fi
fi
echo "     ...Erfolgreich."
echo ""

echo "[3/8] ueberpruefe auf GUI-Abhaengigkeit (tkinter)..."
if ! python3 -c "import tkinter" &> /dev/null; then
    echo "     ...tkinter nicht gefunden. Versuche automatische Installation (erfordert sudo-Passwort)."
    sudo apt update
    sudo apt install -y python3-tk
    if [ $? -ne 0 ]; then
        echo "     FEHLER: Konnte python3-tk nicht automatisch installieren."
        echo "     Bitte installiere es manuell mit 'sudo apt install python3-tk' und starte das Skript erneut."
        exit 1
    fi
fi
echo "     ...Erfolgreich."
echo ""

echo "[4/8] Erstelle eine virtuelle Python-Umgebung im Ordner 'venv'..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "FEHLER beim Erstellen der virtuellen Umgebung."
    exit 1
fi
echo "     ...Erfolgreich."
echo ""

echo "[5/8] Aktiviere die virtuelle Umgebung..."
source venv/bin/activate
echo "     ...Erfolgreich."
echo ""

echo "[6/8] Installiere alle benoetigten Bibliotheken aus requirements.txt..."
echo "     Dies kann einen Moment dauern."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "FEHLER beim Installieren der Bibliotheken."
    echo "Bitte ueberpruefe die Internetverbindung und die requirements.txt."
    exit 1
fi
echo "     ...Alle Bibliotheken erfolgreich installiert."
echo ""

echo "[7/8] Mache benoetigte Skripte ausfuehrbar..."
chmod +x run_crawler_lin.sh
echo "     ...Erfolgreich."
echo ""

echo "[8/8] Erstelle Desktop-Verknuepfung..."
DESKTOP_FILE="$HOME/Desktop/ioc_crawler.desktop"
PYTHON_EXE="$SCRIPT_DIR/venv/bin/python"

echo "[Desktop Entry]
Version=1.0
Name=IOC Crawler
Comment=Startet den IOC Webcrawler
Exec=\"$PYTHON_EXE\" -m ui.gui
Path=$SCRIPT_DIR
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Utility;" > "$DESKTOP_FILE"

chmod +x "$DESKTOP_FILE"

echo "     ...Verknuepfung '$DESKTOP_FILE' erfolgreich erstellt."
echo ""

deactivate

echo "=========================================================="
echo " Setup abgeschlossen!"
echo "=========================================================="
echo "Du kannst die Anwendung jetzt ueber die neue Verknuepfung"
echo "auf deinem Desktop starten."
echo ""