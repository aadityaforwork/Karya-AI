import secrets
import time


def new_id(prefix: str) -> str:
    """Short, sortable-ish, human-readable id: <prefix>_<base36 time><rand>."""
    stamp = int(time.time() * 1000)
    return f"{prefix}_{_b36(stamp)}{secrets.token_hex(2)}"


def _b36(n: int) -> str:
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    if n == 0:
        return "0"
    out = []
    while n:
        n, r = divmod(n, 36)
        out.append(digits[r])
    return "".join(reversed(out))
