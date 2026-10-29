# Setup

## Preview UI
Extract the ZIP and open `frontend/index.html`. If Oracle API is not running, the app explicitly shows demo mode. Demo operations change only browser memory and reset on reload.

## Oracle database
In SQL Workshop / SQL Developer, run in this order:
1. `database/01_schema.sql`
2. `database/02_banking_package.sql`
3. `database/03_audit_trigger.sql`
4. `database/04_seed_data.sql`

Run scripts in a fresh schema or inspect existing objects first. The schema script is not a destructive reset script. Check `USER_OBJECTS` and `USER_ERRORS` after compilation.

## Live API
Python 3.10+ required. From project root:
```
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt
```
Copy `.env.example` to `.env`, enter Oracle credentials and DSN, then:
```
uvicorn backend.app:app --reload
```
Open `http://127.0.0.1:8000/docs`. If browser blocks a local file calling the API, serve frontend:
```
python -m http.server 5173 --directory frontend
```
Open `http://127.0.0.1:5173`.

## Current limits
Live API supports dashboard, customer/account/transaction/audit reads, customer creation, deposits, withdrawals, and transfers. Live account creation, editing, and account closure are not implemented through the API; account creation is available in PL/SQL. Dashboard bar chart is illustrative, not real chart data. Run and verify SQL in your own Oracle environment before claiming it is tested.
