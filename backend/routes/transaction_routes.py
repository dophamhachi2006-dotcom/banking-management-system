"""Transactions routes - deposit / withdraw / transfer + fraud detection."""
from flask import Blueprint, request, g
from core.db_connection import get_cursor
from core.auth import auth_required
from backend.api_response import ok, fail, paginate
from backend.services.transaction_service import (
    do_deposit, do_withdraw, do_transfer
)
from backend.services.fraud_service import detect_for_account
from backend.utils.query_builder import build_filters, build_order, merge_where

bp = Blueprint("transactions", __name__)


@bp.get("")
@auth_required()
def list_tx():
    page, size, offset = paginate(request.args)
    args = request.args
    where, params = [], []

    for k, col in [
        ("account_id", "t.AccountID"),
        ("type",       "t.TxType"),
        ("status",     "t.Status"),
    ]:
        v = args.get(k)
        if v:
            where.append(f"{col}=%s")
            params.append(v)

    if args.get("from"):
        where.append("t.CreatedAt >= %s")
        params.append(args["from"])
    if args.get("to"):
        where.append("t.CreatedAt <= %s")
        params.append(args["to"])
    if args.get("min_amount"):
        where.append("t.Amount >= %s")
        params.append(args["min_amount"])
    if args.get("max_amount"):
        where.append("t.Amount <= %s")
        params.append(args["max_amount"])

    q = (args.get("q") or "").strip()
    if q:
        like = f"%{q}%"
        if q.isdigit():
            where.append(
                "(t.TransactionID=%s OR t.AccountID=%s OR a.AccountNumber LIKE %s)"
            )
            params += [int(q), int(q), like]
        else:
            where.append(
                "(c.FullName LIKE %s OR a.AccountNumber LIKE %s OR t.Description LIKE %s)"
            )
            params += [like, like, like]

    # --- dynamic filters ---
    # Accept both TxType and TransactionType from clients.
    allowed_fields = {
        "Amount": "numeric",
        "BalanceAfter": "numeric",
        "TxType": "string",
        "TransactionType": "string",
    }
    extra_where, extra_params = build_filters(args, allowed_fields, table_alias="t")
    # Map TransactionType -> TxType in SQL produced by build_filters
    extra_where = extra_where.replace("t.TransactionType", "t.TxType")
    where_sql, params = merge_where(where, params, extra_where, extra_params)

    allowed_sort = {"Amount", "BalanceAfter", "CreatedAt", "TransactionID"}
    order_sql = build_order(
        args.get("sort"), allowed_sort,
        default="t.CreatedAt DESC", table_alias="t",
    )

    join_sql = """FROM Transactions t
                  LEFT JOIN Accounts  a ON a.AccountID  = t.AccountID
                  LEFT JOIN Customers c ON c.CustomerID = a.CustomerID"""

    with get_cursor() as cur:
        cur.execute(
            f"SELECT COUNT(*) AS c {join_sql} {where_sql}", params
        )
        total = cur.fetchone()["c"]

        cur.execute(
            f"""SELECT
                  t.*,
                  COALESCE(a.AccountNumber, '') AS AccountNumber,
                  COALESCE(c.FullName, '')      AS CustomerName
                {join_sql}
                {where_sql}
                {order_sql}
                LIMIT %s OFFSET %s""",
            [*params, size, offset],
        )
        rows = cur.fetchall()

    return ok({"items": rows, "total": total, "page": page, "size": size})


@bp.post("/deposit")
@auth_required(roles=["manager", "teller"])
def deposit():
    d = request.get_json(silent=True) or {}
    try:
        tx_id, balance = do_deposit(
            d.get("AccountID"), d.get("Amount"),
            g.current_user["uid"], d.get("Description", "Deposit")
        )
        return ok({"TransactionID": tx_id, "Balance": balance}, "Deposit successful")
    except ValueError as e:
        return fail(str(e), 400)


@bp.post("/withdraw")
@auth_required(roles=["manager", "teller"])
def withdraw():
    d = request.get_json(silent=True) or {}
    try:
        tx_id, balance = do_withdraw(
            d.get("AccountID"), d.get("Amount"),
            g.current_user["uid"], d.get("Description", "Withdrawal")
        )
        return ok({"TransactionID": tx_id, "Balance": balance}, "Withdrawal successful")
    except ValueError as e:
        return fail(str(e), 400)


@bp.post("/transfer")
@auth_required(roles=["manager", "teller"])
def transfer():
    d = request.get_json(silent=True) or {}
    try:
        tx_id = do_transfer(
            d.get("FromAccountID"), d.get("ToAccountID"),
            d.get("Amount"), g.current_user["uid"],
            d.get("Description", "Transfer")
        )
        return ok({"TransactionID": tx_id}, "Transfer successful")
    except ValueError as e:
        return fail(str(e), 400)


@bp.get("/fraud/<int:account_id>")
@auth_required(roles=["manager", "auditor"])
def fraud_check(account_id):
    flags = detect_for_account(account_id)
    return ok({"account_id": account_id, "flags": flags, "risk": "high" if flags else "low"})
