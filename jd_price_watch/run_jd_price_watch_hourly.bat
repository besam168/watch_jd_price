@echo off
setlocal ENABLEDELAYEDEXPANSION
cd /d "%~dp0"
if not exist logs mkdir logs

set "URL=https://item.jd.com/100278222276.html"
set "MAX_ATTEMPTS=3"
set "WAIT_SECONDS=20"
set "SLEEP_SECONDS=3600"

:loop
echo [%date% %time%] starting jd price watch >> logs\hourly_watch_runner.log
set /a ATTEMPT=1

:attempt
echo [%date% %time%] attempt !ATTEMPT!/%MAX_ATTEMPTS% >> logs\hourly_watch_runner.log
start "" "%URL%"
timeout /t %WAIT_SECONDS% /nobreak >nul
python watch_jd_price_multi.py --ocr-only >> logs\hourly_watch_runner.log 2>&1

python -c "import json, pathlib; p=pathlib.Path(r'C:\Users\besam\.openclaw\workspace\jd_price_watch\data\state_multi.json'); d=json.loads(p.read_text(encoding='utf-8')); ok=bool(d.get('last_price') is not None and d.get('last_title') != '未知商品'); print('JD_OK' if ok else 'JD_RETRY')" > logs\last_attempt_status.txt 2>nul
set /p LAST_STATUS=<logs\last_attempt_status.txt
echo [%date% %time%] attempt result !LAST_STATUS! >> logs\hourly_watch_runner.log

if /I "!LAST_STATUS!"=="JD_OK" goto after_attempts
if !ATTEMPT! GEQ %MAX_ATTEMPTS% goto after_attempts
set /a ATTEMPT+=1
echo [%date% %time%] retrying because JD page was not confirmed >> logs\hourly_watch_runner.log
goto attempt

:after_attempts
echo [%date% %time%] sleeping %SLEEP_SECONDS% seconds >> logs\hourly_watch_runner.log
timeout /t %SLEEP_SECONDS% /nobreak >nul
goto loop
