@echo off
setlocal ENABLEDELAYEDEXPANSION
cd /d "%~dp0"
if not exist logs mkdir logs
:loop
echo [%date% %time%] starting jd price watch >> logs\hourly_watch_runner.log
python watch_jd_price_multi.py --ocr-only --open-url --wait-seconds 20 >> logs\hourly_watch_runner.log 2>&1
echo [%date% %time%] sleeping 3600 seconds >> logs\hourly_watch_runner.log
timeout /t 3600 /nobreak >nul
goto loop
