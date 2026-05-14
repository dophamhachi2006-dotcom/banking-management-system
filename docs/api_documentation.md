# API Documentation

Base URL: `http://localhost:5000/api`
All responses: `{ success, data, message, errors? }`. Auth via `Authorization: Bearer <jwt>`.

## Auth
- `POST /auth/login` `{username, password}` → `{token, user}`
- `GET  /auth/me`
- `POST /auth/logout`

## Customers (manager+teller for write, manager for delete)
- `GET    /customers?page&size&q`
- `GET    /customers/:id`
- `POST   /customers`
- `PUT    /customers/:id`
- `DELETE /customers/:id`

## Accounts
- `GET /accounts?customer_id&branch_id&page&size`
- `POST /accounts`
- `PUT /accounts/:id/status` `{Status}`

## Transactions
- `GET  /transactions?account_id&type&from&to&min_amount&max_amount`
- `POST /transactions/deposit` `{AccountID, Amount, Description}`
- `POST /transactions/withdraw`
- `POST /transactions/transfer` `{FromAccountID, ToAccountID, Amount}`

## Employees / Branches / Loans / Cards
Standard CRUD (manager only for write).

## Reports
- `GET /reports/dashboard`
- `GET /reports/top-customers?limit=10`
- `GET /reports/branch-performance`
- `GET /reports/monthly-summary`
- `GET /reports/suspicious` (manager+auditor)

## Audit
- `GET /audit?table&action&user_id&page&size` (manager+auditor)
