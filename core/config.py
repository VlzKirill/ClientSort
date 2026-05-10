class AppConfig:
    def __init__(self):
        self.set_defaults()

    def set_defaults(self):
        self.schedule_url = ""
        self.lunch_url = ""
        self.excel_file = ""