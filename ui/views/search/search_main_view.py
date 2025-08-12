import customtkinter


class SearchView(customtkinter.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master, fg_color="transparent")
        self.controller = controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        filter_frame = customtkinter.CTkFrame(self)
        filter_frame.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="ew")
        ioc_types = ["Alle", "ipv4", "domain", "md5", "sha1", "sha256", "file", "email"]
        self.type_menu = customtkinter.CTkOptionMenu(filter_frame, values=ioc_types,
                                                     command=lambda _: self.controller.perform_search())
        self.type_menu.pack(side="left", padx=10, pady=10)
        self.search_entry = customtkinter.CTkEntry(filter_frame, placeholder_text="IOC-Wert suchen...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        self.search_entry.bind("<Return>", lambda event: self.controller.perform_search())
        self.search_button = customtkinter.CTkButton(filter_frame, text="Suchen",
                                                     command=self.controller.perform_search)
        self.search_button.pack(side="left", padx=10, pady=10)

        header_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=1, column=0, padx=20, pady=(0, 0), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=3)
        header_frame.grid_columnconfigure(1, weight=1)
        header_frame.grid_columnconfigure(2, weight=1)
        header_frame.grid_columnconfigure(3, weight=1)

        headers = [
            ("IOC-Wert", "ioc_value"), ("Typ", "type"),
            ("Quellen", "sources"), ("Letzte Sichtung", "last_sighting")
        ]
        for i, (header_text, column_id) in enumerate(headers):
            button = customtkinter.CTkButton(
                header_frame, text=header_text, fg_color="gray25",
                font=customtkinter.CTkFont(weight="bold"),
                command=lambda col=column_id: self.controller.sort_results(col)
            )
            button.grid(row=0, column=i, padx=(0, 1 if i < len(headers) - 1 else 0), pady=0, sticky="ew")

        self.results_frame = customtkinter.CTkScrollableFrame(self)
        self.results_frame.grid(row=2, column=0, padx=20, pady=(5, 10), sticky="nsew")

        self.results_frame.grid_columnconfigure(0, weight=3)
        self.results_frame.grid_columnconfigure(1, weight=1)
        self.results_frame.grid_columnconfigure(2, weight=1)
        self.results_frame.grid_columnconfigure(3, weight=1)

    def get_type_filter(self):
        return self.type_menu.get()

    def get_value_filter(self):
        return self.search_entry.get()

    def display_results(self, results):
        """Loescht und zeigt NUR die Datenzeilen im scrollbaren Frame an."""
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        if not results:
            label = customtkinter.CTkLabel(self.results_frame, text="Keine Ergebnisse fuer diese Suche gefunden.")
            label.pack(pady=10, padx=10)
            return


        for row_index, ioc in enumerate(results):
            last_sighting_date = "N/A"
            if ioc.sightings:
                last_sighting_ts = max(s.sighting_timestamp for s in ioc.sightings)
                last_sighting_date = last_sighting_ts.strftime('%Y-%m-%d')

            columns = [ioc.value, ioc.type, len(ioc.sightings), last_sighting_date]

            for col_index, col_text in enumerate(columns):
                cell = customtkinter.CTkLabel(self.results_frame, text=str(col_text), anchor="w")
                cell.grid(row=row_index, column=col_index, padx=5, pady=3, sticky="ew")

                cell.bind("<Button-1>", lambda event, ioc_id=ioc.id: self.controller.show_ioc_details(ioc_id))
                cell.bind("<Enter>", lambda e, c=cell: c.configure(font=customtkinter.CTkFont(underline=True)))
                cell.bind("<Leave>", lambda e, c=cell: c.configure(font=customtkinter.CTkFont(underline=False)))