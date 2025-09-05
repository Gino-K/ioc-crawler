#!/bin/bash
# ===================================================================
#  Shell-Skript zur Erstellung einer .desktop-Verknuepfung
#  fuer den IOC Webcrawler unter Linux.
# ===================================================================

echo "Erstelle Verknuepfung fuer IOC Crawler auf dem Desktop..."

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

SHORTCUT_NAME="ioc-crawler.desktop"
DESKTOP_PATH="${HOME}/Desktop"
SHORTCUT_PATH="${DESKTOP_PATH}/${SHORTCUT_NAME}"
PYTHON_EXECUTABLE="${SCRIPT_DIR}/venv/bin/python"
PROJECT_ROOT="${SCRIPT_DIR}"

if [ ! -f "$PYTHON_EXECUTABLE" ]; then
    echo "FEHLER: Python-Executable nicht im venv gefunden unter: $PYTHON_EXECUTABLE"
    echo "Stelle sicher, dass das virtuelle Environment 'venv' existiert."
    exit 1
fi

cat > "$SHORTCUT_PATH" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=IOC Crawler
Comment=Startet den IOC Webcrawler
Exec=${PYTHON_EXECUTABLE} -m ui.gui
Path=${PROJECT_ROOT}
Icon=utilities-terminal
Terminal=false
EOF

chmod +x "$SHORTCUT_PATH"

echo "Verknuepfung '${SHORTCUT_NAME}' erfolgreich auf dem Desktop erstellt."
echo ""
echo "WICHTIGER HINWEIS:"
echo "Je nach Desktop-Umgebung musst du eventuell mit der rechten Maustaste auf die neue Verknuepfung klicken und 'Starten erlauben' (oder eine aehnliche Option) auswaehlen, damit sie funktioniert."
