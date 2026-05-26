import pandas as pd
import customtkinter as ctk
from datetime import datetime
from collections import defaultdict
import random


class MainTable:
    def __init__(self, config, date):
        self.config = config
        self.date = date

        self.df = None
        self.assigned = []
        self.column_widths = []

        self.load_clients_data()

    # =========================================================
    # LOAD CLIENTS
    # =========================================================
    def load_clients_data(self):

        if (
            not hasattr(self.config, "clients_data")
            or not self.config.clients_data
        ):
            self.df = pd.DataFrame(columns=[
                "Время",
                "Гражданин",
                "Цель",
                "Кому назначено",
                "Не менять",
                "Фиксированный сотрудник"
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

            processed.append([
                time_val,
                fio,
                service,
                "",
                keep,
                fixed
            ])

        self.df = pd.DataFrame(processed, columns=[
            "Время",
            "Гражданин",
            "Цель",
            "Кому назначено",
            "Не менять",
            "Фиксированный сотрудник"
        ])

    # =========================================================
    # PARSE TIME
    # =========================================================
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

    # =========================================================
    # AVAILABILITY
    # =========================================================
    def is_lunch_time(self, staff, t):
        tt = t.time()
        return any(a <= tt < b for a, b in staff["lunch"])

    def in_schedule(self, staff, t):
        tt = t.time()
        return staff["start"].time() <= tt < staff["end"].time()

    def is_available(self, staff, t):
        return self.in_schedule(staff, t) and not self.is_lunch_time(staff, t)

    # =========================================================
    # SCORE
    # =========================================================
    def score_staff(self, staff, client, all_staff, group=None):

        score = 0

        current_time_clients = len(
            staff["assigned_times"][client["time"]]
        )

        if current_time_clients >= 2:
            score += 100000

        if client["service"] in staff["assigned_times"][client["time"]]:
            score += 5000

        score += len(staff["assigned"]) * 3
        score += staff["services"][client["service"]] * 4

        if current_time_clients == 1:
            score += 120

        total = sum(len(s["assigned"]) for s in all_staff)
        avg = total / max(len(all_staff), 1)

        score += abs(len(staff["assigned"]) - avg) * 3

        # баланс внутри группы одинакового расписания
        if group:
            sizes = [len(s["assigned"]) for s in group]
            avg_g = sum(sizes) / len(sizes)
            score += abs(len(staff["assigned"]) - avg_g) * 15

        score += random.uniform(0, 2)

        return score

    # =========================================================
    # ASSIGN
    # =========================================================
    def smart_assign(self):

        if self.df.empty:
            return []

        staff_state = self.config.staff_state.get(self.date, {})

        staff = []

        # 👇 ВАЖНО: расписание берём ТОЛЬКО отсюда
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
                "schedule_raw": s.get("schedule", "")
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

        # фиксированные
        for c in clients:

            if c["keep"] and c["fixed"]:
                assigned[c["idx"]] = c["fixed"]

                for s in staff:
                    if s["fio"] == c["fixed"]:
                        s["assigned"].append(c["fio"])
                        s["services"][c["service"]] += 1
                        s["assigned_times"][c["time"]].append(c["service"])

        remaining = [c for c in clients if c["idx"] not in assigned]
        remaining.sort(key=lambda x: (x["time"], random.random()))

        for c in remaining:

            available = [
                s for s in staff
                if self.is_available(s, c["time"])
                and len(s["assigned_times"][c["time"]]) < 2
            ]

            if not available:
                continue

            best = min(
                available,
                key=lambda s: self.score_staff(s, c, staff, available)
            )

            assigned[c["idx"]] = best["fio"]

            best["assigned"].append(c["fio"])
            best["services"][c["service"]] += 1
            best["assigned_times"][c["time"]].append(c["service"])

        self.assigned = [assigned.get(i, "") for i in range(len(self.df))]
        self.df["Кому назначено"] = self.assigned

        return self.assigned

    # =========================================================
    # TABLE
    # =========================================================
    def show_table(self, parent):

        self.smart_assign()

        frame = ctk.CTkScrollableFrame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        headers = [
            "Сотрудник",
            "Первичный прием",
            "Получение услуг/сервисов",
            "Общее кол-во клиентов",
            "Расписание"   # 👈 В КОНЦЕ
        ]

        stats = defaultdict(lambda: {
            "primary": 0,
            "services": 0,
            "total": 0,
            "schedule": ""
        })

        for _, row in self.df.iterrows():

            staff = row["Кому назначено"]
            if not staff:
                continue

            goal = row["Цель"]

            stats[staff]["total"] += 1
            stats[staff]["schedule"] = self.config.staff_state.get(
                self.date, {}
            ).get(staff, {}).get("schedule", "")

            if goal == "Первичный прием":
                stats[staff]["primary"] += 1

            elif goal == "Получение услуг/сервисов":
                stats[staff]["services"] += 1

        self.column_widths = []

        for i, col in enumerate(headers):

            max_len = len(col)

            for staff, d in stats.items():
                vals = [
                    staff,
                    str(d["primary"]),
                    str(d["services"]),
                    str(d["total"]),
                    d["schedule"]
                ]
                max_len = max(max_len, len(vals[i]))

            self.column_widths.append(max_len)

        # HEADER
        header = ctk.CTkFrame(frame)
        header.pack(fill="x", pady=(0, 2))

        for i, col in enumerate(headers):
            ctk.CTkLabel(
                header,
                text=col,
                width=self.column_widths[i] * 10,
                font=("Arial", 14, "bold"),
                anchor="w"
            ).grid(row=0, column=i, sticky="w", padx=5, pady=5)

        # ROWS
        for staff, d in stats.items():

            row_frame = ctk.CTkFrame(frame)
            row_frame.pack(fill="x", pady=1)

            values = [
                staff,
                str(d["primary"]),
                str(d["services"]),
                str(d["total"]),
                d["schedule"]
            ]

            for i, v in enumerate(values):
                ctk.CTkLabel(
                    row_frame,
                    text=v,
                    width=self.column_widths[i] * 10,
                    font=("Arial", 13),
                    anchor="w"
                ).grid(row=0, column=i, sticky="w", padx=5, pady=2)