import json
import os
import tempfile

from core.config import AppConfig

SETTINGS_FILE = os.path.join(
    tempfile.gettempdir(),
    "client_sorter_settings.json"
)


class ConfigManager:

    @staticmethod
    def load():
        config = AppConfig()

        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            config.schedule_url = data.get("schedule_url", "")
            config.lunch_url = data.get("lunch_url", "")
            config.excel_file = data.get("excel_file", "")
            config.staff_state = data.get("staff_state", {})

        return config

    @staticmethod
    def save(config: AppConfig):
        data = {
            "schedule_url": config.schedule_url,
            "lunch_url": config.lunch_url,
            "excel_file": config.excel_file,
            "staff_state": config.staff_state
        }

        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)