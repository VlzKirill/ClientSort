## Version 1.2.0

# Build:
pip install -r requirements.txt

pyinstaller --onefile --windowed --icon=assets/icon.ico main.py

--debug=all для дебага

# Artifacts:
dist/main.exe


# Release build:
pyinstaller --onefile --windowed --icon=assets/icon.ico --collect-all pandas --collect-all jinja2 --collect-all customtkinter --collect-all openpyxl main.py

