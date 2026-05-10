import os
import json
import tempfile
from tkinter import filedialog

import customtkinter as ctk

DEFAULT_SCHEDULE = ""
DEFAULT_LUNCH = ""

SETTINGS_FILE = os.path.join(
    tempfile.gettempdir(),
    "client_sorter_settings.json"
)


class SettingsWindow(ctk.CTkToplevel):

    def __init__(self, parent):
        super().__init__(parent)

        self.title("Настройки")
        self.geometry("800x500")

        self.transient(parent)

        self.selected_excel_file = ""

        self.create_ui()
        self.load_settings()

    def create_ui(self):

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        # ---------------- TITLE ----------------

        title = ctk.CTkLabel(
            self,
            text="Настройки",
            font=("Arial", 22)
        )

        title.grid(
            row=0,
            column=0,
            columnspan=2,
            pady=20
        )

        # ---------------- SCHEDULE ----------------

        self.schedule_label = ctk.CTkLabel(
            self,
            text="Ссылка на Google Таблицу с графиком:"
        )

        self.schedule_label.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="w",
            padx=20
        )

        self.schedule_entry = ctk.CTkEntry(self)

        self.schedule_entry.grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=20,
            pady=(0, 15)
        )

        # ---------------- LUNCH ----------------

        self.lunch_label = ctk.CTkLabel(
            self,
            text="Ссылка на Google Таблицу с обедами:"
        )

        self.lunch_label.grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="w",
            padx=20
        )

        self.lunch_entry = ctk.CTkEntry(self)

        self.lunch_entry.grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=20,
            pady=(0, 20)
        )

        # ---------------- FILE ----------------

        self.file_label = ctk.CTkLabel(
            self,
            text="Excel файл с записанными клиентами:"
        )

        self.file_label.grid(
            row=5,
            column=0,
            columnspan=2,
            sticky="w",
            padx=20
        )

        # кнопка обзор
        self.browse_button = ctk.CTkButton(
            self,
            text="Обзор",
            width=120,
            command=self.select_excel_file
        )

        self.browse_button.grid(
            row=6,
            column=0,
            padx=(20, 10),
            pady=(5, 10),
            sticky="w"
        )

        # поле пути к файлу
        self.file_path_entry = ctk.CTkEntry(self)

        self.file_path_entry.grid(
            row=6,
            column=1,
            padx=(0, 20),
            pady=(5, 10),
            sticky="ew"
        )

        # пустая строка растягивается
        self.grid_rowconfigure(7, weight=1)

        # ---------------- RESET BUTTON ----------------

        self.reset_button = ctk.CTkButton(
            self,
            text="Сброс настроек",
            fg_color="gray",
            command=self.reset_settings
        )

        self.reset_button.grid(
            row=8,
            column=0,
            sticky="sw",
            padx=20,
            pady=20
        )

        # ---------------- APPLY BUTTON ----------------

        self.apply_button = ctk.CTkButton(
            self,
            text="Применить",
            command=self.save_settings
        )

        self.apply_button.grid(
            row=8,
            column=1,
            sticky="se",
            padx=20,
            pady=20
        )

    def select_excel_file(self):

        file_path = filedialog.askopenfilename(
            title="Выберите Excel файл",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*")
            ]
        )

        if file_path:

            self.selected_excel_file = file_path

            self.file_path_entry.delete(0, "end")
            self.file_path_entry.insert(0, file_path)

    def save_settings(self):

        self.selected_excel_file = self.file_path_entry.get()

        settings = {
            "schedule_url": self.schedule_entry.get(),
            "lunch_url": self.lunch_entry.get(),
            "excel_file": self.selected_excel_file
        }

        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)

        print("Настройки сохранены")

        self.destroy()

    def load_settings(self):

        self.schedule_entry.delete(0, "end")
        self.lunch_entry.delete(0, "end")
        self.file_path_entry.delete(0, "end")

        schedule_url = DEFAULT_SCHEDULE
        lunch_url = DEFAULT_LUNCH
        excel_file = ""

        if os.path.exists(SETTINGS_FILE):

            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    settings = json.load(f)

                schedule_url = settings.get(
                    "schedule_url",
                    DEFAULT_SCHEDULE
                )

                lunch_url = settings.get(
                    "lunch_url",
                    DEFAULT_LUNCH
                )

                excel_file = settings.get(
                    "excel_file",
                    ""
                )

            except Exception as e:
                print("Ошибка загрузки настроек:", e)

        self.schedule_entry.insert(0, schedule_url)
        self.lunch_entry.insert(0, lunch_url)
        self.file_path_entry.insert(0, excel_file)

        self.selected_excel_file = excel_file

    def reset_settings(self):

        if os.path.exists(SETTINGS_FILE):
            os.remove(SETTINGS_FILE)

        self.schedule_entry.delete(0, "end")
        self.lunch_entry.delete(0, "end")
        self.file_path_entry.delete(0, "end")

        self.schedule_entry.insert(0, DEFAULT_SCHEDULE)
        self.lunch_entry.insert(0, DEFAULT_LUNCH)

        self.selected_excel_file = ""

        print("Настройки сброшены")