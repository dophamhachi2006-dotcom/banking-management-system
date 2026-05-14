from rich.console import Console
from rich.table import Table
from core.db_connection import get_cursor
console = Console()

def list_accounts():
    with get_cursor() as cur:
        cur.execute("SELECT * FROM vw_account_details LIMIT 50")
        rows = cur.fetchall()
    t = Table(title="Accounts")
    for c in ["AccID","Number","Customer","Branch","Type","Balance","Status"]: t.add_column(c)
    for r in rows:
        t.add_row(str(r["AccountID"]), r["AccountNumber"], r["CustomerName"],
                  r["BranchName"], r["AccountType"], f"{r['Balance']:.2f}", r["Status"])
    console.print(t)

def menu(user):
    while True:
        console.print("  [cyan]1[/] List   [cyan]0[/] Back")
        c = console.input("→ ")
        if c == "1": list_accounts()
        elif c == "0": break
