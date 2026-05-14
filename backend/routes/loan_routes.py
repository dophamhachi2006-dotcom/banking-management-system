"""Loan routes: list / create / payment / interest calculation / close."""
from datetime import date
from flask import Blueprint, request, g
from core.db_connection import get_cursor
from core.auth import auth_required
from backend.api_response import ok, fail, paginate
from backend.utils.query_builder import build_filters, build_order, merge_where

bp = Blueprint("loans", __name__)


def _monthly_payment(principal: float, annual_rate: float, term_months: int) -> float:
    principal = float(principal)
    r = float(annual_rate) / 100.0 / 12.0
    n = int(term_months)
    if n <= 0:
        return 0.0
    if r == 0:
        return round(principal / n, 2)
    return round(principal * r * (1 + r) ** n / ((1 + r) ** n - 1), 2)


@bp.get("")
@auth_required()
def list_loans():
    page, size, offset = paginate(request.args)
    q = (request.args.get("q") or "").strip()
    status = request.args.get("status")
    where, params = [], []
    if status:
        where.append("l.Status=%s")
        params.append(status)
    if q:
        if q.isdigit():
            where.append("(l.LoanID=%s OR l.CustomerID=%s OR c.FullName LIKE %s)")
            params += [int(q), int(q), f"%{q}%"]
        else:
            where.append("c.FullName LIKE %s")
            params.append(f"%{q}%")

    # --- dynamic filters ---
    # NOTE: column is OutstandingBal in DB; expose alias OutstandingBalance too.
    allowed_fields = {
        "Principal": "numeric",
        "InterestRate": "numeric",
        "TermMonths": "numeric",
        "OutstandingBal": "numeric",
        "OutstandingBalance": "numeric",
        "Status": "string",
    }
    extra_where, extra_params = build_filters(request.args, allowed_fields, table_alias="l")
    extra_where = extra_where.replace("l.OutstandingBalance", "l.OutstandingBal")
    where_sql, params = merge_where(where, params, extra_where, extra_params)

    allowed_sort = {"Principal", "InterestRate", "TermMonths",
                    "OutstandingBal", "OutstandingBalance", "LoanID", "StartDate"}
    sort_param = request.args.get("sort")
    if sort_param and sort_param.startswith("OutstandingBalance_"):
        sort_param = sort_param.replace("OutstandingBalance_", "OutstandingBal_", 1)
    order_sql = build_order(
        sort_param, allowed_sort, default="l.LoanID DESC", table_alias="l",
    )

    with get_cursor() as cur:
        cur.execute(
            f"""SELECT COUNT(*) AS c FROM Loans l
                JOIN Customers c ON c.CustomerID=l.CustomerID {where_sql}""",
            params,
        )
        total = cur.fetchone()["c"]
        cur.execute(
            f"""SELECT l.*, c.FullName AS CustomerName
                FROM Loans l JOIN Customers c ON c.CustomerID=l.CustomerID
                {where_sql}
                {order_sql}
                LIMIT %s OFFSET %s""",
            [*params, size, offset],
        )
        rows = cur.fetchall()
    return ok({"items": rows, "total": total, "page": page, "size": size})


@bp.get("/<int:lid>")
@auth_required()
def get_loan(lid):
    with get_cursor() as cur:
        cur.execute(
            """SELECT l.*, c.FullName AS CustomerName
               FROM Loans l JOIN Customers c ON c.CustomerID=l.CustomerID
               WHERE l.LoanID=%s""",
            (lid,),
        )
        row = cur.fetchone()
    if not row:
        return fail("Loan not found", 404)
    row["MonthlyPayment"] = _monthly_payment(
        row["Principal"], row["InterestRate"], row["TermMonths"]
    )
    return ok(row)


@bp.post("")
@auth_required(roles=["manager"])
def create_loan():
    d = request.get_json(silent=True) or {}
    d.pop("LoanID", None)
    needed = ["CustomerID", "Principal", "InterestRate", "TermMonths"]
    if any(d.get(k) in (None, "") for k in needed):
        return fail("Missing fields", 400, needed)

    try:
        principal = float(d["Principal"])
        rate = float(d["InterestRate"])
        term = int(d["TermMonths"])
        if principal <= 0 or rate < 0 or term <= 0:
            return fail("Invalid principal/rate/term", 400)
    except (TypeError, ValueError):
        return fail("Numeric fields invalid", 400)

    start = d.get("StartDate") or date.today().isoformat()
    with get_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO Loans
               (CustomerID,Principal,InterestRate,TermMonths,MonthlyPayment,Status,StartDate,EndDate,OutstandingBal)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                d["CustomerID"], principal, rate, term,
                _monthly_payment(principal, rate, term),
                d.get("Status", "active"), start, d.get("EndDate"),
                principal,
            ),
        )
        new_id = cur.lastrowid
    return ok(
        {"LoanID": new_id, "MonthlyPayment": _monthly_payment(principal, rate, term)},
        "Loan created", 201,
    )


@bp.post("/<int:lid>/payment")
@auth_required(roles=["manager", "teller"])
def pay_loan(lid):
    d = request.get_json(silent=True) or {}
    try:
        amount = float(d.get("Amount") or 0)
        if amount <= 0:
            return fail("Amount must be positive", 400)
    except (TypeError, ValueError):
        return fail("Invalid amount", 400)

    with get_cursor(commit=True) as cur:
        cur.execute(
            "SELECT OutstandingBal, Status FROM Loans WHERE LoanID=%s", (lid,)
        )
        row = cur.fetchone()
        if not row:
            return fail("Loan not found", 404)
        outstanding = float(row["OutstandingBal"] or 0)
        if outstanding <= 0 or row["Status"] == "closed":
            return fail("Loan is already closed", 400)
        new_out = max(0.0, outstanding - amount)
        new_status = "closed" if new_out == 0 else row["Status"]
        cur.execute(
            "UPDATE Loans SET OutstandingBal=%s, Status=%s WHERE LoanID=%s",
            (new_out, new_status, lid),
        )
    return ok(
        {"LoanID": lid, "Outstanding": new_out, "Status": new_status},
        "Payment recorded",
    )


@bp.get("/<int:lid>/interest")
@auth_required()
def loan_interest(lid):
    with get_cursor() as cur:
        cur.execute(
            "SELECT Principal, InterestRate, TermMonths, OutstandingBal FROM Loans WHERE LoanID=%s",
            (lid,),
        )
        row = cur.fetchone()
    if not row:
        return fail("Loan not found", 404)
    principal = float(row["Principal"])
    rate = float(row["InterestRate"])
    term = int(row["TermMonths"])
    outstanding = float(row["OutstandingBal"] or 0)
    monthly = _monthly_payment(principal, rate, term)
    total_paid = monthly * term
    total_interest = round(total_paid - principal, 2)
    remaining_interest = round(
        total_interest * (outstanding / principal) if principal else 0, 2
    )
    return ok({
        "LoanID": lid,
        "MonthlyPayment": monthly,
        "TotalPayable": round(total_paid, 2),
        "TotalInterest": total_interest,
        "Outstanding": outstanding,
        "RemainingInterest": remaining_interest,
    })


@bp.put("/<int:lid>/status")
@auth_required(roles=["manager"])
def set_status(lid):
    d = request.get_json(silent=True) or {}
    if d.get("Status") not in ("pending", "active", "closed", "defaulted"):
        return fail("Invalid status", 400)
    with get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE Loans SET Status=%s WHERE LoanID=%s", (d["Status"], lid)
        )
    return ok(None, "Updated")
