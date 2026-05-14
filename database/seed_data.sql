-- =========================================================
-- Auth-only seed. Real banking data is loaded via:
--   python data_generation/transform_kaggle_data.py
--   mysql --local-infile=1 -u root -p banking < database/load_csv.sql
--   python backend/seed_users.py    (rewrite hashes with werkzeug)
--
-- This file ONLY creates the system-admin user record so the API
-- has someone to log in as before CSV import. NO mock customers,
-- accounts, or transactions are created here.
-- =========================================================
USE banking;

-- Bootstrap users (hashes overwritten by backend/seed_users.py with real
-- werkzeug pbkdf2 hashes for: admin/admin123, teller1/teller123, audit1/audit123).
INSERT INTO Users (Username, PasswordHash, Role, EmployeeID) VALUES
('admin',   'PLACEHOLDER_RUN_seed_users.py', 'manager',  NULL),
('teller1', 'PLACEHOLDER_RUN_seed_users.py', 'teller',   NULL),
('audit1',  'PLACEHOLDER_RUN_seed_users.py', 'auditor',  NULL)
ON DUPLICATE KEY UPDATE Username=Username;
