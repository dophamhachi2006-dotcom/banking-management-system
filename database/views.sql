-- =========================================================
-- Views  —  v6
-- =========================================================
USE banking;

-- Customer summary: ALL accounts counted (no status filter),
-- TotalBalance sums only active accounts to avoid inflating with closed balances.
CREATE OR REPLACE VIEW vw_customer_summary AS
SELECT
  c.CustomerID,
  c.FullName,
  c.Email,
  c.Phone,
  c.City,
  c.IDNumber,
  COUNT(a.AccountID)                                           AS AccountCount,
  COALESCE(SUM(CASE WHEN a.Status='active' THEN a.Balance ELSE 0 END), 0) AS TotalBalance,
  c.CreatedAt
FROM Customers c
LEFT JOIN Accounts a ON a.CustomerID = c.CustomerID
GROUP BY c.CustomerID;

CREATE OR REPLACE VIEW vw_account_details AS
SELECT
  a.AccountID, a.AccountNumber, a.AccountType, a.Balance, a.Currency, a.Status,
  c.CustomerID, c.FullName AS CustomerName, c.Email AS CustomerEmail,
  b.BranchID, b.BranchName, b.City AS BranchCity,
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

-- Monthly transaction summary — one row per month, used by dashboard chart
CREATE OR REPLACE VIEW vw_monthly_tx_summary AS
SELECT
  DATE_FORMAT(CreatedAt,'%Y-%m') AS Month,
  COUNT(*)                       AS TxCount,
  COALESCE(SUM(Amount), 0)       AS TotalAmount
FROM Transactions
GROUP BY Month
ORDER BY Month ASC;
