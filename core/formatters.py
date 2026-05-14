"""Output formatters."""
from decimal import Decimal
from datetime import datetime, date

def format_money(v, currency="USD") -> str:
    try:
        return f"{currency} {Decimal(v):,.2f}"
    except Exception:
        return f"{currency} 0.00"

def format_date(v) -> str:
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    return str(v) if v else ""

def jsonable(obj):
    """Recursively convert Decimal/datetime → JSON-friendly types."""
    if isinstance(obj, list):  return [jsonable(x) for x in obj]
    if isinstance(obj, dict):  return {k: jsonable(v) for k, v in obj.items()}
    if isinstance(obj, Decimal): return float(obj)
    if isinstance(obj, (datetime, date)): return obj.isoformat()
    return obj
