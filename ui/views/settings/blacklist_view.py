import customtkinter


class BlacklistView(customtkinter.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller

        self.label_blacklist = customtkinter.CTkLabel(self,
                                                      text="Blacklist (Keywords in URLs ignorieren, eine pro Zeile)",
                                                      font=customtkinter.CTkFont(size=14, weight="bold"))
        self.label_blacklist.pack(anchor="w", pady=(0, 5))

        self.textbox_blacklist = customtkinter.CTkTextbox(self, height=100)
        self.textbox_blacklist.pack(fill="x", expand=True)

        self.button_save_blacklist = customtkinter.CTkButton(self, text="Blacklist speichern",
                                                             command=self.controller.save_blacklist)
        self.button_save_blacklist.pack(anchor="w", pady=(10, 0))

    def get_keywords(self):
        keywords_text = self.textbox_blacklist.get("1.0", "end").strip()
        return [line.strip() for line in keywords_text.split("\n") if line.strip()]

    def set_keywords(self, keywords):
        self.textbox_blacklist.delete("1.0", "end")
        self.textbox_blacklist.insert("1.0", "\n".join(keywords))