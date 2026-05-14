-- Fix Bug #4: AccountType "credit" → "fixed"
-- Chạy lệnh này trong Docker:
-- docker compose exec mysql mysql -ubank -pbank123 banking < fix_bug4_accounttype.sql

USE banking;

-- Xem trước data bị ảnh hưởng
SELECT AccountType, COUNT(*) AS cnt
FROM Accounts
GROUP BY AccountType;

-- Fix: map "credit" → "fixed" (closest match về business logic)
UPDATE Accounts
SET AccountType = 'fixed'
WHERE AccountType = 'credit';

-- Xác nhận sau fix
SELECT AccountType, COUNT(*) AS cnt
FROM Accounts
GROUP BY AccountType;

SELECT CONCAT(ROW_COUNT(), ' rows updated.') AS result;