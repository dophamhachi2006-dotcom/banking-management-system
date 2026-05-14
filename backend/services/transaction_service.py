"""Transaction service: deposit/withdraw/transfer using stored procs."""
from core.db_connection import get_conn

def _validate_amount(v):
    try:
        amt = float(v)
        if amt <= 0: raise ValueError
        return amt
    except (TypeError, ValueError):
        raise ValueError("Amount must be a positive number")

def do_deposit(account_id, amount, user_id, desc):
    if not account_id: raise ValueError("AccountID required")
    amt = _validate_amount(amount)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.callproc("sp_deposit", (account_id, amt, user_id, desc))
        conn.commit()
        cur.execute("SELECT Balance FROM Accounts WHERE AccountID=%s", (account_id,))
        bal = cur.fetchone()[0]
        cur.execute("""SELECT TransactionID FROM Transactions
                       WHERE AccountID=%s ORDER BY TransactionID DESC LIMIT 1""",
                    (account_id,))
        tx_id = cur.fetchone()[0]
        cur.close()
    return tx_id, float(bal)

def do_withdraw(account_id, amount, user_id, desc):
    if not account_id: raise ValueError("AccountID required")
    amt = _validate_amount(amount)
    with get_conn() as conn:
        cur = conn.cursor()
        try:
            cur.callproc("sp_withdraw", (account_id, amt, user_id, desc))
            conn.commit()
        except Exception as e:
            raise ValueError(str(e))
        cur.execute("SELECT Balance FROM Accounts WHERE AccountID=%s", (account_id,))
        bal = cur.fetchone()[0]
        cur.execute("""SELECT TransactionID FROM Transactions
                       WHERE AccountID=%s ORDER BY TransactionID DESC LIMIT 1""",
                    (account_id,))
        tx_id = cur.fetchone()[0]
        cur.close()
    return tx_id, float(bal)

def do_transfer(from_id, to_id, amount, user_id, desc):
    if not from_id or not to_id: raise ValueError("Both account IDs required")
    if from_id == to_id: raise ValueError("Cannot transfer to same account")
    amt = _validate_amount(amount)
    with get_conn() as conn:
        cur = conn.cursor()
        try:
            cur.callproc("sp_transfer", (from_id, to_id, amt, user_id, desc))
            conn.commit()
        except Exception as e:
            raise ValueError(str(e))
        cur.execute("""SELECT TransactionID FROM Transactions
                       WHERE AccountID=%s ORDER BY TransactionID DESC LIMIT 1""",
                    (from_id,))
        tx_id = cur.fetchone()[0]
        cur.close()
    return tx_id
