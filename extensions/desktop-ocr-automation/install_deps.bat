@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -m pip install --upgrade pip
python -m pip install "paddlepaddle==3.2.2" paddleocr pyautogui pillow opencv-python "numpy<2.4,>=1.24"
pause
