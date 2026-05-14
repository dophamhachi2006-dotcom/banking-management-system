"""Common validators."""
import re
from datetime import datetime

EMAIL_RE = re.compile(r"^[\w.\-+]+@[\w\-]+\.[\w\-.]+$")
PHONE_RE = re.compile(r"^[\d\-\+\s\(\)]{6,20}$")

def is_email(s: str) -> bool:
    return bool(s and EMAIL_RE.match(s))

def is_phone(s: str) -> bool:
    return bool(s and PHONE_RE.match(s))

def is_positive_amount(v) -> bool:
    try:
        return float(v) > 0
    except (TypeError, ValueError):
        return False

def is_iso_date(s: str) -> bool:
    try:
        datetime.strptime(s, "%Y-%m-%d"); return True
    except (TypeError, ValueError):
        return False

def require(data: dict, fields: list[str]) -> list[str]:
    return [f for f in fields if data.get(f) in (None, "", [])]
