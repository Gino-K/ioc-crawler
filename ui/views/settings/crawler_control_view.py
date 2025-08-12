import customtkinter

class CrawlerControlView(customtkinter.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller

        self.label = customtkinter.CTkLabel(self, text="Manueller Crawler Start",
                                            font=customtkinter.CTkFont(size=14, weight="bold"))
        self.label.pack(anchor="w", pady=(0, 10))

        self.button_run_crawler = customtkinter.CTkButton(
            self,
            text="Crawler jetzt starten",
            height=40,
            command=self.controller.run_crawler_manually
        )
        self.button_run_crawler.pack(fill="x")