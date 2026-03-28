@echo off
chcp 65001 >nul
cd /d "C:\Users\besam\.openclaw\workspace"
python daily_tech_report.py >> tech_report_log.txt 2>&1
