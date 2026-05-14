-- =============================================================
-- v6 Fixes — chạy tự động sau 00_init_all.sql (thứ tự alpha)
-- Docker mount: ./database/01_v6_fixes.sql:/docker-entrypoint-initdb.d/01_v6_fixes.sql
-- An toàn khi chạy nhiều lần: dùng IF NOT EXISTS / DROP IF EXISTS / CREATE OR REPLACE
-- =============================================================
USE banking;

-- =============================================================
-- 1. Bảng CardTransactions (thiếu trong 00_init_all.sql)
--    load_csv.py cần bảng này tồn tại trước khi load card_transactions.csv
-- =============================================================
CREATE TABLE IF NOT EXISTS CardTransactions (
  ID            BIGINT AUTO_INCREMENT PRIMARY KEY,
  CardID        INT NOT NULL,
  Amount        DECIMAL(15,2) NOT NULL,
  Merchant      VARCHAR(120),
  Description   VARCHAR(255),
  Status        ENUM('approved','declined','reversed') DEFAULT 'approved',
  CreatedAt     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (CardID) REFERENCES CreditCards(CardID) ON DELETE CASCADE,
  INDEX idx_cardtx_card (CardID),
  INDEX idx_cardtx_date (CreatedAt)
);

-- =============================================================
-- 2. AuditLog table (cần cho trigger logging)
-- =============================================================
CREATE TABLE IF NOT EXISTS AuditLog (
  AuditID      BIGINT AUTO_INCREMENT PRIMARY KEY,
  TableName    VARCHAR(60) NOT NULL,
  RecordID     VARCHAR(60) NOT NULL,
  Action       ENUM('INSERT','UPDATE','DELETE') NOT NULL,
  OldData      JSON NULL,
  NewData      JSON NULL,
  PerformedBy  INT NULL,
  IpAddress    VARCHAR(45),
  CreatedAt    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_audit_table (TableName),
  INDEX idx_audit_date  (CreatedAt),
  INDEX idx_audit_user  (PerformedBy)
);

-- =============================================================
-- 3. User-Defined Functions mới
-- =============================================================
DELIMITER $$

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

DROP FUNCTION IF EXISTS fn_min_balance_check$$
CREATE FUNCTION fn_min_balance_check(
  p_account_id   INT,
  p_withdraw_amt DECIMAL(15,2)
)
RETURNS TINYINT(1)
READS SQL DATA
COMMENT 'Trả về 1 nếu số dư sau rút >= mức tối thiểu, 0 nếu vi phạm'
BEGIN
  DECLARE v_balance DECIMAL(15,2) DEFAULT 0;
  DECLARE v_type    VARCHAR(20)   DEFAULT 'savings';
  DECLARE v_min     DECIMAL(15,2) DEFAULT 0;

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
-- 4. Triggers: auto-log giao dịch + phát hiện đáng ngờ
-- =============================================================
DELIMITER $$

DROP TRIGGER IF EXISTS trg_tx_after_insert$$
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

DROP TRIGGER IF EXISTS trg_tx_suspicious_after_insert$$
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
-- 5. Views đã fix (xoá AND a.Status='active' ở customer summary)
-- =============================================================

-- FIX BUG: Customers → Accounts=0, TotalBalance=0
-- AccountCount đếm TẤT CẢ tài khoản (không lọc status)
-- TotalBalance chỉ cộng tài khoản active
CREATE OR REPLACE VIEW vw_customer_summary AS
SELECT
  c.CustomerID,
  c.FullName,
  c.Email,
  c.Phone,
  c.City,
  c.IDNumber,
  COUNT(a.AccountID) AS AccountCount,
  COALESCE(SUM(CASE WHEN a.Status = 'active' THEN a.Balance ELSE 0 END), 0) AS TotalBalance,
  c.CreatedAt
FROM Customers c
LEFT JOIN Accounts a ON a.CustomerID = c.CustomerID
GROUP BY c.CustomerID;

-- Account details với LEFT JOINs (tài khoản mồ côi từ CSV vẫn hiện)
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

CREATE OR REPLACE VIEW vw_branch_performance AS
SELECT
  b.BranchID, b.BranchName, b.City,
  COUNT(DISTINCT a.AccountID)  AS TotalAccounts,
  COUNT(DISTINCT a.CustomerID) AS TotalCustomers,
  COALESCE(SUM(a.Balance), 0)  AS TotalDeposits,
  COUNT(t.TransactionID)       AS TotalTransactions
FROM Branches b
LEFT JOIN Accounts a     ON a.BranchID = b.BranchID AND a.Status = 'active'
LEFT JOIN Transactions t ON t.AccountID = a.AccountID
  AND t.CreatedAt >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY b.BranchID;

CREATE OR REPLACE VIEW vw_top_customers AS
SELECT
  c.CustomerID, c.FullName, c.Email,
  COALESCE(SUM(a.Balance), 0) AS TotalBalance,
  COUNT(a.AccountID)          AS Accounts
FROM Customers c
LEFT JOIN Accounts a ON a.CustomerID = c.CustomerID AND a.Status = 'active'
GROUP BY c.CustomerID
ORDER BY TotalBalance DESC;

CREATE OR REPLACE VIEW vw_suspicious_transactions AS
SELECT t.*, a.AccountNumber, c.FullName AS CustomerName
FROM Transactions t
JOIN Accounts  a ON a.AccountID  = t.AccountID
JOIN Customers c ON c.CustomerID = a.CustomerID
WHERE t.Amount >= 50000
   OR t.AccountID IN (
       SELECT AccountID FROM Transactions
       WHERE CreatedAt >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
       GROUP BY AccountID HAVING COUNT(*) >= 5
     );

-- Monthly summary: 1 row per month (không tách TxType → dashboard chart đúng)
CREATE OR REPLACE VIEW vw_monthly_tx_summary AS
SELECT
  DATE_FORMAT(CreatedAt,'%Y-%m') AS Month,
  COUNT(*)                       AS TxCount,
  COALESCE(SUM(Amount), 0)       AS TotalAmount
FROM Transactions
GROUP BY Month
ORDER BY Month ASC;

SELECT '01_v6_fixes.sql applied successfully.' AS status;
