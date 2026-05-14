-- =========================================================
-- Audit Log v4 — widen Action column to record business actions
-- (DEPOSIT, WITHDRAW, TRANSFER, ISSUE_CARD, NEW_CUSTOMER, ...)
-- Run AFTER audit_log.sql.
-- =========================================================
USE banking;

ALTER TABLE AuditLog
  MODIFY COLUMN Action VARCHAR(40) NOT NULL;
