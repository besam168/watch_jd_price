@echo off
setlocal
chcp 65001 >nul
cd /d C:\Users\besam\.openclaw\workspace
python "C:\Users\besam\.openclaw\workspace\skills\a-share-opening-flow-v6-auto\scripts\opening_flow_v6_auto.py" --auto-loop --poll-seconds 15 >> "C:\Users\besam\.openclaw\workspace\skills\a-share-opening-flow-v6-auto\output\auto_loop.log" 2>&1
