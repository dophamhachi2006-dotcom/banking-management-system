"""Account routes: list/detail/open/close/freeze + balance + transaction history."""
import time
from flask import Blueprint, request, g
from core.db_connection import get_cursor
from core.auth import auth_required
from backend.api_response import ok, fail, paginate
from backend.utils.query_builder import build_filters, build_order, merge_where
from backend.services.audit_service import log_action

bp = Blueprint("accounts", __name__)


@bp.get("")
@auth_required()
def list_accounts():
    """List accounts with filters + search + dynamic filters/sort."""
    page, size, offset = paginate(request.args)
    args = request.args
    where, params = [], []

    if args.get("customer_id"):
        where.append("a.CustomerID=%s")
        params.append(args["customer_id"])
    if args.get("branch_id"):
        where.append("a.BranchID=%s")
        params.append(args["branch_id"])
    if args.get("status"):
        where.append("a.Status=%s")
        params.append(args["status"])
    if args.get("type"):
        where.append("a.AccountType=%s")
        params.append(args["type"])

    q = (args.get("q") or "").strip()
    if q:
        like = f"%{q}%"
        if q.isdigit():
            where.append(
                "(a.AccountID=%s OR a.AccountNumber LIKE %s OR c.FullName LIKE %s)"
            )
            params += [int(q), like, like]
        else:
            where.append(
                "(a.AccountNumber LIKE %s OR c.FullName LIKE %s)"
            )
            params += [like, like]

    # --- dynamic filters (use alias 'a') ---
    allowed_fields = {
        "Balance": "numeric",
        "AccountType": "string",
    }
    extra_where, extra_params = build_filters(args, allowed_fields, table_alias="a")
    where_sql, params = merge_where(where, params, extra_where, extra_params)

    allowed_sort = {"Balance", "CreatedAt", "OpenedAt", "AccountID"}
    order_sql = build_order(
        args.get("sort"), allowed_sort, default="a.AccountID DESC", table_alias="a"
    )

    base_sql = f"""FROM Accounts a
                   LEFT JOIN Customers c ON c.CustomerID = a.CustomerID
                   LEFT JOIN Branches  b ON b.BranchID  = a.BranchID
                   {where_sql}"""

    with get_cursor() as cur:
        cur.execute(f"SELECT COUNT(*) AS c {base_sql}", params)
        total = cur.fetchone()["c"]

        cur.execute(
            f"""SELECT
                  a.*,
                  COALESCE(c.FullName, '') AS CustomerName,
                  COALESCE(b.BranchName, '') AS BranchName
                {base_sql}
                {order_sql}
                LIMIT %s OFFSET %s""",
            [*params, size, offset],
        )
        rows = cur.fetchall()

    return ok({"items": rows, "total": total, "page": page, "size": size})


@bp.get("/<int:aid>")
@auth_required()
def get_account(aid):
    with get_cursor() as cur:
        cur.execute(
            """SELECT
                 a.AccountID, a.AccountNumber, a.AccountType,
                 a.Balance, a.Currency, a.Status, a.OpenedAt,
                 a.CustomerID, a.BranchID,
                 COALESCE(c.FullName, '') AS CustomerName,
                 COALESCE(b.BranchName, '') AS BranchName
               FROM Accounts a
               LEFT JOIN Customers c ON c.CustomerID = a.CustomerID
               LEFT JOIN Branches  b ON b.BranchID  = a.BranchID
               WHERE a.AccountID = %s""",
            (aid,),
        )
        a = cur.fetchone()
        if not a:
            return fail("Account not found", 404)

        cur.execute(
            """SELECT t.TransactionID, t.TxType, t.Amount, t.BalanceAfter,
                      t.Description, t.CreatedAt
               FROM Transactions t
               WHERE t.AccountID = %s
               ORDER BY t.CreatedAt DESC
               LIMIT 50""",
            (aid,),
        )
        a["recent_transactions"] = cur.fetchall()

    return ok(a)


@bp.get("/<int:aid>/balance")
@auth_required()
def get_balance(aid):
    with get_cursor() as cur:
        cur.execute(
            "SELECT AccountID, AccountNumber, Balance, Currency, Status"
            " FROM Accounts WHERE AccountID=%s",
            (aid,),
        )
        row = cur.fetchone()
        if not row:
            return fail("Account not found", 404)
    return ok(row)


@bp.post("")
@auth_required(roles=["manager", "teller"])
def create_account():
    d = request.get_json(silent=True) or {}
    if not d.get("CustomerID") or not d.get("BranchID"):
        return fail("CustomerID & BranchID required", 400)
    try:
        balance = float(d.get("Balance", 0) or 0)
        if balance < 0:
            return fail("Initial balance cannot be negative", 400)
    except (TypeError, ValueError):
        return fail("Invalid initial balance", 400)

    acc_no = d.get("AccountNumber") or f"ACC{int(time.time() * 1000)}"
    acc_type = d.get("AccountType", "savings")
    if acc_type not in ("savings", "checking", "fixed"):
        acc_type = "savings"

    with get_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO Accounts
               (AccountNumber,CustomerID,BranchID,AccountType,Balance,Currency,Status)
               VALUES (%s,%s,%s,%s,%s,%s,'active')""",
            (
                acc_no,
                d["CustomerID"],
                d["BranchID"],
                acc_type,
                balance,
                d.get("Currency", "USD"),
            ),
        )
        new_id = cur.lastrowid
    log_action("OPEN_ACCOUNT", "Accounts", new_id,
               new={"AccountNumber": acc_no, "CustomerID": d["CustomerID"],
                    "BranchID": d["BranchID"], "AccountType": acc_type,
                    "Balance": balance})
    return ok({"AccountID": new_id, "AccountNumber": acc_no}, "Account opened", 201)


@bp.put("/<int:aid>/status")
@auth_required(roles=["manager"])
def set_status(aid):
    d = request.get_json(silent=True) or {}
    status = d.get("Status")
    if status not in ("active", "frozen", "closed"):
        return fail("Invalid status. Must be active, frozen, or closed.", 400)

    with get_cursor(commit=True) as cur:
        cur.execute(
            "SELECT Balance, Status FROM Accounts WHERE AccountID=%s", (aid,)
        )
        row = cur.fetchone()
        if not row:
            return fail("Account not found", 404)

        current_status = row["Status"]
        balance = float(row["Balance"] or 0)

        if current_status == "closed" and status != "closed":
            return fail("Closed accounts cannot be reactivated.", 400)

        if status == "closed" and balance > 0.0:
            return fail(
                f"Cannot close account with balance ${balance:,.2f}. "
                "Please withdraw or transfer all funds first.",
                400,
            )

        cur.execute(
            "UPDATE Accounts SET Status=%s WHERE AccountID=%s", (status, aid)
        )
    log_action("SET_ACCOUNT_STATUS", "Accounts", aid,
               old={"Status": current_status}, new={"Status": status})
    return ok(None, f"Account status updated to {status}")


@bp.delete("/<int:aid>")
@auth_required(roles=["manager"])
def close_account(aid):
    with get_cursor(commit=True) as cur:
        cur.execute(
            "SELECT Balance FROM Accounts WHERE AccountID=%s", (aid,)
        )
        row = cur.fetchone()
        if not row:
            return fail("Account not found", 404)
        if float(row["Balance"] or 0) > 0.0:
            return fail("Cannot close account with non-zero balance", 400)
        cur.execute(
            "UPDATE Accounts SET Status='closed' WHERE AccountID=%s", (aid,)
        )
    log_action("CLOSE_ACCOUNT", "Accounts", aid, new={"Status": "closed"})
    return ok(None, "Account closed")
