"""Python CLI for Banking Management System."""
import os, sys, getpass
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.security import check_password_hash
from rich.console import Console
from rich.table import Table
from core.db_connection import get_cursor

from python_cli.operations.customers   import menu as customers_menu
from python_cli.operations.accounts    import menu as accounts_menu
from python_cli.operations.transactions import menu as tx_menu
from python_cli.reports.reports        import menu as reports_menu

console = Console()

def login() -> dict | None:
    console.rule("[bold cyan]🏦 Banking Management System CLI[/]")
    for _ in range(3):
        u = console.input("Username: ")
        p = getpass.getpass("Password: ")
        with get_cursor() as cur:
            cur.execute("SELECT * FROM Users WHERE Username=%s AND IsActive=1", (u,))
            user = cur.fetchone()
        if user and check_password_hash(user["PasswordHash"], p):
            console.print(f"[green]✅ Welcome {user['Username']} ({user['Role']})[/]")
            return user
        console.print("[red]Invalid credentials[/]")
    return None

def main():
    user = login()
    if not user: return
    actions = {
        "1": ("Customers",     lambda: customers_menu(user)),
        "2": ("Accounts",      lambda: accounts_menu(user)),
        "3": ("Transactions",  lambda: tx_menu(user)),
        "4": ("Reports",       lambda: reports_menu(user)),
        "0": ("Exit", None),
    }
    while True:
        console.rule("Main menu")
        t = Table(show_header=False, box=None)
        for k,(name,_) in actions.items(): t.add_row(f"[cyan]{k}[/]", name)
        console.print(t)
        choice = console.input("Choose: ").strip()
        if choice == "0": console.print("👋 Bye"); break
        if choice in actions and actions[choice][1]:
            try: actions[choice][1]()
            except Exception as e: console.print(f"[red]Error:[/] {e}")
        else:
            console.print("[yellow]Invalid choice[/]")

if __name__ == "__main__": main()
