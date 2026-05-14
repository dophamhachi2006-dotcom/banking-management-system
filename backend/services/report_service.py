"""Reports / analytics services.

All queries degrade gracefully: if a view or column does not exist in the
user's schema, the function returns an empty list rather than raising.
"""
from core.db_connection import get_cursor


def _safe_fetch(cur, sql, params=(), many=True):
    try:
        cur.execute(sql, params)
        return cur.fetchall() if many else cur.fetchone()
    except Exception:
        return [] if many else {}


def dashboard_stats():
    """Aggregate counts + financial KPIs for the dashboard overview."""
    with get_cursor() as cur:
        health = _safe_fetch(cur, "SELECT * FROM vw_db_health", many=False) or {}
        if not health:
            stats = {}
            for key, table in [
                ("customers", "Customers"),
                ("accounts", "Accounts"),
                ("transactions", "Transactions"),
                ("branches", "Branches"),
                ("employees", "Employees"),
                ("loans", "Loans"),
                ("cards", "CreditCards"),
            ]:
                row = _safe_fetch(
                    cur, f"SELECT COUNT(*) AS c FROM {table}", many=False
                )
                stats[key] = (row or {}).get("c", 0)
            health = stats

        assets = _safe_fetch(
            cur,
            "SELECT COALESCE(SUM(Balance),0) AS total_assets FROM Accounts WHERE Status='active'",
            many=False,
        ) or {"total_assets": 0}

        today = _safe_fetch(
            cur,
            """SELECT COUNT(*) AS today_tx, COALESCE(SUM(Amount),0) AS today_volume
               FROM Transactions WHERE DATE(CreatedAt)=CURDATE()""",
            many=False,
        ) or {"today_tx": 0, "today_volume": 0}

        active_accounts = _safe_fetch(
            cur,
            "SELECT COUNT(*) AS c FROM Accounts WHERE Status='active'",
            many=False,
        ) or {"c": 0}

        loan_stats = _safe_fetch(
            cur,
            """SELECT COUNT(*) AS active_loans,
                      COALESCE(SUM(OutstandingBal),0) AS loan_outstanding
               FROM Loans WHERE Status='active'""",
            many=False,
        ) or {"active_loans": 0, "loan_outstanding": 0}

    return {
        **health,
        **assets,
        **today,
        "active_accounts": active_accounts.get("c", 0),
        **loan_stats,
    }


def top_customers(limit=10):
    with get_cursor() as cur:
        rows = _safe_fetch(
            cur, "SELECT * FROM vw_top_customers LIMIT %s", (limit,)
        )
        if rows:
            return rows
        return _safe_fetch(
            cur,
            """SELECT c.CustomerID, c.FullName,
                      COUNT(a.AccountID) AS Accounts,
                      COALESCE(SUM(a.Balance),0) AS TotalBalance
               FROM Customers c
               LEFT JOIN Accounts a ON a.CustomerID=c.CustomerID AND a.Status='active'
               GROUP BY c.CustomerID, c.FullName
               ORDER BY TotalBalance DESC
               LIMIT %s""",
            (limit,),
        )


def branch_performance():
    """Return top 10 branches by total deposits."""
    with get_cursor() as cur:
        rows = _safe_fetch(
            cur,
            "SELECT * FROM vw_branch_performance ORDER BY TotalDeposits DESC LIMIT 10",
        )
        if rows:
            return rows
        return _safe_fetch(
            cur,
            """SELECT b.BranchID, b.BranchName,
                      COUNT(DISTINCT a.CustomerID) AS TotalCustomers,
                      COUNT(a.AccountID)           AS TotalAccounts,
                      COALESCE(SUM(a.Balance),0)   AS TotalDeposits,
                      0 AS TotalTransactions
               FROM Branches b
               LEFT JOIN Accounts a ON a.BranchID=b.BranchID
               GROUP BY b.BranchID, b.BranchName
               ORDER BY TotalDeposits DESC
               LIMIT 10""",
        )


def monthly_summary():
    with get_cursor() as cur:
        rows = _safe_fetch(cur, "SELECT * FROM vw_monthly_tx_summary LIMIT 24")
        if rows:
            return rows
        return _safe_fetch(
            cur,
            """SELECT DATE_FORMAT(CreatedAt, '%Y-%m') AS Month,
                      COUNT(*) AS TotalCount,
                      COALESCE(SUM(Amount),0) AS TotalAmount
               FROM Transactions
               WHERE CreatedAt >= DATE_SUB(CURDATE(), INTERVAL 24 MONTH)
               GROUP BY Month
               ORDER BY Month ASC""",
        )


def suspicious_transactions():
    with get_cursor() as cur:
        rows = _safe_fetch(
            cur,
            "SELECT * FROM vw_suspicious_transactions ORDER BY CreatedAt DESC LIMIT 100",
        )
        if rows:
            return rows
        return _safe_fetch(
            cur,
            """SELECT t.TransactionID, t.AccountID, a.AccountNumber,
                      c.FullName AS CustomerName, t.TxType, t.Amount, t.CreatedAt
               FROM Transactions t
               JOIN Accounts a  ON a.AccountID=t.AccountID
               JOIN Customers c ON c.CustomerID=a.CustomerID
               WHERE t.Amount >= 10000
                 AND t.CreatedAt >= DATE_SUB(NOW(), INTERVAL 7 DAY)
               ORDER BY t.CreatedAt DESC
               LIMIT 100""",
        )


def revenue_report(months: int = 12):
    """Monthly revenue: sum fees + interest transactions by month."""
    with get_cursor() as cur:
        rows = _safe_fetch(
            cur,
            """SELECT DATE_FORMAT(CreatedAt, '%%Y-%%m') AS Month,
                      COALESCE(SUM(CASE WHEN TxType='fee' THEN Amount ELSE 0 END),0) AS Fees,
                      COALESCE(SUM(CASE WHEN TxType='interest' THEN Amount ELSE 0 END),0) AS Interest,
                      COALESCE(SUM(CASE WHEN TxType IN ('fee','interest') THEN Amount ELSE 0 END),0) AS Total
               FROM Transactions
               WHERE CreatedAt >= DATE_SUB(CURDATE(), INTERVAL %s MONTH)
               GROUP BY Month
               ORDER BY Month""",
            (months,),
        )
        return rows or []


def tx_type_breakdown():
    """Transaction type breakdown across the whole system."""
    with get_cursor() as cur:
        return _safe_fetch(
            cur,
            """SELECT TxType AS type,
                      COUNT(*) AS count,
                      COALESCE(SUM(Amount),0) AS total
               FROM Transactions
               GROUP BY TxType
               ORDER BY count DESC""",
        )


def fraud_overview():
    """Simple rule-based fraud overview."""
    with get_cursor() as cur:
        large = _safe_fetch(
            cur,
            """SELECT COUNT(*) AS c FROM Transactions
               WHERE Amount >= 10000
                 AND CreatedAt >= DATE_SUB(NOW(), INTERVAL 30 DAY)""",
            many=False,
        ) or {"c": 0}

        night = _safe_fetch(
            cur,
            """SELECT COUNT(*) AS c FROM Transactions
               WHERE HOUR(CreatedAt) BETWEEN 0 AND 5
                 AND TxType='withdrawal'
                 AND CreatedAt >= DATE_SUB(NOW(), INTERVAL 30 DAY)""",
            many=False,
        ) or {"c": 0}

        bursts = _safe_fetch(
            cur,
            """SELECT AccountID, COUNT(*) AS tx_count
               FROM Transactions
               WHERE CreatedAt >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
               GROUP BY AccountID
               HAVING tx_count >= 5""",
        )

        recent = _safe_fetch(
            cur,
            """SELECT t.TransactionID, t.AccountID, a.AccountNumber,
                      c.FullName AS CustomerName, t.TxType, t.Amount, t.CreatedAt
               FROM Transactions t
               JOIN Accounts a  ON a.AccountID=t.AccountID
               JOIN Customers c ON c.CustomerID=a.CustomerID
               WHERE t.Amount >= 10000
                  OR (t.TxType='withdrawal' AND HOUR(t.CreatedAt) BETWEEN 0 AND 5)
               ORDER BY t.CreatedAt DESC
               LIMIT 50""",
        )

    return {
        "large_amount_count": large.get("c", 0),
        "late_night_withdrawals": night.get("c", 0),
        "burst_accounts": len(bursts),
        "recent": recent,
    }
