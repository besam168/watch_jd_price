from __future__ import annotations

import ctypes
import time

WHEEL_DELTA = 120
MOUSEEVENTF_WHEEL = 0x0800


def main() -> int:
    user32 = ctypes.windll.user32
    time.sleep(0.5)
    # 分两次下拉：比一次大滚动更稳，更容易加载出更多新闻
    user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, -WHEEL_DELTA * 4, 0)
    time.sleep(0.6)
    user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, -WHEEL_DELTA * 4, 0)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
