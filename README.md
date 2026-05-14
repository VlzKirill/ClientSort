сборка:
pip install -r requirements.txt

pyinstaller --onefile --windowed --icon=assets/icon.ico main.py

--debug=all для дебага

Результат:
dist/main.exe