@echo off
chcp 65001 >nul
cd /d "C:\Users\besam\.openclaw\workspace"
python collect_comprehensive_report.py >> comprehensive_report_log.txt 2>&1
