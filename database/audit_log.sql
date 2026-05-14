-- =========================================================
-- Audit Log (FIXED v3) — full coverage + PerformedBy via @app_user_id
-- =========================================================
USE banking;

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
  INDEX idx_audit_date (CreatedAt),
  INDEX idx_audit_user (PerformedBy)
);

-- CardTransactions (was missing from schema). Used by Cards History.
CREATE TABLE IF NOT EXISTS CardTransactions (
  TransactionID BIGINT AUTO_INCREMENT PRIMARY KEY,
  CardID        INT NOT NULL,
  Merchant      VARCHAR(120),
  Amount        DECIMAL(15,2) NOT NULL,
  Status        ENUM('pending','completed','failed') DEFAULT 'completed',
  CreatedAt     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (CardID) REFERENCES CreditCards(CardID) ON DELETE CASCADE,
  INDEX idx_ctx_card (CardID),
  INDEX idx_ctx_date (CreatedAt)
);

-- Drop old triggers (in case re-run)
DROP TRIGGER IF EXISTS trg_customers_after_insert;
DROP TRIGGER IF EXISTS trg_customers_after_update;
DROP TRIGGER IF EXISTS trg_customers_after_delete;
DROP TRIGGER IF EXISTS trg_accounts_after_insert;
DROP TRIGGER IF EXISTS trg_accounts_after_update;
DROP TRIGGER IF EXISTS trg_accounts_after_delete;
DROP TRIGGER IF EXISTS trg_tx_after_insert;
DROP TRIGGER IF EXISTS trg_loans_after_insert;
DROP TRIGGER IF EXISTS trg_loans_after_update;
DROP TRIGGER IF EXISTS trg_loans_after_delete;
DROP TRIGGER IF EXISTS trg_cards_after_insert;
DROP TRIGGER IF EXISTS trg_cards_after_update;
DROP TRIGGER IF EXISTS trg_cards_after_delete;
DROP TRIGGER IF EXISTS trg_branches_after_insert;
DROP TRIGGER IF EXISTS trg_branches_after_update;
DROP TRIGGER IF EXISTS trg_branches_after_delete;
DROP TRIGGER IF EXISTS trg_employees_after_insert;
DROP TRIGGER IF EXISTS trg_employees_after_update;
DROP TRIGGER IF EXISTS trg_employees_after_delete;

DELIMITER $$

-- ---------- Customers ----------
CREATE TRIGGER trg_customers_after_insert AFTER INSERT ON Customers FOR EACH ROW
BEGIN
  INSERT INTO AuditLog(TableName,RecordID,Action,NewData,PerformedBy)
  VALUES('Customers', NEW.CustomerID, 'INSERT',
    JSON_OBJECT('FullName', NEW.FullName, 'Email', NEW.Email, 'Phone', NEW.Phone),
    @app_user_id);
END$$

CREATE TRIGGER trg_customers_after_update AFTER UPDATE ON Customers FOR EACH ROW
BEGIN
  INSERT INTO AuditLog(TableName,RecordID,Action,OldData,NewData,PerformedBy)
  VALUES('Customers', OLD.CustomerID, 'UPDATE',
    JSON_OBJECT('FullName', OLD.FullName, 'Email', OLD.Email, 'Phone', OLD.Phone),
    JSON_OBJECT('FullName', NEW.FullName, 'Email', NEW.Email, 'Phone', NEW.Phone),
    @app_user_id);
END$$

CREATE TRIGGER trg_customers_after_delete AFTER DELETE ON Customers FOR EACH ROW
BEGIN
  INSERT INTO AuditLog(TableName,RecordID,Action,OldData,PerformedBy)
  VALUES('Customers', OLD.CustomerID, 'DELETE',
    JSON_OBJECT('FullName', OLD.FullName, 'Email', OLD.Email),
    @app_user_id);
END$$

-- ---------- Accounts ----------
CREATE TRIGGER trg_accounts_after_insert AFTER INSERT ON Accounts FOR EACH ROW
BEGIN
  INSERT INTO AuditLog(TableName,RecordID,Action,NewData,PerformedBy)
  VALUES('Accounts', NEW.AccountID, 'INSERT',
    JSON_OBJECT('AccountNumber', NEW.AccountNumber, 'CustomerID', NEW.CustomerID,
                'BranchID', NEW.BranchID, 'Balance', NEW.Balance),
    @app_user_id);
END$$

CREATE TRIGGER trg_accounts_after_update AFTER UPDATE ON Accounts FOR EACH ROW
BEGIN
  IF OLD.Balance <> NEW.Balance OR OLD.Status <> NEW.Status THEN
    INSERT INTO AuditLog(TableName,RecordID,Action,OldData,NewData,PerformedBy)
    VALUES('Accounts', OLD.AccountID, 'UPDATE',
      JSON_OBJECT('Balance', OLD.Balance, 'Status', OLD.Status),
      JSON_OBJECT('Balance', NEW.Balance, 'Status', NEW.Status),
      @app_user_id);
  END IF;
END$$

CREATE TRIGGER trg_accounts_after_delete AFTER DELETE ON Accounts FOR EACH ROW
BEGIN
  INSERT INTO AuditLog(TableName,RecordID,Action,OldData,PerformedBy)
  VALUES('Accounts', OLD.AccountID, 'DELETE',
    JSON_OBJECT('AccountNumber', OLD.AccountNumber, 'Balance', OLD.Balance),
    @app_user_id);
END$$

-- ---------- Transactions ----------
CREATE TRIGGER trg_tx_after_insert AFTER INSERT ON Transactions FOR EACH ROW
BEGIN
  INSERT INTO AuditLog(TableName,RecordID,Action,NewData,PerformedBy)
  VALUES('Transactions', NEW.TransactionID, 'INSERT',
    JSON_OBJECT('AccountID', NEW.AccountID, 'TxType', NEW.TxType,
                'Amount', NEW.Amount, 'Status', NEW.Status),
    @app_user_id);
END$$

-- ---------- Loans ----------
CREATE TRIGGER trg_loans_after_insert AFTER INSERT ON Loans FOR EACH ROW
BEGIN
  INSERT INTO AuditLog(TableName,RecordID,Action,NewData,PerformedBy)
  VALUES('Loans', NEW.LoanID, 'INSERT',
    JSON_OBJECT('CustomerID', NEW.CustomerID, 'Principal', NEW.Principal,
                'Status', NEW.Status),
    @app_user_id);
END$$

CREATE TRIGGER trg_loans_after_update AFTER UPDATE ON Loans FOR EACH ROW
BEGIN
  INSERT INTO AuditLog(TableName,RecordID,Action,OldData,NewData,PerformedBy)
  VALUES('Loans', OLD.LoanID, 'UPDATE',
    JSON_OBJECT('Status', OLD.Status, 'OutstandingBal', OLD.OutstandingBal),
    JSON_OBJECT('Status', NEW.Status, 'OutstandingBal', NEW.OutstandingBal),
    @app_user_id);
END$$

CREATE TRIGGER trg_loans_after_delete AFTER DELETE ON Loans FOR EACH ROW
BEGIN
  INSERT INTO AuditLog(TableName,RecordID,Action,OldData,PerformedBy)
  VALUES('Loans', OLD.LoanID, 'DELETE',
    JSON_OBJECT('CustomerID', OLD.CustomerID, 'Principal', OLD.Principal),
    @app_user_id);
END$$

-- ---------- CreditCards ----------
CREATE TRIGGER trg_cards_after_insert AFTER INSERT ON CreditCards FOR EACH ROW
BEGIN
  INSERT INTO AuditLog(TableName,RecordID,Action,NewData,PerformedBy)
  VALUES('CreditCards', NEW.CardID, 'INSERT',
    JSON_OBJECT('CardNumber', NEW.CardNumber, 'CustomerID', NEW.CustomerID,
                'CreditLimit', NEW.CreditLimit, 'Status', NEW.Status),
    @app_user_id);
END$$

CREATE TRIGGER trg_cards_after_update AFTER UPDATE ON CreditCards FOR EACH ROW
BEGIN
  INSERT INTO AuditLog(TableName,RecordID,Action,OldData,NewData,PerformedBy)
  VALUES('CreditCards', OLD.CardID, 'UPDATE',
    JSON_OBJECT('Status', OLD.Status, 'OutstandingBal', OLD.OutstandingBal),
    JSON_OBJECT('Status', NEW.Status, 'OutstandingBal', NEW.OutstandingBal),
    @app_user_id);
END$$

CREATE TRIGGER trg_cards_after_delete AFTER DELETE ON CreditCards FOR EACH ROW
BEGIN
  INSERT INTO AuditLog(TableName,RecordID,Action,OldData,PerformedBy)
  VALUES('CreditCards', OLD.CardID, 'DELETE',
    JSON_OBJECT('CardNumber', OLD.CardNumber, 'CustomerID', OLD.CustomerID),
    @app_user_id);
END$$

-- ---------- Branches ----------
CREATE TRIGGER trg_branches_after_insert AFTER INSERT ON Branches FOR EACH ROW
BEGIN
  INSERT INTO AuditLog(TableName,RecordID,Action,NewData,PerformedBy)
  VALUES('Branches', NEW.BranchID, 'INSERT',
    JSON_OBJECT('BranchName', NEW.BranchName, 'City', NEW.City),
    @app_user_id);
END$$

CREATE TRIGGER trg_branches_after_update AFTER UPDATE ON Branches FOR EACH ROW
BEGIN
  INSERT INTO AuditLog(TableName,RecordID,Action,OldData,NewData,PerformedBy)
  VALUES('Branches', OLD.BranchID, 'UPDATE',
    JSON_OBJECT('BranchName', OLD.BranchName, 'City', OLD.City, 'ManagerID', OLD.ManagerID),
    JSON_OBJECT('BranchName', NEW.BranchName, 'City', NEW.City, 'ManagerID', NEW.ManagerID),
    @app_user_id);
END$$

CREATE TRIGGER trg_branches_after_delete AFTER DELETE ON Branches FOR EACH ROW
BEGIN
  INSERT INTO AuditLog(TableName,RecordID,Action,OldData,PerformedBy)
  VALUES('Branches', OLD.BranchID, 'DELETE',
    JSON_OBJECT('BranchName', OLD.BranchName, 'City', OLD.City),
    @app_user_id);
END$$

-- ---------- Employees ----------
CREATE TRIGGER trg_employees_after_insert AFTER INSERT ON Employees FOR EACH ROW
BEGIN
  INSERT INTO AuditLog(TableName,RecordID,Action,NewData,PerformedBy)
  VALUES('Employees', NEW.EmployeeID, 'INSERT',
    JSON_OBJECT('FullName', NEW.FullName, 'Email', NEW.Email, 'Position', NEW.Position),
    @app_user_id);
END$$

CREATE TRIGGER trg_employees_after_update AFTER UPDATE ON Employees FOR EACH ROW
BEGIN
  INSERT INTO AuditLog(TableName,RecordID,Action,OldData,NewData,PerformedBy)
  VALUES('Employees', OLD.EmployeeID, 'UPDATE',
    JSON_OBJECT('FullName', OLD.FullName, 'Position', OLD.Position, 'Status', OLD.Status, 'Salary', OLD.Salary),
    JSON_OBJECT('FullName', NEW.FullName, 'Position', NEW.Position, 'Status', NEW.Status, 'Salary', NEW.Salary),
    @app_user_id);
END$$

CREATE TRIGGER trg_employees_after_delete AFTER DELETE ON Employees FOR EACH ROW
BEGIN
  INSERT INTO AuditLog(TableName,RecordID,Action,OldData,PerformedBy)
  VALUES('Employees', OLD.EmployeeID, 'DELETE',
    JSON_OBJECT('FullName', OLD.FullName, 'Email', OLD.Email),
    @app_user_id);
END$$

DELIMITER ;
