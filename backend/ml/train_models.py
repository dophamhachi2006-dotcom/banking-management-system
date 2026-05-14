"""Train ML models from MySQL data.
Run AFTER backend/load_csv.py (or LOAD DATA via load_csv.sql).

Usage:  python backend/ml/train_models.py
"""
import os, sys, joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.cluster import KMeans

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from core.db_connection import get_conn

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))


def fetch_tx_features() -> pd.DataFrame:
    with get_conn() as conn:
        q = """
        SELECT t.TransactionID, t.AccountID, t.Amount, t.TxType,
               HOUR(t.CreatedAt)      AS hour_of_day,
               DAYOFWEEK(t.CreatedAt) AS day_of_week,
               a.Balance,
               CASE WHEN a.Balance > 0 THEN t.Amount/a.Balance
                    ELSE 1 END AS amount_balance_ratio
          FROM Transactions t JOIN Accounts a ON t.AccountID=a.AccountID
        """
        df = pd.read_sql(q, conn)
    return df


def label_fraud(df: pd.DataFrame) -> pd.Series:
    """Heuristic labels matching the synthetic fraud patterns
    injected by transform_kaggle_data.py."""
    spike = (df["Amount"] >= 15000) & (df["TxType"] == "withdrawal")
    late_night = ((df["hour_of_day"] <= 4) & (df["TxType"] == "withdrawal"))
    structuring = (df["TxType"] == "deposit") & df["Amount"].between(8900, 9999)
    # burst: per-account high frequency
    counts = df.groupby("AccountID").size()
    burst_accs = counts[counts > 30].index
    burst = df["AccountID"].isin(burst_accs)
    return (spike | late_night | structuring | burst).astype(int)


def train_fraud():
    print("⚙  Training fraud detector...")
    df = fetch_tx_features()
    if df.empty:
        print("⚠  No transaction data found."); return
    df["is_fraud"] = label_fraud(df)
    pos = int(df["is_fraud"].sum())
    print(f"   total={len(df):,}  positives={pos:,} ({pos/len(df):.2%})")
    if pos < 50:
        print("⚠  Too few fraud samples — skipping."); return
    feats = ["Amount", "hour_of_day", "day_of_week", "amount_balance_ratio"]
    X = df[feats].values
    y = df["is_fraud"].values
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2,
                                          random_state=42, stratify=y)
    scaler = StandardScaler().fit(Xtr)
    model = RandomForestClassifier(n_estimators=120, max_depth=12,
                                   class_weight="balanced",
                                   random_state=42, n_jobs=-1)
    model.fit(scaler.transform(Xtr), ytr)
    print(classification_report(yte, model.predict(scaler.transform(Xte)),
                                digits=3))
    joblib.dump(model, os.path.join(MODEL_DIR, "fraud_model.pkl"))
    joblib.dump(scaler, os.path.join(MODEL_DIR, "fraud_scaler.pkl"))
    print("✅ Fraud model saved.")


def fetch_customer_features() -> pd.DataFrame:
    with get_conn() as conn:
        q = """
        SELECT c.CustomerID,
               COALESCE(SUM(a.Balance),0)            AS total_balance,
               COALESCE(COUNT(t.TransactionID),0)    AS tx_count,
               COALESCE(AVG(t.Amount),0)             AS avg_tx_amount,
               COALESCE(MAX(t.Amount),0)             AS max_tx_amount
          FROM Customers c
          LEFT JOIN Accounts a    ON a.CustomerID=c.CustomerID
          LEFT JOIN Transactions t ON t.AccountID=a.AccountID
         GROUP BY c.CustomerID
        """
        df = pd.read_sql(q, conn)
    return df


def train_segmentation():
    print("⚙  Training customer segmenter...")
    df = fetch_customer_features()
    if len(df) < 4:
        print("⚠  Not enough customers."); return
    feats = ["total_balance", "tx_count", "avg_tx_amount"]
    X = df[feats].values
    scaler = StandardScaler().fit(X)
    model = KMeans(n_clusters=4, random_state=42, n_init=10)
    model.fit(scaler.transform(X))
    # Sort cluster centers by mean balance for stable labels
    centers = scaler.inverse_transform(model.cluster_centers_)
    print("   cluster centers (balance, tx_count, avg_amt):")
    for i, c in enumerate(centers):
        print(f"     #{i}  bal={c[0]:>12,.0f}  n={c[1]:>6.1f}  avg={c[2]:>8,.0f}")
    joblib.dump(model, os.path.join(MODEL_DIR, "segmenter_model.pkl"))
    joblib.dump(scaler, os.path.join(MODEL_DIR, "segmenter_scaler.pkl"))
    print("✅ Segmenter saved.")


if __name__ == "__main__":
    try: train_fraud()
    except Exception as e: print("Fraud training error:", e)
    try: train_segmentation()
    except Exception as e: print("Segmentation training error:", e)
