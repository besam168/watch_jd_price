#!/usr/bin/env python3
import csv
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / 'outputs'
CSV_PATH = OUTPUT_DIR / f'auction_sniper_v2_{datetime.now().strftime("%Y%m%d")}.csv'
XLSX_PATH = OUTPUT_DIR / f'auction_sniper_v2_{datetime.now().strftime("%Y%m%d")}_excel.xlsx'
MD_PATH = OUTPUT_DIR / f'auction_sniper_v2_{datetime.now().strftime("%Y%m%d")}.md'
LOG_PATH = OUTPUT_DIR / 'mail_send.log'

SENDER = '910633260@qq.com'
PASSWORD = 'sghqeeeeyuzjbcbb'
SMTP_HOST = 'smtp.qq.com'
SMTP_PORT = 465
RECIPIENTS = ['besam168168@gmail.com', '758622673@qq.com']

MANUAL_NAMES = {
    'sz002317': '众生药业',
    'sh603985': '恒润股份',
    'sz002580': '圣阳股份',
    'sz002815': '崇达技术',
    'sz000815': '美利云',
}


def log(msg: str):
    stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with LOG_PATH.open('a', encoding='utf-8') as f:
        f.write(f'[{stamp}] {msg}\n')


def load_passed_rows():
    rows = []
    if not CSV_PATH.exists():
        return rows
    with CSV_PATH.open('r', encoding='gbk', errors='replace', newline='') as f:
        reader = csv.DictReader(f)
        for r in reader:
            if str(r.get('passed', '')).lower() == 'true':
                sym = r.get('symbol', '')
                rows.append({
                    'mode': r.get('mode', ''),
                    'symbol': sym.upper(),
                    'name': MANUAL_NAMES.get(sym, r.get('name', '')),
                    'change_pct': r.get('change_pct', ''),
                    'volume_ratio': r.get('volume_ratio', ''),
                })
    return rows


def make_body(rows):
    date_str = datetime.now().strftime('%Y-%m-%d')
    lines = [f'集合竞价狙击手V2日报 - {date_str}', '', f'命中数量：{len(rows)}', '']
    if not rows:
        lines.append('今日无命中标的。')
    else:
        for i, row in enumerate(rows, start=1):
            mode = '三安模式' if row['mode'] == 'sanan' else ('金螳螂模式' if row['mode'] == 'jinmantang' else row['mode'])
            lines.extend([
                f'{i}. {row["symbol"]} {row["name"]}',
                f'   模式：{mode}',
                f'   涨幅：{row["change_pct"]}%',
                f'   量比：{row["volume_ratio"]}',
                ''
            ])
    lines.append('附件：Excel明细表（如已生成）')
    return '\n'.join(lines)


def attach_file(msg, path: Path):
    if not path.exists():
        return False
    with path.open('rb') as f:
        part = MIMEApplication(f.read(), Name=path.name)
    part['Content-Disposition'] = f'attachment; filename="{path.name}"'
    msg.attach(part)
    return True


def main():
    rows = load_passed_rows()
    body = make_body(rows)

    msg = MIMEMultipart()
    msg['From'] = SENDER
    msg['To'] = ', '.join(RECIPIENTS)
    msg['Subject'] = f'集合竞价狙击手V2日报 {datetime.now().strftime("%Y-%m-%d")}'
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    attached = []
    for p in [XLSX_PATH, MD_PATH]:
        if attach_file(msg, p):
            attached.append(str(p))

    log('MAIL_PREP recipients=' + ','.join(RECIPIENTS) + ' attached=' + ','.join(attached))
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(SENDER, PASSWORD)
        server.sendmail(SENDER, RECIPIENTS, msg.as_string())
    log('MAIL_SENT_OK')
    print('MAIL_SENT_OK')


if __name__ == '__main__':
    main()
