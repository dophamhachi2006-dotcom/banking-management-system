"""Transform raw Kaggle CSVs -> schema-compatible CSVs in csv_output/.

Uses FULL Kaggle dataset (50k customers, 75k accounts, 500 branches,
30k loans, 100k cards). Generates realistic Employees + Transactions
(Kaggle source does not include them) with:
  - employee count proportional to branches, salaries by position
  - transactions distributed over 12 months, type mix per account type
  - injected fraud signals: amount spikes, late-night withdrawals,
    burst activity, round-amount structuring

Run:
    pip install faker
    python data_generation/transform_kaggle_data.py
"""
import os, csv, sys, random, hashlib
from datetime import datetime, timedelta, time
from faker import Faker

fake = Faker(["en_US"])
random.seed(42)
Faker.seed(42)

BASE = os.path.dirname(__file__)
RAW  = os.path.join(BASE, "raw_kaggle")
OUT  = os.path.join(BASE, "csv_output")
os.makedirs(OUT, exist_ok=True)

# Tunables (env override) - default = full Kaggle
N_BRANCHES   = int(os.getenv("N_BRANCHES", "500"))
N_EMPLOYEES  = int(os.getenv("N_EMPLOYEES", "5000"))   # ~10 per branch
N_TX_PER_ACC = int(os.getenv("N_TX_PER_ACC", "8"))     # avg, ~600k for 75k accs
FRAUD_RATE   = float(os.getenv("FRAUD_RATE", "0.015")) # ~1.5% suspicious

POSITIONS = {
    "Manager":     (3500, 6500),
    "Auditor":     (2200, 3800),
    "Loan Officer":(1800, 3200),
    "Teller":      ( 900, 1600),
    "Cashier":     ( 800, 1300),
}
POSITION_WEIGHTS = [1, 1, 2, 5, 3]   # most are tellers/cashiers
TX_TYPES_BY_ACCT = {
    "savings":  [("deposit", 4), ("withdrawal", 3), ("transfer", 2), ("interest", 1)],
    "checking": [("deposit", 3), ("withdrawal", 5), ("transfer", 4), ("fee", 1)],
    "fixed":    [("deposit", 2), ("interest", 5), ("withdrawal", 1)],
}


def _read(name, limit=None):
    p = os.path.join(RAW, name)
    if not os.path.exists(p):
        print(f"⚠️  missing {p}", file=sys.stderr)
        return []
    with open(p, newline="", encoding="utf-8", errors="ignore") as f:
        rows = list(csv.DictReader(f))
    return rows[:limit] if limit else rows


def _write(name, header, rows):
    p = os.path.join(OUT, name)
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  ✔ {name:20s} {len(rows):>7,} rows")


def _weighted(items_weights):
    items, weights = zip(*items_weights)
    return random.choices(items, weights=weights, k=1)[0]


# ---------- 1) Branches ----------
def transform_branches():
    src = _read("branches.csv", limit=N_BRANCHES)
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
              "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
              "Austin", "Jacksonville", "Fort Worth", "Columbus", "Charlotte",
              "Indianapolis", "Seattle", "Denver", "Boston", "Miami"]
    rows = []
    for i, r in enumerate(src, 1):
        rows.append([
            r.get("branch_name") or f"Branch {i:04d}",
            fake.street_address(),
            random.choice(cities),
            fake.numerify("###-###-####"),
        ])
    _write("branches.csv",
           ["BranchName","Address","City","Phone"], rows)
    return len(rows)


# ---------- 2) Employees ----------
def transform_employees(n_branches):
    rows = []
    used_emails = set()
    positions, weights = list(POSITIONS.keys()), POSITION_WEIGHTS
    for i in range(1, N_EMPLOYEES + 1):
        first, last = fake.first_name(), fake.last_name()
        full = f"{first} {last}"
        base = f"{first.lower()}.{last.lower()}"
        email = f"{base}@bank.local"
        suffix = 1
        while email in used_emails:
            suffix += 1
            email = f"{base}{suffix}@bank.local"
        used_emails.add(email)

        position = random.choices(positions, weights=weights, k=1)[0]
        lo, hi = POSITIONS[position]
        salary = round(random.uniform(lo, hi), 2)
        hired_days = random.randint(60, 365 * 12)
        hired_at = (datetime.now() - timedelta(days=hired_days)).date()
        status = random.choices(
            ["active","inactive","terminated"], weights=[92, 5, 3])[0]
        rows.append([
            full, email, fake.numerify("###-###-####"),
            position, random.randint(1, n_branches),
            salary, hired_at, status,
        ])
    _write("employees.csv",
           ["FullName","Email","Phone","Position","BranchID",
            "Salary","HiredAt","Status"], rows)


# ---------- 3) Customers ----------
def transform_customers():
    src = _read("customers.csv")
    rows = []
    used_email, used_id = set(), set()
    for i, r in enumerate(src, 1):
        first = (r.get("first_name") or "").strip() or fake.first_name()
        last  = (r.get("last_name") or "").strip()  or fake.last_name()
        full = f"{first} {last}".strip()
        email = (r.get("email") or "").strip() or f"cust{i}@mail.com"
        if email in used_email:
            email = f"cust{i}.{hashlib.md5(email.encode()).hexdigest()[:6]}@mail.com"
        used_email.add(email)
        idnum = f"ID{i:09d}"
        used_id.add(idnum)
        rows.append([
            full, email, fake.numerify("###-###-####"),
            fake.date_of_birth(minimum_age=18, maximum_age=85),
            fake.street_address(),
            (r.get("city") or fake.city())[:80],
            idnum,
        ])
    _write("customers.csv",
           ["FullName","Email","Phone","DateOfBirth",
            "Address","City","IDNumber"], rows)
    return len(rows)


# ---------- 4) Accounts ----------
def transform_accounts(n_customers, n_branches):
    src = _read("accounts.csv")
    seen_num = set()
    rows = []
    # Map kaggle customer_id -> our 1..n_customers (round-robin)
    kaggle_ids = {}
    for r in src:
        cid = r.get("customer_id") or ""
        if cid and cid not in kaggle_ids:
            kaggle_ids[cid] = (len(kaggle_ids) % n_customers) + 1

    for i, r in enumerate(src, 1):
        atype = (r.get("account_type") or "").strip().lower()
        if atype not in ("savings","checking","fixed"):
            atype = random.choice(["savings","checking","fixed"])
        try:
            balance = float(r.get("balance_usd") or 0)
        except ValueError:
            balance = 0
        if balance <= 0:
            balance = round(random.uniform(100, 50000), 2)

        cid = kaggle_ids.get(r.get("customer_id"), ((i-1) % n_customers) + 1)
        num = f"ACC{20000000 + i:09d}"
        if num in seen_num: continue
        seen_num.add(num)
        opened = r.get("open_date") or fake.date_between(
            start_date="-5y", end_date="-1y").isoformat()
        status = random.choices(
            ["active","frozen","closed"], weights=[94, 3, 3])[0]
        rows.append([
            num, cid, random.randint(1, n_branches),
            atype, round(balance, 2), "USD", status, opened,
        ])
    _write("accounts.csv",
           ["AccountNumber","CustomerID","BranchID","AccountType",
            "Balance","Currency","Status","OpenedAt"], rows)
    return len(rows)


# ---------- 5) Transactions ----------
def transform_transactions(n_accounts):
    """Generate realistic transactions with injected fraud patterns."""
    n_tx = n_accounts * N_TX_PER_ACC
    rows = []
    now = datetime.now()
    start = now - timedelta(days=365)

    # Pre-pick which accounts get fraud signals
    fraud_accounts = set(random.sample(
        range(1, n_accounts + 1),
        max(1, int(n_accounts * FRAUD_RATE))))

    # Per-account quick lookup of type (need accounts list -> reread)
    acc_types = []
    with open(os.path.join(OUT, "accounts.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            acc_types.append(row["AccountType"])

    # Normal transactions
    for _ in range(n_tx):
        aid = random.randint(1, n_accounts)
        atype = acc_types[aid - 1]
        txtype = _weighted(TX_TYPES_BY_ACCT[atype])
        # Amount distribution: log-normal-ish
        if txtype == "interest":
            amt = round(random.uniform(5, 800), 2)
        elif txtype == "fee":
            amt = round(random.choice([2.50, 5.00, 12.00, 25.00, 35.00]), 2)
        else:
            amt = round(random.lognormvariate(4.5, 1.2), 2)
            amt = max(1.0, min(amt, 50000.0))
        ts = fake.date_time_between(start_date=start, end_date=now)
        # Business hours weighting: most tx 8-20h
        if random.random() < 0.85:
            ts = ts.replace(hour=random.randint(8, 20),
                            minute=random.randint(0, 59))
        rows.append([aid, txtype, amt,
                     fake.sentence(nb_words=4)[:200], ts.isoformat(sep=" ")])

    # Fraud injections
    for aid in fraud_accounts:
        kind = random.choice(["burst","spike","late_night","structuring"])
        if kind == "burst":
            base_ts = fake.date_time_between(start_date=start, end_date=now)
            for k in range(random.randint(6, 12)):
                rows.append([aid, "withdrawal",
                             round(random.uniform(100, 3000), 2),
                             "ATM rapid withdrawal",
                             (base_ts + timedelta(minutes=k*4)).isoformat(sep=" ")])
        elif kind == "spike":
            ts = fake.date_time_between(start_date=start, end_date=now)
            rows.append([aid, "withdrawal",
                         round(random.uniform(15000, 49000), 2),
                         "Large unusual withdrawal", ts.isoformat(sep=" ")])
        elif kind == "late_night":
            for _ in range(random.randint(3, 6)):
                ts = fake.date_time_between(start_date=start, end_date=now)
                ts = ts.replace(hour=random.randint(0, 4),
                                minute=random.randint(0, 59))
                rows.append([aid, "withdrawal",
                             round(random.uniform(200, 2500), 2),
                             "Late-night withdrawal", ts.isoformat(sep=" ")])
        else:  # structuring: many round amounts just under 10k
            base_ts = fake.date_time_between(start_date=start, end_date=now)
            for k in range(random.randint(4, 8)):
                rows.append([aid, "deposit",
                             round(random.choice([9000, 9500, 9800, 9900]), 2),
                             "Cash deposit",
                             (base_ts + timedelta(hours=k*6)).isoformat(sep=" ")])

    random.shuffle(rows)
    _write("transactions.csv",
           ["AccountID","TxType","Amount","Description","CreatedAt"], rows)


# ---------- 6) Loans ----------
def transform_loans(n_customers):
    src = _read("loans.csv")
    rows = []
    for r in src:
        try: principal = float(r.get("loan_amount") or 0)
        except ValueError: principal = 0
        if principal <= 0:
            principal = round(random.uniform(1000, 200000), 2)
        try: rate = float(r.get("interest_rate") or 0)
        except ValueError: rate = 0
        if rate <= 0: rate = round(random.uniform(3, 15), 2)
        term = random.choice([12, 24, 36, 48, 60, 84, 120])
        mr = rate / 100 / 12
        monthly = principal * mr / (1 - (1 + mr) ** -term) if mr else principal/term
        outstanding = round(principal * random.uniform(0.1, 1.0), 2)
        sd_str = r.get("start_date") or "2023-01-01"
        try: sd = datetime.strptime(sd_str, "%Y-%m-%d").date()
        except ValueError: sd = datetime(2023,1,1).date()
        ed = sd + timedelta(days=term * 30)
        status = random.choices(
            ["active","closed","pending","defaulted"],
            weights=[60, 25, 10, 5])[0]
        # Hash kaggle customer_id to a stable customer in our range
        cid = (abs(hash(r.get("customer_id") or "")) % n_customers) + 1
        rows.append([cid, round(principal,2), round(rate,2), term,
                     round(monthly,2), outstanding, status, sd, ed])
    _write("loans.csv",
           ["CustomerID","Principal","InterestRate","TermMonths",
            "MonthlyPayment","OutstandingBal","Status",
            "StartDate","EndDate"], rows)


# ---------- 7) Cards ----------
def transform_cards(n_customers):
    src = _read("cards.csv")
    seen = set()
    rows = []
    for r in src:
        while True:
            num = "".join(str(random.randint(0,9)) for _ in range(16))
            if num not in seen:
                seen.add(num); break
        limit = round(random.uniform(1000, 50000), 2)
        outstanding = round(limit * random.uniform(0, 0.8), 2)
        expiry = r.get("expiration_date") or fake.date_between(
            start_date="today", end_date="+5y").isoformat()
        status = random.choices(["active","blocked","expired"],
                                weights=[85,10,5])[0]
        cid = (abs(hash(r.get("account_id") or "")) % n_customers) + 1
        rows.append([num, cid, limit, outstanding, expiry, status])
    _write("cards.csv",
           ["CardNumber","CustomerID","CreditLimit",
            "OutstandingBal","ExpiryDate","Status"], rows)


if __name__ == "__main__":
    print(f"RAW = {RAW}\nOUT = {OUT}\n")
    print("→ Branches");      n_b = transform_branches()
    print("→ Employees");     transform_employees(n_b)
    print("→ Customers");     n_c = transform_customers()
    print("→ Accounts");      n_a = transform_accounts(n_c, n_b)
    print("→ Transactions");  transform_transactions(n_a)
    print("→ Loans");         transform_loans(n_c)
    print("→ Cards");          transform_cards(n_c)
    print("\n🎉 Done. Next:")
    print("   1) python backend/seed_users.py          (create auth users)")
    print("   2) mysql --local-infile=1 -u root -p banking < database/load_csv.sql")
    print("   3) python backend/ml/train_models.py     (train fraud + segmentation)")
