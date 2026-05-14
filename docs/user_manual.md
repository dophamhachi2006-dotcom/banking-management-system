# User Manual

## Roles
- **Manager**: Full access (CRUD all, manage users, view audit)
- **Teller**: Customers/Accounts/Transactions (no delete, no employee mgmt)
- **Auditor**: Read-only + audit log + reports

## Quick flows
1. **Login** → enter username/password (default: admin/admin123)
2. **Create customer** → Customers → New
3. **Open account** → Accounts → New, pick customer & branch
4. **Deposit/Withdraw/Transfer** → Transactions tab
5. **View reports** → Reports tab (dashboard charts, top customers, suspicious tx)
6. **Audit log** (manager/auditor) → Audit tab, filter by table/action/user

## Tips
- Large transactions (≥ $50,000) trigger an email alert (if SMTP configured)
- Negative balance is blocked at DB level (trigger)
- All edits to customers/accounts are logged automatically
