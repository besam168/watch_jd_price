#!/usr/bin/env python3
import argparse
import json
import os
import smtplib
import ssl
import subprocess
import sys
import time
from datetime import datetime
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PLUGIN_NAME = 'A股开盘风向与实时盯盘插件 V6自动指令版'
BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE = BASE_DIR.parent.parent
FORMAL_SCRIPT = WORKSPACE / 'skills' / 'a-share-opening-flow' / 'scripts' / 'opening_flow.py'
TEST_SCRIPT = WORKSPACE / 'skills' / 'a-share-opening-flow-v6-test' / 'scripts' / 'opening_flow_v6_test.py'
STATE_DIR = BASE_DIR / 'output'
STATE_FILE = STATE_DIR / 'auto_state.json'
HEARTBEAT_SECONDS = 30

SMTP_SERVER = 'smtp.qq.com'
SMTP_PORT = 465
SENDER_EMAIL = '910633260@qq.com'
SMTP_PASSWORD = 'sghqeeeeyuzjbcbb'
RECIPIENTS = ['besam168168@gmail.com', '758622673@qq.com']
EMAIL_STAGE_TIMES = {'09:25', '09:33', '09:38', '09:45'}

PYTHON_EXE = sys.executable

DEFAULT_STAGES = [
    ('09:15', '启动阶段', '载入当天自动流程', None),
    ('09:25', '竞价风向阶段', '正式版优先，测试版兜底', [PYTHON_EXE, str(FORMAL_SCRIPT), '--json']),
    ('09:33', '第一轮初筛阶段', '正式版优先，测试版兜底', [PYTHON_EXE, str(FORMAL_SCRIPT), '--json']),
    ('09:38', '第二轮筛选逻辑阶段', '正式版优先，测试版兜底', [PYTHON_EXE, str(FORMAL_SCRIPT), '--json']),
    ('09:43', '二次强弱确认阶段', '正式版优先，测试版兜底', [PYTHON_EXE, str(FORMAL_SCRIPT), '--json']),
    ('09:45', '上午主看名单阶段', '正式版优先，测试版兜底', [PYTHON_EXE, str(FORMAL_SCRIPT), '--json']),
]


def ensure_state_dir():
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def load_state():
    ensure_state_dir()
    default_state = {
        'trading_day': datetime.now().strftime('%Y-%m-%d'),
        'executed': [],
        'emailed': [],
    }
    if not STATE_FILE.exists():
        return default_state
    try:
        data = json.loads(STATE_FILE.read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            return default_state
        data.setdefault('trading_day', default_state['trading_day'])
        data.setdefault('executed', [])
        data.setdefault('emailed', [])
        return data
    except Exception:
        return default_state


def save_state(state):
    ensure_state_dir()
    state['updated_at'] = datetime.now().isoformat(timespec='seconds')
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')


def refresh_state_for_today(state):
    today = datetime.now().strftime('%Y-%m-%d')
    if state.get('trading_day') != today:
        state = {'trading_day': today, 'executed': [], 'emailed': []}
        save_state(state)
    return state


def fmt_pct(value):
    try:
        return f"{float(value):.2f}%"
    except Exception:
        return str(value)


def fmt_yi(value):
    try:
        return f"{float(value):.2f}亿"
    except Exception:
        return f"{value}亿"


def pick_focus_list(stage_time: str, payload: dict):
    if stage_time == '09:25':
        return payload.get('first_round_candidates', [])[:3]
    if stage_time == '09:33':
        return payload.get('first_round_candidates', [])[:3]
    if stage_time == '09:38':
        items = payload.get('passed', [])[:3]
        return items if items else payload.get('partial', [])[:3]
    if stage_time == '09:45':
        items = payload.get('resonance_core', [])[:3]
        return items if items else payload.get('resonance_follow', [])[:3]
    return []


def build_stage_summary(stage_time: str, payload: dict):
    if stage_time == '09:25':
        sectors = payload.get('top_sectors', [])[:2]
        names = '、'.join([x.get('name', '') for x in sectors if x.get('name')]) or '板块尚在轮动'
        return f'竞价阶段最强方向集中在{name}，先看板块热度是否能在开盘后转成个股承接。'
    if stage_time == '09:33':
        candidates = payload.get('first_round_candidates', [])[:3]
        names = '、'.join([x.get('name', '') for x in candidates if x.get('name')]) or '候选池前排'
        return f'初筛阶段前排已开始分化，当前优先盯{name}，重点看量价延续与分时承接。'
    if stage_time == '09:38':
        passed = payload.get('passed', [])[:3]
        names = '、'.join([x.get('name', '') for x in passed if x.get('name')]) or '通过票'
        return f'二筛后强弱已拉开，当前通过票里优先看{name}，其余只保留观察，不追杂毛。'
    if stage_time == '09:45':
        core = payload.get('resonance_core', [])[:3]
        names = '、'.join([x.get('name', '') for x in core if x.get('name')]) or '核心票'
        return f'上午主看名单已经成形，当前核心优先盯{names}，后续只做留强去弱。'
    return '阶段结果已生成。'


def render_focus_text(row):
    parts = [f"{row.get('name', '')} {row.get('code', '')}"]
    if row.get('change_pct') is not None:
        parts.append(f"涨幅{fmt_pct(row.get('change_pct', 0))}")
    if row.get('amount_yi') not in (None, ''):
        parts.append(f"成交额{fmt_yi(row.get('amount_yi', 0))}")
    if row.get('score') is not None:
        parts.append(f"score={row.get('score', 0)}")
    return '｜'.join(parts)


def build_action_advice(stage_time: str, payload: dict):
    if stage_time == '09:25':
        main_watch = pick_focus_list(stage_time, payload)
        follow = payload.get('first_round_candidates', [])[3:6]
        avoid = []
    elif stage_time == '09:33':
        main_watch = pick_focus_list(stage_time, payload)
        follow = payload.get('first_round_candidates', [])[3:6]
        avoid = []
    elif stage_time == '09:38':
        main_watch = payload.get('passed', [])[:3]
        follow = payload.get('partial', [])[:5]
        avoid = payload.get('failed', [])[:5]
    elif stage_time == '09:45':
        main_watch = payload.get('resonance_core', [])[:5]
        follow = payload.get('resonance_follow', [])[:5]
        avoid = payload.get('partial', [])[:5]
    else:
        main_watch, follow, avoid = [], [], []
    return {
        '主看': main_watch,
        '跟随': follow,
        '不追': avoid,
    }


def build_risk_tips(stage_time: str, payload: dict):
    risks = []
    universe = []
    for key in ['first_round_candidates', 'passed', 'partial', 'failed', 'resonance_core', 'resonance_follow']:
        universe.extend(payload.get(key, []))

    high_gap = [x for x in universe if float(x.get('change_pct', 0) or 0) >= 15][:3]
    if high_gap:
        names = '、'.join([x.get('name', '') for x in high_gap if x.get('name')])
        risks.append(f'高开过猛提醒：{names} 涨幅偏大，若开盘后承接不足，容易出现冲高回落。')

    fake_amount = [x for x in universe if float(x.get('amount_yi', 0) or 0) < 1][:3]
    if fake_amount:
        names = '、'.join([x.get('name', '') for x in fake_amount if x.get('name')])
        risks.append(f'成交额虚高/样本偏轻提醒：{names} 当前成交额偏小，别只看涨幅，先看换手和持续成交。')

    st_names = []
    seen = set()
    for x in universe:
        name = str(x.get('name', '') or '')
        if 'ST' in name.upper() and name not in seen:
            st_names.append(name)
            seen.add(name)
    if st_names:
        risks.append(f'ST剔除提醒：{"、".join(st_names[:5])} 属于高风险样本，默认只观察，不纳入正常主攻池。')

    if stage_time in {'09:25', '09:33'}:
        risks.append('早盘前半段信号容易失真，任何候选都必须结合开盘后 3-5 分钟承接再确认。')
    if not risks:
        risks.append('当前阶段未发现特别极端风险，但仍需防止板块轮动过快导致前排切换。')
    return risks


def render_stage_email(stage_time: str, stage_name: str, payload: dict):
    date_str = datetime.now().strftime('%Y-%m-%d')
    focus = pick_focus_list(stage_time, payload)
    focus_names = '、'.join([f"{x.get('name', '')}{x.get('code', '')}" for x in focus if x.get('name') and x.get('code')]) or '暂无明确前三'
    subject = f'【A股早盘盯盘-{stage_time}】{date_str} {stage_name}｜前三：{focus_names}'
    summary = build_stage_summary(stage_time, payload)
    action_advice = build_action_advice(stage_time, payload)
    risk_tips = build_risk_tips(stage_time, payload)
    lines = [
        'A股早盘自动盯盘分阶段简报',
        f'插件：{PLUGIN_NAME}',
        f'日期：{date_str}',
        f'阶段：{stage_time} {stage_name}',
        f'阶段结论：{summary}',
        '',
        '本阶段最值得盯的前3只',
    ]
    for row in focus:
        lines.append(f'- {render_focus_text(row)}')
    lines.append('')
    html_parts = [
        '<html><body style="font-family:Arial,Microsoft YaHei,sans-serif;line-height:1.7;color:#222;">',
        f'<h2 style="margin-bottom:8px;">【A股早盘盯盘-{stage_time}】{date_str} {stage_name}</h2>',
        '<div style="padding:12px 14px;border:1px solid #e5e7eb;border-radius:10px;background:#f8fafc;">',
        f'<p style="margin:0 0 8px 0;"><b>插件：</b>{PLUGIN_NAME}<br><b>日期：</b>{date_str}<br><b>阶段：</b>{stage_time} {stage_name}</p>',
        f'<p style="margin:0;"><b>阶段结论：</b>{summary}</p>',
        '</div>',
        '<h3 style="margin-top:18px;">本阶段最值得盯的前3只</h3>',
        '<ol>'
    ]
    for row in focus:
        html_parts.append(f'<li>{render_focus_text(row)}</li>')
    html_parts.append('</ol>')

    def add_section(title: str, rows, row_to_text, row_to_html=None):
        if not rows:
            return
        lines.append(title)
        for row in rows:
            lines.append(f'- {row_to_text(row)}')
        lines.append('')
        html_parts.append(f'<h3>{title}</h3><ul>')
        for row in rows:
            text = row_to_html(row) if row_to_html else row_to_text(row)
            html_parts.append(f'<li>{text}</li>')
        html_parts.append('</ul>')

    for title in ['主看', '跟随', '不追']:
        rows = action_advice.get(title, [])
        add_section(title=f'操作建议：{title}', rows=rows, row_to_text=render_focus_text)

    if risk_tips:
        lines.append('风险提示')
        for tip in risk_tips:
            lines.append(f'- {tip}')
        lines.append('')
        html_parts.append('<h3>风险提示</h3><ul>')
        for tip in risk_tips:
            html_parts.append(f'<li>{tip}</li>')
        html_parts.append('</ul>')

    if stage_time == '09:25':
        add_section(
            '竞价最强板块',
            payload.get('top_sectors', [])[:3],
            lambda x: f"{x.get('name', '')} {fmt_pct(x.get('change_pct', 0))}｜龙头{x.get('leading_stock', '')}",
        )
        add_section(
            '盘前观察池',
            payload.get('first_round_candidates', [])[:8],
            lambda x: f"{x.get('name', '')} {x.get('code', '')}",
        )
    elif stage_time == '09:33':
        add_section(
            '第一轮候选池',
            payload.get('first_round_candidates', [])[:12],
            lambda x: f"{x.get('name', '')} {x.get('code', '')}｜{fmt_pct(x.get('change_pct', 0))}｜成交额{fmt_yi(x.get('amount_yi', 0))}",
        )
    elif stage_time == '09:38':
        add_section(
            '第二轮通过',
            payload.get('passed', []),
            lambda x: f"{x.get('name', '')} {x.get('code', '')}｜score={x.get('score', 0)}",
        )
        add_section(
            '第二轮部分通过',
            payload.get('partial', []),
            lambda x: f"{x.get('name', '')} {x.get('code', '')}｜score={x.get('score', 0)}",
        )
        add_section(
            '第二轮不通过',
            payload.get('failed', []),
            lambda x: f"{x.get('name', '')} {x.get('code', '')}｜score={x.get('score', 0)}",
        )
    elif stage_time == '09:45':
        add_section(
            '上午主看核心票',
            payload.get('resonance_core', []),
            lambda x: f"{x.get('name', '')} {x.get('code', '')}",
        )
        add_section(
            '上午主看跟随票',
            payload.get('resonance_follow', []),
            lambda x: f"{x.get('name', '')} {x.get('code', '')}",
        )
        add_section(
            '降级观察票',
            payload.get('partial', []),
            lambda x: f"{x.get('name', '')} {x.get('code', '')}",
        )

    html_parts.append('</body></html>')
    return subject, '\n'.join(lines).strip() + '\n', ''.join(html_parts)


def save_email_preview(stage_time: str, subject: str, text_body: str, html_body: str):
    preview_dir = STATE_DIR / 'mail_previews'
    preview_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d')
    base = preview_dir / f'{stamp}_{stage_time.replace(":", "")}'
    (base.with_suffix('.txt')).write_text(f'Subject: {subject}\n\n{text_body}', encoding='utf-8')
    (base.with_suffix('.html')).write_text(html_body, encoding='utf-8')


def send_stage_email(stage_time: str, stage_name: str, payload: dict):
    subject, text_body, html_body = render_stage_email(stage_time, stage_name, payload)
    save_email_preview(stage_time, subject, text_body, html_body)
    msg = MIMEMultipart('alternative')
    msg['Subject'] = str(Header(subject, 'utf-8'))
    msg['From'] = SENDER_EMAIL
    msg['To'] = ', '.join(RECIPIENTS)
    msg['Date'] = formatdate(localtime=True)
    msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context, timeout=30) as server:
        server.login(SENDER_EMAIL, SMTP_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENTS, msg.as_string())


def print_schedule(now_only: bool = False):
    now_str = datetime.now().strftime('%H:%M')
    printed = False
    for time_str, stage_name, desc, _ in DEFAULT_STAGES:
        if now_only and time_str != now_str:
            continue
        printed = True
        print(f'[{time_str}] {stage_name}')
        print(f'  - {desc}')
    if now_only and not printed:
        print(f'当前时间 {now_str} 不在自动时段内。')


def stage_view(stage_name: str, payload: dict):
    top_sectors = payload.get('top_sectors', [])
    candidates = payload.get('first_round_candidates', [])
    passed = payload.get('passed', [])
    partial = payload.get('partial', [])
    failed = payload.get('failed', [])
    core = payload.get('resonance_core', [])
    follow = payload.get('resonance_follow', [])

    if stage_name == '竞价风向阶段':
        print('竞价最强板块：')
        for x in top_sectors[:3]:
            print(f"- {x.get('name', '')} {x.get('change_pct', 0)}%｜龙头{x.get('leading_stock', '')}")
        print('盘前观察池：')
        for x in candidates[:8]:
            print(f"- {x.get('name', '')} {x.get('code', '')}")
        return

    if stage_name == '第一轮初筛阶段':
        print('第一轮候选池：')
        for x in candidates[:10]:
            print(f"- {x.get('name', '')} {x.get('code', '')}｜{x.get('change_pct', 0)}%｜成交额{x.get('amount_yi', 0)}亿")
        return

    if stage_name == '第二轮筛选逻辑阶段':
        print('第二轮通过：')
        for x in passed:
            print(f"- {x.get('name', '')} {x.get('code', '')}｜score={x.get('score', 0)}")
        print('第二轮部分通过：')
        for x in partial:
            print(f"- {x.get('name', '')} {x.get('code', '')}｜score={x.get('score', 0)}")
        print('第二轮不通过：')
        for x in failed:
            print(f"- {x.get('name', '')} {x.get('code', '')}｜score={x.get('score', 0)}")
        return

    if stage_name == '二次强弱确认阶段':
        print('共振核心（继续观察）：')
        for x in core:
            print(f"- {x.get('name', '')} {x.get('code', '')}")
        print('共振跟随（留强去弱）：')
        for x in follow:
            print(f"- {x.get('name', '')} {x.get('code', '')}")
        return

    if stage_name == '上午主看名单阶段':
        print('上午主看核心票：')
        for x in core:
            print(f"- {x.get('name', '')} {x.get('code', '')}")
        print('上午主看跟随票：')
        for x in follow:
            print(f"- {x.get('name', '')} {x.get('code', '')}")
        print('降级观察票：')
        for x in partial:
            print(f"- {x.get('name', '')} {x.get('code', '')}")
        return


def run_data_script(primary_command):
    env = dict(os.environ)
    env['PYTHONIOENCODING'] = 'utf-8'
    attempts = [
        primary_command,
        [PYTHON_EXE, str(TEST_SCRIPT), '--json'],
    ]
    last = None
    for command in attempts:
        try:
            result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=120, env=env)
            last = (command, result)
            if result.returncode == 0 and result.stdout.strip():
                return command, result
        except Exception as e:
            last = (command, e)
            continue
    return last


def run_stage(stage, state=None):
    time_str, stage_name, desc, command = stage
    print(f'[{time_str}] {stage_name}')
    print(f'  - {desc}')
    if not command:
        print('  - 无需外部脚本调用')
        return 0
    try:
        attempted = run_data_script(command)
        if not attempted:
            print('  - 调用失败: 无可用脚本')
            return 1
        used_command, result = attempted
        if isinstance(result, Exception):
            print(f'  - 调用失败: {result}')
            return 1
        print(f"  - 调用: {' '.join(used_command)}")
        if result.returncode != 0:
            if result.stdout.strip():
                print(result.stdout.strip())
            if result.stderr.strip():
                print(result.stderr.strip())
            return result.returncode
        output = result.stdout.strip()
        payload = None
        try:
            payload = json.loads(output)
            stage_view(stage_name, payload)
        except Exception:
            if output:
                print(output)
        if state is not None and time_str in EMAIL_STAGE_TIMES and payload is not None:
            emailed = set(state.get('emailed', []))
            if time_str not in emailed:
                send_stage_email(time_str, stage_name, payload)
                emailed.add(time_str)
                state['emailed'] = sorted(emailed)
                save_state(state)
                print(f'  - 邮件已发送: {", ".join(RECIPIENTS)}')
        return 0
    except Exception as e:
        print(f'  - 调用失败: {e}')
        return 1


def get_due_stage(now_str: str):
    due = [s for s in DEFAULT_STAGES if s[0] <= now_str]
    if not due:
        return None
    return due[-1]


def run_current_stage(allow_catchup: bool = False):
    state = refresh_state_for_today(load_state())
    now_str = datetime.now().strftime('%H:%M')
    matched = [s for s in DEFAULT_STAGES if s[0] == now_str]
    if matched:
        return run_stage(matched[0], state=state)
    if allow_catchup:
        due = get_due_stage(now_str)
        if due:
            print(f'当前时间 {now_str} 不在自动时段内，补跑最近阶段 {due[0]}。')
            return run_stage(due, state=state)
    print(f'当前时间 {now_str} 不在自动时段内。')
    return 0


def run_auto_loop(poll_seconds: int = 20):
    state = refresh_state_for_today(load_state())
    executed = set(state.get('executed', []))
    print('进入自动调度模式。')
    print(f'状态文件: {STATE_FILE}')
    last_heartbeat = 0.0
    while True:
        now = datetime.now()
        now_str = now.strftime('%H:%M')
        for stage in DEFAULT_STAGES:
            time_str = stage[0]
            if time_str <= now_str and time_str not in executed:
                print(f'触发自动阶段：当前 {now_str}，执行计划节点 {time_str}')
                rc = run_stage(stage, state=state)
                if rc == 0:
                    executed.add(time_str)
                    state['executed'] = sorted(executed)
                    save_state(state)
        if len(executed) == len(DEFAULT_STAGES):
            print('今日自动流程已全部执行完毕。')
            return 0
        now_ts = time.time()
        if now_ts - last_heartbeat >= HEARTBEAT_SECONDS:
            pending = [s[0] for s in DEFAULT_STAGES if s[0] not in executed]
            print(f"[heartbeat {now.strftime('%H:%M:%S')}] 运行中，待执行阶段: {', '.join(pending)}")
            last_heartbeat = now_ts
        time.sleep(poll_seconds)


def main():
    parser = argparse.ArgumentParser(description=PLUGIN_NAME)
    parser.add_argument('--show-schedule', action='store_true', help='显示完整时间流程表')
    parser.add_argument('--run-current-stage', action='store_true', help='只执行当前时间点对应阶段')
    parser.add_argument('--run-nearest-stage', action='store_true', help='若错过整点，则补跑最近一个已到阶段')
    parser.add_argument('--dry-run', action='store_true', help='做一次自动流程模拟')
    parser.add_argument('--auto-loop', action='store_true', help='进入自动调度循环，按时间点执行')
    parser.add_argument('--poll-seconds', type=int, default=20, help='自动调度轮询秒数')
    args = parser.parse_args()

    print(f'{PLUGIN_NAME} 已创建')
    print('流程口诀：9:15启动，9:25竞价，9:33初筛，9:38二筛，9:43确认，9:45定名单。')

    if args.show_schedule:
        print('\n完整时间流程表：')
        print_schedule(now_only=False)

    if args.run_current_stage:
        print('\n当前阶段执行：')
        return run_current_stage(allow_catchup=False)

    if args.run_nearest_stage:
        print('\n最近阶段补跑：')
        return run_current_stage(allow_catchup=True)

    if args.dry_run:
        print('\n自动流程模拟：')
        state = {'trading_day': datetime.now().strftime('%Y-%m-%d'), 'executed': [], 'emailed': []}
        for stage in DEFAULT_STAGES:
            run_stage(stage, state=state)
        print('当前自动指令版已按五个时间点分开输出口径。')
        return 0

    if args.auto_loop:
        return run_auto_loop(args.poll_seconds)

    if not args.show_schedule and not args.run_current_stage and not args.run_nearest_stage and not args.dry_run and not args.auto_loop:
        print('可用参数：--show-schedule / --run-current-stage / --run-nearest-stage / --dry-run / --auto-loop')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
