from flask import Blueprint, request
from core.db_connection import get_cursor
from core.auth import auth_required
from core.validators import require, is_email
from backend.api_response import ok, fail, paginate
from backend.utils.query_builder import build_filters, build_order, merge_where

bp = Blueprint("employees", __name__)

@bp.get("")
@auth_required()
def list_employees():
    page, size, offset = paginate(request.args)
    branch = request.args.get("branch_id")
    q = (request.args.get("q") or "").strip()
    where, params = [], []
    if branch:
        where.append("e.BranchID=%s")
        params.append(branch)
    if q:
        if q.isdigit():
            where.append(
                "(e.EmployeeID=%s OR e.FullName LIKE %s OR e.Email LIKE %s"
                " OR e.Position LIKE %s OR b.BranchName LIKE %s)"
            )
            like = f"%{q}%"
            params += [int(q), like, like, like, like]
        else:
            where.append(
                "(e.FullName LIKE %s OR e.Email LIKE %s"
                " OR e.Position LIKE %s OR b.BranchName LIKE %s)"
            )
            like = f"%{q}%"
            params += [like, like, like, like]

    allowed_fields = {"Salary": "numeric", "Status": "string"}
    extra_where, extra_params = build_filters(request.args, allowed_fields, table_alias="e")
    where_sql, params = merge_where(where, params, extra_where, extra_params)

    allowed_sort = {"Salary", "EmployeeID", "HiredAt"}
    order_sql = build_order(
        request.args.get("sort"), allowed_sort,
        default="e.EmployeeID DESC", table_alias="e",
    )

    with get_cursor() as cur:
        cur.execute(
            f"""SELECT COUNT(*) AS c FROM Employees e
                LEFT JOIN Branches b ON b.BranchID=e.BranchID
                {where_sql}""",
            params,
        )
        total = cur.fetchone()["c"]
        cur.execute(
            f"""SELECT e.*, b.BranchName FROM Employees e
                LEFT JOIN Branches b ON b.BranchID=e.BranchID
                {where_sql}
                {order_sql}
                LIMIT %s OFFSET %s""",
            [*params, size, offset],
        )
        rows = cur.fetchall()
    return ok({"items": rows, "total": total, "page": page, "size": size})

@bp.get("/<int:eid>")
@auth_required()
def get_employee(eid):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM Employees WHERE EmployeeID=%s", (eid,))
        e = cur.fetchone()
    return ok(e) if e else fail("Not found", 404)

@bp.post("")
@auth_required(roles=["manager"])
def create_employee():
    d = request.get_json(silent=True) or {}
    miss = require(d, ["FullName","Email"])
    if miss: return fail("Missing fields", 400, miss)
    if not is_email(d["Email"]): return fail("Invalid email", 400)
    with get_cursor(commit=True) as cur:
        cur.execute("""INSERT INTO Employees
            (FullName,Email,Phone,Position,BranchID,Salary,HiredAt,Status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (d["FullName"], d["Email"], d.get("Phone"), d.get("Position"),
             d.get("BranchID"), d.get("Salary",0), d.get("HiredAt"),
             d.get("Status","active")))
        new_id = cur.lastrowid
    return ok({"EmployeeID": new_id}, "Created", 201)

@bp.put("/<int:eid>")
@auth_required(roles=["manager"])
def update_employee(eid):
    d = request.get_json(silent=True) or {}
    fields = ["FullName","Email","Phone","Position","BranchID","Salary","Status"]
    sets, params = [], []
    for f in fields:
        if f in d: sets.append(f"{f}=%s"); params.append(d[f])
    if not sets: return fail("No fields", 400)
    params.append(eid)
    with get_cursor(commit=True) as cur:
        cur.execute(f"UPDATE Employees SET {','.join(sets)} WHERE EmployeeID=%s", params)
    return ok(None, "Updated")

@bp.delete("/<int:eid>")
@auth_required(roles=["manager"])
def delete_employee(eid):
    with get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM Employees WHERE EmployeeID=%s", (eid,))
    return ok(None, "Deleted")
