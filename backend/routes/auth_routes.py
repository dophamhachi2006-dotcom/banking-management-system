"""Auth routes: login / me / logout."""
from flask import Blueprint, request, g
from werkzeug.security import check_password_hash
from core.db_connection import get_cursor
from core.auth import issue_token, auth_required
from backend.api_response import ok, fail

bp = Blueprint("auth", __name__)

@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username, password = data.get("username"), data.get("password")
    if not username or not password:
        return fail("username & password required", 400)
    with get_cursor() as cur:
        cur.execute("SELECT * FROM Users WHERE Username=%s AND IsActive=1", (username,))
        user = cur.fetchone()
    if not user or not check_password_hash(user["PasswordHash"], password):
        return fail("Invalid credentials", 401)
    with get_cursor(commit=True) as cur:
        cur.execute("UPDATE Users SET LastLoginAt=NOW() WHERE UserID=%s", (user["UserID"],))
    token = issue_token(user)
    return ok({"token": token, "user": {
        "id": user["UserID"], "username": user["Username"], "role": user["Role"]
    }}, "Login successful")

@bp.get("/me")
@auth_required()
def me():
    return ok(g.current_user)

@bp.post("/logout")
@auth_required()
def logout():
    # Stateless JWT — client deletes token. Could blacklist if Redis available.
    return ok(None, "Logged out")
