"""Run once after `mysql < seed_data.sql` to set real bcrypt-style hashes
for the default users (admin / teller1 / audit1)."""
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.security import generate_password_hash
from core.db_connection import get_cursor

DEFAULTS = [
    ("admin",  "admin123"),
    ("teller1","teller123"),
    ("audit1", "audit123"),
]

if __name__ == "__main__":
    with get_cursor(commit=True) as cur:
        for u, p in DEFAULTS:
            cur.execute("UPDATE Users SET PasswordHash=%s WHERE Username=%s",
                        (generate_password_hash(p), u))
    print("✅ Default user passwords updated:", ", ".join(u for u,_ in DEFAULTS))
