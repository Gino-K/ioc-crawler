import customtkinter


class SourceURLView(customtkinter.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master, fg_color="transparent")
        self.controller = controller

        self.label_sources = customtkinter.CTkLabel(self, text="Quell-URLs (eine pro Zeile)",
                                                    font=customtkinter.CTkFont(size=14, weight="bold"))
        self.label_sources.pack(anchor="w", padx=0, pady=(0, 5))

        self.textbox_sources = customtkinter.CTkTextbox(self, height=150)
        self.textbox_sources.pack(fill="x", expand=True)

        self.button_save_sources = customtkinter.CTkButton(self, text="Quellen speichern",
                                                           command=self.controller.save_sources)
        self.button_save_sources.pack(anchor="w", pady=(10, 0))

    def get_urls(self):
        urls_text = self.textbox_sources.get("1.0", "end").strip()
        return [line.strip() for line in urls_text.split("\n") if line.strip()]

    def set_urls(self, urls):
        self.textbox_sources.delete("1.0", "end")
        self.textbox_sources.insert("1.0", "\n".join(urls))