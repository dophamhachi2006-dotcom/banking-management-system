"""JWT helpers."""
import os, jwt, datetime as dt
from functools import wraps
from flask import request, jsonify, g

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_ALG = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "8"))

def issue_token(user: dict) -> str:
    payload = {
        "uid":  user["UserID"],
        "uname": user["Username"],
        "role": user["Role"],
        "exp":  dt.datetime.utcnow() + dt.timedelta(hours=JWT_EXPIRE_HOURS),
        "iat":  dt.datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])

def auth_required(roles: list[str] | None = None):
    """Decorator: protect a route. Optionally restrict by role."""
    def deco(fn):
        @wraps(fn)
        def wrapper(*a, **kw):
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return jsonify({"success": False, "message": "Missing token"}), 401
            try:
                payload = decode_token(auth.split(" ", 1)[1])
            except jwt.ExpiredSignatureError:
                return jsonify({"success": False, "message": "Token expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"success": False, "message": "Invalid token"}), 401
            if roles and payload["role"] not in roles:
                return jsonify({"success": False, "message": "Forbidden"}), 403
            g.current_user = payload
            return fn(*a, **kw)
        return wrapper
    return deco
