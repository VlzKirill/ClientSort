import customtkinter as ctk
from datetime import datetime
from ui.settings_window import SettingsWindow
from ui.staff_window import StaffWindow
from core.config_manager import ConfigManager
from ui.help_window import HelpWindow
from ui.main_table import MainTable
import tkinter.messagebox as mb
from tkinter import filedialog

class MainWindow(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.DEFAULT_DATE_TEXT = "Выберите дату"
        self.geometry("1200x800")
        self.title("Client Sorter")

        self.config = ConfigManager.load()

        self.help_window = None
        self.settings_window = None
        self.staff_window = None
        self.selected_date = None
        self.date_menu = None
        self.main_table_frame = None
        self.table = None
        self.bottom_panel = None

        self.create_ui()
        self.update_dates()

    def create_ui(self):
        # ------------------- ВЕРХНЯЯ ПАНЕЛЬ -------------------
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

        # кнопка персонала
        staff_button = ctk.CTkButton(
            top_frame,
            text="👥 Персонал",
            width=40,
            height=40,
            font=("Arial", 20),
            command=self.open_staff
        )
        staff_button.pack(side="left", padx=5, pady=5)

        # выбор даты
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

        # кнопка распределить
        distribute_button = ctk.CTkButton(
            top_frame,
            text="Распределить",
            width=40,
            height=40,
            font=("Arial", 18),
            command=self.show_main_table
        )
        distribute_button.pack(side="left", padx=5, pady=5)

        # кнопка справки
        help_button = ctk.CTkButton(
            top_frame,
            text="?",
            width=40,
            height=40,
            font=("Arial", 20),
            command=self.open_help
        )
        help_button.pack(side="right", padx=10)

        # ------------------- НИЖНЯЯ ПАНЕЛЬ КНОПОК Excel/PDF -------------------
        self.bottom_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_panel.pack(side="bottom", fill="x", padx=10, pady=10)
        self.bottom_panel.grid_columnconfigure(0, weight=1)

        right_buttons = ctk.CTkFrame(self.bottom_panel, fg_color="transparent")
        right_buttons.grid(row=0, column=1, sticky="e")

        # Excel
        excel_btn = ctk.CTkButton(
            right_buttons,
            text="Сохранить в Excel",
            width=40,
            height=40,
            font=("Arial", 18),
            command=self.save_table_excel
        )
        excel_btn.pack(side="left", padx=5)

    # ------------------- ОТКРЫТЬ ОКНА -------------------
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

    # ------------------- ДАТЫ -------------------
    def sort_dates(self, date_list):
        valid_dates = []
        for d in date_list:
            try:
                datetime.strptime(d, "%d.%m")
                valid_dates.append(d)
            except ValueError:
                continue
        return sorted(valid_dates, key=lambda d: datetime.strptime(d, "%d.%m"))

    def update_dates(self):
        saved_dates = list(self.config.staff_state.keys())
        saved_dates = self.sort_dates(saved_dates)
        if self.date_menu:
            self.date_menu.configure(values=[self.DEFAULT_DATE_TEXT] + saved_dates)
        current = self.selected_date.get()
        if current not in saved_dates or current == self.DEFAULT_DATE_TEXT:
            self.selected_date.set(self.DEFAULT_DATE_TEXT)

    # ------------------- ОТОБРАЖЕНИЕ ТАБЛИЦЫ -------------------
    def show_main_table(self):
        if hasattr(self, "main_table_frame") and self.main_table_frame is not None:
            self.main_table_frame.destroy()

        if self.selected_date.get() == self.DEFAULT_DATE_TEXT:
            mb.showerror("Ошибка", "Выберите дату!")
            return

        if not self.config.excel_file:
            mb.showerror("Ошибка", "Выберите Excel файл!")
            return

        self.main_table_frame = ctk.CTkFrame(self)
        self.main_table_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        self.table = MainTable(self.config, self.selected_date.get())
        self.table.show_table(self.main_table_frame)

    # ------------------- СОХРАНЕНИЕ В EXCEL -------------------
    def save_table_excel(self):
        if self.table is None:
            mb.showerror("Ошибка", "Сначала выполните распределение")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Сохранить таблицу в Excel"
        )
        if not file_path:
            return

        df = self.table.df.copy()
        # берём уже существующее распределение, если есть
        if hasattr(self.table, "assigned") and self.table.assigned:
            df["Кому назначено"] = self.table.assigned
        else:
            df["Кому назначено"] = [""] * len(df)

        try:
            df.to_excel(file_path, index=False)
            mb.showinfo("Успех", f"Таблица сохранена в {file_path}")
        except Exception as e:
            mb.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")
