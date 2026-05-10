import customtkinter as ctk
from ui.settings_window import SettingsWindow

class MainWindow(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.geometry("1600x900")
        self.title("Client Sorter")

#        self.schedule_parser = None
#        self.lunch_parser = None
        self.settings_window = None
        self.create_ui()

    def create_ui(self):

        # верхняя панель
        top_frame = ctk.CTkFrame(self, height=50)
        top_frame.pack(fill="x", padx=10, pady=10)

        # кнопка настроек
        settings_button = ctk.CTkButton(
            top_frame,
            text="⚙",
            width=40,
            height=40,
            font=("Arial", 20),
            command=self.open_settings
        )
        settings_button.pack(side="left", padx=5, pady=5)

    def open_settings(self):

        # если окно уже открыто — просто вывести поверх
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self)
        else:
            self.settings_window.focus()
