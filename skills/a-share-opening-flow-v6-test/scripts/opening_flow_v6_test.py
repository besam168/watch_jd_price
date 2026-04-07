#!/usr/bin/env python3
import argparse


PLUGIN_NAME = 'A股开盘风向与实时盯盘插件 V6（测试版）'


def main():
    parser = argparse.ArgumentParser(description=PLUGIN_NAME)
    parser.add_argument('--auction-window', default='09:20-09:25', help='竞价窗口')
    parser.add_argument('--open-window', default='09:30-09:35', help='开盘验证窗口')
    parser.add_argument('--date', default='today', help='交易日')
    parser.add_argument('--filter-volume-3d', action='store_true', help='启用近3日放量过滤')
    parser.add_argument('--filter-price-3d', action='store_true', help='启用近3日拉升过滤')
    parser.add_argument('--filter-ma5-soft', action='store_true', help='启用5日线宽松辅助过滤')
    args = parser.parse_args()

    print(f'{PLUGIN_NAME} 已创建')
    print(f'竞价窗口: {args.auction_window}')
    print(f'开盘窗口: {args.open_window}')
    print(f'交易日: {args.date}')
    print('当前版本为测试版骨架，基于正式版早盘判断，叠加近3日放量拉升过滤。')
    print(f'近3日放量过滤: {"开" if args.filter_volume_3d else "关"}')
    print(f'近3日拉升过滤: {"开" if args.filter_price_3d else "关"}')
    print(f'5日线宽松辅助: {"开" if args.filter_ma5_soft else "关"}')


if __name__ == '__main__':
    main()
