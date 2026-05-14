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
