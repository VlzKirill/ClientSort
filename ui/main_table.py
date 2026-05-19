import pandas as pd
import customtkinter as ctk
from datetime import datetime, time
from collections import defaultdict
import random  # 🔥 ДОБАВИЛИ


class MainTable:
    def __init__(self, config, date):
        self.config = config
        self.date = date
        self.df = None
        self.assigned = []
        self.load_clients_data()

    # ------------------- ЗАГРУЗКА КЛИЕНТОВ -------------------
    def load_clients_data(self):
        if not hasattr(self.config, "clients_data") or not self.config.clients_data:
            self.df = pd.DataFrame(columns=[
                "Время", "Гражданин", "Цель", "Кому назначено",
                "Не менять", "Фиксированный сотрудник"
            ])
            return

        processed = []

        for row in self.config.clients_data:
            if isinstance(row, dict):
                keep = row.get("keep", row.get("Не менять", False))
                time_val = row.get("time", row.get("Время", ""))
                fio = row.get("citizen", row.get("Гражданин", ""))
                service = row.get("service", row.get("Цель", ""))
                fixed = row.get("assigned", row.get("Фиксированный сотрудник", ""))
            else:
                vals = list(row)
                keep = vals[0] if len(vals) > 0 else False
                time_val = vals[1] if len(vals) > 1 else ""
                fio = vals[2] if len(vals) > 2 else ""
                service = vals[3] if len(vals) > 3 else ""
                fixed = vals[4] if len(vals) > 4 else ""

            processed.append([time_val, fio, service, "", keep, fixed])

        self.df = pd.DataFrame(processed, columns=[
            "Время", "Гражданин", "Цель", "Кому назначено",
            "Не менять", "Фиксированный сотрудник"
        ])

    # ------------------- ПАРСИНГ -------------------
    def parse_time(self, t):
        try:
            return datetime.strptime(str(t).strip(), "%H:%M")
        except:
            return None

    def parse_schedule(self, s):
        try:
            s = str(s).replace(" ", "")
            start, end = s.split("-")
            return (
                datetime.strptime(start, "%H:%M"),
                datetime.strptime(end, "%H:%M")
            )
        except:
            return None, None

    def parse_lunches(self, s):
        result = []
        if not s:
            return result

        for part in str(s).split("/"):
            try:
                a, b = part.split("-")
                result.append((
                    datetime.strptime(a.strip(), "%H:%M").time(),
                    datetime.strptime(b.strip(), "%H:%M").time()
                ))
            except:
                continue
        return result

    # ------------------- ДОСТУПНОСТЬ -------------------
    def is_lunch_time(self, staff, t):
        tt = t.time()
        for a, b in staff["lunch"]:
            if a <= tt < b:
                return True
        return False

    def in_schedule(self, staff, t):
        tt = t.time()
        return staff["start"].time() <= tt < staff["end"].time()

    def is_available(self, staff, t):
        return self.in_schedule(staff, t) and not self.is_lunch_time(staff, t)

    # ------------------- SCORING -------------------
    def score_staff(self, staff, client, all_staff):
        score = 0

        # 1. перегрузка
        score += len(staff["assigned"]) * 2

        # 2. баланс услуг
        score += staff["services"].get(client["service"], 0) * 3

        # 3. занятость времени
        if client["time"] in staff["assigned_times"]:
            score += 50

        # 4. баланс
        total = sum(len(s["assigned"]) for s in all_staff)
        avg = total / max(len(all_staff), 1)
        score += abs(len(staff["assigned"]) - avg) * 2

        # 🔥 ВАЖНО: микро-рандом (главный источник разнообразия)
        score += random.uniform(0, 1.2)

        return score

    # ------------------- АЛГОРИТМ -------------------
    def smart_assign(self):
        if self.df.empty:
            return []

        staff_state = self.config.staff_state.get(self.date, {})

        staff = []
        for fio, s in staff_state.items():
            if not s.get("active", False):
                continue

            start, end = self.parse_schedule(s.get("schedule", "09:00-18:00"))
            lunches = self.parse_lunches(s.get("lunch", ""))

            staff.append({
                "fio": fio,
                "start": start,
                "end": end,
                "lunch": lunches,
                "assigned": [],
                "assigned_times": defaultdict(list),
                "services": defaultdict(int),
            })

        if not staff:
            return []

        clients = []
        for i, r in self.df.iterrows():
            t = self.parse_time(r["Время"])
            if not t:
                continue

            clients.append({
                "idx": i,
                "time": t,
                "fio": r["Гражданин"],
                "service": r["Цель"],
                "keep": r["Не менять"],
                "fixed": r["Фиксированный сотрудник"]
            })

        assigned = {}

        # ------------------- фиксированные -------------------
        for c in clients:
            if c["keep"] and c["fixed"]:
                assigned[c["idx"]] = c["fixed"]
                for s in staff:
                    if s["fio"] == c["fixed"]:
                        s["assigned"].append(c["fio"])
                        s["services"][c["service"]] += 1
                        s["assigned_times"][c["time"]].append(c["service"])

        remaining = [c for c in clients if c["idx"] not in assigned]
        remaining.sort(key=lambda x: (x["time"], random.random()))  # 🔥 РАНДОМИЗАЦИЯ ПОРЯДКА

        # ------------------- РАСПРЕДЕЛЕНИЕ -------------------
        for c in remaining:

            available = [s for s in staff if self.is_available(s, c["time"])]

            if not available:
                continue

            best = None
            best_score = float("inf")

            for s in available:
                sc = self.score_staff(s, c, staff)
                if sc < best_score:
                    best_score = sc
                    best = s

            assigned[c["idx"]] = best["fio"]
            best["assigned"].append(c["fio"])
            best["services"][c["service"]] += 1
            best["assigned_times"][c["time"]].append(c["service"])

        self.assigned = [assigned.get(i, "") for i in range(len(self.df))]
        self.df["Кому назначено"] = self.assigned
        return self.assigned

    # ------------------- UI -------------------
    def show_table(self, parent):
        table_frame = ctk.CTkScrollableFrame(parent)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        headers = ["Время", "Гражданин", "Цель", "Кому назначено"]
        self.column_widths = []

        for i, col in enumerate(headers):
            max_len = len(col)
            if i < 3 and not self.df.empty:
                for v in self.df.iloc[:, i]:
                    max_len = max(max_len, len(str(v)))
            self.column_widths.append(max_len)

        header = ctk.CTkFrame(table_frame)
        header.pack(fill="x", pady=(0, 2))

        for i, col in enumerate(headers):
            ctk.CTkLabel(
                header,
                text=col,
                width=self.column_widths[i] * 10,
                anchor="w",
                font=("Arial", 14, "bold")
            ).grid(row=0, column=i, padx=5, pady=5, sticky="w")

        self.smart_assign()

        for idx, row in self.df.iterrows():
            row_frame = ctk.CTkFrame(table_frame)
            row_frame.pack(fill="x", pady=1)

            for i in range(4):
                text = str(row.iloc[i]) if i < 3 else self.assigned[idx]

                ctk.CTkLabel(
                    row_frame,
                    text=text,
                    width=self.column_widths[i] * 10,
                    anchor="w",
                    font=("Arial", 13)
                ).grid(row=0, column=i, padx=5, pady=2, sticky="w")