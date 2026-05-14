# main_table.py
import pandas as pd
import customtkinter as ctk
from datetime import datetime, timedelta
import random

class MainTable:
    def __init__(self, config, date):
        self.config = config
        self.date = date
        self.df = None
        self.assigned = []
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

    # ---------------- Вспомогательные функции ----------------
    def parse_time(self, timestr):
        try:
            return datetime.strptime(str(timestr).split()[1], "%H:%M")
        except:
            return None

    def parse_schedule(self, schedule_str):
        if "-" not in schedule_str:
            return None, None
        start, end = schedule_str.split("-")
        return datetime.strptime(start.strip(), "%H:%M"), datetime.strptime(end.strip(), "%H:%M")

    def parse_lunches(self, lunch_str):
        lunches = []
        if not lunch_str:
            return lunches
        for rng in lunch_str.split("/"):
            try:
                start, end = rng.split("-")
                lunches.append((
                    datetime.strptime(start.strip(), "%H:%M"),
                    datetime.strptime(end.strip(), "%H:%M")
                ))
            except:
                continue
        return lunches

    def is_available(self, staff_member, time_obj):
        # Проверка рабочего времени
        if not (staff_member["start"] <= time_obj <= staff_member["end"]):
            return False
        # Проверка обеда
        for lunch_start, lunch_end in staff_member["lunch"]:
            if lunch_start <= time_obj < lunch_end:
                return False
        return True

    # ---------------- Алгоритм распределения ----------------
    def smart_assign(self):
        if self.df.empty:
            return ["Не назначен"] * 0

        staff_for_date = self.config.staff_state.get(self.date, {})
        staff_data = []

        # Подготовка сотрудников
        for fio, s in staff_for_date.items():
            if not s.get("active", False):
                continue
            start, end = self.parse_schedule(s.get("расписание", "09:00-18:00"))
            lunches = self.parse_lunches(s.get("обед", ""))
            staff_data.append({
                "fio": fio,
                "start": start,
                "end": end,
                "lunch": lunches,
                "assigned": [],
                "services": {},  # количество клиентов по типу услуги
            })

        if not staff_data:
            return ["Не назначен"] * len(self.df)

        # Подготовка клиентов
        clients = []
        for idx, row in self.df.iterrows():
            time_obj = self.parse_time(row.iloc[0])  # первый столбец "Время"
            if not time_obj:
                continue
            clients.append({
                "idx": idx,
                "fio": row.iloc[1],  # второй столбец "Гражданин"
                "service": row.iloc[2],  # третий столбец "Цель"
                "time": time_obj
            })

        # Сортировка по времени
        clients.sort(key=lambda x: x["time"])

        # Группировка по времени
        from collections import defaultdict
        clients_by_time = defaultdict(list)
        for c in clients:
            clients_by_time[c["time"]].append(c)

        assigned_dict = {}

        # Распределяем клиентов по времени
        for time_slot in sorted(clients_by_time.keys()):
            clients_this_time = clients_by_time[time_slot]
            random.shuffle(clients_this_time)

            for client in clients_this_time:
                # Список доступных сотрудников
                available_staff = [s for s in staff_data if self.is_available(s, time_slot)]
                if not available_staff:
                    available_staff = sorted(staff_data, key=lambda s: len(s["assigned"]))

                # Выбираем того, у кого меньше клиентов этого типа
                available_staff.sort(key=lambda s: s["services"].get(client["service"], 0))
                chosen = available_staff[0]

                assigned_dict[client["idx"]] = chosen["fio"]
                chosen["assigned"].append(client["fio"])
                chosen["services"][client["service"]] = chosen["services"].get(client["service"], 0) + 1

        # Формируем список назначений по индексам DataFrame
        assigned_list = [assigned_dict.get(idx, "Не назначен") for idx in range(len(self.df))]
        return assigned_list

    # ---------------- Отображение таблицы ----------------
    def show_table(self, parent):
        # Скроллируемый фрейм
        table_frame = ctk.CTkScrollableFrame(parent)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # ---------------- HEADER ----------------
        headers = ["Время", "Гражданин", "Цель", "Кому назначено"]
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

        # ---------------- Назначение сотрудников ----------------
        self.assigned = self.smart_assign()

        # ---------------- ROWS ----------------
        for idx, row in self.df.iterrows():
            row_frame = ctk.CTkFrame(table_frame)
            row_frame.pack(fill="x", pady=1)
            for i in range(4):
                if i < 3:
                    val = row.iloc[i]
                    text = str(val) if pd.notna(val) else ""
                else:
                    text = self.assigned[idx]
                lbl = ctk.CTkLabel(
                    row_frame,
                    text=text,
                    width=self.column_widths[i]*10,
                    anchor="w",
                    font=("Arial", 13),
                )
                lbl.grid(row=0, column=i, padx=5, pady=2, sticky="w")