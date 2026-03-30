@echo off
chcp 65001 >nul
cd /d "C:\Users\besam\.openclaw\workspace"
python send_collected_comprehensive_report.py >> comprehensive_report_log.txt 2>&1
