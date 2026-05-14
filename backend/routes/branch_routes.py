from flask import Blueprint, request
from core.db_connection import get_cursor
from core.auth import auth_required
from backend.api_response import ok, fail, paginate
from backend.services.audit_service import log_action

bp = Blueprint("branches", __name__)

@bp.get("")
@auth_required()
def list_branches():
    page, size, offset = paginate(request.args)
    q = (request.args.get("q") or "").strip()
    where, params = [], []
    if q:
        if q.isdigit():
            where.append(
                "(b.BranchID=%s OR b.BranchName LIKE %s OR b.City LIKE %s"
                " OR b.Phone LIKE %s OR e.FullName LIKE %s)"
            )
            like = f"%{q}%"
            params += [int(q), like, like, like, like]
        else:
            where.append(
                "(b.BranchName LIKE %s OR b.City LIKE %s"
                " OR b.Phone LIKE %s OR e.FullName LIKE %s)"
            )
            like = f"%{q}%"
            params += [like, like, like, like]

    # HasManager filter
    has_mgr = request.args.get("HasManager_eq")
    if has_mgr is not None and has_mgr != "":
        truthy = str(has_mgr).lower() in ("true", "1", "yes")
        where.append("b.ManagerID IS NOT NULL" if truthy else "b.ManagerID IS NULL")

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    with get_cursor() as cur:
        cur.execute(
            f"""SELECT COUNT(*) AS c FROM Branches b
                LEFT JOIN Employees e ON e.EmployeeID=b.ManagerID
                {where_sql}""",
            params,
        )
        total = cur.fetchone()["c"]
        cur.execute(
            f"""SELECT b.*, e.FullName AS ManagerName
                FROM Branches b
                LEFT JOIN Employees e ON e.EmployeeID=b.ManagerID
                {where_sql}
                ORDER BY b.BranchID
                LIMIT %s OFFSET %s""",
            [*params, size, offset],
        )
        rows = cur.fetchall()
    return ok({"items": rows, "total": total, "page": page, "size": size})

@bp.get("/<int:bid>")
@auth_required()
def get_branch(bid):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM Branches WHERE BranchID=%s", (bid,))
        b = cur.fetchone()
    return ok(b) if b else fail("Not found", 404)

@bp.post("")
@auth_required(roles=["manager"])
def create_branch():
    d = request.get_json(silent=True) or {}
    if not d.get("BranchName"): return fail("BranchName required", 400)
    with get_cursor(commit=True) as cur:
        cur.execute("""INSERT INTO Branches (BranchName,Address,City,Phone,ManagerID)
                       VALUES (%s,%s,%s,%s,%s)""",
                    (d["BranchName"], d.get("Address"), d.get("City"),
                     d.get("Phone"), d.get("ManagerID")))
        new_id = cur.lastrowid
    log_action("NEW_BRANCH", "Branches", new_id,
               new={"BranchName": d.get("BranchName"), "City": d.get("City"),
                    "ManagerID": d.get("ManagerID")})
    return ok({"BranchID": new_id}, "Created", 201)

@bp.put("/<int:bid>")
@auth_required(roles=["manager"])
def update_branch(bid):
    d = request.get_json(silent=True) or {}
    fields = ["BranchName","Address","City","Phone","ManagerID"]
    sets, params = [], []
    for f in fields:
        if f in d: sets.append(f"{f}=%s"); params.append(d[f])
    if not sets: return fail("No fields", 400)
    params.append(bid)
    with get_cursor(commit=True) as cur:
        cur.execute(f"UPDATE Branches SET {','.join(sets)} WHERE BranchID=%s", params)
    log_action("UPDATE_BRANCH", "Branches", bid, new={k: d[k] for k in d})
    return ok(None, "Updated")

@bp.delete("/<int:bid>")
@auth_required(roles=["manager"])
def delete_branch(bid):
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("DELETE FROM Branches WHERE BranchID=%s", (bid,))
    except Exception as exc:
        msg = str(exc).lower()
        if "foreign key" in msg or "1451" in msg or "constraint" in msg:
            return fail(
                "Cannot delete this branch: it still has accounts or employees attached. "
                "Please reassign or remove them first.",
                409,
            )
        raise
    log_action("DELETE_BRANCH", "Branches", bid)
    return ok(None, "Deleted")
