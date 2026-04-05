#!/usr/bin/env python3
import argparse


def main():
    parser = argparse.ArgumentParser(description='A股竞价与开盘风向识别原型')
    parser.add_argument('--auction-window', default='09:20-09:25', help='竞价窗口')
    parser.add_argument('--open-window', default='09:30-09:35', help='开盘验证窗口')
    parser.add_argument('--date', default='today', help='交易日')
    args = parser.parse_args()

    print('A股开盘风向 V6 原型已创建')
    print(f'竞价窗口: {args.auction_window}')
    print(f'开盘窗口: {args.open_window}')
    print(f'交易日: {args.date}')
    print('当前版本为骨架版，下一步接真实数据采集与板块归类。')


if __name__ == '__main__':
    main()
