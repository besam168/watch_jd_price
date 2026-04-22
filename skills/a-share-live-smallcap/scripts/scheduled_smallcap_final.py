#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
import sys
import json
import smtplib
import subprocess
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

MIN_CHANGE = 3
MAX_CHANGE = 5
MAX_MV = 100
MAX_CIRC_MV = 100
MIN_AMOUNT = 0.03

SMTP_SERVER = 'smtp.qq.com'
SMTP_PORT = 465
SENDER = '910633260@qq.com'
PASSWORD = 'sghqeeeeyuzjbcbb'
RECEIVERS = ['besam168168@gmail.com', '758622673@qq.com']

SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'live_smallcap.py')


def run_scan():
    cmd = [
        sys.executable,
        SCRIPT_PATH,
        '--min-change-pct', str(MIN_CHANGE),
        '--max-change-pct', str(MAX_CHANGE),
        '--max-total-mv-yi', str(MAX_MV),
        '--max-circ-mv-yi', str(MAX_CIRC_MV),
        '--min-amount-yi', str(MIN_AMOUNT),
        '--json'
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=180)
        if result.returncode == 0:
            return json.loads(result.stdout)
        return None
    except Exception:
        return None


def summary_text(data):
    s = data.get('chinese_summary', '无最新数据')
    if isinstance(s, dict):
        return s.get('overall', '无最新数据')
    return str(s)


def generate_text_report(data):
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    report = [
        '=' * 60,
        f'A股中小盘强势股扫描报告（pytdx版） - {now}',
        '=' * 60,
        f'选股条件：涨幅{MIN_CHANGE}%-{MAX_CHANGE}% | 5亿股+100亿流通市值新池 | 成交额≥{MIN_AMOUNT}亿',
        f"数据来源：{data.get('market_scan_source', 'pytdx-live-universe')}",
        '=' * 60,
        '',
        '【盯盘总结】',
        summary_text(data),
        '',
        '【真龙头股】',
    ]

    for s in data.get('true_leaders', []):
        report.append(f"★ {s['name']}({s['code']}) | 涨幅：{s['change_pct']}% | 成交额：{s.get('amount_yi', 0)}亿")

    report.extend(['', '【强跟风股】'])
    for s in data.get('strong_followers', []):
        report.append(f"● {s['name']}({s['code']}) | 涨幅：{s['change_pct']}% | 成交额：{s.get('amount_yi', 0)}亿")

    report.extend(['', '【候选观察】'])
    for s in data.get('watchlist', [])[:10]:
        report.append(f"○ {s['name']}({s['code']}) | 涨幅：{s['change_pct']}% | 成交额：{s.get('amount_yi', 0)}亿")

    report.extend(['', '【伪强观察】'])
    for s in data.get('pseudo_strong', [])[:10]:
        report.append(f"- {s['name']}({s['code']}) | 涨幅：{s.get('change_pct', 0)}% | 二轮过滤未完全通过")

    report.extend([
        '',
        '=' * 60,
        '⚠️ 本报告由沈万三数字管家自动生成，仅供参考，不构成投资建议',
        '=' * 60,
    ])
    return '\n'.join(report)


def send_email(report_text):
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    msg = MIMEMultipart()
    msg['Subject'] = f'【盘中扫描】A股中小盘强势股报告（pytdx版） {now}'
    msg['From'] = SENDER
    msg['To'] = ', '.join(RECEIVERS)
    msg.attach(MIMEText(report_text, 'plain', 'utf-8'))
    try:
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER, PASSWORD)
        server.sendmail(SENDER, RECEIVERS, msg.as_string())
        server.quit()
        return True
    except Exception:
        return False


if __name__ == '__main__':
    data = run_scan()
    if not data:
        sys.exit(1)
    report = generate_text_report(data)
    success = send_email(report)
    sys.exit(0 if success else 1)
