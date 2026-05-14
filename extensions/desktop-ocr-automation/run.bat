@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 桌面 OCR 自动化工具
echo.
echo 默认只识别并点击主屏幕，不操作副屏。
echo.
set /p TARGET_TEXT=请输入要点击的文字（例如：确定）：
if "%TARGET_TEXT%"=="" set TARGET_TEXT=确定
python desktop_ocr_agent.py --text "%TARGET_TEXT%"
echo.
pause
