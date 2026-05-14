"""Audit log: read + basic filters + synthesized activity view."""
from flask import Blueprint, request
from core.db_connection import get_cursor
from core.auth import auth_required
from backend.api_response import ok, paginate

bp = Blueprint("audit", __name__)


@bp.get("")
@auth_required(roles=["manager", "auditor"])
def list_audit():
    """List audit log entries with filters for table / action / user / date range."""
    page, size, offset = paginate(request.args)
    args = request.args
    where, params = [], []
    if args.get("table"):
        where.append("TableName=%s")
        params.append(args["table"])
    if args.get("action"):
        where.append("Action=%s")
        params.append(args["action"])
    if args.get("user_id"):
        where.append("PerformedBy=%s")
        params.append(args["user_id"])
    if args.get("from"):
        where.append("CreatedAt >= %s")
        params.append(args["from"])
    if args.get("to"):
        where.append("CreatedAt <= %s")
        params.append(args["to"])
    q = (args.get("q") or "").strip()
    if q:
        if q.isdigit():
            where.append("(AuditID=%s OR RecordID=%s)")
            params += [int(q), int(q)]
        else:
            where.append("(TableName LIKE %s OR Action LIKE %s)")
            like = f"%{q}%"
            params += [like, like]

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    with get_cursor() as cur:
        try:
            cur.execute(
                f"SELECT COUNT(*) AS c FROM AuditLog {where_sql}", params
            )
            total = cur.fetchone()["c"]
            cur.execute(
                f"""SELECT a.*, u.Username AS PerformedByName
                    FROM AuditLog a
                    LEFT JOIN Users u ON u.UserID=a.PerformedBy
                    {where_sql}
                    ORDER BY a.CreatedAt DESC LIMIT %s OFFSET %s""",
                [*params, size, offset],
            )
            rows = cur.fetchall()
        except Exception:
            # If JOIN fails because Users table shape differs, fall back to plain
            cur.execute(
                f"""SELECT * FROM AuditLog {where_sql}
                    ORDER BY CreatedAt DESC LIMIT %s OFFSET %s""",
                [*params, size, offset],
            )
            rows = cur.fetchall()
    return ok({"items": rows, "total": total, "page": page, "size": size})


@bp.get("/summary")
@auth_required(roles=["manager", "auditor"])
def audit_summary():
    """Audit summary: counts by action + by table for dashboards."""
    with get_cursor() as cur:
        by_action = []
        by_table = []
        try:
            cur.execute(
                """SELECT Action, COUNT(*) AS c FROM AuditLog
                   GROUP BY Action ORDER BY c DESC"""
            )
            by_action = cur.fetchall()
            cur.execute(
                """SELECT TableName, COUNT(*) AS c FROM AuditLog
                   GROUP BY TableName ORDER BY c DESC"""
            )
            by_table = cur.fetchall()
        except Exception:
            pass
    return ok({"by_action": by_action, "by_table": by_table})
