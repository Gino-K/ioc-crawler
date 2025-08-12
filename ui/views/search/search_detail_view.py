import customtkinter


class SearchDetailView(customtkinter.CTkToplevel):
    def __init__(self, master, ioc_data, controller):
        super().__init__(master)

        self.ioc_data = ioc_data
        self.controller = controller
        self.title(f"Details für IOC: {ioc_data.value}")
        self.geometry("700x500")
        self.transient(master)

        main_frame = customtkinter.CTkFrame(self)
        main_frame.pack(fill="x", padx=10, pady=10)

        customtkinter.CTkLabel(main_frame, text="Wert:", font=customtkinter.CTkFont(weight="bold")).grid(row=0,
                                                                                                         column=0,
                                                                                                         sticky="w",
                                                                                                         padx=5)
        value_box = customtkinter.CTkTextbox(main_frame, height=10, activate_scrollbars=False, wrap="none")
        value_box.insert("1.0", ioc_data.value)
        value_box.configure(state="disabled", fg_color="transparent", border_width=0)
        value_box.grid(row=0, column=1, sticky="w")

        customtkinter.CTkLabel(main_frame, text="Typ:", font=customtkinter.CTkFont(weight="bold")).grid(row=1, column=0,
                                                                                                        sticky="w",
                                                                                                        padx=5)
        customtkinter.CTkLabel(main_frame, text=ioc_data.type).grid(row=1, column=1, sticky="w")

        scroll_frame = customtkinter.CTkScrollableFrame(self,
                                                        label_text=f"{len(ioc_data.sightings)} Sichtung(en) gefunden")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        for i, sighting in enumerate(ioc_data.sightings):
            sighting_frame = customtkinter.CTkFrame(scroll_frame, fg_color=("gray85", "gray19"))
            sighting_frame.pack(fill="x", pady=5, padx=5)

            info_text = (
                f"Quelle: {sighting.source_article_url}\n"
                f"Zeitstempel: {sighting.sighting_timestamp}\n"
                f"Kontext: {sighting.context_snippet}\n"
            )

            if sighting.apts:
                info_text += f"Assoziierte APTs: {', '.join([apt.name for apt in sighting.apts])}\n"
            if sighting.countries:
                info_text += f"Assoziierte Länder: {', '.join([c.name for c in sighting.countries])}\n"
            if sighting.cves:
                info_text += f"Assoziierte CVEs: {', '.join([cve.name for cve in sighting.cves])}\n"

            details_box = customtkinter.CTkTextbox(sighting_frame, wrap="word", activate_scrollbars=False)
            details_box.insert("1.0", info_text)
            details_box.configure(state="disabled", height=(info_text.count('\n') + 1) * 20)
            details_box.pack(anchor="w", padx=10, pady=10, fill="x")

            false_positive_button = customtkinter.CTkButton(
                self,
                text="False-Positiv",
                fg_color="#D32F2F",
                hover_color="#B71C1C",
                command=lambda: self.controller.mark_as_false_positive(self.ioc_data)
            )
            false_positive_button.pack(side="bottom", pady=10, padx=10)
