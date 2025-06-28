import subprocess
import sys
import os
import shlex

# --- Pfade und Konstanten ---
PYTHON_EXECUTABLE_PATH = sys.executable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MAIN_SCRIPT_PATH = os.path.join(PROJECT_ROOT, 'crawler', 'main.py')

# Eindeutige Namen für die Aufgaben, um sie wiederzufinden
WINDOWS_TASK_NAME = "IOC_Webcrawler_Scheduled_Run"
CRON_JOB_MARKER = "# IOC_WEBCRAWLER_TASK"


def create_or_update_windows_task(day_of_week_str: str, time_str: str) -> bool:
    """Erstellt oder aktualisiert eine geplante Aufgabe im Windows Task Scheduler."""
    print(f"Windows erkannt. Versuche, die Aufgabe '{WINDOWS_TASK_NAME}' zu erstellen/aktualisieren...")

    command = (
        f'schtasks /Create /TN "{WINDOWS_TASK_NAME}" '
        f'/TR "\"{PYTHON_EXECUTABLE_PATH}\" \"{MAIN_SCRIPT_PATH}\"" '
        f'/SC WEEKLY /D {day_of_week_str} /ST {time_str} '
        f'/F /RL HIGHEST'
    )

    print(f"\nFühre folgenden Befehl aus:\n{command}\n")
    try:
        subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("ERFOLG: Die geplante Windows-Aufgabe wurde erfolgreich erstellt oder aktualisiert.")
        return True
    except subprocess.CalledProcessError as e:
        print("FEHLER: Die geplante Windows-Aufgabe konnte nicht erstellt werden.")
        print(f"Fehlermeldung (stderr): {e.stderr}")
        print("\n>>> WICHTIG: Wurde das Skript mit Administratorrechten ausgeführt? <<<")
        return False


def create_or_update_cron_job(day_of_week_num: int, time_str: str) -> bool:
    """
    Erstellt oder aktualisiert einen Cron-Job für Linux/macOS-ähnliche Systeme.
    Liest die bestehende crontab aus, entfernt den alten Job (falls vorhanden)
    und fügt den neuen hinzu.
    """
    print(f"Linux erkannt. Versuche, einen Cron-Job zu erstellen/aktualisieren...")

    hour, minute = time_str.split(':')

    command_to_run = f"{shlex.quote(PYTHON_EXECUTABLE_PATH)} {shlex.quote(MAIN_SCRIPT_PATH)}"
    new_cron_job = f"{minute} {hour} * * {day_of_week_num} {command_to_run} {CRON_JOB_MARKER}"

    print(f"\nNeuer Cron-Eintrag:\n{new_cron_job}\n")

    try:
        current_crontab = subprocess.run(['crontab', '-l'], capture_output=True, text=True, check=False)

        new_crontab_lines = []
        if current_crontab.returncode == 0:
            for line in current_crontab.stdout.splitlines():
                if CRON_JOB_MARKER not in line:
                    new_crontab_lines.append(line)

        new_crontab_lines.append(new_cron_job)

        new_crontab_content = "\n".join(new_crontab_lines) + "\n"

        subprocess.run(['crontab', '-'], input=new_crontab_content, text=True, check=True)

        print("ERFOLG: Der Cron-Job wurde erfolgreich erstellt oder aktualisiert.")
        return True

    except FileNotFoundError:
        print("FEHLER: 'crontab'-Befehl nicht gefunden. Ist dies ein Standard-Linux-System?")
        return False
    except subprocess.CalledProcessError as e:
        print("FEHLER: Der Cron-Job konnte nicht geschrieben werden.")
        print(f"Fehlermeldung (stderr): {e.stderr}")
        return False


def setup_scheduled_task(day_of_week: str, time_str: str) -> bool:
    """
    Hauptfunktion, die das Betriebssystem erkennt und die passende
    Scheduling-Methode aufruft.

    Args:
        day_of_week (str): Der deutsche Name des Wochentags (z.B. "Montag").
        time_str (str): Die Uhrzeit im HH:MM-Format (z.B. '17:00').

    Returns:
        bool: True bei Erfolg, sonst False.
    """
    day_map_windows = {"Montag": "MON", "Dienstag": "TUE", "Mittwoch": "WED", "Donnerstag": "THU", "Freitag": "FRI",
                       "Samstag": "SAT", "Sonntag": "SUN"}
    day_map_linux = {"Montag": 1, "Dienstag": 2, "Mittwoch": 3, "Donnerstag": 4, "Freitag": 5, "Samstag": 6,
                     "Sonntag": 7}

    if day_of_week not in day_map_windows:
        print(f"FEHLER: Ungültiger Wochentag '{day_of_week}'.")
        return False

    # Automatische Systemerkennung
    if sys.platform == "win32":
        return create_or_update_windows_task(day_map_windows[day_of_week], time_str)
    elif sys.platform == "linux":
        return create_or_update_cron_job(day_map_linux[day_of_week], time_str)
    elif sys.platform == "darwin":
        print("HINWEIS: macOS wird derzeit für die automatische Erstellung von geplanten Aufgaben nicht unterstützt.")
        print("Bitte erstellen Sie den Cron-Job manuell, z.B. mit 'crontab -e'.")
        return False
    else:
        print(f"FEHLER: Unbekanntes Betriebssystem '{sys.platform}' wird nicht unterstützt.")
        return False
