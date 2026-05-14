#!/bin/sh
set -e

DB_HOST="${DB_HOST:-mysql}"
DB_PORT="${DB_PORT:-3306}"
DB_USER="${DB_USER:-bank}"
DB_PASSWORD="${DB_PASSWORD:-bank123}"
DB_NAME="${DB_NAME:-banking}"

echo "⏳ Waiting for MySQL at ${DB_HOST}:${DB_PORT} to be fully ready..."

MAX_RETRIES=60
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  if python3 -c "
import mysql.connector, sys
try:
    conn = mysql.connector.connect(
        host='${DB_HOST}', port=int('${DB_PORT}'),
        user='${DB_USER}', password='${DB_PASSWORD}',
        database='${DB_NAME}', connect_timeout=5
    )
    conn.ping(reconnect=True)
    conn.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; then
    echo "✅ MySQL is ready!"
    break
  fi

  RETRY_COUNT=$((RETRY_COUNT + 1))
  echo "   MySQL not ready yet (attempt ${RETRY_COUNT}/${MAX_RETRIES}), retrying in 3s..."
  sleep 3
done

if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
  echo "❌ MySQL did not become ready in time. Exiting."
  exit 1
fi

# ---- Seed users ----
echo "🔑 Seeding user passwords..."
python3 backend/seed_users.py || echo "⚠️ Seed đã chạy trước đó, bỏ qua."

# ---- Guard: kiểm tra DB đã có data chưa ----
echo "🔍 Checking existing data in DB..."

ROW_COUNT=$(mysql -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASSWORD" -N -B -e \
  "SELECT COUNT(*) FROM ${DB_NAME}.transactions;" 2>/dev/null || echo 0)

echo "📊 Current transactions count: $ROW_COUNT"

if [ "$ROW_COUNT" -gt 1000 ]; then
  echo "✅ DB đã có data ($ROW_COUNT rows) → bỏ qua init nặng."

else
  echo "⚠️ DB trống → chạy full pipeline init..."

  echo "📊 Generating CSV data from Kaggle + Faker..."
  python3 data_generation/transform_kaggle_data.py \
    || echo "⚠️ Data generation lỗi, tiếp tục..."

  # v6: generate card transaction history TRƯỚC khi load CSV
  echo "💳 Generating card transaction data (v6)..."
  python3 data_generation/generate_card_transactions.py \
    || echo "⚠️ Card transaction generation lỗi, tiếp tục..."

  echo "📥 Loading CSV data vào MySQL..."
  python3 backend/load_csv.py \
    || echo "⚠️ Load CSV lỗi, tiếp tục..."

  # v6: zero-out balance của closed accounts (fix Close account bug)
  echo "🔧 Fixing closed account balances..."
  python3 -c "
import mysql.connector, os
conn = mysql.connector.connect(
    host=os.getenv('DB_HOST','mysql'),
    user=os.getenv('DB_USER','bank'),
    password=os.getenv('DB_PASSWORD','bank123'),
    database=os.getenv('DB_NAME','banking')
)
cur = conn.cursor()
cur.execute(\"UPDATE Accounts SET Balance=0.00 WHERE Status='closed' AND Balance>0\")
conn.commit()
print(f'  ✔ {cur.rowcount} closed account(s) balance zeroed out.')
conn.close()
" || echo "⚠️ Balance fix lỗi, bỏ qua."

  echo "🤖 Training ML models..."
  python3 backend/ml/train_models.py \
    || echo "⚠️ Train ML lỗi, bỏ qua."
fi

# ---- Start app ----
echo "🚀 Starting Flask..."
exec python3 backend/app.py
