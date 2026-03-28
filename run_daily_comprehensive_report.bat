@echo off
chcp 65001 >nul
cd /d "C:\Users\besam\.openclaw\workspace"
python daily_news_brief.py --mode comprehensive >> comprehensive_report_log.txt 2>&1
