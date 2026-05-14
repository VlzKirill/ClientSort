import customtkinter as ctk
from datetime import datetime
from ui.settings_window import SettingsWindow
from ui.staff_window import StaffWindow
from core.config_manager import ConfigManager
from ui.help_window import HelpWindow
from ui.main_table import MainTable
import tkinter.messagebox as mb

class MainWindow(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.DEFAULT_DATE_TEXT = "Выберите дату"

        self.geometry("1000x600")
        self.title("Client Sorter")

        self.config = ConfigManager.load()

        self.help_window = None
        self.settings_window = None
        self.staff_window = None
        self.selected_date = None
        self.date_menu = None
        self.main_table_frame = None

        self.create_ui()
        self.update_dates()

    def create_ui(self):

        # верхняя панель
        top_frame = ctk.CTkFrame(self, height=50)
        top_frame.pack(fill="x", padx=10, pady=10)

        # кнопка настроек
        settings_button = ctk.CTkButton(
            top_frame,
            text="⚙ Настройки",
            width=40,
            height=40,
            font=("Arial", 20),
            command=self.open_settings
        )
        settings_button.pack(side="left", padx=5, pady=5)

        #кнопка Персонала
        staff_button = ctk.CTkButton(
            top_frame,
            text="👥 Персонал",
            width=40,
            height=40,
            font=("Arial", 20),
            command=self.open_staff
        )
        staff_button.pack(side="left", padx=5, pady=5)

        # Выбор даты
        self.selected_date = ctk.StringVar(value=self.DEFAULT_DATE_TEXT)

        saved_dates = list(self.config.staff_state.keys())

        self.date_menu = ctk.CTkOptionMenu(
            top_frame,
            width=40,
            height=40,
            font=("Arial", 18),
            variable=self.selected_date,
            values=[self.DEFAULT_DATE_TEXT] + saved_dates
        )

        self.date_menu.pack(side="left", padx=10)

        #Кнопка распределить
        distribute_button = ctk.CTkButton(
            top_frame,
            text="Распределить",
            width=40,
            height=40,
            font=("Arial", 18),
            command=self.show_main_table
        )
        distribute_button.pack(side="left", padx=5, pady=5)

        # Кнопка справки
        help_button = ctk.CTkButton(
            top_frame,
            text="?",
            width=40,
            height=40,
            font=("Arial", 20),
            command=self.open_help
        )
        help_button.pack(side="right", padx=10)

    def open_settings(self):

        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self, self.config)
        else:
            self.settings_window.focus()

    def open_staff(self):

        if self.staff_window is None or not self.staff_window.winfo_exists():
            self.staff_window = StaffWindow(self, self.config)
        else:
            self.staff_window.focus()

    def open_help(self):
        if self.help_window is None or not self.help_window.winfo_exists():
            self.help_window = HelpWindow(self)
        else:
            self.help_window.focus()

    def sort_dates(self, date_list):
        valid_dates = []
        for d in date_list:
            try:
                # проверяем, можно ли распарсить
                datetime.strptime(d, "%d.%m")
                valid_dates.append(d)
            except ValueError:
                continue  # пропускаем некорректные значения

        # сортируем только валидные даты
        return sorted(valid_dates, key=lambda d: datetime.strptime(d, "%d.%m"))

    def update_dates(self):
        saved_dates = list(self.config.staff_state.keys())
        saved_dates = self.sort_dates(saved_dates)

        if self.date_menu:
            self.date_menu.configure(values=[self.DEFAULT_DATE_TEXT] + saved_dates)

        current = self.selected_date.get()

        if current not in saved_dates or current == self.DEFAULT_DATE_TEXT:
            self.selected_date.set(self.DEFAULT_DATE_TEXT)

    from ui.main_table import MainTable

    def show_main_table(self):
        # если уже есть старая таблица, уничтожаем
        if hasattr(self, "main_table_frame") and self.main_table_frame is not None:
            self.main_table_frame.destroy()

        if self.selected_date.get() == self.DEFAULT_DATE_TEXT:
            mb.showerror("Ошибка", "Выберите дату!")
            return

        if not self.config.excel_file:
            mb.showerror("Ошибка", "Выберите Excel файл!")
            return

        # Создаём таблицу и сразу рендерим
        self.main_table_frame = ctk.CTkFrame(self)
        self.main_table_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        table = MainTable(self.config, self.selected_date.get())
        table.show_table(self.main_table_frame)