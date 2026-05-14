# Emerald Bank — Banking Management System

> **Full-stack internal banking platform** · Flask · MySQL · React · Docker
>
> This is the final project for the **Database Management Systems** course — a complete internal banking management system, from relational database design to web interface and administrative CLI.

---

## Student Information

| Full Name | Student ID | Class |
|---|---|---|
| Do Pham Ha Chi | 11245851 | DSEB |

**Supervisor:** Dr. Tran Hung
**University:** National Economics University — Faculty of Information Technology
**Date:** May 2026 · Version 2.1

---

## Project Links

| Resource | Link |
|---|---|
| **GitHub Repository** | [banking-management-system](https://github.com/dophamhachi2006-dotcom/banking-management-system.git) |
| **Google Drive (Source + Demo)** | [Open Drive](https://drive.google.com/drive/folders/1iEXz_0lLntYiUt0YUI0Rfg2ABhlRzKXM?usp=sharing) |
| **Demo Video (YouTube)** | [Watch on YouTube](https://youtu.be/dsyAgmjXpu8) |

---

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Quick Start (Docker)](#quick-start--docker-recommended)
- [Manual Installation](#manual-installation-without-docker)
- [Default Accounts](#default-accounts)
- [Project Structure](#project-structure)
- [Database](#database)
- [Useful Commands](#useful-commands)
- [Testing](#testing)

---

## Project Overview

**Emerald Bank BMS** simulates the internal operating system of a real-world bank, focusing on applying core DBMS concepts to a concrete business problem.

The system is built around **five main objectives**:

- **Data integrity** — 3NF schema design; fund transfers are executed through a stored procedure with row-level `FOR UPDATE` locks, guaranteeing strict atomicity.
- **Automatic auditing** — Every change to sensitive tables is recorded by MySQL triggers into an immutable `AuditLog` table — no code path can bypass it.
- **Decoupled architecture** — The Flask API and React SPA communicate over HTTP using stateless JWT; each layer can be replaced without affecting the others.
- **Operational tooling** — Docker Compose plus `start.sh` brings the entire stack up with one command; a Python CLI supports back-office operations.
- **Analytics & fraud detection** — Dashboards with Sankey diagrams, D3 network graphs, transaction heatmaps, and a fraud-detection module combining rule-based logic with an ML model.

---

## Features

| Group | Details |
|---|---|
| **Authentication & Authorization** | JWT login, three roles with distinct permissions |
| **Customer Management** | Full CRUD — create, view, update, soft delete |
| **Account Management** | Open, freeze, close accounts; balance tracking |
| **Transactions** | Deposit, withdraw, transfer (atomic via stored procedure) |
| **Loans & Credit Cards** | Loan applications, credit card issuance and management |
| **Reporting & Analytics** | Top customers, branch KPIs, transaction volumes |
| **Audit Log** | All database changes auto-recorded via MySQL triggers |
| **Fraud Detection** | Rule-based alerts (large amounts, rapid transactions, unusual hours) plus ML classifier |
| **UX** | Toast notifications, loading skeletons, Zod form validation |
| **Interface** | Dark mode, mobile responsive, command palette (⌘K / Ctrl+K) |
| **Docker** | Launch the entire stack with a single command |
| **Python CLI** | Terminal tool for batch operations and reporting |

---

## System Architecture

The platform follows a three-tier architecture. The presentation tier (React SPA) communicates with the application tier (Flask REST API) over HTTP using stateless JWT authentication. The application tier persists state in a MySQL 8 database where business rules are enforced through stored procedures, triggers, and views. A Python administrative CLI sits alongside the API and may also connect directly to the database for back-office operations. All services run within an isolated Docker Compose network.

```text
                          Presentation Tier
        +-------------------------------------------------+
        |  React 18 SPA  (Vite, TanStack Router, Tailwind)|
        |  Port 5173                                      |
        +-------------------------------------------------+
                              |
                              |  HTTPS / JSON  +  JWT (Bearer)
                              v
                          Application Tier
        +-------------------------------------------------+
        |  Flask 3 REST API                               |
        |  SQLAlchemy  ·  Flask-JWT-Extended  ·  bcrypt   |
        |  Port 5000                                      |
        +-------------------------------------------------+
                  ^                           |
                  |                           |  SQL  (parameterised)
                  |                           v
   +----------------------------+   +---------------------------------+
   |  Python CLI                |   |  Data Tier                      |
   |  Rich  ·  Typer            |   |  MySQL 8.0  (InnoDB)            |
   |  Admin / batch operations  |-->|  Tables · Views · Procedures    |
   |                            |   |  Triggers · Indexes · AuditLog  |
   +----------------------------+   |  Port 3306 (internal only)      |
                                    +---------------------------------+

                          Docker Compose Network
```

**Component responsibilities**

| Tier | Component | Responsibility |
|---|---|---|
| Presentation | React SPA | Rendering, routing, client-side validation, state management |
| Application | Flask API | Authentication, authorization, business logic, request validation |
| Application | Python CLI | Administrative operations, batch jobs, reporting |
| Data | MySQL 8 | Persistence, transactional integrity, audit logging, reporting views |

**Cross-cutting concerns**

- **Security** — JWT issued by the API; passwords hashed with PBKDF2-SHA256 and per-user salt; all queries use bound parameters.
- **Auditability** — Database triggers write every mutation on sensitive tables to `AuditLog`, independent of the calling service.
- **Atomicity** — Fund transfers run inside a stored procedure with `SELECT ... FOR UPDATE` row locks.
- **Isolation** — MySQL is reachable only inside the Docker network; the host does not publish port 3306.

---

## Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, Vite 5, TanStack Router, Tailwind CSS, Zod, Axios |
| **Backend** | Python 3.11, Flask 3.x, Flask-JWT-Extended, mysql-connector-python, bcrypt |
| **Database** | MySQL 8.0 (InnoDB) — stored procedures, triggers, views, indexes, 3NF schema |
| **ML / Fraud** | scikit-learn RandomForest plus rule-based fallback |
| **DevOps** | Docker, Docker Compose, GitHub Actions |
| **CLI** | Python 3.11, Rich, Typer |

> **Why raw SQL instead of an ORM?** This is a DBMS course project: every query, join, and aggregation must be transparent so the reviewer can trace each business operation down to the executed SQL.

---

## Quick Start — Docker (Recommended)

### Requirements
- [Docker Desktop](https://docs.docker.com/get-docker/) installed and **running**
- Bash shell (Linux/macOS native · Windows: Git Bash or WSL2)

### Steps

```bash
# 1. Clone the project
git clone https://github.com/dophamhachi2006-dotcom/banking-management-system.git
cd banking-management-system

# 2. Launch with one command
chmod +x start.sh
./start.sh
```

The script automatically:
1. Verifies Docker is running
2. Copies `.env.example` to `.env`
3. Builds all Docker images
4. Starts MySQL → Backend → Frontend in order
5. Waits for each service to become healthy
6. Prints access URLs when ready

### Access the application

| Service | URL |
|---|---|
| **Frontend** | http://localhost:5173 |
| **Backend API** | http://localhost:5000 |
| **MySQL** | localhost:3306 (user: `bank` / pass: `bank123`) |

---

## Open with VS Code + Terminal

```
1. Open VS Code
2. File → Open Folder → choose the project directory
3. Open terminal:  Ctrl + ` (backtick key, below Esc)
4. Run: ./start.sh
```

> **Windows:** use a **Git Bash** or **WSL** terminal inside VS Code, not PowerShell.
> Switch terminal: click the dropdown next to `+` and choose **Git Bash** or **WSL**.

---

## Manual Installation (without Docker)

### 1. MySQL

```bash
mysql -u root -p < database/schema.sql
mysql -u root -p banking < database/views.sql
mysql -u root -p banking < database/stored_procedures.sql
mysql -u root -p banking < database/triggers.sql
mysql -u root -p banking < database/audit_log.sql
mysql -u root -p banking < database/seed_data.sql
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
cp ../.env.example ../.env   # Edit DATABASE_URL
python app.py
# → http://localhost:5000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### 4. Python CLI (optional)

```bash
cd python_cli
python main.py --help
```

---

## Default Accounts

> These are **pre-seeded demo accounts** intended only for testing purposes.

| Username | Password | Role | Permissions |
|---|---|---|---|
| `admin` | `admin123` | **Manager** | Full access — all features |
| `teller1` | `teller123` | **Teller** | Transactions, customers, accounts |
| `audit1` | `audit123` | **Auditor** | Read-only plus audit log and fraud alerts |

### Permission Matrix

| Permission | Manager | Teller | Auditor |
|:---|:---:|:---:|:---:|
| View customers and accounts | Yes | Yes | Yes |
| Create / edit customers | Yes | Yes | No |
| Execute transactions | Yes | Yes | No |
| Freeze / close accounts | Yes | No | No |
| Manage employees | Yes | No | No |
| Issue credit cards | Yes | No | No |
| View audit log | Yes | No | Yes |
| View fraud alerts | Yes | No | Yes |
| View analytics reports | Yes | Limited | Yes |
| Delete records | Yes | No | No |

---

## Project Structure

```
banking-management-system/
├── core/                       # Shared utilities for backend and CLI
│   ├── db_connection.py        # Connection pool and context-managed cursor
│   ├── validators.py
│   ├── formatters.py
│   └── auth.py                 # JWT issue/decode/auth_required
│
├── database/
│   ├── schema.sql              # Table DDL in dependency order
│   ├── views.sql               # Reporting views
│   ├── stored_procedures.sql   # sp_transfer_funds, sp_monthly_report ...
│   ├── triggers.sql            # Fraud detection and audit triggers
│   ├── indexes.sql             # Performance indexes
│   └── seed_data.sql           # Demo data and default accounts
│
├── backend/                    # Flask REST API
│   ├── app.py                  # Application factory
│   ├── routes/                 # 11 blueprints: auth, customers, accounts, transactions...
│   ├── services/               # Business logic: transaction, fraud, report
│   ├── ml/                     # Fraud detection model
│   └── requirements.txt
│
├── frontend/                   # React SPA
│   └── src/
│       ├── routes/             # TanStack file-based routes
│       ├── components/         # UI components (charts: Sankey, NetworkGraph, Heatmap)
│       ├── hooks/              # Custom React hooks
│       └── lib/                # Axios instance, Zod schemas, utils
│
├── python_cli/                 # Admin CLI (Rich + Typer)
│   └── main.py
│
├── data_generation/            # Kaggle data import pipeline (~1.26M records)
│   ├── download_kaggle.py
│   └── transform_kaggle_data.py
│
├── docs/
│   ├── api_documentation.md
│   ├── user_manual.md
│   └── er_diagram.png
│
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── start.sh                    # ← One-click launcher
└── README.md
```

---

## Database

### Main Tables

| Table | Description |
|---|---|
| `Branches` | Bank branches, ManagerID nullable (ON DELETE SET NULL) |
| `Employees` | Staff records, linked to branches and Users |
| `Users` | Login accounts; passwords hashed with PBKDF2-SHA256 plus per-user salt |
| `Customers` | Customer KYC information; IDNumber UNIQUE |
| `Accounts` | Bank accounts (savings/checking/fixed); Balance changes only via stored procedure |
| `Transactions` | Immutable ledger; Amount always positive, direction inferred from TxType |
| `Loans` | Loan records; MonthlyPayment precomputed by annuity formula |
| `CreditCards` | Credit cards with CreditLimit and OutstandingBal |
| `CardTransactions` | Separate card transaction history |
| `AuditLog` | Auto-recorded by triggers; OldData/NewData stored as JSON |

### Key Stored Procedure

```sql
-- Atomic fund transfer: row-locks with FOR UPDATE before reading balances
CALL sp_transfer(from_account_id, to_account_id, amount, user_id);
```

### Demo Data (Kaggle)
The system seeds approximately 1.26 million records from a synthetic Kaggle dataset, including four types of fraud signals deliberately injected to train the ML model.

---

## Useful Commands

```bash
# Start the entire stack
./start.sh

# Tail logs in real time
docker compose logs -f
docker compose logs -f backend

# Stop everything
docker compose down

# Full reset (drops DB volumes)
docker compose down -v

# Rebuild after code changes
docker compose build --no-cache && docker compose up -d

# Open MySQL shell
docker compose exec mysql mysql -u bank -pbank123 banking

# Restart a single service
docker compose restart backend
```

---

## Import Kaggle Data

```bash
# 1. Place kaggle.json API key in ~/.kaggle/
cd data_generation

# 2. Download dataset
python download_kaggle.py

# 3. Transform into CSV
python transform_kaggle_data.py
# → output written to csv_output/

# 4. Load into MySQL
mysql -u bank -pbank123 banking < ../database/load_csv.sql
```

---

## Testing

```bash
# Backend unit tests
cd backend
pytest

# Backend with coverage report
pytest --cov=. --cov-report=html

# Frontend unit tests
cd frontend
npm run test

# E2E tests (Playwright)
npx playwright test
npx playwright test --ui    # visual mode
```

---

## Security

- Passwords hashed with **PBKDF2-SHA256** plus per-user salt (Werkzeug)
- Stateless JWT, 8-hour expiry, secret loaded from `.env`
- All SQL uses **bound parameters** (SQL injection protection)
- Dynamic filter/sort routed through `query_builder.py` with column-name whitelisting
- MySQL port 3306 is **not published** to the Docker host network
- Flask-Limiter: 200 req/min, with stricter limits on `/auth/login`
- Audit triggers live inside the database — no service can bypass logging

---

## Documentation

- [API Reference](docs/api_documentation.md)
- [User Manual](docs/user_manual.md)
- [ER Diagram](docs/er_diagram.png)
- [Google Drive (source + video)](https://drive.google.com/drive/folders/1iEXz_0lLntYiUt0YUI0Rfg2ABhlRzKXM?usp=sharing)
- [Demo Video (YouTube)](https://youtu.be/dsyAgmjXpu8)

---

## License

MIT — for academic and educational purposes.
