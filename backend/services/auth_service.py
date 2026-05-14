"""Auth service utilities."""
from werkzeug.security import generate_password_hash
from core.db_connection import get_cursor

def create_user(username: str, password: str, role: str, employee_id=None):
    with get_cursor(commit=True) as cur:
        cur.execute("""INSERT INTO Users (Username,PasswordHash,Role,EmployeeID)
                       VALUES (%s,%s,%s,%s)""",
                    (username, generate_password_hash(password), role, employee_id))
        return cur.lastrowid
