-- =========================================================
-- Triggers (business rules)  —  v6
-- =========================================================
USE banking;
DELIMITER $$

-- Drop all triggers before recreating (safe re-run)
DROP TRIGGER IF EXISTS trg_accounts_before_update$$
DROP TRIGGER IF EXISTS trg_accounts_before_insert$$
DROP TRIGGER IF EXISTS trg_loans_before_insert$$
DROP TRIGGER IF EXISTS trg_tx_after_insert$$
DROP TRIGGER IF EXISTS trg_tx_suspicious_after_insert$$

-- 1. Prevent negative balance on direct UPDATE
CREATE TRIGGER trg_accounts_before_update
BEFORE UPDATE ON Accounts FOR EACH ROW
BEGIN
  IF NEW.Balance < 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Balance cannot be negative';
  END IF;
END$$

-- 2. Auto-generate account number and default OpenedAt on INSERT
CREATE TRIGGER trg_accounts_before_insert
BEFORE INSERT ON Accounts FOR EACH ROW
BEGIN
  IF NEW.AccountNumber IS NULL OR NEW.AccountNumber = '' THEN
    SET NEW.AccountNumber = CONCAT('ACC', LPAD(FLOOR(RAND()*99999999), 8, '0'));
  END IF;
  IF NEW.OpenedAt IS NULL THEN
    SET NEW.OpenedAt = CURDATE();
  END IF;
END$$

-- 3. Auto-compute loan EMI (MonthlyPayment) and OutstandingBal on INSERT
CREATE TRIGGER trg_loans_before_insert
BEFORE INSERT ON Loans FOR EACH ROW
BEGIN
  IF NEW.MonthlyPayment IS NULL THEN
    SET NEW.MonthlyPayment = fn_calculate_emi(NEW.Principal, NEW.InterestRate, NEW.TermMonths);
  END IF;
  IF NEW.OutstandingBal IS NULL THEN
    SET NEW.OutstandingBal = NEW.Principal;
  END IF;
END$$

-- 4. Auto-log every new Transaction into AuditLog at DB level
--    This fires even when the Python layer is bypassed (direct SQL, scripts, etc.)
CREATE TRIGGER trg_tx_after_insert
AFTER INSERT ON Transactions FOR EACH ROW
BEGIN
  INSERT INTO AuditLog(TableName, RecordID, Action, NewData, PerformedBy)
  VALUES (
    'Transactions',
    NEW.TransactionID,
    'INSERT',
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

-- 5. Flag suspicious transactions automatically
--    Criteria: single amount >= 50 000  OR  5+ transactions for same account in 1 hour.
--    Suspicious rows are written into AuditLog with TableName='SuspiciousActivity'.
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
      'SuspiciousActivity',
      NEW.TransactionID,
      'INSERT',
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
