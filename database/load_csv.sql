-- =========================================================
-- Bulk-load real CSV data into MySQL.
--
-- Run AFTER:
--   python data_generation/transform_kaggle_data.py
--   python data_generation/generate_card_transactions.py   (v6: tạo card_transactions.csv)
--
-- Then:
--   cd <project-root>
--   mysql --local-infile=1 -u root -p banking < database/load_csv.sql
--
-- Requires: server my.cnf -> local_infile=1 (or SET GLOBAL local_infile=1).
-- For Docker: use Python loader instead (backend/load_csv.py).
-- =========================================================
USE banking;
SET FOREIGN_KEY_CHECKS=0;
SET UNIQUE_CHECKS=0;
SET autocommit=0;

-- Wipe existing rows (keep schema + Users).
DELETE FROM CardTransactions;
DELETE FROM Transactions;
DELETE FROM CreditCards;
DELETE FROM Loans;
DELETE FROM Accounts;
DELETE FROM Customers;
DELETE FROM Employees;
UPDATE Branches SET ManagerID=NULL;
DELETE FROM Branches;

-- ---------- Branches ----------
LOAD DATA LOCAL INFILE 'data_generation/csv_output/branches.csv'
INTO TABLE Branches
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 LINES
(BranchName, Address, City, Phone);

-- ---------- Employees ----------
LOAD DATA LOCAL INFILE 'data_generation/csv_output/employees.csv'
INTO TABLE Employees
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 LINES
(FullName, Email, Phone, Position, BranchID, Salary, HiredAt, Status);

-- Promote one employee per branch to manager.
UPDATE Branches b
JOIN (SELECT BranchID, MIN(EmployeeID) AS mid FROM Employees
      WHERE Position='Manager' GROUP BY BranchID) m ON m.BranchID=b.BranchID
SET b.ManagerID=m.mid;

-- ---------- Customers ----------
LOAD DATA LOCAL INFILE 'data_generation/csv_output/customers.csv'
INTO TABLE Customers
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 LINES
(FullName, Email, Phone, DateOfBirth, Address, City, IDNumber);

-- ---------- Accounts ----------
LOAD DATA LOCAL INFILE 'data_generation/csv_output/accounts.csv'
INTO TABLE Accounts
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 LINES
(AccountNumber, CustomerID, BranchID, AccountType, Balance, Currency, Status, OpenedAt);

-- ---------- Transactions ----------
LOAD DATA LOCAL INFILE 'data_generation/csv_output/transactions.csv'
INTO TABLE Transactions
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 LINES
(AccountID, TxType, Amount, Description, CreatedAt);

-- ---------- Loans ----------
LOAD DATA LOCAL INFILE 'data_generation/csv_output/loans.csv'
INTO TABLE Loans
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 LINES
(CustomerID, Principal, InterestRate, TermMonths, MonthlyPayment,
 OutstandingBal, Status, StartDate, EndDate);

-- ---------- Credit Cards ----------
LOAD DATA LOCAL INFILE 'data_generation/csv_output/cards.csv'
INTO TABLE CreditCards
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 LINES
(CardNumber, CustomerID, CreditLimit, OutstandingBal, ExpiryDate, Status);

-- ---------- Card Transactions (v6) ----------
LOAD DATA LOCAL INFILE 'data_generation/csv_output/card_transactions.csv'
INTO TABLE CardTransactions
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 LINES
(CardID, Amount, Merchant, Description, Status, CreatedAt);

-- ---------- Fix closed account balances (v6) ----------
UPDATE Accounts SET Balance = 0.00 WHERE Status = 'closed' AND Balance > 0;

COMMIT;
SET FOREIGN_KEY_CHECKS=1;
SET UNIQUE_CHECKS=1;

SELECT 'branches'         tbl, COUNT(*) n FROM Branches      UNION ALL
SELECT 'employees',            COUNT(*) FROM Employees        UNION ALL
SELECT 'customers',            COUNT(*) FROM Customers        UNION ALL
SELECT 'accounts',             COUNT(*) FROM Accounts         UNION ALL
SELECT 'transactions',         COUNT(*) FROM Transactions     UNION ALL
SELECT 'loans',                COUNT(*) FROM Loans            UNION ALL
SELECT 'credit_cards',         COUNT(*) FROM CreditCards      UNION ALL
SELECT 'card_transactions',    COUNT(*) FROM CardTransactions;
