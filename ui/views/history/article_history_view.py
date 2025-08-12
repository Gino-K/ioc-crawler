import customtkinter


class ArticleHistoryView(customtkinter.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master, fg_color="transparent")
        self.controller = controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        filter_frame = customtkinter.CTkFrame(self)
        filter_frame.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="ew")

        self.domain_menu = customtkinter.CTkOptionMenu(filter_frame, values=["Alle"],
                                                       command=lambda _: self.controller.perform_search())
        self.domain_menu.pack(side="left", padx=10, pady=10)

        self.search_entry = customtkinter.CTkEntry(filter_frame, placeholder_text="Keyword in URL suchen...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        self.search_entry.bind("<Return>", lambda event: self.controller.perform_search())

        self.search_button = customtkinter.CTkButton(filter_frame, text="Suchen", width=100,
                                                     command=self.controller.perform_search)
        self.search_button.pack(side="left", padx=5, pady=10)

        header_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=1, column=0, padx=20, pady=0, sticky="ew")
        header_frame.grid_columnconfigure(0, weight=3)
        header_frame.grid_columnconfigure(1, weight=1)

        headers = [("URL", "url"), ("Zuletzt gescannt", "last_scanned")]
        for i, (text, col_id) in enumerate(headers):
            button = customtkinter.CTkButton(header_frame, text=text, fg_color="gray25",
                                             font=customtkinter.CTkFont(weight="bold"),
                                             command=lambda c=col_id: self.controller.sort_results(c))
            button.grid(row=0, column=i, padx=(0, 1), sticky="ew")

        self.results_frame = customtkinter.CTkScrollableFrame(self)
        self.results_frame.grid(row=2, column=0, padx=20, pady=(5, 10), sticky="nsew")
        self.results_frame.grid_columnconfigure(0, weight=3)
        self.results_frame.grid_columnconfigure(1, weight=1)

    def get_domain_filter(self):
        return self.domain_menu.get()

    def get_keyword_filter(self):
        return self.search_entry.get()

    def set_domains(self, domains):
        self.domain_menu.configure(values=domains)

    def reset_filters(self):
        """Setzt die UI-Filterelemente auf ihren Standardzustand zurueck."""
        self.domain_menu.set("Alle")
        self.search_entry.delete(0, "end")

    def display_results(self, results):
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        if not results:
            label = customtkinter.CTkLabel(self.results_frame, text="Keine Eintraege gefunden.")
            label.pack(pady=10)
            return

        for i, item in enumerate(results):
            url_label = customtkinter.CTkLabel(self.results_frame, text=item.url, anchor="w")
            url_label.grid(row=i, column=0, padx=5, pady=3, sticky="ew")

            date_str = item.last_scanned.strftime('%Y-%m-%d %H:%M:%S')
            date_label = customtkinter.CTkLabel(self.results_frame, text=date_str, anchor="w")
            date_label.grid(row=i, column=1, padx=5, pady=3, sticky="ew")