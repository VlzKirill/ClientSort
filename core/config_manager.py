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
        """Загрузить конфиг с диска (только основные настройки)"""
        config = AppConfig()

        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)

                config.schedule_url = data.get("schedule_url", "")
                config.lunch_url = data.get("lunch_url", "")
                config.excel_file = data.get("excel_file", "")
            except Exception as e:
                print("Ошибка чтения настроек:", e)

        # временные данные всегда пустые при старте
        config.staff_state = {}
        config.clients_data = []

        return config

    @staticmethod
    def save(config: AppConfig):
        """Сохраняем только основные настройки на диск"""
        data = {
            "schedule_url": config.schedule_url,
            "lunch_url": config.lunch_url,
            "excel_file": config.excel_file
        }

        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print("Ошибка сохранения настроек:", e)