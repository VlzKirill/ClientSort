сборка:
pip install -r requirements.txt

pyinstaller --onefile --windowed --icon=assets/icon.ico main.py

--debug=all для дебага

Результат:
dist/main.exe


1.0.1 build
pyinstaller --onefile --windowed --icon=assets/icon.ico --collect-all pandas --collect-all jinja2 --collect-all customtkinter --collect-all openpyxl main.py