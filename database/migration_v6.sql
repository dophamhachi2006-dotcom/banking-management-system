-- =============================================================
-- Migration v6  —  chạy file này trên database ĐANG CÓ SẴN
-- để áp dụng toàn bộ bổ sung & fix của v6.
--
-- An toàn khi chạy nhiều lần: dùng DROP IF EXISTS trước khi tạo lại.
-- Thứ tự: functions → triggers → views → data fixes → card data seed.
-- =============================================================

USE banking;

-- =============================================================
-- SECTION 1: User-Defined Functions mới
-- =============================================================

DELIMITER $$

-- 1a. Tính lãi đơn cho một tài khoản
--     Dùng: SELECT fn_calculate_interest(account_id, annual_rate_pct, days);
DROP FUNCTION IF EXISTS fn_calculate_interest$$
CREATE FUNCTION fn_calculate_interest(
  p_account_id  INT,
  p_annual_rate DECIMAL(5,2),
  p_days        INT
)
RETURNS DECIMAL(15,2)
READS SQL DATA
COMMENT 'Tính lãi đơn: Balance × (rate/100) × (days/365)'
BEGIN
  DECLARE v_principal DECIMAL(15,2) DEFAULT 0;
  SELECT Balance INTO v_principal FROM Accounts WHERE AccountID = p_account_id;
  RETURN ROUND(v_principal * (p_annual_rate / 100) * (p_days / 365.0), 2);
END$$

-- 1b. Kiểm tra số dư tối thiểu trước khi rút tiền
--     Trả về 1 (được rút) hoặc 0 (vi phạm mức tối thiểu)
--     Mức tối thiểu: savings=$100, checking=$50, fixed=$500, khác=$0
DROP FUNCTION IF EXISTS fn_min_balance_check$$
CREATE FUNCTION fn_min_balance_check(
  p_account_id   INT,
  p_withdraw_amt DECIMAL(15,2)
)
RETURNS TINYINT(1)
READS SQL DATA
COMMENT 'Trả về 1 nếu số dư sau rút >= mức tối thiểu theo loại tài khoản, 0 nếu vi phạm'
BEGIN
  DECLARE v_balance       DECIMAL(15,2) DEFAULT 0;
  DECLARE v_type          VARCHAR(20)   DEFAULT 'savings';
  DECLARE v_min           DECIMAL(15,2) DEFAULT 0;

  SELECT Balance, AccountType INTO v_balance, v_type
  FROM Accounts WHERE AccountID = p_account_id;

  SET v_min = CASE v_type
    WHEN 'savings'  THEN 100.00
    WHEN 'checking' THEN  50.00
    WHEN 'fixed'    THEN 500.00
    ELSE 0.00
  END;

  RETURN IF((v_balance - p_withdraw_amt) >= v_min, 1, 0);
END$$

DELIMITER ;

-- =============================================================
-- SECTION 2: Triggers mới / cập nhật
-- =============================================================

DELIMITER $$

DROP TRIGGER IF EXISTS trg_tx_after_insert$$
DROP TRIGGER IF EXISTS trg_tx_suspicious_after_insert$$

-- 2a. Tự động log mọi giao dịch mới vào AuditLog ở tầng DB
CREATE TRIGGER trg_tx_after_insert
AFTER INSERT ON Transactions FOR EACH ROW
BEGIN
  INSERT INTO AuditLog(TableName, RecordID, Action, NewData, PerformedBy)
  VALUES (
    'Transactions', NEW.TransactionID, 'INSERT',
    JSON_OBJECT(
      'AccountID',    NEW.AccountID,
      'TxType',       NEW.TxType,
      'Amount',       NEW.Amount,
      'BalanceAfter', NEW.BalanceAfter,
      'Status',       NEW.Status,
      'Description',  NEW.Description
    ),
    NEW.PerformedBy
  );
END$$

-- 2b. Phát hiện và ghi nhận giao dịch đáng ngờ
--     Tiêu chí: amount >= 50.000 HOẶC >= 5 giao dịch trong 1 giờ cùng tài khoản
CREATE TRIGGER trg_tx_suspicious_after_insert
AFTER INSERT ON Transactions FOR EACH ROW
BEGIN
  DECLARE v_rapid_count INT DEFAULT 0;

  SELECT COUNT(*) INTO v_rapid_count
  FROM   Transactions
  WHERE  AccountID = NEW.AccountID
    AND  CreatedAt >= DATE_SUB(NOW(), INTERVAL 1 HOUR);

  IF NEW.Amount >= 50000 OR v_rapid_count >= 5 THEN
    INSERT INTO AuditLog(TableName, RecordID, Action, NewData, PerformedBy)
    VALUES (
      'SuspiciousActivity', NEW.TransactionID, 'INSERT',
      JSON_OBJECT(
        'AccountID', NEW.AccountID,
        'TxType',    NEW.TxType,
        'Amount',    NEW.Amount,
        'Reason',    IF(NEW.Amount >= 50000, 'large_amount', 'rapid_transactions'),
        'TxCount1h', v_rapid_count
      ),
      NEW.PerformedBy
    );
  END IF;
END$$

DELIMITER ;

-- =============================================================
-- SECTION 3: Views cập nhật (fix AccountCount=0 / TotalBalance=0)
-- =============================================================

-- AccountCount đếm TẤT CẢ tài khoản, TotalBalance chỉ cộng active
CREATE OR REPLACE VIEW vw_customer_summary AS
SELECT
  c.CustomerID, c.FullName, c.Email, c.Phone, c.City, c.IDNumber,
  COUNT(a.AccountID) AS AccountCount,
  COALESCE(SUM(CASE WHEN a.Status = 'active' THEN a.Balance ELSE 0 END), 0) AS TotalBalance,
  c.CreatedAt
FROM Customers c
LEFT JOIN Accounts a ON a.CustomerID = c.CustomerID
GROUP BY c.CustomerID;

-- LEFT JOINs để tài khoản mồ côi (FK hỏng từ CSV) vẫn hiện
CREATE OR REPLACE VIEW vw_account_details AS
SELECT
  a.AccountID, a.AccountNumber, a.AccountType, a.Balance, a.Currency, a.Status,
  COALESCE(c.CustomerID, 0)  AS CustomerID,
  COALESCE(c.FullName,  '')  AS CustomerName,
  COALESCE(c.Email,     '')  AS CustomerEmail,
  COALESCE(b.BranchID,  0)   AS BranchID,
  COALESCE(b.BranchName,'')  AS BranchName,
  COALESCE(b.City,      '')  AS BranchCity,
  a.OpenedAt
FROM Accounts a
LEFT JOIN Customers c ON c.CustomerID = a.CustomerID
LEFT JOIN Branches  b ON b.BranchID   = a.BranchID;

-- =============================================================
-- SECTION 4: Fix data — Close account bị reject (balance > 0)
-- Các tài khoản đã Status='closed' trong DB (import từ CSV) nhưng
-- Balance > 0 sẽ bị rule "cannot close with balance" block mãi mãi.
-- Zero-out để nhất quán với business rule.
-- =============================================================

UPDATE Accounts
SET Balance = 0.00
WHERE Status = 'closed' AND Balance > 0;

SELECT CONCAT(ROW_COUNT(), ' closed account(s) balance zeroed out.') AS info;

-- =============================================================
-- SECTION 5: Seed CardTransactions (fix Credit Cards History trống)
-- Tạo ~10 giao dịch ngẫu nhiên cho mỗi thẻ active/expired.
-- Chạy an toàn: chỉ insert khi bảng đang trống để tránh duplicate.
-- =============================================================

SET @ct_count = (SELECT COUNT(*) FROM CardTransactions);

SET @insert_sql = IF(@ct_count = 0,
  'INSERT INTO CardTransactions (CardID, Amount, Merchant, Description, Status, CreatedAt)
   SELECT
     cc.CardID,
     ROUND(5 + RAND() * 1495, 2),
     ELT(1 + FLOOR(RAND() * 12),
       ''Amazon'',''Walmart'',''Starbucks'',''Netflix'',''Uber'',
       ''Apple Store'',''Google Pay'',''Target'',''Shell'',''McDonald''s'',
       ''Grab'',''Shopee''),
     ELT(1 + FLOOR(RAND() * 4),
       ''Online purchase'',''In-store purchase'',
       ''Subscription'',''Bill payment''),
     ELT(1 + FLOOR(RAND() * 10),
       ''approved'',''approved'',''approved'',''approved'',''approved'',
       ''approved'',''approved'',''approved'',''declined'',''reversed''),
     DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 365) DAY)
   FROM CreditCards cc
   CROSS JOIN (
     SELECT 1 n UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5
     UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION SELECT 10
   ) nums
   WHERE cc.Status IN (''active'', ''expired'')',
  'SELECT ''CardTransactions already has data, skipping seed.'' AS info'
);

PREPARE _stmt FROM @insert_sql;
EXECUTE _stmt;
DEALLOCATE PREPARE _stmt;

SELECT CONCAT(
  (SELECT COUNT(*) FROM CardTransactions), ' total rows in CardTransactions.'
) AS info;

SELECT 'Migration v6 complete.' AS status;
