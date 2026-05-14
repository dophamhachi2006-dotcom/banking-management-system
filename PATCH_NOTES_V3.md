# Patch v3 — Bug fixes from QA report

## DB / SQL
- `database/views.sql`
  - `vw_customer_summary`: thêm cột `IDNumber` → fix lỗi 1054 khi search Customers theo IDNumber + AccountCount/TotalBalance hiển thị đúng.
  - `vw_monthly_tx_summary`: gộp theo Month, ORDER BY ASC → fix các nhãn `2026-05` lặp & sai thứ tự.
- `database/audit_log.sql`
  - Thêm bảng `CardTransactions` (cho Cards History).
  - Thêm trigger INSERT/UPDATE/DELETE cho Customers, Accounts, Transactions, Loans, CreditCards, Branches, Employees.
  - Mọi trigger ghi `PerformedBy = @app_user_id`.

## Backend
- `core/db_connection.py`: tự động `SET @app_user_id = current_user.uid` ở mỗi cursor → audit log có user.
- `backend/routes/loan_routes.py`: đổi `Outstanding` → `OutstandingBal` (đúng tên cột schema), set `MonthlyPayment` khi tạo loan → fix lỗi 1054 cho Pay/Interest.
- `backend/services/report_service.py`: sửa `SUM(Outstanding)` → `SUM(OutstandingBal)` → KPI ACTIVE LOANS / LOAN OUTSTANDING hiển thị đúng. ORDER BY Month ASC.
- `backend/routes/branch_routes.py`: bắt FK error khi xóa branch (HTTP 409 thân thiện thay vì raw SQL error 1451).

## Frontend
- `lib/utils.ts`: thêm `fmtMoneyCompact`, `fmtCompact`, `fmtMonth`. `fmtMoney` chuẩn hóa không hiển thị `.00`.
- `components/StatCard.tsx`: `truncate`, rút gọn số lớn → fix tràn KPI cards.
- `routes/dashboard.tsx`: rewrite charts — margin trái 60px, format YAxis compact, format XAxis Month, sort theo thời gian, leader-line cho Pie, empty-state cho Revenue.
- `routes/reports.tsx`: cùng pattern format/margin; Revenue chart sort, empty-state; Branch performance bar chart cao 400, xoay nhãn.
- `routes/employees.tsx`: thêm thanh search (ID, name, email, position, branch).
- `routes/cards.tsx`: cell Customer hiển thị fallback `Customer #ID` khi name rỗng (tránh hiện chuỗi rác từ data lệch).
- `routes/transactions.tsx`: thêm ô search `q` (đẩy xuống backend, đã hỗ trợ JOIN Customers/Accounts).
- `hooks/useDebounce.ts`: helper sẵn để bạn dùng debounce input nếu cần.

## Cần làm thủ công sau khi giải nén
1. Re-apply database (chỉ cần re-run views & triggers, KHÔNG cần drop database):
   ```
   mysql -u root -p banking < database/views.sql
   mysql -u root -p banking < database/audit_log.sql
   ```
2. Restart backend Flask.
3. Hard-refresh frontend (Ctrl+F5).

## Vẫn cần bạn xác minh
- **Cards search hiện cột Customer rác (lỗi 99998/99997)** → khả năng do `backend/load_csv.py` mapping cột lệch khi import. Nếu sau patch UI vẫn còn → cần re-import bảng Customers từ CSV với mapping đúng. Mở `load_csv.py` và kiểm tra thứ tự field.
- **Cards History rỗng** → nếu `CardTransactions` chưa có dữ liệu seed thì History sẽ luôn rỗng (đúng thiết kế hiện tại). Cần generate seed nếu muốn demo.
