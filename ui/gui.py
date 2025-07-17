import customtkinter
from settings.user_settings import UserSettings
from scheduler import task_manager

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.settings = UserSettings(filepath='settings.json')
        self.title("IOC Webcrawler - Konfiguration & Dashboard")
        self.geometry("800x700")
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
        settings_tab.grid_columnconfigure(1, weight=1)

        # --- Sektion 1: Quell-URLs ---
        self.label_sources = customtkinter.CTkLabel(settings_tab, text="Quell-URLs (eine pro Zeile)",
                                                    font=customtkinter.CTkFont(size=14, weight="bold"))
        self.label_sources.grid(row=0, column=0, columnspan=2, padx=20, pady=(10, 5), sticky="w")
        self.textbox_sources = customtkinter.CTkTextbox(settings_tab, height=150)
        self.textbox_sources.grid(row=1, column=0, columnspan=2, padx=20, pady=5, sticky="ew")
        self.button_save_sources = customtkinter.CTkButton(settings_tab, text="Quellen speichern",
                                                           command=self.save_sources_event)
        self.button_save_sources.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="w")

        # --- Sektion 2: Blacklist ---
        self.label_blacklist = customtkinter.CTkLabel(settings_tab,
                                                      text="Blacklist (Keywords in URLs ignorieren, eine pro Zeile)",
                                                      font=customtkinter.CTkFont(size=14, weight="bold"))
        self.label_blacklist.grid(row=3, column=0, columnspan=2, padx=20, pady=(10, 5), sticky="w")
        self.textbox_blacklist = customtkinter.CTkTextbox(settings_tab, height=100)
        self.textbox_blacklist.grid(row=4, column=0, columnspan=2, padx=20, pady=5, sticky="ew")
        self.button_save_blacklist = customtkinter.CTkButton(settings_tab, text="Blacklist speichern",
                                                             command=self.save_blacklist_event)
        self.button_save_blacklist.grid(row=5, column=0, padx=20, pady=(10, 20), sticky="w")

        # --- Sektion 3: Scheduler ---
        self.label_scheduler = customtkinter.CTkLabel(settings_tab, text="Geplante Ausführung (Scheduler)",
                                                      font=customtkinter.CTkFont(size=14, weight="bold"))
        self.label_scheduler.grid(row=6, column=0, columnspan=2, padx=20, pady=(20, 5), sticky="w")
        scheduler_frame = customtkinter.CTkFrame(settings_tab, fg_color="transparent")
        scheduler_frame.grid(row=7, column=0, columnspan=2, padx=20, sticky="ew")
        self.switch_scheduler = customtkinter.CTkSwitch(scheduler_frame, text="Aktiviert")
        self.switch_scheduler.grid(row=0, column=0, padx=(0, 20))
        days = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
        self.optionmenu_day = customtkinter.CTkOptionMenu(scheduler_frame, values=days)
        self.optionmenu_day.grid(row=0, column=1, padx=(0, 10))
        times = [f"{h:02d}:00" for h in range(24)]
        self.optionmenu_time = customtkinter.CTkOptionMenu(scheduler_frame, values=times)
        self.optionmenu_time.grid(row=0, column=2, padx=(0, 20))
        self.button_save_schedule = customtkinter.CTkButton(settings_tab, text="Zeitplan anwenden",
                                                            command=self.save_schedule_event)
        self.button_save_schedule.grid(row=8, column=0, padx=20, pady=10, sticky="w")

    def load_settings_into_gui(self):
        """Lädt alle Einstellungen aus dem Objekt in die GUI-Felder."""
        print("[GUI] Lade aktuelle Einstellungen in die Ansicht.")
        self.textbox_sources.delete("1.0", "end")
        self.textbox_sources.insert("1.0", "\n".join(self.settings.source_urls))

        self.textbox_blacklist.delete("1.0", "end")
        self.textbox_blacklist.insert("1.0", "\n".join(self.settings.blacklist_keywords))

        schedule_settings = self.settings.schedule
        self.optionmenu_day.set(schedule_settings.get('day', 'Montag'))
        self.optionmenu_time.set(schedule_settings.get('time', '17:00'))

        if schedule_settings.get('enabled', False):
            self.switch_scheduler.select()
        else:
            self.switch_scheduler.deselect()

    def save_sources_event(self):
        """Liest nur die Quell-URLs aus der Textbox und speichert sie."""
        print("Button 'Quellen speichern' geklickt.")
        urls_from_textbox = self.textbox_sources.get("1.0", "end").strip()
        self.settings.source_urls = [line.strip() for line in urls_from_textbox.split("\n") if line.strip()]
        self.settings.save()

    def save_blacklist_event(self):
        """Liest nur die Blacklist-Keywords aus der Textbox und speichert sie."""
        print("Button 'Blacklist speichern' geklickt.")
        blacklist_from_textbox = self.textbox_blacklist.get("1.0", "end").strip()
        self.settings.blacklist_keywords = [line.strip() for line in blacklist_from_textbox.split("\n") if line.strip()]
        self.settings.save()

    def save_schedule_event(self):
        """Liest die Scheduler-Werte, speichert sie und wendet den Zeitplan an."""
        print("Button 'Zeitplan anwenden' geklickt.")
        day = self.optionmenu_day.get()
        time = self.optionmenu_time.get()
        is_enabled = self.switch_scheduler.get() == 1

        self.settings.schedule['day'] = day
        self.settings.schedule['time'] = time
        self.settings.schedule['enabled'] = is_enabled
        self.settings.save()

        success = task_manager.manage_schedule(day, time, is_enabled)
        if success:
            print("GUI: Betriebssystem-Aufgabe erfolgreich verwaltet.")
        else:
            print("GUI: Fehler bei der Verwaltung der Betriebssystem-Aufgabe.")


if __name__ == "__main__":
    app = App()
    app.mainloop()