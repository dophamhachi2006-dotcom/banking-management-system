from rich.console import Console
from rich.prompt import FloatPrompt, IntPrompt
from backend.services.transaction_service import do_deposit, do_withdraw, do_transfer
console = Console()

def deposit(user):
    aid = IntPrompt.ask("AccountID"); amt = FloatPrompt.ask("Amount")
    try:
        tid, bal = do_deposit(aid, amt, user["UserID"], "CLI deposit")
        console.print(f"[green]✅ TX #{tid}, new balance {bal:.2f}[/]")
    except Exception as e: console.print(f"[red]{e}[/]")

def withdraw(user):
    aid = IntPrompt.ask("AccountID"); amt = FloatPrompt.ask("Amount")
    try:
        tid, bal = do_withdraw(aid, amt, user["UserID"], "CLI withdraw")
        console.print(f"[green]✅ TX #{tid}, new balance {bal:.2f}[/]")
    except Exception as e: console.print(f"[red]{e}[/]")

def transfer(user):
    f = IntPrompt.ask("From AccID"); t = IntPrompt.ask("To AccID"); a = FloatPrompt.ask("Amount")
    try:
        tid = do_transfer(f, t, a, user["UserID"], "CLI transfer")
        console.print(f"[green]✅ TX #{tid}[/]")
    except Exception as e: console.print(f"[red]{e}[/]")

def menu(user):
    if user["Role"] == "auditor":
        console.print("[red]Auditors are read-only[/]"); return
    actions = {"1":("Deposit",deposit), "2":("Withdraw",withdraw),
               "3":("Transfer",transfer), "0":("Back",None)}
    while True:
        for k,(n,_) in actions.items(): console.print(f"  [cyan]{k}[/] {n}")
        c = console.input("→ ")
        if c == "0": break
        if c in actions and actions[c][1]: actions[c][1](user)
