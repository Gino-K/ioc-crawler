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
        subprocess.run(command, shell=True, check=True, capture_output=True, text=True, encoding='utf-8')
        print("ERFOLG: Die geplante Windows-Aufgabe wurde erfolgreich erstellt oder aktualisiert.")
        return True
    except subprocess.CalledProcessError as e:
        print("FEHLER: Die geplante Windows-Aufgabe konnte nicht erstellt werden.")
        print(f"Fehlermeldung (stderr): {e.stderr}")
        print("\n>>> WICHTIG: Wurde die Anwendung mit Administratorrechten ausgeführt? <<<")
        return False
    except FileNotFoundError:
        print("FEHLER: 'schtasks.exe' wurde nicht gefunden. Dieses Skript ist nur für Windows geeignet.")
        return False


def delete_windows_task() -> bool:
    """Löscht die geplante Aufgabe aus dem Windows Task Scheduler."""
    print(f"Windows erkannt. Versuche, die Aufgabe '{WINDOWS_TASK_NAME}' zu löschen...")
    command = f'schtasks /Delete /TN "{WINDOWS_TASK_NAME}" /F'
    try:
        subprocess.run(command, shell=True, check=True, capture_output=True, text=True, encoding='utf-8')
        print("ERFOLG: Die geplante Windows-Aufgabe wurde gelöscht.")
        return True
    except subprocess.CalledProcessError as e:
        # Fehlercode 1 bedeutet oft "Task nicht gefunden", was okay ist
        if e.returncode == 1:
            print("INFO: Geplante Aufgabe existierte nicht, nichts zu löschen.")
            return True
        print(f"FEHLER beim Löschen der Aufgabe: {e.stderr}")
        return False


def create_or_update_cron_job(day_of_week_num: int, time_str: str) -> bool:
    """
    Erstellt oder aktualisiert einen Cron-Job für Linux-Systeme.
    Liest die bestehende crontab aus, entfernt den alten Job und fügt den neuen hinzu.
    """
    print(f"Linux erkannt. Versuche, einen Cron-Job zu erstellen/aktualisieren...")

    hour, minute = time_str.split(':')

    command_to_run = f"{shlex.quote(PYTHON_EXECUTABLE_PATH)} {shlex.quote(MAIN_SCRIPT_PATH)}"
    new_cron_job = f"{minute} {hour} * * {day_of_week_num} {command_to_run} {CRON_JOB_MARKER}"

    print(f"\nNeuer Cron-Eintrag:\n{new_cron_job}\n")

    try:
        current_crontab = subprocess.run(['crontab', '-l'], capture_output=True, text=True, check=False).stdout

        new_crontab_lines = [line for line in current_crontab.splitlines() if CRON_JOB_MARKER not in line]

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


def delete_cron_job() -> bool:
    """Entfernt den Cron-Job aus der crontab des Benutzers."""
    print(f"Linux erkannt. Versuche, den Cron-Job zu löschen...")
    try:
        current_crontab = subprocess.run(['crontab', '-l'], capture_output=True, text=True, check=False).stdout
        new_crontab_lines = [line for line in current_crontab.splitlines() if CRON_JOB_MARKER not in line]

        if len(new_crontab_lines) == len(current_crontab.splitlines()):
            print("INFO: Kein Cron-Job mit dem Marker gefunden, nichts zu löschen.")
            return True

        if not new_crontab_lines:
            subprocess.run(['crontab', '-r'], check=True)
            print("ERFOLG: Der Cron-Job wurde gelöscht und die crontab war danach leer.")
        else:
            new_crontab_content = "\n".join(new_crontab_lines) + "\n"
            subprocess.run(['crontab', '-'], input=new_crontab_content, text=True, check=True)
            print("ERFOLG: Der Cron-Job wurde aus der crontab entfernt.")
        return True
    except Exception as e:
        print(f"FEHLER beim Löschen des Cron-Jobs: {e}")
        return False


def manage_schedule(day_of_week: str, time_str: str, enabled: bool) -> bool:
    """
    Hauptfunktion, die eine geplante Aufgabe erstellt, aktualisiert oder löscht.
    Wird von der GUI aufgerufen.
    """
    day_map_windows = {"Montag": "MON", "Dienstag": "TUE", "Mittwoch": "WED", "Donnerstag": "THU", "Freitag": "FRI", "Samstag": "SAT", "Sonntag": "SUN"}
    day_map_linux = {"Montag": 1, "Dienstag": 2, "Mittwoch": 3, "Donnerstag": 4, "Freitag": 5, "Samstag": 6, "Sonntag": 0} # Sonntag ist 0 für cron

    if day_of_week not in day_map_windows:
        print(f"FEHLER: Ungültiger Wochentag '{day_of_week}'.")
        return False

    # Automatische Systemerkennung
    if sys.platform == "win32":
        if enabled:
            return create_or_update_windows_task(day_map_windows[day_of_week], time_str)
        else:
            return delete_windows_task()
    elif sys.platform == "linux":
        if enabled:
            return create_or_update_cron_job(day_map_linux[day_of_week], time_str)
        else:
            return delete_cron_job()
    elif sys.platform == "darwin":
        print("HINWEIS: macOS wird derzeit für die automatische Erstellung von geplanten Aufgaben nicht unterstützt.")
        print("Bitte erstellen Sie den Cron-Job manuell, z.B. mit 'crontab -e'.")
        return False
    else:
        print(f"FEHLER: Unbekanntes Betriebssystem '{sys.platform}' wird nicht unterstützt.")
        return False
