#!/usr/bin/env python3
import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PLUGIN_NAME = 'A股开盘风向与实时盯盘插件 V6自动指令版'
BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE = BASE_DIR.parent.parent
TEST_SCRIPT = WORKSPACE / 'skills' / 'a-share-opening-flow-v6-test' / 'scripts' / 'opening_flow_v6_test.py'

DEFAULT_STAGES = [
    ('09:15', '启动阶段', '载入当天自动流程', None),
    ('09:25', '竞价风向阶段', '看竞价最强板块、竞价龙头、盘前观察池', ['python', str(TEST_SCRIPT)]),
    ('09:33', '第一轮初筛阶段', '看开盘后真强票、最强板块、龙头、第一轮候选池', ['python', str(TEST_SCRIPT)]),
    ('09:38', '第二轮筛选逻辑阶段', '对第一轮候选池跑近3日放量、近3日拉升、5日线宽松辅助', ['python', str(TEST_SCRIPT), '--filter-volume-3d', '--filter-price-3d', '--filter-ma5-soft']),
    ('09:43', '二次强弱确认阶段', '留强去弱，更新主线、龙头、掉队票', ['python', str(TEST_SCRIPT), '--filter-volume-3d', '--filter-price-3d', '--filter-ma5-soft']),
    ('09:45', '上午主看名单阶段', '定主看核心票、主看跟随票、降级观察票和风险预警', ['python', str(TEST_SCRIPT), '--filter-volume-3d', '--filter-price-3d', '--filter-ma5-soft']),
]


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


def run_stage(stage):
    time_str, stage_name, desc, command = stage
    print(f'[{time_str}] {stage_name}')
    print(f'  - {desc}')
    if not command:
        print('  - 无需外部脚本调用')
        return 0
    print(f'  - 调用: {' '.join(command)}')
    try:
        env = dict(**__import__('os').environ)
        env['PYTHONIOENCODING'] = 'utf-8'
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60, env=env)
        if result.stdout.strip():
            print(result.stdout.strip())
        if result.stderr.strip():
            print(result.stderr.strip())
        return result.returncode
    except Exception as e:
        print(f'  - 调用失败: {e}')
        return 1


def run_current_stage():
    now_str = datetime.now().strftime('%H:%M')
    matched = [s for s in DEFAULT_STAGES if s[0] == now_str]
    if not matched:
        print(f'当前时间 {now_str} 不在自动时段内。')
        return 0
    return run_stage(matched[0])


def run_auto_loop(poll_seconds: int = 20):
    print('进入自动调度模式。')
    executed = set()
    while True:
        now_str = datetime.now().strftime('%H:%M')
        for stage in DEFAULT_STAGES:
            time_str = stage[0]
            if time_str == now_str and time_str not in executed:
                run_stage(stage)
                executed.add(time_str)
        if len(executed) == len(DEFAULT_STAGES):
            print('今日自动流程已全部执行完毕。')
            return 0
        time.sleep(poll_seconds)


def main():
    parser = argparse.ArgumentParser(description=PLUGIN_NAME)
    parser.add_argument('--show-schedule', action='store_true', help='显示完整时间流程表')
    parser.add_argument('--run-current-stage', action='store_true', help='只执行当前时间点对应阶段')
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
        return run_current_stage()

    if args.dry_run:
        print('\n自动流程模拟：')
        for stage in DEFAULT_STAGES:
            run_stage(stage)
        print('当前为自动指令版增强骨架，已能按阶段调用 V6测试版入口。')
        return 0

    if args.auto_loop:
        return run_auto_loop(args.poll_seconds)

    if not args.show_schedule and not args.run_current_stage and not args.dry_run and not args.auto_loop:
        print('可用参数：--show-schedule / --run-current-stage / --dry-run / --auto-loop')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
