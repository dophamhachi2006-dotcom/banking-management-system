"""
Dynamic filter & sort builder for SQL queries.

Usage:
    from backend.utils.query_builder import build_filters, build_order, merge_where

    where_sql, params = build_filters(request.args, allowed_fields={
        "TotalBalance": "numeric",
        "City": "string",
    })
    order_sql = build_order(request.args.get("sort"),
                            allowed_sort={"TotalBalance", "CreatedAt"},
                            default="CustomerID DESC")
"""

OPERATORS = {
    "gt":  ">",
    "lt":  "<",
    "eq":  "=",
    "gte": ">=",
    "lte": "<=",
    "ne":  "!=",
    "like": "LIKE",
}

# Reserved query params that must NOT be parsed as filters even when they
# accidentally contain an underscore matching an operator suffix.
RESERVED_PARAMS = {
    "page", "size", "q", "sort", "limit", "offset",
    "from", "to", "min_amount", "max_amount",
    "account_id", "branch_id", "customer_id",
    "type", "status",
}


def build_filters(args, allowed_fields: dict, table_alias: str = ""):
    """Build a parameterized WHERE clause from query string args.

    args            : werkzeug ImmutableMultiDict (request.args)
    allowed_fields  : { "FieldName": "numeric" | "string" | "enum" | "bool" | "date" }
    table_alias     : optional prefix (e.g. "t") -> emits "t.FieldName ..."

    Returns: (where_sql, params)
        where_sql is "" or "WHERE ..." ready to splice into SQL.
    """
    where_parts, params = [], []
    prefix = f"{table_alias}." if table_alias else ""

    for key in args:
        if key in RESERVED_PARAMS:
            continue
        if "_" not in key:
            continue
        field, op = key.rsplit("_", 1)
        if op not in OPERATORS:
            continue
        if field not in allowed_fields:
            # Unknown -> ignore (anti SQL-injection: only whitelisted fields)
            continue

        raw = args.get(key)
        if raw is None or raw == "":
            continue

        ftype = allowed_fields[field]
        sql_op = OPERATORS[op]

        try:
            if ftype == "numeric":
                val = float(raw)
            elif ftype == "bool":
                val = 1 if str(raw).lower() in ("true", "1", "yes") else 0
            else:
                val = str(raw)
        except (TypeError, ValueError):
            continue

        if op == "like":
            where_parts.append(f"{prefix}{field} LIKE %s")
            params.append(f"%{val}%")
        else:
            where_parts.append(f"{prefix}{field} {sql_op} %s")
            params.append(val)

    where_sql = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
    return where_sql, params


def build_order(sort_param: str, allowed_sort, default: str = "", table_alias: str = ""):
    """Build a safe ORDER BY clause.

    sort_param   : 'FieldName_desc' | 'FieldName_asc'
    allowed_sort : iterable of allowed field names (whitelist)
    default      : fallback ORDER BY content (no leading 'ORDER BY')
    """
    fallback = f"ORDER BY {default}" if default else ""
    if not sort_param or "_" not in sort_param:
        return fallback

    field, direction = sort_param.rsplit("_", 1)
    if field not in set(allowed_sort):
        return fallback
    direction = "DESC" if direction.lower() == "desc" else "ASC"
    prefix = f"{table_alias}." if table_alias else ""
    return f"ORDER BY {prefix}{field} {direction}"


def merge_where(existing_where_parts, existing_params, extra_where_sql, extra_params):
    """Merge an already-built list of WHERE parts with the result of build_filters()."""
    parts = list(existing_where_parts)
    params = list(existing_params)
    if extra_where_sql:
        parts.append(extra_where_sql.replace("WHERE ", "", 1))
        params.extend(extra_params)
    where_sql = ("WHERE " + " AND ".join(parts)) if parts else ""
    return where_sql, params
