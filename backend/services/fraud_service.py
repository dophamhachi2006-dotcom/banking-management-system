"""Simple rule-based fraud detection.
Flags accounts with: 5+ tx in 1 hour, sudden >10x avg amount, late-night withdrawals."""
from core.db_connection import get_cursor

def detect_for_account(account_id: int):
    flags = []
    with get_cursor() as cur:
        cur.execute("""SELECT COUNT(*) AS c FROM Transactions
                       WHERE AccountID=%s AND CreatedAt >= DATE_SUB(NOW(), INTERVAL 1 HOUR)""",
                    (account_id,))
        if cur.fetchone()["c"] >= 5:
            flags.append("burst_activity")

        cur.execute("""SELECT AVG(Amount) AS avg_amt FROM Transactions
                       WHERE AccountID=%s AND CreatedAt >= DATE_SUB(NOW(), INTERVAL 30 DAY)""",
                    (account_id,))
        avg = cur.fetchone()["avg_amt"] or 0
        cur.execute("""SELECT MAX(Amount) AS max_amt FROM Transactions
                       WHERE AccountID=%s AND CreatedAt >= DATE_SUB(NOW(), INTERVAL 1 DAY)""",
                    (account_id,))
        mx = cur.fetchone()["max_amt"] or 0
        if avg and mx > avg * 10:
            flags.append("amount_spike")

        cur.execute("""SELECT COUNT(*) AS c FROM Transactions
                       WHERE AccountID=%s AND TxType='withdrawal'
                         AND HOUR(CreatedAt) BETWEEN 0 AND 5
                         AND CreatedAt >= DATE_SUB(NOW(), INTERVAL 7 DAY)""",
                    (account_id,))
        if cur.fetchone()["c"] >= 3:
            flags.append("late_night_withdrawals")
    return flags
