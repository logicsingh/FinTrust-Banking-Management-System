# FinTrust — Banking Management System

Educational Oracle Database + PL/SQL banking project with a responsive web UI and an optional FastAPI layer.

## Preview
Extract the ZIP and open `frontend/index.html`. Without a configured Oracle API, the interface uses clearly labelled in-memory demo data; it does not pretend to be live. Demo operations reset when the page is reloaded.

## Live Oracle setup
Follow [docs/SETUP.md](docs/SETUP.md). Run SQL scripts in order:
1. `database/01_schema.sql`
2. `database/02_banking_package.sql`
3. `database/03_audit_trigger.sql`
4. `database/04_seed_data.sql`

The optional API uses Python FastAPI and `python-oracledb`, configured through `.env` copied from `.env.example`.

## Security and scope
This is an educational demonstration, not production banking software. **The API currently has no authentication or authorization.** It must remain bound to localhost and must not be exposed to a network or public deployment. CORS restrictions do not replace authentication. Do not use real customer data, credentials, or funds.

The live API supports dashboard, customer/account/transaction/audit reads, customer creation, deposits, withdrawals, and transfers. Live account creation, editing, and account closure are not implemented through the API; account creation is available in PL/SQL.

Database compilation and integration tests must be run in your own Oracle environment; this repository does not claim they have been run. The dashboard bar chart is illustrative, not live chart data.
