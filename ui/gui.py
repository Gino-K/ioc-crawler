import customtkinter
from settings.user_settings import UserSettings

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.settings = UserSettings(filepath='settings.json')

        self.title("IOC Webcrawler - Konfiguration & Dashboard")
        self.geometry("800x600")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tabview = customtkinter.CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.tabview.add("Dashboard")
        self.tabview.add("Einstellungen")
        self.tabview.tab("Dashboard").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Einstellungen").grid_columnconfigure(0, weight=1)

        self.dashboard_label = customtkinter.CTkLabel(self.tabview.tab("Dashboard"),
                                                      text="Dashboard-Inhalte werden hier in Zukunft angezeigt.",
                                                      font=customtkinter.CTkFont(size=16))
        self.dashboard_label.grid(row=0, column=0, padx=20, pady=20)

        self.setup_settings_tab()

        self.load_settings_into_gui()

    def setup_settings_tab(self):
        settings_tab = self.tabview.tab("Einstellungen")

        # --- Sektion 1: Quell-URLs verwalten ---
        self.label_sources = customtkinter.CTkLabel(settings_tab, text="Quell-URLs (eine pro Zeile)",
                                                    font=customtkinter.CTkFont(size=14, weight="bold"))
        self.label_sources.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        self.textbox_sources = customtkinter.CTkTextbox(settings_tab, width=400, height=150)
        self.textbox_sources.grid(row=1, column=0, columnspan=2, padx=20, pady=5, sticky="ew")
        self.button_load_sources = customtkinter.CTkButton(settings_tab, text="Quellen laden",
                                                           command=self.load_sources_button_event)
        self.button_load_sources.grid(row=2, column=0, padx=(20, 10), pady=10, sticky="w")
        self.button_save_sources = customtkinter.CTkButton(settings_tab, text="Quellen speichern",
                                                           command=self.save_sources_button_event)
        self.button_save_sources.grid(row=2, column=1, padx=(10, 20), pady=10, sticky="w")

        # --- Sektion 2: Scheduler konfigurieren ---
        self.label_scheduler = customtkinter.CTkLabel(settings_tab, text="Geplante Ausführung (Scheduler)",
                                                      font=customtkinter.CTkFont(size=14, weight="bold"))
        self.label_scheduler.grid(row=3, column=0, padx=20, pady=(20, 5), sticky="w")

        days = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
        self.optionmenu_day = customtkinter.CTkOptionMenu(settings_tab, values=days)
        self.optionmenu_day.grid(row=4, column=0, padx=(20, 10), pady=5, sticky="w")

        times = [f"{h:02d}:00" for h in range(24)]
        self.optionmenu_time = customtkinter.CTkOptionMenu(settings_tab, values=times)
        self.optionmenu_time.grid(row=4, column=1, padx=(10, 20), pady=5, sticky="w")
        self.optionmenu_time.set("17:00")  # Setze einen Standardwert

        self.button_save_schedule = customtkinter.CTkButton(settings_tab, text="Zeitplan speichern",
                                                            command=self.save_schedule_button_event)
        self.button_save_schedule.grid(row=5, column=0, padx=20, pady=10, sticky="w")

        # --- Sektion 3: Blacklist / Whitelist ---
        self.label_blacklist = customtkinter.CTkLabel(settings_tab, text="Blacklist (zu ignorierende Keywords in URLs)",
                                                      font=customtkinter.CTkFont(size=14, weight="bold"))
        self.label_blacklist.grid(row=6, column=0, padx=20, pady=(20, 5), sticky="w")

        self.textbox_blacklist = customtkinter.CTkTextbox(settings_tab, width=400, height=80)
        self.textbox_blacklist.grid(row=7, column=0, columnspan=2, padx=20, pady=5, sticky="ew")

    def load_settings_into_gui(self):
        """Lädt die aktuellen Einstellungen aus dem Objekt in die GUI-Felder."""
        print("[GUI] Lade aktuelle Einstellungen in die Ansicht.")
        self.textbox_sources.delete("1.0", "end")
        self.textbox_sources.insert("1.0", "\n".join(self.settings.source_urls))

        # Lade die Blacklist (Beispiel)
        # self.textbox_blacklist.delete("1.0", "end")
        # self.textbox_blacklist.insert("1.0", "\n".join(self.settings.blacklist_keywords))

        # Lade den Zeitplan (Beispiel)
        # self.optionmenu_day.set(self.settings.schedule['day'])
        # self.optionmenu_time.set(self.settings.schedule['time'])

    def load_sources_button_event(self):
        """Lädt die Einstellungen aus der Datei neu und aktualisiert die GUI."""
        self.settings.load()
        self.load_settings_into_gui()
        print("Button 'Quellen laden' geklickt. Einstellungen aus Datei neu geladen.")

    def save_sources_button_event(self):
        """Liest die Daten aus der GUI, aktualisiert das Settings-Objekt und speichert es."""
        urls_from_textbox = self.textbox_sources.get("1.0", "end").strip()
        self.settings.source_urls = [line.strip() for line in urls_from_textbox.split("\n") if line.strip()]

        self.settings.save()
        print("Button 'Quellen speichern' geklickt. URLs wurden in settings.json gespeichert.")

    def save_schedule_button_event(self):
        print("Button 'Zeitplan speichern' geklickt.")


if __name__ == "__main__":
    app = App()
    app.mainloop()