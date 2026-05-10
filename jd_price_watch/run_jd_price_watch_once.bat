@echo off
setlocal
cd /d "%~dp0"
python watch_jd_price_multi.py --ocr-only --open-url --wait-seconds 20
