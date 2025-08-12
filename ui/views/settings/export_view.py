import customtkinter


class ExportSettingsView(customtkinter.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller

        self.label = customtkinter.CTkLabel(self, text="Dateiexport-Formate",
                                            font=customtkinter.CTkFont(size=14, weight="bold"))
        self.label.pack(anchor="w", pady=(0, 10))

        switch_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        switch_frame.pack(fill="x")

        self.switch_json = customtkinter.CTkSwitch(switch_frame, text="JSON")
        self.switch_json.pack(side="left", padx=(0, 20))

        self.switch_csv = customtkinter.CTkSwitch(switch_frame, text="CSV")
        self.switch_csv.pack(side="left", padx=(0, 20))

        self.switch_stix = customtkinter.CTkSwitch(switch_frame, text="STIX 2.1")
        self.switch_stix.pack(side="left")

        self.button_save = customtkinter.CTkButton(self, text="Export-Einstellungen speichern",
                                                   command=self.controller.save_export_settings)
        self.button_save.pack(anchor="w", pady=(20, 0))

    def get_settings(self) -> dict:
        """Gibt den aktuellen Status der Schalter als Dictionary zurück."""
        return {
            "json": self.switch_json.get() == 1,
            "csv": self.switch_csv.get() == 1,
            "stix": self.switch_stix.get() == 1,
        }

    def set_settings(self, export_formats: dict):
        """Setzt den Status der Schalter basierend auf einem Dictionary."""
        if export_formats.get("json"):
            self.switch_json.select()
        else:
            self.switch_json.deselect()

        if export_formats.get("csv"):
            self.switch_csv.select()
        else:
            self.switch_csv.deselect()

        if export_formats.get("stix"):
            self.switch_stix.select()
        else:
            self.switch_stix.deselect()