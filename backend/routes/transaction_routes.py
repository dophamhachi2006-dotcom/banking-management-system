"""Transactions routes - deposit / withdraw / transfer + fraud detection."""
from flask import Blueprint, request, g
from core.db_connection import get_cursor
from core.auth import auth_required
from backend.api_response import ok, fail, paginate
from backend.services.transaction_service import (
    do_deposit, do_withdraw, do_transfer
)
from backend.services.fraud_service import detect_for_account
from backend.services.audit_service import log_action
from backend.utils.query_builder import build_filters, build_order, merge_where

bp = Blueprint("transactions", __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _coerce_account_id(value, field_name="AccountID"):
    """Validate and cast an AccountID to int. Raises ValueError on bad input."""
    if value in (None, "", 0, "0"):
        raise ValueError(f"{field_name} is required")
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid {field_name}: {value!r}")


def _ensure_account_exists(cur, account_id, field_name="AccountID",
                           require_active=True):
    """Look up an account, return the row, or raise ValueError with a
    user-friendly message if it doesn't exist / isn't usable."""
    cur.execute(
        "SELECT AccountID, Status FROM Accounts WHERE AccountID=%s",
        (account_id,),
    )
    row = cur.fetchone()
    if not row:
        raise ValueError(f"{field_name} #{account_id} does not exist")
    if require_active and row.get("Status") and row["Status"] != "active":
        raise ValueError(
            f"{field_name} #{account_id} is {row['Status']}, "
            f"cannot be used for transactions"
        )
    return row


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
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

    allowed_fields = {
        "Amount": "numeric",
        "BalanceAfter": "numeric",
        "TxType": "string",
        "TransactionType": "string",
    }
    extra_where, extra_params = build_filters(args, allowed_fields, table_alias="t")
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
        acc_id = _coerce_account_id(d.get("AccountID"))
        with get_cursor() as cur:
            _ensure_account_exists(cur, acc_id)
        tx_id, balance = do_deposit(
            acc_id, d.get("Amount"),
            g.current_user["uid"], d.get("Description", "Deposit")
        )
        log_action("DEPOSIT", "Transactions", tx_id,
                   new={"AccountID": acc_id, "Amount": float(d.get("Amount") or 0),
                        "BalanceAfter": balance, "Description": d.get("Description")})
        return ok({"TransactionID": tx_id, "Balance": balance}, "Deposit successful")
    except ValueError as e:
        return fail(str(e), 400)


@bp.post("/withdraw")
@auth_required(roles=["manager", "teller"])
def withdraw():
    d = request.get_json(silent=True) or {}
    try:
        acc_id = _coerce_account_id(d.get("AccountID"))
        with get_cursor() as cur:
            _ensure_account_exists(cur, acc_id)
        tx_id, balance = do_withdraw(
            acc_id, d.get("Amount"),
            g.current_user["uid"], d.get("Description", "Withdrawal")
        )
        log_action("WITHDRAW", "Transactions", tx_id,
                   new={"AccountID": acc_id, "Amount": float(d.get("Amount") or 0),
                        "BalanceAfter": balance, "Description": d.get("Description")})
        return ok({"TransactionID": tx_id, "Balance": balance}, "Withdrawal successful")
    except ValueError as e:
        return fail(str(e), 400)


@bp.post("/transfer")
@auth_required(roles=["manager", "teller"])
def transfer():
    d = request.get_json(silent=True) or {}
    try:
        from_id = _coerce_account_id(d.get("FromAccountID"), "FromAccountID")
        to_id   = _coerce_account_id(d.get("ToAccountID"),   "ToAccountID")
        if from_id == to_id:
            return fail("Cannot transfer to the same account", 400)
        with get_cursor() as cur:
            _ensure_account_exists(cur, from_id, "FromAccountID")
            _ensure_account_exists(cur, to_id,   "ToAccountID")
        tx_id = do_transfer(
            from_id, to_id,
            d.get("Amount"), g.current_user["uid"],
            d.get("Description", "Transfer")
        )
        log_action("TRANSFER", "Transactions", tx_id,
                   new={"FromAccountID": from_id, "ToAccountID": to_id,
                        "Amount": float(d.get("Amount") or 0),
                        "Description": d.get("Description")})
        return ok({"TransactionID": tx_id}, "Transfer successful")
    except ValueError as e:
        return fail(str(e), 400)


@bp.get("/fraud/<int:account_id>")
@auth_required(roles=["manager", "auditor"])
def fraud_check(account_id):
    flags = detect_for_account(account_id)
    return ok({"account_id": account_id, "flags": flags, "risk": "high" if flags else "low"})
