from __future__ import annotations

import argparse
import sys

import pyperclip

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description="Set Windows clipboard text reliably")
    parser.add_argument("text")
    args = parser.parse_args()
    pyperclip.copy(args.text)
    sys.stdout.write(f"Clipboard text set ({len(args.text)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
