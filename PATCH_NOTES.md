# 🔧 PATCH NOTES — v2 improvements

This patch adds the missing pieces highlighted in the review.

## 1. Real SMTP email (`backend/services/notification_service.py`)

- New `NotificationService` with TLS SMTP + automatic mock fallback
  when SMTP credentials are missing.
- Templated helpers:
  - `notify_large_withdrawal(email, amount, account_number)`
  - `notify_account_opened(email, account_number)`
  - `notify_suspicious_activity(email, reason)`
- Test it: `python backend/test_email.py you@example.com`
- Configure via `backend/.env` (see `.env.example`):
  ```env
  SMTP_SERVER=smtp.gmail.com
  SMTP_PORT=587
  SMTP_USER=you@gmail.com
  SMTP_PASS=app-password
  ```

## 2. Machine-Learning models (`backend/ml/`)

| File | Purpose |
|------|---------|
| `fraud_detection_model.py` | RandomForest fraud classifier wrapper |
| `customer_segmentation.py` | KMeans (4 clusters: VIP / Active / Regular / Inactive) |
| `train_models.py`          | Train both models from MySQL |

Both wrappers degrade gracefully to **rule-based fallback** if `.pkl`
files aren't trained yet, so the API works out of the box.

```bash
pip install -r backend/requirements.txt   # adds scikit-learn / pandas / joblib
python backend/ml/train_models.py         # trains & saves *.pkl
```

### New API routes (`/api/ml/*`)

| Method | Endpoint | Body |
|--------|----------|------|
| GET  | `/api/ml/status` | — |
| POST | `/api/ml/predict-fraud` | `{amount, hour_of_day, day_of_week, amount_balance_ratio}` |
| POST | `/api/ml/segment-customer` | `{total_balance, tx_count, avg_tx_amount}` |

## 3. D3.js advanced charts (`frontend/src/components/charts/`)

- `TransactionHeatmap.tsx` — Hour × Day heatmap.
- `MoneyFlowSankey.tsx` — Sankey diagram for branch → account-type money flow.
- `NetworkGraph.tsx` — Force-directed customer relationship network.
- New page: `/reports/advanced` (`frontend/src/routes/reports.advanced.tsx`).

```bash
cd frontend && npm install   # picks up d3 + d3-sankey
npm run dev
# open http://localhost:5173/reports/advanced
```

## 4. Fake data generator (`data_generation/generate_all.py`)

Use this if you can't (or don't want to) pull from Kaggle:

```bash
pip install faker
python data_generation/generate_all.py
ls data_generation/csv_output/
```

Creates: `branches.csv` (10), `employees.csv` (510), `customers.csv`
(510), `accounts.csv` (510), `transactions.csv` (2000) — ready for
`database/load_csv.sql`.

## 5. Misc

- `.env.example` added for both quick setup.
- `requirements.txt` updated: `bcrypt`, `pytest-cov`, ML stack, `faker`.
- `app.py` registers the new `ml_bp` blueprint.
- `routeTree.tsx` registers `/reports/advanced`.

---
**Drop-in:** unzip on top of your existing `bms/` folder; only listed files
are added/changed.
