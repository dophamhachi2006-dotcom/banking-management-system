from rich.console import Console
from rich.table import Table
from backend.services.report_service import (
    dashboard_stats, top_customers, branch_performance, suspicious_transactions
)
console = Console()

def show_dashboard():
    s = dashboard_stats()
    t = Table(title="Dashboard")
    for k,v in s.items(): t.add_row(k, str(v))
    console.print(t)

def show_top():
    rows = top_customers(10)
    t = Table(title="Top 10 customers")
    for c in ["ID","Name","Total Balance","Accounts"]: t.add_column(c)
    for r in rows: t.add_row(str(r["CustomerID"]), r["FullName"],
                             f"{r['TotalBalance']:.2f}", str(r["Accounts"]))
    console.print(t)

def show_branches():
    rows = branch_performance()
    t = Table(title="Branch performance")
    for c in ["ID","Branch","Accts","Custs","Deposits","30d Tx"]: t.add_column(c)
    for r in rows: t.add_row(str(r["BranchID"]), r["BranchName"],
        str(r["TotalAccounts"]), str(r["TotalCustomers"]),
        f"{r['TotalDeposits']:.2f}", str(r["TotalTransactions"]))
    console.print(t)

def show_suspicious():
    rows = suspicious_transactions()
    t = Table(title="🚨 Suspicious")
    for c in ["TxID","Account","Customer","Type","Amount","When"]: t.add_column(c)
    for r in rows[:30]:
        t.add_row(str(r["TransactionID"]), r["AccountNumber"], r["CustomerName"],
                  r["TxType"], f"{r['Amount']:.2f}", str(r["CreatedAt"]))
    console.print(t)

def menu(user):
    actions = {"1":("Dashboard",show_dashboard), "2":("Top customers",show_top),
               "3":("Branch perf",show_branches),
               "4":("Suspicious",show_suspicious), "0":("Back",None)}
    while True:
        for k,(n,_) in actions.items(): console.print(f"  [cyan]{k}[/] {n}")
        c = console.input("→ ")
        if c == "0": break
        if c in actions and actions[c][1]: actions[c][1]()
