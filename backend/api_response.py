"""Standardized API response helpers."""
from flask import jsonify
from core.formatters import jsonable

def ok(data=None, message="OK", status=200):
    return jsonify({"success": True, "data": jsonable(data), "message": message}), status

def fail(message="Error", status=400, errors=None):
    return jsonify({"success": False, "data": None, "message": message,
                    "errors": errors or []}), status

def paginate(query_args, default=25, maximum=200):
    try:
        page = max(1, int(query_args.get("page", 1)))
        size = min(maximum, max(1, int(query_args.get("size", default))))
    except ValueError:
        page, size = 1, default
    return page, size, (page - 1) * size
