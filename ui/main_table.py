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

        if not hasattr(self.config, "clients_data") or not self.config.clients_data:
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
                time_val = row.get("time", "")
                fio = row.get("citizen", "")
                service = row.get("service", "")
                fixed = row.get("assigned", "")

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
    def parse_time(self, t):
        try:
            return datetime.strptime(str(t).strip(), "%H:%M")
        except:
            return None

    def parse_schedule(self, s):
        try:
            start, end = str(s).replace(" ", "").split("-")
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
    # SMART ASSIGN
    # =========================================================
    def smart_assign(self):

        if self.df.empty:
            return []

        staff_state = self.config.staff_state.get(self.date, {})

        # =========================================================
        # STAFF BUILD
        # =========================================================
        staff = []
        staff_by_name = {}

        for fio, s in staff_state.items():

            if not s.get("active", False):
                continue

            start, end = self.parse_schedule(s.get("schedule", "09:00-18:00"))
            if not start or not end:
                continue

            lunch = self.parse_lunches(s.get("lunch", ""))

            shift_minutes = (end.hour * 60 + end.minute) - (start.hour * 60 + start.minute)

            obj = {
                "fio": fio,
                "start": start,
                "end": end,
                "lunch": lunch,
                "shift_minutes": shift_minutes,

                "assigned": [],
                "assigned_times": defaultdict(list),
                "load": 0
            }

            staff.append(obj)
            staff_by_name[fio] = obj

        # =========================================================
        # CLIENTS
        # =========================================================
        clients = []
        for i, r in self.df.iterrows():

            t = self.parse_time(r["Время"])
            if not t:
                continue

            clients.append({
                "idx": i,
                "time": t,
                "service": r["Цель"],
                "keep": r["Не менять"],
                "fixed": r["Фиксированный сотрудник"]
            })

        # =========================================================
        def is_lunch(st, t):
            tt = t.time()
            return any(a <= tt < b for a, b in st["lunch"])

        def available(st, t):
            return (
                st["start"].time() <= t.time() < st["end"].time()
                and not is_lunch(st, t)
            )

        def effective_load(st):
            capacity = max(1, st["shift_minutes"] / 60)
            return st["load"] / capacity

        # =========================================================
        # FIXED ASSIGNMENT (ВАЖНОЕ ИСПРАВЛЕНИЕ)
        # =========================================================
        assigned = {}

        for c in clients:
            if c["keep"] and c["fixed"]:

                assigned[c["idx"]] = c["fixed"]

                # если сотрудник есть в системе — учитываем в нагрузке
                if c["fixed"] in staff_by_name:
                    s = staff_by_name[c["fixed"]]
                    s["assigned"].append(c["service"])
                    s["assigned_times"][c["time"]].append(c["service"])
                    s["load"] += 1

        remaining = [c for c in clients if c["idx"] not in assigned]

        primary = [c for c in remaining if c["service"] == "Первичный прием"]
        service = [c for c in remaining if c["service"] == "Получение услуг/сервисов"]

        random.shuffle(primary)
        random.shuffle(service)

        # =========================================================
        # PICK STAFF
        # =========================================================
        def pick_staff(c):

            candidates = []

            for s in staff:

                if not available(s, c["time"]):
                    continue

                slot = s["assigned_times"][c["time"]]

                if len(slot) >= 2:
                    continue

                score = effective_load(s)
                score += random.uniform(0, 0.2)

                candidates.append((score, s))

            if not candidates:
                return None

            candidates.sort(key=lambda x: x[0])
            return candidates[0][1]

        # =========================================================
        # PHASE 1
        # =========================================================
        for c in primary:
            chosen = pick_staff(c)
            if not chosen:
                continue

            assigned[c["idx"]] = chosen["fio"]
            chosen["assigned"].append(c["service"])
            chosen["assigned_times"][c["time"]].append(c["service"])
            chosen["load"] += 1

        # =========================================================
        # PHASE 2
        # =========================================================
        for c in service:

            def score_fn(s):

                if not available(s, c["time"]):
                    return 10**9

                slot = s["assigned_times"][c["time"]]

                penalty = 0
                if len(slot) >= 2:
                    penalty += 100

                return effective_load(s) + penalty + random.random() * 0.2

            chosen = min(staff, key=score_fn)

            if not chosen or not available(chosen, c["time"]):
                continue

            slot = chosen["assigned_times"][c["time"]]

            if len(slot) >= 2:
                continue

            assigned[c["idx"]] = chosen["fio"]
            chosen["assigned"].append(c["service"])
            slot.append(c["service"])
            chosen["load"] += 1

        # =========================================================
        # OUTPUT
        # =========================================================
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
            "Расписание"
        ]

        stats = defaultdict(lambda: {
            "primary": 0,
            "services": 0,
            "total": 0,
            "schedule": ""
        })

        for _, r in self.df.iterrows():
            s = r["Кому назначено"]
            if not s:
                continue

            stats[s]["total"] += 1

            if r["Цель"] == "Первичный прием":
                stats[s]["primary"] += 1
            else:
                stats[s]["services"] += 1

        staff_state = self.config.staff_state.get(self.date, {})

        # добавляем только тех, кто реально есть в stats
        for fio in list(stats.keys()):
            if fio in staff_state:
                stats[fio]["schedule"] = staff_state[fio].get("schedule", "")

        self.column_widths = []

        for i, col in enumerate(headers):
            max_len = len(col)

            for s, d in stats.items():
                vals = [
                    s,
                    str(d["primary"]),
                    str(d["services"]),
                    str(d["total"]),
                    d["schedule"]
                ]
                max_len = max(max_len, len(vals[i]))

            self.column_widths.append(max_len)

        header = ctk.CTkFrame(frame)
        header.pack(fill="x")

        for i, col in enumerate(headers):
            ctk.CTkLabel(
                header,
                text=col,
                width=self.column_widths[i] * 10,
                font=("Arial", 14, "bold"),
                anchor="w"
            ).grid(row=0, column=i, sticky="w")

        for s, d in sorted(stats.items(), key=lambda x: x[0]):

            row = ctk.CTkFrame(frame)
            row.pack(fill="x")

            vals = [
                s,
                d["primary"],
                d["services"],
                d["total"],
                d["schedule"]
            ]

            for i, v in enumerate(vals):
                ctk.CTkLabel(
                    row,
                    text=v,
                    width=self.column_widths[i] * 10,
                    anchor="w"
                ).grid(row=0, column=i, sticky="w")