"""Reports + Analytics routes."""
from flask import Blueprint, request
from core.db_connection import get_cursor
from core.auth import auth_required
from backend.api_response import ok
from backend.services.report_service import (
    dashboard_stats, top_customers, branch_performance,
    monthly_summary, suspicious_transactions, revenue_report,
    tx_type_breakdown, fraud_overview,
)
from backend.utils.query_builder import build_filters, build_order

bp = Blueprint("reports", __name__)


@bp.get("/dashboard")
@auth_required()
def dashboard():
    return ok(dashboard_stats())


@bp.get("/top-customers")
@auth_required()
def top():
    limit = int(request.args.get("limit", 10))
    return ok(top_customers(limit))


@bp.get("/branch-performance")
@auth_required()
def branches():
    return ok(branch_performance())


@bp.get("/monthly-summary")
@auth_required()
def monthly():
    return ok(monthly_summary())


@bp.get("/revenue")
@auth_required()
def revenue():
    months = int(request.args.get("months", 12))
    return ok(revenue_report(months))


@bp.get("/tx-breakdown")
@auth_required()
def tx_breakdown():
    return ok(tx_type_breakdown())


@bp.get("/fraud")
@auth_required(roles=["manager", "auditor"])
def fraud():
    return ok(fraud_overview())


@bp.get("/suspicious")
@auth_required(roles=["manager", "auditor"])
def suspicious():
    """Suspicious transactions with optional dynamic filters & sort.

    Falls back to the original suspicious_transactions() service when no
    filter/sort is supplied, preserving previous behavior.
    """
    args = request.args
    has_dynamic = any(
        k for k in args.keys()
        if k == "sort" or any(k.endswith(f"_{op}") for op in
                              ("gt", "lt", "eq", "gte", "lte", "like", "ne"))
    )
    if not has_dynamic:
        return ok(suspicious_transactions())

    allowed_fields = {
        "Amount": "numeric",
        "Timestamp": "string",   # ISO datetime string compares lexically OK
        "CreatedAt": "string",
    }
    extra_where, params = build_filters(args, allowed_fields, table_alias="t")
    extra_where = extra_where.replace("t.Timestamp", "t.CreatedAt")

    allowed_sort = {"Amount", "Timestamp", "CreatedAt"}
    sort_param = args.get("sort")
    if sort_param and sort_param.startswith("Timestamp_"):
        sort_param = sort_param.replace("Timestamp_", "CreatedAt_", 1)
    order_sql = build_order(
        sort_param, allowed_sort, default="t.CreatedAt DESC", table_alias="t",
    )

    base_where = "t.Amount >= 10000 AND t.CreatedAt >= DATE_SUB(NOW(), INTERVAL 30 DAY)"
    if extra_where:
        where_sql = f"WHERE {base_where} AND " + extra_where.replace("WHERE ", "", 1)
    else:
        where_sql = f"WHERE {base_where}"

    sql = f"""
        SELECT t.TransactionID, t.AccountID, a.AccountNumber,
               c.FullName AS CustomerName, t.TxType, t.Amount, t.CreatedAt
        FROM Transactions t
        LEFT JOIN Accounts  a ON a.AccountID  = t.AccountID
        LEFT JOIN Customers c ON c.CustomerID = a.CustomerID
        {where_sql}
        {order_sql}
        LIMIT 200
    """
    with get_cursor() as cur:
        try:
            cur.execute(sql, params)
            rows = cur.fetchall()
        except Exception:
            rows = []
    return ok(rows)
