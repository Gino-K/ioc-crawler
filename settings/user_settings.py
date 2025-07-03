import json

class UserSettings:
    """
    Verwaltet die Benutzereinstellungen durch Laden und Speichern
    aus einer zentralen JSON-Datei.
    """

    def __init__(self, filepath='settings.json'):
        self.filepath = filepath

        # Standardeinstellungen, falls keine Datei existiert
        self.source_urls = [
            "https://www.bleepingcomputer.com/",
            "https://thehackernews.com/",
            "https://blog.talosintelligence.com/"
        ]
        self.blacklist_keywords = ["/offer/", "/deals/"]
        self.schedule = {"day": "Montag", "time": "17:00", "enabled": False}

        self.load()

    def load(self):
        """Lädt die Einstellungen aus der JSON-Datei."""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                settings_data = json.load(f)

                self.source_urls = settings_data.get('source_urls', self.source_urls)
                self.blacklist_keywords = settings_data.get('blacklist_keywords', self.blacklist_keywords)
                self.schedule = settings_data.get('schedule', self.schedule)
                print(f"[UserSettings] Einstellungen erfolgreich aus '{self.filepath}' geladen.")

        except FileNotFoundError:
            print(
                f"[UserSettings] WARNUNG: Einstellungsdatei '{self.filepath}' nicht gefunden. Erstelle eine neue mit Standardwerten.")
            self.save()  # Speichere die Standardeinstellungen, um die Datei zu erstellen
        except json.JSONDecodeError:
            print(f"[UserSettings] FEHLER: Einstellungsdatei '{self.filepath}' ist fehlerhaft. Verwende Standardwerte.")
        except Exception as e:
            print(f"[UserSettings] Ein unerwarteter Fehler ist beim Laden der Einstellungen aufgetreten: {e}")

    def save(self):
        """Speichert die aktuellen Einstellungen in die JSON-Datei."""
        settings_data = {
            'source_urls': self.source_urls,
            'blacklist_keywords': self.blacklist_keywords,
            'schedule': self.schedule
        }
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=4, ensure_ascii=False)
            print(f"[UserSettings] Einstellungen erfolgreich in '{self.filepath}' gespeichert.")
        except Exception as e:
            print(f"[UserSettings] FEHLER beim Speichern der Einstellungen: {e}")
