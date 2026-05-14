@echo off
chcp 65001 >nul
cd /d "%~dp0"
python desktop_ocr_agent.py --scan
pause
