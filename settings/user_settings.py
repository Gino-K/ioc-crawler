import json
from pathlib import Path

LAST_PRELOAD_KEY = 'last_preload_timestamp'

def _find_project_root():
    """Findet das Projekt-Hauptverzeichnis, indem es nach der .gitignore-Datei sucht."""
    current_path = Path(__file__).resolve()
    while not (current_path / '.gitignore').exists():
        if current_path.parent == current_path:
            return Path.cwd()
        current_path = current_path.parent
    return current_path

class UserSettings:
    """
    Verwaltet die Benutzereinstellungen durch Laden und Speichern
    aus einer zentralen JSON-Datei.
    """

    def __init__(self):
        self.last_preload_timestamp = None
        project_root = _find_project_root()
        self.filepath = project_root / "settings" / "crawler_settings.json"

        self.source_urls = [
            "https://www.bleepingcomputer.com/",
            "https://thehackernews.com/",
            "https://blog.talosintelligence.com/"
        ]
        self.blacklist_keywords = ["/offer/", "/deals/"]
        self.schedule = {"day": "Montag", "time": "17:00", "enabled": False}

        self.export_formats = {
            "json": True,
            "csv": True,
            "stix": True
        }

        self.load()

    def load(self):
        """Laedt die Einstellungen aus der JSON-Datei."""
        try:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)

            with open(self.filepath, 'r', encoding='utf-8') as f:
                settings_data = json.load(f)

                self.source_urls = settings_data.get('source_urls', self.source_urls)
                self.blacklist_keywords = settings_data.get('blacklist_keywords', self.blacklist_keywords)
                self.schedule = settings_data.get('schedule', self.schedule)
                self.last_preload_timestamp = settings_data.get(LAST_PRELOAD_KEY, None)
                self.export_formats = settings_data.get('export_formats', self.export_formats)
                print(f"[UserSettings] Einstellungen erfolgreich aus '{self.filepath}' geladen.")

        except FileNotFoundError:
            print(
                f"[UserSettings] WARNUNG: Einstellungsdatei '{self.filepath}' nicht gefunden. Erstelle eine neue mit Standardwerten.")
            self.save()
        except json.JSONDecodeError:
            print(f"[UserSettings] FEHLER: Einstellungsdatei '{self.filepath}' ist fehlerhaft. Verwende Standardwerte.")
        except Exception as e:
            print(f"[UserSettings] Ein unerwarteter Fehler ist beim Laden der Einstellungen aufgetreten: {e}")

    def save(self):
        """Speichert die aktuellen Einstellungen in die JSON-Datei."""
        settings_data = {
            'source_urls': self.source_urls,
            'blacklist_keywords': self.blacklist_keywords,
            'schedule': self.schedule,
            'last_preload_timestamp': self.last_preload_timestamp,
            'export_formats': self.export_formats,
            LAST_PRELOAD_KEY: self.last_preload_timestamp
        }
        try:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)

            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=4, ensure_ascii=False)
            print(f"[UserSettings] Einstellungen erfolgreich in '{self.filepath}' gespeichert.")
        except Exception as e:
            print(f"[UserSettings] FEHLER beim Speichern der Einstellungen: {e}")

    def add_to_whitelist(self, ioc_value: str, ioc_type: str):
        """Fuegt einen IOC-Wert zur passenden Liste in der whitelist.json hinzu."""
        project_root = _find_project_root()
        whitelist_path = project_root / "settings" / "whitelist.json"

        key = ""
        if ioc_type in ["domain", "url"]:
            key = "domains"
        elif ioc_type in ["ipv4"]:
            key = "ips"
        elif ioc_type == "file":
            key = "files"
        elif ioc_type == "email":
            key = "emails"
        elif ioc_type == "md5":
            key = "md5"
        elif ioc_type == "sha1":
            key = "sha1"
        elif ioc_type == "sha256":
            key = "sha256"
        else:
            print(f"[UserSettings] Whitelist fuer IOC-Typ '{ioc_type}' nicht unterstuetzt.")
            return

        try:
            with open(whitelist_path, 'r', encoding='utf-8') as f:
                whitelist_data = json.load(f)

            if ioc_value.lower() not in [item.lower() for item in whitelist_data.get(key, [])]:
                whitelist_data.setdefault(key, []).append(ioc_value)
                print(f"[UserSettings] Fuege '{ioc_value}' zur Whitelist ('{key}') hinzu.")
            else:
                print(f"[UserSettings] '{ioc_value}' ist bereits auf der Whitelist.")
                return

            with open(whitelist_path, 'w', encoding='utf-8') as f:
                json.dump(whitelist_data, f, indent=2, ensure_ascii=False)

        except FileNotFoundError:
            print(f"[UserSettings] FEHLER: Konnte '{whitelist_path}' nicht finden.")
        except Exception as e:
            print(f"[UserSettings] FEHLER beim Aktualisieren der Whitelist: {e}")
