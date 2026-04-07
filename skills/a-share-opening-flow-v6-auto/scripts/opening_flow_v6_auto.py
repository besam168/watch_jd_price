#!/usr/bin/env python3
import argparse
from datetime import datetime

PLUGIN_NAME = 'A股开盘风向与实时盯盘插件 V6自动指令版'
DEFAULT_STAGES = [
    ('09:15', '启动阶段', '载入当天自动流程'),
    ('09:25', '竞价风向阶段', '看竞价最强板块、竞价龙头、盘前观察池'),
    ('09:33', '第一轮初筛阶段', '看开盘后真强票、最强板块、龙头、第一轮候选池'),
    ('09:38', '第二轮筛选逻辑阶段', '对第一轮候选池跑近3日放量、近3日拉升、5日线宽松辅助'),
    ('09:43', '二次强弱确认阶段', '留强去弱，更新主线、龙头、掉队票'),
    ('09:45', '上午主看名单阶段', '定主看核心票、主看跟随票、降级观察票和风险预警'),
]


def print_schedule(now_only: bool = False):
    now_str = datetime.now().strftime('%H:%M')
    printed = False
    for time_str, stage_name, desc in DEFAULT_STAGES:
        if now_only and time_str != now_str:
            continue
        printed = True
        print(f'[{time_str}] {stage_name}')
        print(f'  - {desc}')
    if now_only and not printed:
        print(f'当前时间 {now_str} 不在自动时段内。')


def main():
    parser = argparse.ArgumentParser(description=PLUGIN_NAME)
    parser.add_argument('--show-schedule', action='store_true', help='显示完整时间流程表')
    parser.add_argument('--run-current-stage', action='store_true', help='只显示当前时间点对应阶段')
    parser.add_argument('--dry-run', action='store_true', help='做一次自动流程模拟，不接入真实选股逻辑')
    args = parser.parse_args()

    print(f'{PLUGIN_NAME} 已创建')
    print('流程口诀：9:15启动，9:25竞价，9:33初筛，9:38二筛，9:43确认，9:45定名单。')

    if args.show_schedule:
        print('\n完整时间流程表：')
        print_schedule(now_only=False)

    if args.run_current_stage:
        print('\n当前阶段：')
        print_schedule(now_only=True)

    if args.dry_run:
        print('\n自动流程模拟：')
        for time_str, stage_name, desc in DEFAULT_STAGES:
            print(f'[{time_str}] {stage_name} -> {desc}')
        print('当前为自动指令版骨架，后续再接入真实时段调度与选股逻辑。')

    if not args.show_schedule and not args.run_current_stage and not args.dry_run:
        print('可用参数：--show-schedule / --run-current-stage / --dry-run')


if __name__ == '__main__':
    main()
