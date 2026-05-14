"""Generate card_transactions.csv for CardTransactions table.

Tạo ~10-15 giao dịch thẻ ngẫu nhiên cho mỗi thẻ active/expired trong cards.csv.
Output: data_generation/csv_output/card_transactions.csv

Run AFTER transform_kaggle_data.py:
    python data_generation/generate_card_transactions.py
"""
import os, csv, random
from datetime import datetime, timedelta

random.seed(42)

BASE   = os.path.dirname(__file__)
OUT    = os.path.join(BASE, "csv_output")
CARDS  = os.path.join(OUT, "cards.csv")
OUTPUT = os.path.join(OUT, "card_transactions.csv")

MERCHANTS = [
    "Amazon", "Walmart", "Starbucks", "Netflix", "Uber",
    "Apple Store", "Google Play", "Target", "Shell", "McDonald's",
    "Grab", "Shopee", "Lazada", "Booking.com", "Spotify",
    "AliExpress", "Zara", "H&M", "IKEA", "Airbnb",
]

DESCRIPTIONS = [
    "Online purchase", "In-store purchase", "Subscription",
    "Bill payment", "Food & beverage", "Travel booking",
    "Entertainment", "Fuel", "Grocery",
]

STATUSES = (
    ["approved"] * 8 + ["declined"] * 1 + ["reversed"] * 1
)


def rand_date(days_back=365):
    delta = timedelta(days=random.randint(0, days_back))
    return (datetime.now() - delta).strftime("%Y-%m-%d %H:%M:%S")


def main():
    if not os.path.exists(CARDS):
        print(f"⚠️  {CARDS} not found. Run transform_kaggle_data.py first.")
        return

    os.makedirs(OUT, exist_ok=True)

    # Read card IDs from cards.csv — column order: CardNumber,CustomerID,...
    card_ids = []
    with open(CARDS, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            status = (row.get("Status") or "active").strip().lower()
            if status in ("active", "expired"):
                # cards.csv doesn't have CardID (auto-increment); use row index
                card_ids.append(None)   # placeholder — we'll use DB order

    # Since we don't know the auto-increment IDs assigned by MySQL after LOAD DATA,
    # we generate transactions keyed to sequential CardID starting from 1.
    # This matches MySQL's AUTO_INCREMENT behavior when cards.csv is loaded clean.
    rows = []
    for card_id_seq, _ in enumerate(card_ids, start=1):
        n_tx = random.randint(8, 15)
        for _ in range(n_tx):
            rows.append({
                "CardID":      card_id_seq,
                "Amount":      round(random.uniform(5.0, 1500.0), 2),
                "Merchant":    random.choice(MERCHANTS),
                "Description": random.choice(DESCRIPTIONS),
                "Status":      random.choice(STATUSES),
                "CreatedAt":   rand_date(365),
            })

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["CardID","Amount","Merchant",
                                               "Description","Status","CreatedAt"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"✔ card_transactions.csv — {len(rows):,} rows written to {OUTPUT}")


if __name__ == "__main__":
    main()
