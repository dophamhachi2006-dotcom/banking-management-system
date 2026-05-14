"""Business-level audit logging.

Triggers in `database/audit_log.sql` only record generic INSERT/UPDATE/DELETE
rows. This service writes a *meaningful* row per user action:
DEPOSIT, WITHDRAW, TRANSFER, NEW_CUSTOMER, UPDATE_CUSTOMER, OPEN_ACCOUNT,
SET_ACCOUNT_STATUS, ISSUE_CARD, SET_CARD_STATUS, NEW_LOAN, LOAN_PAYMENT, ...

Use:
    from backend.services.audit_service import log_action
    log_action("DEPOSIT", "Transactions", tx_id,
               new={"AccountID": acc_id, "Amount": amt})
"""
import json
import logging

from flask import g, request, has_request_context

from core.db_connection import get_cursor

logger = logging.getLogger(__name__)


def _user_id():
    try:
        if has_request_context() and getattr(g, "current_user", None):
            return g.current_user.get("uid")
    except Exception:
        pass
    return None


def _ip():
    try:
        if has_request_context():
            xff = request.headers.get("X-Forwarded-For")
            if xff:
                return xff.split(",")[0].strip()[:45]
            return (request.remote_addr or "")[:45] or None
    except Exception:
        pass
    return None


def _json(value):
    if value is None:
        return None
    try:
        return json.dumps(value, default=str, ensure_ascii=False)
    except Exception:
        return json.dumps({"_repr": repr(value)})


def log_action(action, table, record_id, *, old=None, new=None):
    """Insert a row into AuditLog. Never raises — auditing must not break
    the main flow."""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                """INSERT INTO AuditLog
                   (TableName, RecordID, Action, OldData, NewData,
                    PerformedBy, IpAddress)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (
                    str(table)[:60],
                    str(record_id) if record_id is not None else "",
                    str(action)[:40],
                    _json(old),
                    _json(new),
                    _user_id(),
                    _ip(),
                ),
            )
    except Exception as exc:  # pragma: no cover - never break callers
        logger.warning("audit log_action failed (%s/%s): %s", action, table, exc)
