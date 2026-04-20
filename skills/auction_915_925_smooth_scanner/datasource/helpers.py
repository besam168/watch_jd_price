from datetime import datetime


def in_auction_window(value: str) -> bool:
    try:
        t = datetime.strptime(value, "%H:%M:%S").time()
    except Exception:
        return False
    return "09:15:00" <= t.strftime("%H:%M:%S") <= "09:25:00"


def normalize_symbol(symbol: str) -> str:
    s = symbol.strip().lower()
    if s.startswith(("sh", "sz")):
        return s
    digits = "".join(ch for ch in s if ch.isdigit())
    if digits.startswith(("60", "68", "51", "58", "11")):
        return f"sh{digits}"
    return f"sz{digits}"


def is_sz_mainboard_target(symbol: str) -> bool:
    s = normalize_symbol(symbol)
    if not s.startswith("sz"):
        return False
    code = s[2:]
    if not code.startswith("00"):
        return False
    if code.startswith(("300", "301", "688", "689", "8", "4")):
        return False
    return True
