"""Python CSV loader (fallback when LOAD DATA LOCAL INFILE is not available,
e.g. Docker / managed MySQL).

Usage:
    python data_generation/transform_kaggle_data.py
    python data_generation/generate_card_transactions.py   # <-- v6: tạo card_transactions.csv
    python backend/load_csv.py [--truncate]
"""
import os, sys, csv, argparse
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db_connection import get_conn

CSV_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data_generation", "csv_output")

TABLES = [
    # (table, csv_file, columns)
    ("Branches",         "branches.csv",
        ["BranchName","Address","City","Phone"]),
    ("Employees",        "employees.csv",
        ["FullName","Email","Phone","Position","BranchID","Salary","HiredAt","Status"]),
    ("Customers",        "customers.csv",
        ["FullName","Email","Phone","DateOfBirth","Address","City","IDNumber"]),
    ("Accounts",         "accounts.csv",
        ["AccountNumber","CustomerID","BranchID","AccountType","Balance",
         "Currency","Status","OpenedAt"]),
    ("Transactions",     "transactions.csv",
        ["AccountID","TxType","Amount","Description","CreatedAt"]),
    ("Loans",            "loans.csv",
        ["CustomerID","Principal","InterestRate","TermMonths","MonthlyPayment",
         "OutstandingBal","Status","StartDate","EndDate"]),
    ("CreditCards",      "cards.csv",
        ["CardNumber","CustomerID","CreditLimit","OutstandingBal",
         "ExpiryDate","Status"]),
    # v6: card transaction history (requires generate_card_transactions.py first)
    ("CardTransactions", "card_transactions.csv",
        ["CardID","Amount","Merchant","Description","Status","CreatedAt"]),
]

BATCH = 5000


def truncate_all(conn):
    cur = conn.cursor()
    cur.execute("SET FOREIGN_KEY_CHECKS=0")
    for t in ["CardTransactions","Transactions","CreditCards","Loans","Accounts",
              "Customers","Employees"]:
        cur.execute(f"DELETE FROM {t}")
    cur.execute("UPDATE Branches SET ManagerID=NULL")
    cur.execute("DELETE FROM Branches")
    cur.execute("SET FOREIGN_KEY_CHECKS=1")
    conn.commit()


def load_table(conn, table, csv_file, cols):
    path = os.path.join(CSV_DIR, csv_file)
    if not os.path.exists(path):
        print(f"  ⚠️  skip {table}: {path} missing"); return 0
    placeholders = ",".join(["%s"] * len(cols))
    sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
    cur = conn.cursor()
    n = 0
    batch = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            batch.append(tuple(row.get(c) or None for c in cols))
            if len(batch) >= BATCH:
                cur.executemany(sql, batch); conn.commit()
                n += len(batch); batch = []
        if batch:
            cur.executemany(sql, batch); conn.commit()
            n += len(batch)
    print(f"  ✔ {table:18s} {n:>8,} rows")
    return n


def fix_closed_account_balances(conn):
    """Zero-out Balance for accounts already marked Status='closed'.
    Prevents the 'Cannot close account with balance' rejection in the UI.
    """
    cur = conn.cursor()
    cur.execute("UPDATE Accounts SET Balance=0.00 WHERE Status='closed' AND Balance>0")
    affected = cur.rowcount
    conn.commit()
    if affected:
        print(f"  ✔ Zeroed balance on {affected:,} closed account(s)")


def link_branch_managers(conn):
    cur = conn.cursor()
    cur.execute("""UPDATE Branches b JOIN (
                     SELECT BranchID, MIN(EmployeeID) AS mid FROM Employees
                     WHERE Position='Manager' GROUP BY BranchID
                   ) m ON m.BranchID=b.BranchID
                   SET b.ManagerID=m.mid""")
    conn.commit()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--truncate", action="store_true",
                    help="Wipe data tables before loading")
    args = ap.parse_args()

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SET FOREIGN_KEY_CHECKS=0"); cur.execute("SET UNIQUE_CHECKS=0")
        if args.truncate:
            print("→ Truncating tables..."); truncate_all(conn)
        for t, f, c in TABLES:
            load_table(conn, t, f, c)
        print("→ Linking branch managers..."); link_branch_managers(conn)
        print("→ Fixing closed account balances..."); fix_closed_account_balances(conn)
        cur.execute("SET FOREIGN_KEY_CHECKS=1"); cur.execute("SET UNIQUE_CHECKS=1")
    print("\n✅ Done. Now run: python backend/seed_users.py")


if __name__ == "__main__":
    main()
