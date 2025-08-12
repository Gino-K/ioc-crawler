#!/bin/bash
cd "$(dirname "$0")" || exit

echo "[SHELL] Aktiviere Virtual Environment..."
source venv/bin/activate

echo "[SHELL] Starte Crawler-Skript..."
python crawler/crawler_orch.py

echo "[SHELL] Crawler-Skript beendet."