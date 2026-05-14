"""Credit card routes: list / issue / block-unblock / transactions."""
from datetime import date
from flask import Blueprint, request
from core.db_connection import get_cursor
from core.auth import auth_required
from backend.api_response import ok, fail, paginate
from backend.utils.query_builder import build_filters, build_order, merge_where

bp = Blueprint("cards", __name__)


@bp.get("")
@auth_required()
def list_cards():
    page, size, offset = paginate(request.args)
    q = (request.args.get("q") or "").strip()
    status = request.args.get("status")
    where, params = [], []

    if status:
        where.append("cc.Status=%s")
        params.append(status)
    if q:
        like = f"%{q}%"
        if q.isdigit():
            where.append(
                "(cc.CardID=%s OR cc.CardNumber LIKE %s OR c.FullName LIKE %s)"
            )
            params += [int(q), like, like]
        else:
            where.append("(cc.CardNumber LIKE %s OR c.FullName LIKE %s)")
            params += [like, like]

    # HasTransactions handled separately (sub-query EXISTS)
    has_tx = request.args.get("HasTransactions_eq")
    if has_tx is not None and has_tx != "":
        truthy = str(has_tx).lower() in ("true", "1", "yes")
        if truthy:
            where.append(
                "EXISTS (SELECT 1 FROM CardTransactions ct WHERE ct.CardID = cc.CardID)"
            )
        else:
            where.append(
                "NOT EXISTS (SELECT 1 FROM CardTransactions ct WHERE ct.CardID = cc.CardID)"
            )

    # --- dynamic filters ---
    allowed_fields = {
        "CreditLimit": "numeric",
        "OutstandingBal": "numeric",
        "OutstandingBalance": "numeric",
        "Status": "string",
    }
    extra_where, extra_params = build_filters(request.args, allowed_fields, table_alias="cc")
    extra_where = extra_where.replace("cc.OutstandingBalance", "cc.OutstandingBal")
    where_sql, params = merge_where(where, params, extra_where, extra_params)

    allowed_sort = {"CreditLimit", "OutstandingBal", "OutstandingBalance",
                    "CreatedAt", "CardID"}
    sort_param = request.args.get("sort")
    if sort_param and sort_param.startswith("OutstandingBalance_"):
        sort_param = sort_param.replace("OutstandingBalance_", "OutstandingBal_", 1)
    order_sql = build_order(
        sort_param, allowed_sort, default="cc.CardID DESC", table_alias="cc",
    )

    with get_cursor() as cur:
        try:
            cur.execute(
                f"""SELECT COUNT(*) AS c
                    FROM CreditCards cc
                    LEFT JOIN Customers c ON c.CustomerID = cc.CustomerID
                    {where_sql}""",
                params,
            )
            total = cur.fetchone()["c"]

            cur.execute(
                f"""SELECT cc.CardID, cc.CardNumber, cc.CustomerID, cc.CreditLimit,
                           cc.OutstandingBal, cc.ExpiryDate, cc.Status, cc.CreatedAt,
                           COALESCE(c.FullName, '') AS CustomerName
                    FROM CreditCards cc
                    LEFT JOIN Customers c ON c.CustomerID = cc.CustomerID
                    {where_sql}
                    {order_sql}
                    LIMIT %s OFFSET %s""",
                [*params, size, offset],
            )
            rows = cur.fetchall()
        except Exception as exc:
            # CardTransactions table may not exist yet -> retry without HasTransactions
            if "CardTransactions" in str(exc):
                return fail(
                    "HasTransactions filter requires CardTransactions table. "
                    "Run database/01_v6_fixes.sql to enable.",
                    400,
                )
            raise

    return ok({"items": rows, "total": total, "page": page, "size": size})


@bp.get("/<int:cid>")
@auth_required()
def get_card(cid):
    with get_cursor() as cur:
        cur.execute(
            """SELECT cc.CardID, cc.CardNumber, cc.CustomerID, cc.CreditLimit,
                      cc.OutstandingBal, cc.ExpiryDate, cc.Status, cc.CreatedAt,
                      COALESCE(c.FullName, '') AS CustomerName
               FROM CreditCards cc
               LEFT JOIN Customers c ON c.CustomerID = cc.CustomerID
               WHERE cc.CardID=%s""",
            (cid,),
        )
        card = cur.fetchone()
    return ok(card) if card else fail("Card not found", 404)


@bp.get("/<int:cid>/transactions")
@auth_required()
def card_transactions(cid):
    with get_cursor() as cur:
        cur.execute(
            "SELECT CardID FROM CreditCards WHERE CardID=%s", (cid,)
        )
        if not cur.fetchone():
            return fail("Card not found", 404)

        try:
            cur.execute(
                """SELECT ct.ID AS TransactionID, ct.CardID, ct.Amount,
                          ct.Merchant, ct.Description, ct.Status, ct.CreatedAt
                   FROM CardTransactions ct
                   INNER JOIN CreditCards cc ON cc.CardID = ct.CardID
                   WHERE ct.CardID=%s
                   ORDER BY ct.CreatedAt DESC
                   LIMIT 100""",
                (cid,),
            )
            rows = cur.fetchall()
        except Exception as exc:
            msg = str(exc)
            if "1146" in msg or "doesn't exist" in msg.lower():
                return ok(
                    [],
                    "CardTransactions table not found. "
                    "Please run database/01_v6_fixes.sql to create it.",
                )
            raise

    return ok(rows)


@bp.post("")
@auth_required(roles=["manager"])
def issue_card():
    d = request.get_json(silent=True) or {}
    d.pop("CardID", None)
    needed = ["CustomerID", "CreditLimit"]
    if any(d.get(k) in (None, "") for k in needed):
        return fail("Missing fields", 400, needed)

    try:
        credit_limit = float(d["CreditLimit"])
        if credit_limit <= 0:
            return fail("CreditLimit must be positive", 400)
    except (TypeError, ValueError):
        return fail("Invalid CreditLimit", 400)

    card_number = d.get("CardNumber")
    if not card_number:
        import random
        card_number = "4" + "".join(str(random.randint(0, 9)) for _ in range(15))

    expiry = d.get("ExpiryDate")
    if not expiry:
        y = date.today().year + 4
        expiry = f"{y}-{date.today().month:02d}-01"

    with get_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO CreditCards
               (CardNumber,CustomerID,CreditLimit,OutstandingBal,ExpiryDate,Status)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (
                card_number, d["CustomerID"], credit_limit,
                d.get("OutstandingBal", 0), expiry,
                d.get("Status", "active"),
            ),
        )
        new_id = cur.lastrowid

    return ok({"CardID": new_id, "CardNumber": card_number}, "Card issued", 201)


@bp.put("/<int:cid>/status")
@auth_required(roles=["manager"])
def set_status(cid):
    d = request.get_json(silent=True) or {}
    if d.get("Status") not in ("active", "blocked", "expired"):
        return fail("Invalid status", 400)
    with get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE CreditCards SET Status=%s WHERE CardID=%s",
            (d["Status"], cid),
        )
    return ok(None, f"Card status updated to {d['Status']}")
