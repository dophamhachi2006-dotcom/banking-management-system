"""Inspect downloaded Kaggle CSV/SQLite headers."""
import os, sqlite3, csv

RAW = os.path.join(os.path.dirname(__file__), "kaggle_raw")

def main():
    if not os.path.isdir(RAW):
        print("Run download_kaggle.py first."); return
    for root,_,files in os.walk(RAW):
        for f in files:
            p = os.path.join(root, f)
            print(f"\n--- {p} ---")
            if f.endswith(".csv"):
                with open(p, encoding="utf-8", errors="ignore") as fh:
                    reader = csv.reader(fh); print("columns:", next(reader, []))
            elif f.endswith(".sqlite") or f.endswith(".db"):
                con = sqlite3.connect(p)
                for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'"):
                    print("table:", t)
                    cols = con.execute(f"PRAGMA table_info({t})").fetchall()
                    print("  columns:", [c[1] for c in cols])
                con.close()

if __name__ == "__main__": main()
