-- =========================================================
-- Banking Management System - Schema
-- MySQL 8.0+
-- =========================================================
DROP DATABASE IF EXISTS banking;
CREATE DATABASE banking CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
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

-- ---------- Card Transactions ----------
CREATE TABLE CardTransactions (
  ID            BIGINT AUTO_INCREMENT PRIMARY KEY,
  CardID        INT NOT NULL,
  Amount        DECIMAL(15,2) NOT NULL,
  Merchant      VARCHAR(120),
  Description   VARCHAR(255),
  Status        ENUM('approved','declined','reversed') DEFAULT 'approved',
  CreatedAt     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (CardID) REFERENCES CreditCards(CardID) ON DELETE CASCADE,
  INDEX idx_cardtx_card (CardID),
  INDEX idx_cardtx_date (CreatedAt)
);
