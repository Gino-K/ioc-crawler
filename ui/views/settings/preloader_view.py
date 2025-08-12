import customtkinter


class PreloaderView(customtkinter.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller

        self.label = customtkinter.CTkLabel(self, text="Daten-Aktualisierung",
                                            font=customtkinter.CTkFont(size=14, weight="bold"))
        self.label.pack(anchor="w", pady=(0, 10))

        button_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x")

        self.button_tlds = customtkinter.CTkButton(button_frame, text="TLDs aktualisieren",
                                                   command=self.controller.run_tld_preloader)
        self.button_tlds.pack(side="left", padx=(0, 10))

        self.button_countries = customtkinter.CTkButton(button_frame, text="Länder aktualisieren",
                                                        command=self.controller.run_country_preloader)
        self.button_countries.pack(side="left", padx=(0, 10))

        self.button_apts = customtkinter.CTkButton(button_frame, text="MITRE APTs aktualisieren",
                                                   command=self.controller.run_apt_preloader)
        self.button_apts.pack(side="left", padx=(0, 10))

        self.button_all = customtkinter.CTkButton(self, text="Alle Daten aktualisieren",
                                                  command=self.controller.run_all_preloaders)
        self.button_all.pack(anchor="w", pady=(20, 0))