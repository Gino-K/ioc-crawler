import customtkinter


class SchedulerView(customtkinter.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller

        self.label_scheduler = customtkinter.CTkLabel(self, text="Geplante Ausführung",
                                                      font=customtkinter.CTkFont(size=14, weight="bold"))
        self.label_scheduler.pack(anchor="w", pady=(0, 5))

        scheduler_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        scheduler_frame.pack(fill="x")

        self.switch_scheduler = customtkinter.CTkSwitch(scheduler_frame, text="Aktiviert")
        self.switch_scheduler.pack(side="left", padx=(0, 20))

        days = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
        self.optionmenu_day = customtkinter.CTkOptionMenu(scheduler_frame, values=days)
        self.optionmenu_day.pack(side="left", padx=(0, 10))

        times = [f"{h:02d}:00" for h in range(24)]
        self.optionmenu_time = customtkinter.CTkOptionMenu(scheduler_frame, values=times)
        self.optionmenu_time.pack(side="left")

        self.button_save_schedule = customtkinter.CTkButton(self, text="Zeitplan anwenden",
                                                            command=self.controller.save_schedule)
        self.button_save_schedule.pack(anchor="w", pady=(10, 0))

    def get_schedule_data(self):
        return {
            "day": self.optionmenu_day.get(),
            "time": self.optionmenu_time.get(),
            "enabled": self.switch_scheduler.get() == 1
        }

    def set_schedule_data(self, schedule_data):
        self.optionmenu_day.set(schedule_data.get('day', 'Montag'))
        self.optionmenu_time.set(schedule_data.get('time', '17:00'))
        if schedule_data.get('enabled', False):
            self.switch_scheduler.select()
        else:
            self.switch_scheduler.deselect()