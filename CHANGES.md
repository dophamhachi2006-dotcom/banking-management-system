# Banking Management System — Production Refactor

This patch removes all test/mock data and switches the system to use the
**full Kaggle dataset** with realistic generated Employees and Transactions.

## What changed

### Data pipeline
- `data_generation/transform_kaggle_data.py` — **rewritten**. Now consumes the
  ENTIRE Kaggle dataset (no 510-row cap):
  - 500 branches, 50 000 customers, 75 000 accounts,
    30 000 loans, 100 000 cards.
  - Generates **5 000 employees** (≈10/branch) with realistic salary
    distributions per position (Manager, Auditor, Loan Officer, Teller,
    Cashier) and an `active|inactive|terminated` Status column.
  - Generates **~605 000 transactions** with:
    - per-account-type type mix (savings vs checking vs fixed),
    - log-normal amount distribution and business-hours weighting,
    - **injected fraud signals** for ~1.5 % of accounts:
      burst activity, amount spikes, late-night withdrawals,
      sub-$10k structuring deposits.
- `data_generation/generate_employees.py` and `generate_all.py` —
  **removed** (replaced by transform_kaggle_data.py).
- `database/seed_data.sql` — **stripped**. No more 20-customer mock
  data; only bootstraps the three auth users.
- `database/load_csv.sql` — updated to match the new wider Accounts/
  Employees CSV columns and to truncate before reload.
- `backend/load_csv.py` — **new** Python loader as a fallback when
  `LOAD DATA LOCAL INFILE` is not available (Docker / managed MySQL).
  Streams CSVs in 5 000-row batches and links one Manager per branch.

### Email notifications (now actually fire)
- `backend/routes/transaction_routes.py` — withdrawal / transfer / deposit
  endpoints now invoke `notifier` for:
  - **Large withdrawals** (≥ $10 000) → `notify_large_withdrawal`
  - **Suspicious activity** (any rule flag) → `notify_suspicious_activity`
- `backend/routes/account_routes.py` — `POST /accounts` now sends
  `notify_account_opened` to the customer's email and auto-generates an
  AccountNumber when missing. Added `status`, `type`, `q` filters.
- `backend/services/notification_service.py` — unchanged (already
  supports SMTP via env vars with mock fallback).

### ML pipeline
- `backend/ml/train_models.py`:
  - Fixed broken `get_connection` import → `get_conn`.
  - Fraud labels now match the synthetic patterns the generator injects
    (spike, late_night, structuring, burst), so the RandomForest learns
    the right signals.
  - Trains on full Transactions table (~605k rows), prints
    `classification_report`.
  - Customer segmentation prints cluster centers for interpretability.
- Inference wrappers (`fraud_detection_model.py`, `customer_segmentation.py`)
  unchanged.

### Search & filter
- `transaction_routes.py` adds `q` query parameter (matches customer
  name / account number / description).
- `account_routes.py` adds `status`, `type`, `q` filters.
- `customer_routes.py` already supports `q` (name / email / phone).

### Audit & reporting
- `audit_routes.py` already supports `table`, `action`, `user_id` filters
  with pagination — kept unchanged.
- `report_routes.py` exposes dashboard stats, top customers, branch
  performance, monthly summaries, suspicious transactions — kept.

## How to run

```bash
# 1. Generate CSVs from raw Kaggle data (~1 min)
pip install -r backend/requirements.txt
python data_generation/transform_kaggle_data.py

# 2. Initialize schema
mysql -u root -p < database/00_init_all.sql

# 3a. Bulk load via LOAD DATA LOCAL INFILE (fastest, needs local_infile=1)
mysql --local-infile=1 -u root -p banking < database/load_csv.sql

# 3b. OR Python fallback (works on Docker / managed MySQL)
python backend/load_csv.py --truncate

# 4. Set real auth user passwords
python backend/seed_users.py

# 5. Train ML models (~30s on the ~600k tx dataset)
python backend/ml/train_models.py

# 6. Boot the API
python backend/app.py
```

## Tunables

The generator honors environment variables:

| Var              | Default | Effect                          |
|------------------|---------|---------------------------------|
| `N_BRANCHES`     | 500     | branches to keep from Kaggle    |
| `N_EMPLOYEES`    | 5000    | total employees to generate     |
| `N_TX_PER_ACC`   | 8       | mean transactions per account   |
| `FRAUD_RATE`     | 0.015   | fraction of accounts with fraud |

Email SMTP is configured via:
`SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`.
If `SMTP_USER`/`SMTP_PASS` are unset, the notifier prints a `[MOCK EMAIL]`
log line and returns `True` — the rest of the system works unchanged.
