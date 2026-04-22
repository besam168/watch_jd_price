#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时中小盘选股扫描脚本（pytdx版）
功能：盘中定时扫描 5亿股+100亿流通市值 新股票池，生成报告发送邮件
"""
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'
import sys
import json
import smtplib
import subprocess
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

MIN_CHANGE_PCT = 3
MAX_CHANGE_PCT = 5
MAX_TOTAL_MV_YI = 100
MAX_CIRC_MV_YI = 100
MIN_AMOUNT_YI = 0.03
TOP_N = 120
PICK_COUNT = 24

LIVE_SMALLCAP_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'live_smallcap.py')

SMTP_SERVER = 'smtp.qq.com'
SMTP_PORT = 465
SENDER_EMAIL = '910633260@qq.com'
SENDER_PASSWORD = 'sghqeeeeyuzjbcbb'
RECEIVERS = ['besam168168@gmail.com', '758622673@qq.com']


def run_scan():
    cmd = [
        sys.executable,
        LIVE_SMALLCAP_SCRIPT,
        '--min-change-pct', str(MIN_CHANGE_PCT),
        '--max-change-pct', str(MAX_CHANGE_PCT),
        '--max-total-mv-yi', str(MAX_TOTAL_MV_YI),
        '--max-circ-mv-yi', str(MAX_CIRC_MV_YI),
        '--min-amount-yi', str(MIN_AMOUNT_YI),
        '--top-n', str(TOP_N),
        '--pick-count', str(PICK_COUNT),
        '--json'
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=180)
        if result.returncode != 0:
            print(f"❌ 选股脚本执行失败：{result.stderr}")
            return None
        return json.loads(result.stdout)
    except Exception as e:
        print(f"❌ 执行选股出错：{str(e)}")
        return None


def _summary_text(summary):
    if isinstance(summary, dict):
        return summary.get('overall', '无数据')
    return str(summary or '无数据')


def generate_report(result):
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    html = f"""
    <html>
    <head>
        <meta charset=\"UTF-8\">
        <title>A股中小盘强势股扫描报告 - {now}</title>
        <style>
            body {{ font-family: '微软雅黑', Arial; line-height: 1.6; padding: 20px; }}
            h1 {{ color: #c00; text-align: center; }}
            .header {{ background: #f5f5f5; padding: 10px; margin-bottom: 20px; border-radius: 5px; }}
            .section {{ margin-bottom: 25px; }}
            .section h2 {{ color: #333; border-bottom: 2px solid #c00; padding-bottom: 5px; }}
            .stock-item {{ margin: 8px 0; padding: 8px; border-bottom: 1px solid #eee; }}
            .stock-name {{ font-weight: bold; font-size: 16px; }}
            .stock-info {{ color: #666; font-size: 14px; }}
            .pseudo {{ color: #999; text-decoration: line-through; }}
            .summary {{ background: #fff3cd; padding: 15px; border-radius: 5px; font-size: 16px; }}
            .footer {{ color: #999; font-size: 12px; text-align: center; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <h1>📈 A股中小盘强势股扫描报告（pytdx版）</h1>
        <div class=\"header\">
            <p><strong>扫描时间：</strong>{now}</p>
            <p><strong>选股条件：</strong>涨幅3%-5%、5亿股+100亿流通市值新池、近3日放量、5日线支撑</p>
            <p><strong>实时来源：</strong>{result.get('market_scan_source', 'pytdx-live-universe')}</p>
        </div>

        <div class=\"section\">
            <h2>📝 盯盘总结</h2>
            <div class=\"summary\">{_summary_text(result.get('chinese_summary'))}</div>
        </div>

        <div class=\"section\">
            <h2>🏆 真龙头（{len(result.get('true_leaders', []))}只）</h2>
            {''.join([f'<div class="stock-item"><span class="stock-name">{s["name"]} ({s["code"]})</span> <span class="stock-info">涨幅：{s["change_pct"]}% 成交额：{s.get("amount_yi", "0")}亿</span></div>' for s in result.get('true_leaders', [])])}
        </div>

        <div class=\"section\">
            <h2>🔥 强跟风（{len(result.get('strong_followers', []))}只）</h2>
            {''.join([f'<div class="stock-item"><span class="stock-name">{s["name"]} ({s["code"]})</span> <span class="stock-info">涨幅：{s["change_pct"]}% 成交额：{s.get("amount_yi", "0")}亿</span></div>' for s in result.get('strong_followers', [])])}
        </div>

        <div class=\"section\">
            <h2>👀 候选观察（{len(result.get('watchlist', []))}只）</h2>
            {''.join([f'<div class="stock-item"><span class="stock-name">{s["name"]} ({s["code"]})</span> <span class="stock-info">涨幅：{s["change_pct"]}% 成交额：{s.get("amount_yi", "0")}亿</span></div>' for s in result.get('watchlist', [])])}
        </div>

        <div class=\"section\">
            <h2>⚠️ 伪强剔除（{len(result.get('pseudo_strong', []))}只）</h2>
            {''.join([f'<div class="stock-item pseudo"><span>{s["name"]} ({s["code"]})</span> <span>涨幅：{s.get("change_pct", 0)}% 说明：二轮过滤未完全通过</span></div>' for s in result.get('pseudo_strong', [])[:10]])}
        </div>

        <div class=\"footer\">
            <p>本报告由沈万三数字管家自动生成，仅供参考，不构成投资建议</p>
        </div>
    </body>
    </html>
    """
    return html


def send_email(report_html):
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    subject = f'【盘中扫描】A股中小盘强势股报告（pytdx版） - {now}'
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = ', '.join(RECEIVERS)
    msg['Subject'] = subject
    msg.attach(MIMEText(report_html, 'html', 'utf-8'))
    try:
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVERS, msg.as_string())
        server.quit()
        print(f"✅ 邮件发送成功，已发送到：{', '.join(RECEIVERS)}")
        return True
    except Exception as e:
        print(f"❌ 邮件发送失败：{str(e)}")
        return False


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    print(f"开始扫描中小盘强势股（pytdx版），时间：{datetime.now()}")
    result = run_scan()
    if not result:
        print('❌ 选股失败，无返回数据')
        sys.exit(1)
    report = generate_report(result)
    report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../reports/smallcap')
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f'smallcap_scan_pytdx_{datetime.now().strftime("%Y%m%d_%H%M")}.html')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"📄 报告已保存到：{report_path}")
    send_success = send_email(report)
    sys.exit(0 if send_success else 1)
