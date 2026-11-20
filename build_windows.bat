@echo off
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean --windowed --name ProPomodoro --collect-all kivy --collect-all plyer main.py
echo.
echo Windows app created at dist\ProPomodoro\ProPomodoro.exe
pause
