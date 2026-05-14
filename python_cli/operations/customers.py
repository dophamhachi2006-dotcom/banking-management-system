from rich.console import Console
from rich.table import Table
from core.db_connection import get_cursor
console = Console()

def list_customers():
    with get_cursor() as cur:
        cur.execute("SELECT CustomerID,FullName,Email,Phone,City FROM Customers LIMIT 50")
        rows = cur.fetchall()
    t = Table(title="Customers (first 50)")
    for c in ["ID","Name","Email","Phone","City"]: t.add_column(c)
    for r in rows: t.add_row(str(r["CustomerID"]),r["FullName"],r["Email"] or "",r["Phone"] or "",r["City"] or "")
    console.print(t)

def add_customer(user):
    if user["Role"] == "auditor":
        console.print("[red]Auditors cannot create customers[/]"); return
    name  = console.input("Full name: ")
    email = console.input("Email: ")
    phone = console.input("Phone: ")
    with get_cursor(commit=True) as cur:
        cur.execute("INSERT INTO Customers (FullName,Email,Phone,CreatedBy) VALUES (%s,%s,%s,%s)",
                    (name, email or None, phone or None, user["UserID"]))
    console.print("[green]✅ Created[/]")

def menu(user):
    actions = {"1": ("List", list_customers),
               "2": ("Add",  lambda: add_customer(user)),
               "0": ("Back", None)}
    while True:
        for k,(n,_) in actions.items(): console.print(f"  [cyan]{k}[/] {n}")
        c = console.input("→ ")
        if c == "0": break
        if c in actions and actions[c][1]: actions[c][1]()
