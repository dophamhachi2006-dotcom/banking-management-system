-- Auto-generated: chạy theo đúng thứ tự, không bị lỗi FK

-- =========================================================
-- Banking Management System - Schema
-- MySQL 8.0+
-- =========================================================
CREATE DATABASE IF NOT EXISTS banking CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE banking;
-- ---------- Branches ----------
CREATE TABLE Branches (
  BranchID      INT AUTO_INCREMENT PRIMARY KEY,
  BranchName    VARCHAR(100) NOT NULL,
  Address       VARCHAR(255),
  City          VARCHAR(80),
  Phone         VARCHAR(20),
  ManagerID     INT NULL,
  CreatedAt     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_branch_city (City)
);

-- ---------- Employees ----------
CREATE TABLE Employees (
  EmployeeID    INT AUTO_INCREMENT PRIMARY KEY,
  FullName      VARCHAR(120) NOT NULL,
  Email         VARCHAR(120) UNIQUE NOT NULL,
  Phone         VARCHAR(20),
  Position      VARCHAR(60),
  BranchID      INT,
  Salary        DECIMAL(12,2) DEFAULT 0,
  HiredAt       DATE,
  Status        ENUM('active','inactive','terminated') DEFAULT 'active',
  CreatedAt     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (BranchID) REFERENCES Branches(BranchID) ON DELETE SET NULL,
  INDEX idx_emp_branch (BranchID),
  INDEX idx_emp_status (Status)
);

ALTER TABLE Branches
  ADD CONSTRAINT fk_branch_manager
  FOREIGN KEY (ManagerID) REFERENCES Employees(EmployeeID) ON DELETE SET NULL;

-- ---------- Users (Auth) ----------
CREATE TABLE Users (
  UserID        INT AUTO_INCREMENT PRIMARY KEY,
  Username      VARCHAR(60) UNIQUE NOT NULL,
  PasswordHash  VARCHAR(255) NOT NULL,
  Role          ENUM('manager','teller','auditor') NOT NULL,
  EmployeeID    INT NULL,
  IsActive      BOOLEAN DEFAULT TRUE,
  LastLoginAt   TIMESTAMP NULL,
  CreatedAt     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID) ON DELETE SET NULL,
  INDEX idx_user_role (Role)
);

-- ---------- Customers ----------
CREATE TABLE Customers (
  CustomerID    INT AUTO_INCREMENT PRIMARY KEY,
  FullName      VARCHAR(120) NOT NULL,
  Email         VARCHAR(120) UNIQUE,
  Phone         VARCHAR(20),
  DateOfBirth   DATE,
  Address       VARCHAR(255),
  City          VARCHAR(80),
  IDNumber      VARCHAR(30) UNIQUE,
  CreatedAt     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CreatedBy     INT NULL,
  INDEX idx_cust_name (FullName),
  INDEX idx_cust_city (City),
  FOREIGN KEY (CreatedBy) REFERENCES Users(UserID) ON DELETE SET NULL
);

-- ---------- Accounts ----------
CREATE TABLE Accounts (
  AccountID     INT AUTO_INCREMENT PRIMARY KEY,
  AccountNumber VARCHAR(20) UNIQUE NOT NULL,
  CustomerID    INT NOT NULL,
  BranchID      INT NOT NULL,
  AccountType   ENUM('savings','checking','fixed') DEFAULT 'savings',
  Balance       DECIMAL(15,2) DEFAULT 0,
  Currency      CHAR(3) DEFAULT 'USD',
  Status        ENUM('active','frozen','closed') DEFAULT 'active',
  OpenedAt      DATE,
  CreatedAt     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID) ON DELETE CASCADE,
  FOREIGN KEY (BranchID)   REFERENCES Branches(BranchID),
  INDEX idx_acc_customer (CustomerID),
  INDEX idx_acc_branch (BranchID),
  INDEX idx_acc_status (Status)
);

-- ---------- Transactions ----------
CREATE TABLE Transactions (
  TransactionID  BIGINT AUTO_INCREMENT PRIMARY KEY,
  AccountID      INT NOT NULL,
  RelatedAccount INT NULL,                      -- for transfers
  TxType         ENUM('deposit','withdrawal','transfer','fee','interest') NOT NULL,
  Amount         DECIMAL(15,2) NOT NULL,
  BalanceAfter   DECIMAL(15,2),
  Description    VARCHAR(255),
  PerformedBy    INT NULL,
  Status         ENUM('pending','completed','failed','reversed') DEFAULT 'completed',
  CreatedAt      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (AccountID)      REFERENCES Accounts(AccountID) ON DELETE CASCADE,
  FOREIGN KEY (RelatedAccount) REFERENCES Accounts(AccountID) ON DELETE SET NULL,
  FOREIGN KEY (PerformedBy)    REFERENCES Users(UserID) ON DELETE SET NULL,
  INDEX idx_tx_account (AccountID),
  INDEX idx_tx_date (CreatedAt),
  INDEX idx_tx_type (TxType)
);

-- ---------- Loans ----------
CREATE TABLE Loans (
  LoanID         INT AUTO_INCREMENT PRIMARY KEY,
  CustomerID     INT NOT NULL,
  Principal      DECIMAL(15,2) NOT NULL,
  InterestRate   DECIMAL(5,2)  NOT NULL,        -- annual %
  TermMonths     INT NOT NULL,
  MonthlyPayment DECIMAL(15,2),
  OutstandingBal DECIMAL(15,2),
  Status         ENUM('pending','active','closed','defaulted') DEFAULT 'pending',
  StartDate      DATE,
  EndDate        DATE,
  CreatedAt      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID) ON DELETE CASCADE,
  INDEX idx_loan_customer (CustomerID),
  INDEX idx_loan_status (Status)
);

-- ---------- Credit Cards ----------
CREATE TABLE CreditCards (
  CardID            INT AUTO_INCREMENT PRIMARY KEY,
  CardNumber        VARCHAR(20) UNIQUE NOT NULL,
  CustomerID        INT NOT NULL,
  CreditLimit       DECIMAL(15,2) NOT NULL,
  OutstandingBal    DECIMAL(15,2) DEFAULT 0,
  ExpiryDate        DATE,
  Status            ENUM('active','blocked','expired') DEFAULT 'active',
  CreatedAt         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID) ON DELETE CASCADE,
  INDEX idx_card_customer (CustomerID)
);

-- =========================================================
-- Audit Log
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

-- Customer audit
DELIMITER $$
CREATE TRIGGER trg_customers_after_update
AFTER UPDATE ON Customers FOR EACH ROW
BEGIN
  INSERT INTO AuditLog(TableName, RecordID, Action, OldData, NewData)
  VALUES('Customers', OLD.CustomerID, 'UPDATE',
    JSON_OBJECT('FullName', OLD.FullName, 'Email', OLD.Email, 'Phone', OLD.Phone),
    JSON_OBJECT('FullName', NEW.FullName, 'Email', NEW.Email, 'Phone', NEW.Phone));
END$$

CREATE TRIGGER trg_customers_after_delete
AFTER DELETE ON Customers FOR EACH ROW
BEGIN
  INSERT INTO AuditLog(TableName, RecordID, Action, OldData)
  VALUES('Customers', OLD.CustomerID, 'DELETE',
    JSON_OBJECT('FullName', OLD.FullName, 'Email', OLD.Email));
END$$

CREATE TRIGGER trg_accounts_after_update
AFTER UPDATE ON Accounts FOR EACH ROW
BEGIN
  IF OLD.Balance <> NEW.Balance OR OLD.Status <> NEW.Status THEN
    INSERT INTO AuditLog(TableName, RecordID, Action, OldData, NewData)
    VALUES('Accounts', OLD.AccountID, 'UPDATE',
      JSON_OBJECT('Balance', OLD.Balance, 'Status', OLD.Status),
      JSON_OBJECT('Balance', NEW.Balance, 'Status', NEW.Status));
  END IF;
END$$
DELIMITER ;

-- Functions
USE banking;
DELIMITER $$

DROP FUNCTION IF EXISTS fn_customer_total_balance$$
CREATE FUNCTION fn_customer_total_balance(p_customer_id INT)
RETURNS DECIMAL(15,2)
READS SQL DATA
BEGIN
  DECLARE v_total DECIMAL(15,2);
  SELECT COALESCE(SUM(Balance),0) INTO v_total
  FROM Accounts WHERE CustomerID=p_customer_id AND Status='active';
  RETURN v_total;
END$$

DROP FUNCTION IF EXISTS fn_account_age_days$$
CREATE FUNCTION fn_account_age_days(p_account_id INT)
RETURNS INT
READS SQL DATA
BEGIN
  DECLARE v_age INT;
  SELECT DATEDIFF(CURDATE(), OpenedAt) INTO v_age FROM Accounts WHERE AccountID=p_account_id;
  RETURN v_age;
END$$

DELIMITER ;

-- =========================================================
-- Stored Procedures
-- =========================================================
USE banking;
DELIMITER $$

-- Deposit
DROP PROCEDURE IF EXISTS sp_deposit$$
CREATE PROCEDURE sp_deposit(
  IN p_account_id INT,
  IN p_amount DECIMAL(15,2),
  IN p_user_id INT,
  IN p_desc VARCHAR(255)
)
BEGIN
  DECLARE v_balance DECIMAL(15,2);
  START TRANSACTION;
    SELECT Balance INTO v_balance FROM Accounts WHERE AccountID=p_account_id FOR UPDATE;
    UPDATE Accounts SET Balance = Balance + p_amount WHERE AccountID=p_account_id;
    INSERT INTO Transactions(AccountID, TxType, Amount, BalanceAfter, Description, PerformedBy)
    VALUES (p_account_id,'deposit',p_amount, v_balance + p_amount, p_desc, p_user_id);
  COMMIT;
END$$

-- Withdraw
DROP PROCEDURE IF EXISTS sp_withdraw$$
CREATE PROCEDURE sp_withdraw(
  IN p_account_id INT, IN p_amount DECIMAL(15,2),
  IN p_user_id INT, IN p_desc VARCHAR(255)
)
BEGIN
  DECLARE v_balance DECIMAL(15,2);
  START TRANSACTION;
    SELECT Balance INTO v_balance FROM Accounts WHERE AccountID=p_account_id FOR UPDATE;
    IF v_balance < p_amount THEN
      ROLLBACK;
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Insufficient funds';
    ELSE
      UPDATE Accounts SET Balance = Balance - p_amount WHERE AccountID=p_account_id;
      INSERT INTO Transactions(AccountID, TxType, Amount, BalanceAfter, Description, PerformedBy)
      VALUES (p_account_id,'withdrawal',p_amount, v_balance - p_amount, p_desc, p_user_id);
      COMMIT;
    END IF;
END$$

-- Transfer
DROP PROCEDURE IF EXISTS sp_transfer$$
CREATE PROCEDURE sp_transfer(
  IN p_from INT, IN p_to INT, IN p_amount DECIMAL(15,2),
  IN p_user_id INT, IN p_desc VARCHAR(255)
)
BEGIN
  DECLARE v_from_bal DECIMAL(15,2);
  DECLARE v_to_bal   DECIMAL(15,2);
  START TRANSACTION;
    SELECT Balance INTO v_from_bal FROM Accounts WHERE AccountID=p_from FOR UPDATE;
    SELECT Balance INTO v_to_bal   FROM Accounts WHERE AccountID=p_to   FOR UPDATE;
    IF v_from_bal < p_amount THEN
      ROLLBACK;
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Insufficient funds';
    ELSE
      UPDATE Accounts SET Balance = Balance - p_amount WHERE AccountID=p_from;
      UPDATE Accounts SET Balance = Balance + p_amount WHERE AccountID=p_to;
      INSERT INTO Transactions(AccountID, RelatedAccount, TxType, Amount, BalanceAfter, Description, PerformedBy)
      VALUES (p_from, p_to, 'transfer', p_amount, v_from_bal - p_amount, p_desc, p_user_id);
      INSERT INTO Transactions(AccountID, RelatedAccount, TxType, Amount, BalanceAfter, Description, PerformedBy)
      VALUES (p_to, p_from, 'transfer', p_amount, v_to_bal + p_amount, p_desc, p_user_id);
      COMMIT;
    END IF;
END$$

-- Calculate loan EMI
DROP FUNCTION IF EXISTS fn_calculate_emi$$
CREATE FUNCTION fn_calculate_emi(
  p_principal DECIMAL(15,2),
  p_annual_rate DECIMAL(5,2),
  p_months INT
) RETURNS DECIMAL(15,2)
DETERMINISTIC
BEGIN
  DECLARE r DECIMAL(15,8);
  SET r = p_annual_rate / 100 / 12;
  IF r = 0 THEN
    RETURN p_principal / p_months;
  END IF;
  RETURN p_principal * r * POW(1+r, p_months) / (POW(1+r, p_months) - 1);
END$$

DELIMITER ;

-- =========================================================
-- Triggers (business rules)
-- =========================================================
USE banking;
DELIMITER $$

-- Prevent negative balance on direct UPDATE
CREATE TRIGGER trg_accounts_before_update
BEFORE UPDATE ON Accounts FOR EACH ROW
BEGIN
  IF NEW.Balance < 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Balance cannot be negative';
  END IF;
END$$

-- Auto-generate account number if missing
CREATE TRIGGER trg_accounts_before_insert
BEFORE INSERT ON Accounts FOR EACH ROW
BEGIN
  IF NEW.AccountNumber IS NULL OR NEW.AccountNumber = '' THEN
    SET NEW.AccountNumber = CONCAT('ACC', LPAD(FLOOR(RAND()*99999999),8,'0'));
  END IF;
  IF NEW.OpenedAt IS NULL THEN SET NEW.OpenedAt = CURDATE(); END IF;
END$$

-- Compute loan EMI on insert
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

DELIMITER ;

USE banking;
-- Composite/extra indexes for performance
CREATE INDEX idx_tx_account_date ON Transactions(AccountID, CreatedAt DESC);
CREATE INDEX idx_acc_cust_status ON Accounts(CustomerID, Status);
CREATE INDEX idx_loan_status_cust ON Loans(Status, CustomerID);

-- Roles & permissions (DB-level — separate from app-level auth)
USE banking;

-- Read-only for auditor
CREATE USER IF NOT EXISTS 'auditor_db'@'%' IDENTIFIED BY 'auditor_db_pass';
GRANT SELECT ON banking.* TO 'auditor_db'@'%';

-- Teller: read all + insert/update transactions, customers, accounts
CREATE USER IF NOT EXISTS 'teller_db'@'%' IDENTIFIED BY 'teller_db_pass';
GRANT SELECT ON banking.* TO 'teller_db'@'%';
GRANT INSERT, UPDATE ON banking.Customers   TO 'teller_db'@'%';
GRANT INSERT, UPDATE ON banking.Accounts    TO 'teller_db'@'%';
GRANT INSERT         ON banking.Transactions TO 'teller_db'@'%';
GRANT EXECUTE        ON banking.*           TO 'teller_db'@'%';

-- Manager: full
CREATE USER IF NOT EXISTS 'manager_db'@'%' IDENTIFIED BY 'manager_db_pass';
GRANT ALL PRIVILEGES ON banking.* TO 'manager_db'@'%';
FLUSH PRIVILEGES;

-- =========================================================
-- Views
-- =========================================================
USE banking;

-- Customer summary (account count + total balance)
CREATE OR REPLACE VIEW vw_customer_summary AS
SELECT
  c.CustomerID,
  c.FullName,
  c.Email,
  c.Phone,
  c.City,
  COUNT(a.AccountID) AS AccountCount,
  COALESCE(SUM(a.Balance),0) AS TotalBalance,
  c.CreatedAt
FROM Customers c
LEFT JOIN Accounts a ON a.CustomerID = c.CustomerID AND a.Status = 'active'
GROUP BY c.CustomerID;

-- Account details with customer + branch
CREATE OR REPLACE VIEW vw_account_details AS
SELECT
  a.AccountID, a.AccountNumber, a.AccountType, a.Balance, a.Currency, a.Status,
  c.CustomerID, c.FullName AS CustomerName, c.Email AS CustomerEmail,
  b.BranchID, b.BranchName, b.City AS BranchCity,
  a.OpenedAt
FROM Accounts a
JOIN Customers c ON c.CustomerID = a.CustomerID
JOIN Branches  b ON b.BranchID   = a.BranchID;

-- Branch performance
CREATE OR REPLACE VIEW vw_branch_performance AS
SELECT
  b.BranchID, b.BranchName, b.City,
  COUNT(DISTINCT a.AccountID) AS TotalAccounts,
  COUNT(DISTINCT a.CustomerID) AS TotalCustomers,
  COALESCE(SUM(a.Balance),0)  AS TotalDeposits,
  COUNT(t.TransactionID)      AS TotalTransactions
FROM Branches b
LEFT JOIN Accounts a ON a.BranchID = b.BranchID AND a.Status='active'
LEFT JOIN Transactions t ON t.AccountID = a.AccountID
  AND t.CreatedAt >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY b.BranchID;

-- Top customers by balance
CREATE OR REPLACE VIEW vw_top_customers AS
SELECT
  c.CustomerID, c.FullName, c.Email,
  COALESCE(SUM(a.Balance),0) AS TotalBalance,
  COUNT(a.AccountID) AS Accounts
FROM Customers c
LEFT JOIN Accounts a ON a.CustomerID=c.CustomerID AND a.Status='active'
GROUP BY c.CustomerID
ORDER BY TotalBalance DESC;

-- Suspicious transactions: > threshold or rapid bursts
CREATE OR REPLACE VIEW vw_suspicious_transactions AS
SELECT t.*, a.AccountNumber, c.FullName AS CustomerName
FROM Transactions t
JOIN Accounts a   ON a.AccountID  = t.AccountID
JOIN Customers c  ON c.CustomerID = a.CustomerID
WHERE t.Amount >= 50000
   OR t.AccountID IN (
       SELECT AccountID FROM Transactions
       WHERE CreatedAt >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
       GROUP BY AccountID HAVING COUNT(*) >= 5
     );

-- Monthly transaction summary
CREATE OR REPLACE VIEW vw_monthly_tx_summary AS
SELECT
  DATE_FORMAT(CreatedAt,'%Y-%m') AS Month,
  TxType,
  COUNT(*) AS Count,
  SUM(Amount) AS TotalAmount
FROM Transactions
GROUP BY Month, TxType
ORDER BY Month DESC;

-- Backup / recovery helpers (run from shell, not in MySQL)
-- mysqldump -u root -p banking > backup_$(date +%F).sql
-- mysql    -u root -p banking < backup_2025-05-03.sql
USE banking;

-- Logical "soft delete" support
-- (apps can mark Accounts.Status='closed' instead of physical DELETE)

-- Quick health-check view
CREATE OR REPLACE VIEW vw_db_health AS
SELECT
  (SELECT COUNT(*) FROM Customers)    AS customers,
  (SELECT COUNT(*) FROM Accounts)     AS accounts,
  (SELECT COUNT(*) FROM Transactions) AS transactions,
  (SELECT COUNT(*) FROM Branches)     AS branches,
  (SELECT COUNT(*) FROM Employees)    AS employees,
  NOW() AS checked_at;

-- =========================================================
-- Seed data (FK checks tắt tạm để tránh lỗi thứ tự insert)
-- =========================================================
SET FOREIGN_KEY_CHECKS = 0;
-- =========================================================
-- Seed data (small ~25 rows/table for quick testing)
-- Default users:
--   admin / admin123  (manager)
--   teller1 / teller123
--   audit1  / audit123
-- Hashes generated with werkzeug.security.generate_password_hash
-- =========================================================
USE banking;

-- ---------- Branches ----------
INSERT INTO Branches (BranchName, Address, City, Phone) VALUES
('Downtown HQ',    '1 Central Ave',   'Hanoi',     '024-1111111'),
('Saigon Central', '99 Le Loi',       'Ho Chi Minh','028-2222222'),
('Da Nang Branch', '45 Bach Dang',    'Da Nang',   '0236-333333'),
('Hue Branch',     '12 Hung Vuong',   'Hue',       '0234-444444'),
('Can Tho Branch', '88 Tran Phu',     'Can Tho',   '0292-555555');

-- ---------- Employees ----------
INSERT INTO Employees (FullName, Email, Phone, Position, BranchID, Salary, HiredAt) VALUES
('Nguyen Van An',     'an.nv@bank.local',     '0901111111','Manager',   1, 3500, '2020-01-15'),
('Tran Thi Binh',     'binh.tt@bank.local',   '0901111112','Teller',    1, 1200, '2021-03-10'),
('Le Hoang Cuong',    'cuong.lh@bank.local',  '0901111113','Teller',    2, 1300, '2021-05-20'),
('Pham Thi Dung',     'dung.pt@bank.local',   '0901111114','Auditor',   1, 1800, '2019-09-01'),
('Vo Minh En',        'en.vm@bank.local',     '0901111115','Manager',   2, 3600, '2018-11-11'),
('Hoang Thi Phuong',  'phuong.ht@bank.local', '0901111116','Teller',    3, 1100, '2022-02-14'),
('Bui Van Giang',     'giang.bv@bank.local',  '0901111117','Teller',    4, 1100, '2022-06-01'),
('Do Thi Hoa',        'hoa.dt@bank.local',    '0901111118','Manager',   3, 3400, '2017-08-20'),
('Ngo Van Hung',      'hung.nv@bank.local',   '0901111119','Teller',    5, 1100, '2023-01-09'),
('Dang Thi Lan',      'lan.dt@bank.local',    '0901111120','Auditor',   2, 1900, '2020-04-22');

UPDATE Branches SET ManagerID=1 WHERE BranchID=1;
UPDATE Branches SET ManagerID=5 WHERE BranchID=2;
UPDATE Branches SET ManagerID=8 WHERE BranchID=3;

-- ---------- Users (passwords below are pbkdf2:sha256 of admin123/teller123/audit123) ----------
INSERT INTO Users (Username, PasswordHash, Role, EmployeeID) VALUES
('admin',  'pbkdf2:sha256:600000$seedSalt1$d6f9a5d6c1f6d0a13a3b6f1e9d8b7c5a4e3f2d1c0b9a8f7e6d5c4b3a2918070', 'manager', 1),
('teller1','pbkdf2:sha256:600000$seedSalt2$0e1d2c3b4a5968778695a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3', 'teller',  2),
('audit1', 'pbkdf2:sha256:600000$seedSalt3$9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b', 'auditor', 4);
-- NOTE: hashes above are placeholders. Run `python backend/seed_users.py` after DB init
-- to overwrite them with real werkzeug hashes.

-- ---------- Customers ----------
INSERT INTO Customers (FullName, Email, Phone, DateOfBirth, Address, City, IDNumber) VALUES
('Customer 01', 'cust01@mail.com', '0911000001', '1990-01-01', 'Addr 1', 'Hanoi', 'ID00000001'),
('Customer 02', 'cust02@mail.com', '0911000002', '1985-05-12', 'Addr 2', 'Hanoi', 'ID00000002'),
('Customer 03', 'cust03@mail.com', '0911000003', '1992-07-08', 'Addr 3', 'Ho Chi Minh', 'ID00000003'),
('Customer 04', 'cust04@mail.com', '0911000004', '1978-11-23', 'Addr 4', 'Ho Chi Minh', 'ID00000004'),
('Customer 05', 'cust05@mail.com', '0911000005', '1995-03-14', 'Addr 5', 'Da Nang', 'ID00000005'),
('Customer 06', 'cust06@mail.com', '0911000006', '1988-09-30', 'Addr 6', 'Da Nang', 'ID00000006'),
('Customer 07', 'cust07@mail.com', '0911000007', '1991-12-19', 'Addr 7', 'Hue', 'ID00000007'),
('Customer 08', 'cust08@mail.com', '0911000008', '1983-04-02', 'Addr 8', 'Hue', 'ID00000008'),
('Customer 09', 'cust09@mail.com', '0911000009', '1996-06-17', 'Addr 9', 'Can Tho', 'ID00000009'),
('Customer 10', 'cust10@mail.com', '0911000010', '1994-08-25', 'Addr 10','Can Tho', 'ID00000010'),
('Customer 11', 'cust11@mail.com', '0911000011', '1987-02-11', 'Addr 11','Hanoi', 'ID00000011'),
('Customer 12', 'cust12@mail.com', '0911000012', '1993-10-05', 'Addr 12','Hanoi', 'ID00000012'),
('Customer 13', 'cust13@mail.com', '0911000013', '1981-07-21', 'Addr 13','Ho Chi Minh', 'ID00000013'),
('Customer 14', 'cust14@mail.com', '0911000014', '1989-01-30', 'Addr 14','Ho Chi Minh', 'ID00000014'),
('Customer 15', 'cust15@mail.com', '0911000015', '1997-05-16', 'Addr 15','Da Nang', 'ID00000015'),
('Customer 16', 'cust16@mail.com', '0911000016', '1990-11-04', 'Addr 16','Hue', 'ID00000016'),
('Customer 17', 'cust17@mail.com', '0911000017', '1986-03-22', 'Addr 17','Can Tho', 'ID00000017'),
('Customer 18', 'cust18@mail.com', '0911000018', '1992-08-08', 'Addr 18','Hanoi', 'ID00000018'),
('Customer 19', 'cust19@mail.com', '0911000019', '1984-12-12', 'Addr 19','Ho Chi Minh', 'ID00000019'),
('Customer 20', 'cust20@mail.com', '0911000020', '1998-02-28', 'Addr 20','Da Nang', 'ID00000020');

-- ---------- Accounts ----------
INSERT INTO Accounts (AccountNumber, CustomerID, BranchID, AccountType, Balance, OpenedAt) VALUES
('ACC10000001', 1, 1,'savings',  15000.00,'2022-01-10'),
('ACC10000002', 2, 1,'checking',  3200.50,'2022-02-15'),
('ACC10000003', 3, 2,'savings',  85000.00,'2021-06-01'),
('ACC10000004', 4, 2,'fixed',   120000.00,'2020-09-12'),
('ACC10000005', 5, 3,'savings',   2500.00,'2023-04-19'),
('ACC10000006', 6, 3,'checking',  7800.00,'2022-08-22'),
('ACC10000007', 7, 4,'savings',  43000.00,'2021-11-03'),
('ACC10000008', 8, 4,'savings',   9100.00,'2022-12-25'),
('ACC10000009', 9, 5,'checking',  1800.75,'2023-01-30'),
('ACC10000010',10, 5,'savings',  61000.00,'2021-03-14'),
('ACC10000011',11, 1,'savings',  22000.00,'2022-05-05'),
('ACC10000012',12, 1,'checking',  4500.00,'2023-02-12'),
('ACC10000013',13, 2,'fixed',    98000.00,'2020-12-18'),
('ACC10000014',14, 2,'savings',  17000.00,'2022-07-07'),
('ACC10000015',15, 3,'savings',   5300.00,'2023-06-21'),
('ACC10000016',16, 4,'checking',  3400.00,'2022-10-10'),
('ACC10000017',17, 5,'savings',  29000.00,'2021-09-09'),
('ACC10000018',18, 1,'fixed',    75000.00,'2020-04-04'),
('ACC10000019',19, 2,'checking',  6700.00,'2022-11-11'),
('ACC10000020',20, 3,'savings',  12500.00,'2023-03-03');

-- ---------- Transactions (sample) ----------
INSERT INTO Transactions (AccountID, TxType, Amount, BalanceAfter, Description, PerformedBy, CreatedAt) VALUES
(1,'deposit',     500.00, 15500.00,'Initial deposit',       2, NOW() - INTERVAL 10 DAY),
(1,'withdrawal',  200.00, 15300.00,'ATM',                    2, NOW() - INTERVAL  9 DAY),
(2,'deposit',    1000.00,  4200.50,'Salary',                 2, NOW() - INTERVAL  8 DAY),
(3,'deposit',    5000.00, 90000.00,'Cash deposit',           3, NOW() - INTERVAL  7 DAY),
(4,'interest',    600.00,120600.00,'Quarterly interest',     1, NOW() - INTERVAL  6 DAY),
(5,'withdrawal',  100.00,  2400.00,'POS payment',            6, NOW() - INTERVAL  5 DAY),
(7,'deposit',    2000.00, 45000.00,'Cash',                   7, NOW() - INTERVAL  4 DAY),
(10,'deposit',  60000.00,121000.00,'Wire transfer in',       9, NOW() - INTERVAL  3 DAY),
(13,'deposit',  30000.00,128000.00,'Term renewal',           3, NOW() - INTERVAL  2 DAY),
(18,'withdrawal',5000.00, 70000.00,'Cash',                   2, NOW() - INTERVAL  1 DAY);

-- ---------- Loans ----------
INSERT INTO Loans (CustomerID, Principal, InterestRate, TermMonths, Status, StartDate, EndDate) VALUES
(1, 20000, 8.5, 24,'active','2024-01-01','2026-01-01'),
(3, 50000, 7.0, 36,'active','2023-06-01','2026-06-01'),
(7,100000, 6.5, 60,'active','2022-09-01','2027-09-01');

-- ---------- Credit Cards ----------
INSERT INTO CreditCards (CardNumber, CustomerID, CreditLimit, OutstandingBal, ExpiryDate) VALUES
('4000-1111-2222-3333', 1,  5000,  1200.00,'2027-12-31'),
('4000-1111-2222-3334', 4, 20000,  8400.00,'2026-08-31'),
('4000-1111-2222-3335',10, 10000,     0.00,'2028-03-31');

SET FOREIGN_KEY_CHECKS = 1;
-- Re-grant app user privileges after DB recreation
GRANT ALL PRIVILEGES ON banking.* TO 'bank'@'%';
FLUSH PRIVILEGES;
