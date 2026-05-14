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
