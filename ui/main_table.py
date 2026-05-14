# main_table.py
import pandas as pd
import customtkinter as ctk
import random

class MainTable:
    def __init__(self, config, date):
        self.config = config
        self.date = date
        self.df = None
        self.load_excel()

    def load_excel(self):
        try:
            if not self.config.excel_file:
                print("Excel файл не выбран")
                self.df = pd.DataFrame(columns=["Время", "Гражданин", "Цель"])
                return
            self.df = pd.read_excel(self.config.excel_file, engine='openpyxl')
            self.df = self.df.iloc[:, :3]  # берём только первые 3 столбца
        except Exception as e:
            print("Ошибка загрузки Excel:", e)
            self.df = pd.DataFrame(columns=["Время", "Гражданин", "Цель"])

    def show_table(self, parent):
        # Скроллируемый фрейм
        table_frame = ctk.CTkScrollableFrame(parent)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # ---------------- HEADER ----------------
        headers = ["Время", "Гражданин", "Цель", "Кому назначено"]

        # Вычисляем ширину колонок по содержимому
        self.column_widths = []
        for i, col in enumerate(headers):
            max_len = len(col)
            if i < 3 and not self.df.empty:
                for val in self.df.iloc[:, i]:
                    if pd.notna(val):
                        max_len = max(max_len, len(str(val)))
            self.column_widths.append(max_len)

        header_row = ctk.CTkFrame(table_frame)
        header_row.pack(fill="x", pady=(0, 2))

        for i, col in enumerate(headers):
            lbl = ctk.CTkLabel(
                header_row,
                text=col,
                width=self.column_widths[i]*10,
                anchor="w",
                font=("Arial", 14, "bold"),
            )
            lbl.grid(row=0, column=i, padx=5, pady=5, sticky="w")

        # ---------------- Логика распределения сотрудников ----------------
        assigned_employees = []

        # Берём активных сотрудников на выбранную дату
        staff_for_date = self.config.staff_state.get(self.date, {})
        active_employees = [fio for fio, s in staff_for_date.items() if s.get("active", False)]

        if not active_employees:
            print("Нет активных сотрудников на выбранную дату")
            assigned_employees = ["Не назначен"] * len(self.df)
        else:
            # Если сотрудников меньше, чем клиентов, повторяем список
            while len(active_employees) < len(self.df):
                active_employees += active_employees
            assigned_employees = active_employees[:len(self.df)]
            random.shuffle(assigned_employees)

        # ---------------- ROWS ----------------
        for idx, row in self.df.iterrows():
            row_frame = ctk.CTkFrame(table_frame)
            row_frame.pack(fill="x", pady=1)

            for i in range(4):
                if i < 3:
                    val = row.iloc[i]
                    text = str(val) if pd.notna(val) else ""
                else:
                    text = assigned_employees[idx]  # 4-й столбец — назначенный сотрудник

                lbl = ctk.CTkLabel(
                    row_frame,
                    text=text,
                    width=self.column_widths[i]*10,
                    anchor="w",
                    font=("Arial", 13),
                )
                lbl.grid(row=0, column=i, padx=5, pady=2, sticky="w")