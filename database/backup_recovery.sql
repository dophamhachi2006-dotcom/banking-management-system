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
