#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双时点多轮采样版中小盘扫描任务
- 09:35 跑第一轮多轮采样
- 09:45 跑第二轮多轮采样
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

SMTP_SERVER = 'smtp.qq.com'
SMTP_PORT = 465
SENDER_EMAIL = '910633260@qq.com'
SENDER_PASSWORD = 'sghqeeeeyuzjbcbb'
RECEIVERS = ['besam168168@gmail.com', '758622673@qq.com']
LIVE_SMALLCAP_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'live_smallcap.py')
REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../reports/smallcap')
os.makedirs(REPORT_DIR, exist_ok=True)

CONFIGS = {
    '0935': {
        'sample_label': '0935',
        'min_change_pct': 0.5,
        'max_change_pct': 7,
        'min_amount_yi': 0.005,
        'rounds': 3,
        'interval_seconds': 8,
        'pick_count': 24,
        'role': '先手苗子池',
        'desc': '09:35 偏放宽，优先抓早盘先手苗子和板块刚冒头的小票。',
    },
    '0945': {
        'sample_label': '0945',
        'min_change_pct': 0.6,
        'max_change_pct': 8,
        'min_amount_yi': 0.005,
        'rounds': 4,
        'interval_seconds': 8,
        'pick_count': 24,
        'role': '留强确认池',
        'desc': '09:45 偏确认，优先保留已经走出来、强度还在延续的票。',
    }
}


def run_scan(slot: str):
    cfg = CONFIGS[slot]
    cmd = [
        sys.executable,
        LIVE_SMALLCAP_SCRIPT,
        '--sample-label', cfg['sample_label'],
        '--min-change-pct', str(cfg['min_change_pct']),
        '--max-change-pct', str(cfg['max_change_pct']),
        '--min-amount-yi', str(cfg['min_amount_yi']),
        '--max-total-mv-yi', '100',
        '--max-circ-mv-yi', '100',
        '--top-n', '120',
        '--pick-count', str(cfg['pick_count']),
        '--rounds', str(cfg['rounds']),
        '--interval-seconds', str(cfg['interval_seconds']),
        '--json',
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=300)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or 'scan_failed')
    return json.loads(result.stdout)


def summary_text(summary):
    if isinstance(summary, dict):
        return summary.get('overall', '无数据')
    return str(summary or '无数据')


def build_html(payload: dict, slot: str) -> str:
    cfg = CONFIGS[slot]
    return f"""
    <html><head><meta charset='UTF-8'><title>中小盘双时点扫描 {slot}</title></head>
    <body style='font-family:微软雅黑,Arial;padding:20px;line-height:1.6;'>
    <h1>A股中小盘双时点多轮采样报告 - {slot}</h1>
    <p><b>角色定位：</b>{cfg['role']}</p>
    <p><b>说明：</b>{cfg['desc']}</p>
    <p><b>生成时间：</b>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p><b>策略：</b>{payload.get('strategy')}</p>
    <p><b>总结：</b>{summary_text(payload.get('chinese_summary'))}</p>
    <h2>真龙头</h2>
    {''.join([f"<div>{x['name']} ({x['code']}) 涨幅 {x.get('change_pct')}% / track_score {x.get('track_score')}</div>" for x in payload.get('true_leaders', [])])}
    <h2>强跟风</h2>
    {''.join([f"<div>{x['name']} ({x['code']}) 涨幅 {x.get('change_pct')}% / track_score {x.get('track_score')}</div>" for x in payload.get('strong_followers', [])[:10]])}
    <h2>观察池</h2>
    {''.join([f"<div>{x['name']} ({x['code']}) 涨幅 {x.get('change_pct')}% / track_score {x.get('track_score')}</div>" for x in payload.get('watchlist', [])[:10]])}
    </body></html>
    """


def send_email(subject: str, html: str):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = ', '.join(RECEIVERS)
    msg['Subject'] = subject
    msg.attach(MIMEText(html, 'html', 'utf-8'))
    server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.sendmail(SENDER_EMAIL, RECEIVERS, msg.as_string())
    server.quit()


def main():
    slot = '0935'
    if len(sys.argv) > 1:
        slot = sys.argv[1].strip()
    if slot not in CONFIGS:
        raise SystemExit('slot must be 0935 or 0945')
    payload = run_scan(slot)
    payload['slot_role'] = CONFIGS[slot]['role']
    payload['slot_desc'] = CONFIGS[slot]['desc']
    html = build_html(payload, slot)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_path = os.path.join(REPORT_DIR, f'smallcap_dual_slot_{slot}_{ts}.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    send_email(f'【{slot}｜{CONFIGS[slot]["role"]}】A股中小盘双时点多轮采样报告', html)
    print(json.dumps({'slot': slot, 'role': CONFIGS[slot]['role'], 'report': out_path, 'true_leaders': len(payload.get('true_leaders', [])), 'strong_followers': len(payload.get('strong_followers', [])), 'watchlist': len(payload.get('watchlist', []))}, ensure_ascii=False))


if __name__ == '__main__':
    main()
