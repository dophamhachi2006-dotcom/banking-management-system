USE banking;
-- Composite/extra indexes for performance
CREATE INDEX idx_tx_account_date ON Transactions(AccountID, CreatedAt DESC);
CREATE INDEX idx_acc_cust_status ON Accounts(CustomerID, Status);
CREATE INDEX idx_loan_status_cust ON Loans(Status, CustomerID);
