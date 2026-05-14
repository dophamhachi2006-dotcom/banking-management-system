# 🏦 Emerald Bank — Banking Management System

> Full-stack internal banking platform: **Flask · MySQL · React · Docker**
> Scope: internal bank operations · Roles: Manager / Teller / Auditor

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#️-architecture)
- [Tech Stack](#-tech-stack)
- [Quick Start (Docker)](#-quick-start--docker-recommended)
- [Open with VS Code](#-open-with-vs-code--terminal)
- [Manual Setup](#-manual-setup-no-docker)
- [Default Accounts](#-default-accounts)
- [Project Structure](#-project-structure)
- [Useful Commands](#-useful-commands)
- [Kaggle Data Import](#-kaggle-data-import)
- [Testing](#-testing)

---

## ✨ Features

| Category | Details |
|---|---|
| 🔐 **Auth & RBAC** | JWT-based login, 3 roles with different permissions |
| 👥 **Customers** | Full CRUD — create, view, edit, soft-delete |
| 🏦 **Accounts** | Open, freeze, close accounts; balance tracking |
| 💸 **Transactions** | Deposit, withdraw, transfer (atomic via stored procedure) |
| 💳 **Loans & Cards** | Apply for loans, issue & track credit cards |
| 📊 **Reports** | Top customers, branch KPIs, daily transaction volume |
| 📜 **Audit Log** | Every DB change is auto-logged via MySQL triggers |
| 🚨 **Fraud Detection** | Rule-based alerts (large amounts, rapid transactions, odd hours) |
| 🔔 **UX** | Toast notifications, loading skeletons, Zod form validation |
| 📱 **Responsive** | Dark mode, mobile-ready, command palette (⌘K / Ctrl+K) |
| 🐳 **Docker** | One-command startup — MySQL + Backend + Frontend |
| 🤖 **Python CLI** | Admin terminal tool for bulk operations & reporting |

---

## 🏗️ Architecture

```
┌─────────────────────┐         HTTP + JWT        ┌──────────────────┐       SQL      ┌───────────┐
│   React 18 (Vite)   │ ◄──────────────────────► │   Flask 3 API    │ ────────────► │  MySQL 8  │
│   TanStack Start    │                            │   SQLAlchemy     │               │           │
│   Tailwind + Zod    │                            │   Flask-JWT-Ext  │               │ Triggers  │
└─────────────────────┘                            └──────────────────┘               │ Procs     │
         :5173                                              :5000                      │ Views     │
                                                            ▲                          └───────────┘
                                                            │                               :3306
                                                   ┌────────┴────────┐
                                                   │   Python CLI    │
                                                   │  (rich + typer) │
                                                   └─────────────────┘
```

All three services run inside a **Docker Compose** network. The Python CLI can call
either the Flask API or connect to MySQL directly for admin tasks.

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, Vite, TanStack Start, Tailwind CSS, Zod, Axios |
| **Backend** | Python 3.11, Flask 3.x, Flask-JWT-Extended, SQLAlchemy, bcrypt |
| **Database** | MySQL 8.0 — with stored procedures, triggers, views, indexes |
| **DevOps** | Docker, Docker Compose, GitHub Actions |
| **CLI** | Python 3.11, Rich, Typer |

---

## 🚀 Quick Start — Docker (Recommended)

### Requirements
- [Docker Desktop](https://docs.docker.com/get-docker/) installed and **running**
- Bash shell (Linux/macOS native · Windows: Git Bash or WSL2)

### Steps

```bash
# 1. Clone the project
git clone <repo-url>
cd banking-management-system

# 2. Run the one-click launcher
chmod +x start.sh
./start.sh
```

The script will:
1. Check Docker is running
2. Copy `.env.example` → `.env` (if not exists)
3. Build all Docker images
4. Start MySQL → Backend → Frontend
5. Wait for each service to become healthy
6. Print access URLs when ready

### Access the app

| Service | URL |
|---|---|
| 🌐 **Frontend** | http://localhost:5173 |
| ⚙️ **Backend API** | http://localhost:5000 |
| 🗄️ **MySQL** | localhost:3306 (`bank` / `bank123`) |

---

## 💻 Open with VS Code + Terminal

```
1. Open VS Code
2. File → Open Folder → select the project folder
3. Open terminal:  Ctrl + `  (backtick key, below Esc)
4. Run: ./start.sh
```

> **Windows users:** use the **Git Bash** or **WSL** terminal profile in VS Code,
> not PowerShell — `start.sh` is a Bash script.
>
> Switch terminal: click the dropdown arrow next to `+` in the terminal panel
> → select **Git Bash** or **WSL**.

---

## 🔧 Manual Setup (No Docker)

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
cp ../.env.example ../.env        # then edit DATABASE_URL
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

## 👤 Default Accounts

> ⚠️ These are **seeded demo accounts** for demonstration only.
> In a real deployment, accounts must be provisioned individually by an administrator.

| Username | Password | Role | Access Level |
|---|---|---|---|
| `admin` | `admin123` | **Manager** | Full access — all features |
| `teller1` | `teller123` | **Teller** | Transactions, customers, accounts |
| `audit1` | `audit123` | **Auditor** | Read-only + audit log + fraud alerts |

### Role Permissions Summary

| Permission | Manager | Teller | Auditor |
|---|:---:|:---:|:---:|
| View customers & accounts | ✅ | ✅ | ✅ |
| Create / edit customers | ✅ | ✅ | ❌ |
| Process transactions | ✅ | ✅ | ❌ |
| Freeze / close accounts | ✅ | ❌ | ❌ |
| Manage employees | ✅ | ❌ | ❌ |
| Issue credit cards | ✅ | ❌ | ❌ |
| View audit log | ✅ | ❌ | ✅ |
| View fraud alerts | ✅ | ❌ | ✅ |
| View analytics reports | ✅ | Limited | ✅ |
| Delete records | ✅ | ❌ | ❌ |

---

## 📁 Project Structure

```
banking-management-system/
├── backend/                    # Flask REST API
│   ├── app.py                  # App factory & config
│   ├── blueprints/             # auth, customers, accounts, transactions, reports
│   ├── models/                 # SQLAlchemy models
│   ├── services/               # Business logic layer
│   └── requirements.txt
│
├── frontend/                   # React SPA
│   └── src/
│       ├── routes/             # TanStack file-based routes
│       ├── components/         # Reusable UI components
│       ├── hooks/              # Custom React hooks
│       └── lib/                # Axios instance, Zod schemas, utils
│
├── database/
│   ├── 00_init_all.sql         # Combined init (used by Docker)
│   ├── schema.sql              # Table definitions
│   ├── views.sql               # Reporting views
│   ├── stored_procedures.sql   # sp_transfer_funds, sp_monthly_report ...
│   ├── triggers.sql            # Fraud detection + audit triggers
│   └── seed_data.sql           # Demo data + default accounts
│
├── python_cli/                 # Admin CLI (rich + typer)
│   └── main.py
│
├── data_generation/            # Kaggle dataset import pipeline
│   ├── download_kaggle.py
│   └── transform_kaggle_data.py
│
├── docs/
│   ├── api_documentation.md
│   ├── user_manual.md
│   └── er_diagram.png
│
├── Dockerfile.backend
├── Dockerfile.frontend
├── docker-compose.yml
├── docker-entrypoint.sh
├── start.sh                    # ← One-click launcher
├── .env.example
└── README.md
```

---

## 🛠 Useful Commands

```bash
# Start everything
./start.sh

# View live logs (all services)
docker compose logs -f

# View logs for one service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f mysql

# Stop all services
docker compose down

# Stop and delete DB data (full reset)
docker compose down -v

# Rebuild after code changes
docker compose build --no-cache
docker compose up -d

# Open MySQL shell
docker compose exec mysql mysql -u bank -pbank123 banking

# Restart one service
docker compose restart backend
```

---

## 📥 Kaggle Data Import

Imports synthetic banking data (~10k customers) from Kaggle.

```bash
# 1. Place your kaggle.json API key in ~/.kaggle/
cd data_generation

# 2. Download the dataset
python download_kaggle.py

# 3. Transform to CSV
python transform_kaggle_data.py
# → outputs to csv_output/

# 4. Load into MySQL
mysql -u bank -pbank123 banking < ../database/load_csv.sql
```

---

## 🧪 Testing

```bash
# Backend unit tests
cd backend
pytest

# Backend with coverage
pytest --cov=. --cov-report=html

# Frontend unit tests
cd frontend
npm run test

# E2E tests (Playwright)
npx playwright test
npx playwright test --ui    # visual mode
```

---

## 📚 Documentation

- [API Reference](docs/api_documentation.md)
- [User Manual](docs/user_manual.md)
- [ER Diagram](docs/er_diagram.png)

---

## 📄 License

MIT — for academic/educational use.
