-- =========================================================
-- User-Defined Functions  —  v6
-- =========================================================
USE banking;
DELIMITER $$

-- 1. Total balance across ALL active accounts for a customer
DROP FUNCTION IF EXISTS fn_customer_total_balance$$
CREATE FUNCTION fn_customer_total_balance(p_customer_id INT)
RETURNS DECIMAL(15,2)
READS SQL DATA
COMMENT 'Sum of Balance for all active accounts belonging to a customer.'
BEGIN
  DECLARE v_total DECIMAL(15,2);
  SELECT COALESCE(SUM(Balance),0) INTO v_total
  FROM Accounts WHERE CustomerID=p_customer_id AND Status='active';
  RETURN v_total;
END$$

-- 2. Age of an account in calendar days
DROP FUNCTION IF EXISTS fn_account_age_days$$
CREATE FUNCTION fn_account_age_days(p_account_id INT)
RETURNS INT
READS SQL DATA
COMMENT 'Number of days since the account was opened.'
BEGIN
  DECLARE v_age INT;
  SELECT DATEDIFF(CURDATE(), OpenedAt) INTO v_age
  FROM Accounts WHERE AccountID = p_account_id;
  RETURN v_age;
END$$

-- 3. Simple interest: Balance × (rate/100) × (days/365)
DROP FUNCTION IF EXISTS fn_calculate_interest$$
CREATE FUNCTION fn_calculate_interest(
  p_account_id  INT,
  p_annual_rate DECIMAL(5,2),
  p_days        INT
)
RETURNS DECIMAL(15,2)
READS SQL DATA
COMMENT 'Calculates simple interest for an account over p_days at p_annual_rate% p.a.'
BEGIN
  DECLARE v_principal DECIMAL(15,2) DEFAULT 0;
  DECLARE v_interest  DECIMAL(15,2) DEFAULT 0;

  SELECT Balance INTO v_principal
  FROM Accounts WHERE AccountID = p_account_id;

  SET v_interest = v_principal * (p_annual_rate / 100) * (p_days / 365.0);
  RETURN ROUND(v_interest, 2);
END$$

-- 4. Minimum-balance check before a withdrawal
--    Returns 1 (OK) or 0 (would breach minimum).
--    Minimums: savings=100, checking=50, fixed=500, others=0.
DROP FUNCTION IF EXISTS fn_min_balance_check$$
CREATE FUNCTION fn_min_balance_check(
  p_account_id   INT,
  p_withdraw_amt DECIMAL(15,2)
)
RETURNS TINYINT(1)
READS SQL DATA
COMMENT 'Returns 1 if balance after withdrawal >= type minimum, 0 otherwise.'
BEGIN
  DECLARE v_balance      DECIMAL(15,2) DEFAULT 0;
  DECLARE v_type         VARCHAR(20)   DEFAULT 'savings';
  DECLARE v_min          DECIMAL(15,2) DEFAULT 0;
  DECLARE v_balance_after DECIMAL(15,2);

  SELECT Balance, AccountType
  INTO   v_balance, v_type
  FROM   Accounts
  WHERE  AccountID = p_account_id;

  SET v_min = CASE v_type
    WHEN 'savings'  THEN 100.00
    WHEN 'checking' THEN  50.00
    WHEN 'fixed'    THEN 500.00
    ELSE 0.00
  END;

  SET v_balance_after = v_balance - p_withdraw_amt;
  RETURN IF(v_balance_after >= v_min, 1, 0);
END$$

DELIMITER ;
