# FinTrust — Banking Management System

Educational Oracle Database + PL/SQL banking project with a responsive web UI.

## Preview
Extract the ZIP and open `frontend/index.html`. Without a configured Oracle API, the interface uses clearly labelled in-memory demo data; it does not pretend to be live.

## Live Oracle setup
Follow `docs/SETUP.md`. Run SQL scripts in order:
1. `database/01_schema.sql`
2. `database/02_banking_package.sql`
3. `database/03_audit_trigger.sql`
4. `database/04_seed_data.sql`

Optional API: Python FastAPI + `python-oracledb`, configured using `.env` copied from `.env.example`.

## Important
This is an educational demo, not production banking software. Database compilation/integration tests must be run in your own Oracle environment; this package does not claim they were run. The interface supports demo operations; the live API supports dashboard, customer/account/transaction/audit reads, customer creation, deposit, withdrawal, and transfer. Account creation through the live API is not included yet.
