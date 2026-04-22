#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多时点多轮采样版中小盘扫描任务（含板块正式版）
支持时点：09:24 / 09:35 / 09:45 / 10:04 / 13:01 / 13:03 / 14:21 / 14:23

正式原则：
1. 每个时间点都必须独立扫描一次，单独寻找当时符合条件的股票。
2. 不能只沿用前一个时间点的旧名单来做缩圈，否则会漏掉盘中新冒头、午后回流、尾盘异动的票。
3. 跨时点分析（留强 / 新冒头 / 掉队 / 板块演化）必须建立在“各时点先独立扫描”的基础上。
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
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LIVE_SMALLCAP_SCRIPT = os.path.join(SCRIPT_DIR, 'live_smallcap.py')
SECTOR_SCRIPT = os.path.join(SCRIPT_DIR, 'sector_hotspots_live.py')
REPORT_DIR = os.path.join(SCRIPT_DIR, '../../../../reports/smallcap')
os.makedirs(REPORT_DIR, exist_ok=True)

CONFIGS = {
    '0924': {'sample_label': '0924', 'min_change_pct': 0.0, 'max_change_pct': 6, 'min_amount_yi': 0.001, 'rounds': 3, 'interval_seconds': 6, 'pick_count': 24, 'role': '竞价尾声观察池', 'desc': '09:24 用来盯集合竞价尾声和临近开盘前的异动小票。'},
    '0935': {'sample_label': '0935', 'min_change_pct': 0.5, 'max_change_pct': 7, 'min_amount_yi': 0.005, 'rounds': 3, 'interval_seconds': 8, 'pick_count': 24, 'role': '先手苗子池', 'desc': '09:35 偏放宽，优先抓早盘先手苗子和板块刚冒头的小票。'},
    '0945': {'sample_label': '0945', 'min_change_pct': 0.6, 'max_change_pct': 8, 'min_amount_yi': 0.005, 'rounds': 4, 'interval_seconds': 8, 'pick_count': 24, 'role': '留强确认池', 'desc': '09:45 偏确认，优先保留已经走出来、强度还在延续的票。'},
    '1004': {'sample_label': '1004', 'min_change_pct': 1.0, 'max_change_pct': 10, 'min_amount_yi': 0.01, 'rounds': 4, 'interval_seconds': 8, 'pick_count': 24, 'role': '热点定型池', 'desc': '10:04 看上午热点是否开始定型，优先看板块成团。'},
    '1301': {'sample_label': '1301', 'min_change_pct': 0.8, 'max_change_pct': 10, 'min_amount_yi': 0.008, 'rounds': 3, 'interval_seconds': 8, 'pick_count': 24, 'role': '午后回流观察池', 'desc': '13:01 看午后开盘第一波回流，优先找有承接的方向。'},
    '1303': {'sample_label': '1303', 'min_change_pct': 0.8, 'max_change_pct': 10, 'min_amount_yi': 0.008, 'rounds': 3, 'interval_seconds': 8, 'pick_count': 24, 'role': '午后回流确认池', 'desc': '13:03 看午后第一波回流里谁不是假动作。'},
    '1421': {'sample_label': '1421', 'min_change_pct': 1.0, 'max_change_pct': 10, 'min_amount_yi': 0.01, 'rounds': 4, 'interval_seconds': 8, 'pick_count': 24, 'role': '尾盘异动观察池', 'desc': '14:21 看尾盘异动预热，优先看板块脉冲。'},
    '1423': {'sample_label': '1423', 'min_change_pct': 1.0, 'max_change_pct': 10, 'min_amount_yi': 0.01, 'rounds': 4, 'interval_seconds': 8, 'pick_count': 24, 'role': '尾盘留强池', 'desc': '14:23 看尾盘真正留强和次日预期票。'},
}


def run_scan(slot: str):
    cfg = CONFIGS[slot]
    out_json = os.path.join(SCRIPT_DIR, '..', 'output', f'latest_{slot}.json')
    cmd = [
        sys.executable, LIVE_SMALLCAP_SCRIPT,
        '--sample-label', cfg['sample_label'],
        '--min-change-pct', str(cfg['min_change_pct']),
        '--max-change-pct', str(cfg['max_change_pct']),
        '--min-amount-yi', str(cfg['min_amount_yi']),
        '--max-total-mv-yi', '100', '--max-circ-mv-yi', '100',
        '--top-n', '120', '--pick-count', str(cfg['pick_count']),
        '--rounds', str(cfg['rounds']), '--interval-seconds', str(cfg['interval_seconds']),
        '--output-json', out_json,
        '--json',
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=300)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or 'scan_failed')
    return json.loads(result.stdout), out_json


def run_sector(slot: str, result_json: str):
    cmd = [sys.executable, SECTOR_SCRIPT, '--input', result_json, '--slot', slot, '--json']
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=180)
    if result.returncode != 0 or not result.stdout:
        return {}
    try:
        return json.loads(result.stdout)
    except Exception:
        return {}


def summary_text(summary):
    if isinstance(summary, dict):
        return summary.get('overall', '无数据')
    return str(summary or '无数据')


def html_stock_block(title, items):
    rows = []
    for x in items[:10]:
        rows.append(f"<div>{x.get('name')} ({x.get('code')}) 涨幅 {x.get('change_pct')}% / track_score {x.get('track_score')}</div>")
    return f"<h2>{title}</h2>{''.join(rows) or '<div>无</div>'}"


def html_sector_block(sector_payload):
    leaders = sector_payload.get('hot_sectors', []) if isinstance(sector_payload, dict) else []
    rows = []
    for i, x in enumerate(leaders[:8], 1):
        leader = x.get('leader') or {}
        followers = x.get('followers') or []
        leader_text = f"龙头：{leader.get('name')} {leader.get('code')} {leader.get('change_pct')}%" if leader else '龙头：无'
        follower_text = '；跟风：' + '、'.join([f"{f.get('name')} {f.get('code')} {f.get('change_pct')}%" for f in followers]) if followers else ''
        rows.append(f"<div>{i}. {x.get('sector')}｜出现{x.get('count')}只｜{leader_text}{follower_text}</div>")
    return f"<h2>热点板块</h2>{''.join(rows) or '<div>暂无板块聚集</div>'}"


def build_html(payload: dict, slot: str, sector_payload: dict) -> str:
    cfg = CONFIGS[slot]
    return f"""
    <html><head><meta charset='UTF-8'><title>中小盘多时点扫描 {slot}</title></head>
    <body style='font-family:微软雅黑,Arial;padding:20px;line-height:1.6;'>
    <h1>A股中小盘多时点多轮采样报告 - {slot}</h1>
    <p><b>角色定位：</b>{cfg['role']}</p>
    <p><b>说明：</b>{cfg['desc']}</p>
    <p><b>生成时间：</b>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p><b>策略：</b>{payload.get('strategy')}</p>
    <p><b>总结：</b>{summary_text(payload.get('chinese_summary'))}</p>
    {html_sector_block(sector_payload)}
    {html_stock_block('真龙头', payload.get('true_leaders', []))}
    {html_stock_block('强跟风', payload.get('strong_followers', []))}
    {html_stock_block('观察池', payload.get('watchlist', []))}
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
        raise SystemExit('slot must be one of: ' + ', '.join(CONFIGS.keys()))
    payload, out_json = run_scan(slot)
    sector_payload = run_sector(slot, out_json)
    payload['slot_role'] = CONFIGS[slot]['role']
    payload['slot_desc'] = CONFIGS[slot]['desc']
    payload['sector_hotspots'] = sector_payload
    html = build_html(payload, slot, sector_payload)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_path = os.path.join(REPORT_DIR, f'smallcap_slot_{slot}_{ts}.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    send_email(f'【{slot}｜{CONFIGS[slot]["role"]}】A股中小盘多时点板块报告', html)
    print(json.dumps({'slot': slot, 'role': CONFIGS[slot]['role'], 'report': out_path, 'true_leaders': len(payload.get('true_leaders', [])), 'strong_followers': len(payload.get('strong_followers', [])), 'watchlist': len(payload.get('watchlist', [])), 'hot_sectors': sector_payload.get('hot_sectors', [])[:5]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
