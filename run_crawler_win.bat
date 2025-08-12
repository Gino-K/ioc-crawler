@echo
cd /D "%~dp0"

echo [BATCH] Aktiviere Virtual Environment...
call venv\Scripts\activate

echo [BATCH] Starte Crawler-Skript...
python crawler\crawler_orch.py

echo [BATCH] Crawler-Skript beendet.
