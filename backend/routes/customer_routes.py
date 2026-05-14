from flask import Blueprint, request, g
from core.db_connection import get_cursor
from core.auth import auth_required
from core.validators import require, is_email
from backend.api_response import ok, fail, paginate
from backend.utils.query_builder import build_filters, build_order, merge_where

bp = Blueprint("customers", __name__)


@bp.get("")
@auth_required()
def list_customers():
    """List customers using vw_customer_summary with dynamic filters & sort."""
    page, size, offset = paginate(request.args)
    q = (request.args.get("q") or "").strip()

    where_parts, params = [], []

    if q:
        like = f"%{q}%"
        if q.isdigit():
            where_parts.append(
                "(CustomerID = %s OR FullName LIKE %s OR Email LIKE %s OR Phone LIKE %s OR IDNumber LIKE %s)"
            )
            params += [int(q), like, like, like, like]
        else:
            where_parts.append(
                "(FullName LIKE %s OR Email LIKE %s OR Phone LIKE %s OR IDNumber LIKE %s OR City LIKE %s)"
            )
            params += [like, like, like, like, like]

    # --- dynamic filters ---
    allowed_fields = {
        "TotalBalance": "numeric",
        "AccountCount": "numeric",
        "City": "string",
        "FullName": "string",
    }
    extra_where, extra_params = build_filters(request.args, allowed_fields)
    where_sql, params = merge_where(where_parts, params, extra_where, extra_params)

    # --- dynamic sort ---
    allowed_sort = {"TotalBalance", "AccountCount", "CreatedAt", "CustomerID"}
    order_sql = build_order(
        request.args.get("sort"), allowed_sort, default="CustomerID DESC"
    )

    with get_cursor() as cur:
        cur.execute(
            f"SELECT COUNT(*) AS total FROM vw_customer_summary {where_sql}",
            params,
        )
        total = cur.fetchone()["total"]

        cur.execute(
            f"""
            SELECT
                CustomerID, FullName, Email, Phone, City, IDNumber, CreatedAt,
                AccountCount AS AccountCount,
                TotalBalance AS TotalBalance
            FROM vw_customer_summary
            {where_sql}
            {order_sql}
            LIMIT %s OFFSET %s
            """,
            [*params, size, offset],
        )
        rows = cur.fetchall()

    return ok({"items": rows, "total": total, "page": page, "size": size})


@bp.get("/<int:cid>")
@auth_required()
def get_customer(cid):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM Customers WHERE CustomerID=%s", (cid,))
        cust = cur.fetchone()
        if not cust:
            return fail("Customer not found", 404)

        cur.execute(
            """SELECT a.*, b.BranchName
               FROM Accounts a
               LEFT JOIN Branches b ON b.BranchID = a.BranchID
               WHERE a.CustomerID = %s
               ORDER BY a.AccountID DESC""",
            (cid,),
        )
        cust["accounts"] = cur.fetchall()

        cur.execute(
            """SELECT t.*, a.AccountNumber
               FROM Transactions t
               JOIN Accounts a ON a.AccountID = t.AccountID
               WHERE a.CustomerID = %s
               ORDER BY t.CreatedAt DESC
               LIMIT 20""",
            (cid,),
        )
        cust["recent_transactions"] = cur.fetchall()

        cur.execute(
            "SELECT * FROM Loans WHERE CustomerID=%s ORDER BY LoanID DESC",
            (cid,),
        )
        cust["loans"] = cur.fetchall()

        cur.execute(
            "SELECT * FROM CreditCards WHERE CustomerID=%s ORDER BY CardID DESC",
            (cid,),
        )
        cust["cards"] = cur.fetchall()

    return ok(cust)


@bp.post("")
@auth_required(roles=["manager", "teller"])
def create_customer():
    d = request.get_json(silent=True) or {}
    d.pop("CustomerID", None)

    miss = require(d, ["FullName"])
    if miss:
        return fail("Missing fields", 400, miss)

    if d.get("Email") and not is_email(d["Email"]):
        return fail("Invalid email", 400)

    def _clean(v):
        if v is None:
            return None
        v = str(v).strip()
        return v or None

    with get_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO Customers
               (FullName,Email,Phone,DateOfBirth,Address,City,IDNumber,CreatedBy)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                _clean(d.get("FullName")),
                _clean(d.get("Email")),
                _clean(d.get("Phone")),
                _clean(d.get("DateOfBirth")),
                _clean(d.get("Address")),
                _clean(d.get("City")),
                _clean(d.get("IDNumber")),
                g.current_user["uid"],
            ),
        )
        new_id = cur.lastrowid

    return ok({"CustomerID": new_id}, "Created", 201)


@bp.put("/<int:cid>")
@auth_required(roles=["manager", "teller"])
def update_customer(cid):
    d = request.get_json(silent=True) or {}

    if d.get("Email") and not is_email(d["Email"]):
        return fail("Invalid email", 400)

    fields = ["FullName", "Email", "Phone", "DateOfBirth", "Address", "City", "IDNumber"]

    sets, params = [], []
    for f in fields:
        if f in d:
            val = d[f]
            if isinstance(val, str) and val.strip() == "":
                val = None
            sets.append(f"{f}=%s")
            params.append(val)

    if not sets:
        return fail("No fields to update", 400)

    params.append(cid)

    with get_cursor(commit=True) as cur:
        cur.execute(
            f"UPDATE Customers SET {','.join(sets)} WHERE CustomerID=%s",
            params,
        )

    return ok(None, "Updated")


@bp.delete("/<int:cid>")
@auth_required(roles=["manager"])
def delete_customer(cid):
    with get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM Customers WHERE CustomerID=%s", (cid,))
    return ok(None, "Deleted")
