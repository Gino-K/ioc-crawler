@echo off
setlocal enabledelayedexpansion

set "PROJECT_ROOT=%~dp0"

set "YEAR=%date:~-4%"
set "MONTH=%date:~-7,2%"
set "LOG_DIR=%PROJECT_ROOT%crawler_log\win\!YEAR!\!MONTH!"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

set "CURRENT_TIME=%time: =0%"
set "CURRENT_TIME=%CURRENT_TIME::=-%"
set "LOGFILE=%LOG_DIR%\crawler_log_%date:~-4%-%date:~-7,2%-%date:~-10,2%_%CURRENT_TIME:~0,8%.txt"

echo [BATCH] Versuche, in folgende Log-Datei zu schreiben: %LOGFILE%

set "PYTHON_EXE=%PROJECT_ROOT%venv\Scripts\python.exe"
set "CRAWLER_MODULE=crawler.crawler_orch"

if not exist "%PYTHON_EXE%" (
    echo [BATCH] FEHLER: Python Executable nicht gefunden unter: %PYTHON_EXE%
    echo [BATCH] Stelle sicher, dass das Virtual Environment existiert und korrekt eingerichtet ist.
    pause
    exit /b 1
)

(
    echo [BATCH] Log-Sitzung gestartet um %date% %time%
    echo.
    echo [BATCH] Projekt-Root: %PROJECT_ROOT%
    echo [BATCH] Python Executable: %PYTHON_EXE%
    echo [BATCH] Crawler Modul: %CRAWLER_MODULE%
    echo.

    set "PYTHONPATH=%PROJECT_ROOT%"
    echo [BATCH] PYTHONPATH gesetzt auf: !PYTHONPATH!
    echo.

    echo [BATCH] Starte Crawler-Skript...

    "%PYTHON_EXE%" -m %CRAWLER_MODULE%

    echo.
    echo [BATCH] Crawler-Skript beendet.

) >> "%LOGFILE%" 2>&1

echo.
echo [BATCH] Skriptausfuehrung beendet. Pruefe die Log-Datei: %LOGFILE%
exit 0