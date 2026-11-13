import os
from decimal import Decimal

import oracledb
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr

load_dotenv()

app = FastAPI(title="FinTrust API", version="1.0.0")
allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "FINTRUST_ALLOWED_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def conn():
    u, p, d = (
        os.getenv("ORACLE_USER"),
        os.getenv("ORACLE_PASSWORD"),
        os.getenv("ORACLE_DSN"),
    )
    if not all([u, p, d]):
        raise RuntimeError(
            "Configure ORACLE_USER, ORACLE_PASSWORD and ORACLE_DSN in .env"
        )
    return oracledb.connect(user=u, password=p, dsn=d)


def rows(cur):
    names = [d[0].lower() for d in cur.description]
    return [dict(zip(names, row)) for row in cur.fetchall()]


@app.get("/api/health")
def health():
    try:
        with conn() as connection:
            with connection.cursor() as cursor:
                cursor.execute("select 'ok' from dual")
                cursor.fetchone()
        return {"status": "ok", "database": "connected"}
    except Exception:
        return {"status": "not_connected", "detail": "Database connection failed"}


@app.get("/api/dashboard")
def dashboard():
    try:
        with conn() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """select (select count(*) from customers) total_customers,
                    (select count(*) from bank_accounts where status='ACTIVE') active_accounts,
                    (select nvl(sum(balance),0) from bank_accounts where status='ACTIVE') total_balance,
                    (select count(*) from bank_transactions where created_at>=trunc(sysdate)) today_transactions,
                    (select nvl(sum(amount),0) from bank_transactions where transaction_type='DEPOSIT' and created_at>=trunc(sysdate)) today_deposits,
                    (select nvl(sum(amount),0) from bank_transactions where transaction_type='WITHDRAWAL' and created_at>=trunc(sysdate)) today_withdrawals from dual"""
                )
                summary = dict(zip([d[0].lower() for d in cursor.description], cursor.fetchone()))
                cursor.execute(
                    """select t.transaction_id,t.account_id,a.account_number,c.full_name,
                    t.transaction_type,t.amount,t.description,t.reference_number,t.created_at
                    from bank_transactions t
                    join bank_accounts a on a.account_id=t.account_id
                    join customers c on c.customer_id=a.customer_id
                    order by t.created_at desc fetch first 8 rows only"""
                )
                return {"summary": summary, "recent_transactions": rows(cursor)}
    except Exception:
        raise HTTPException(503, detail="Could not load dashboard data")


@app.get("/api/customers")
def customers():
    try:
        with conn() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "select customer_id,full_name,email,phone,created_at "
                    "from customers order by customer_id desc"
                )
                return rows(cursor)
    except Exception:
        raise HTTPException(503, detail="Could not load customers")


class Customer(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=25)


@app.post("/api/customers", status_code=201)
def add_customer(customer: Customer):
    try:
        with conn() as connection:
            with connection.cursor() as cursor:
                out = cursor.var(oracledb.NUMBER)
                cursor.execute(
                    "insert into customers(full_name,email,phone) "
                    "values(:n,:e,:p) returning customer_id into :i",
                    n=customer.full_name.strip(),
                    e=str(customer.email).lower(),
                    p=customer.phone,
                    i=out,
                )
                ident = int(out.getvalue()[0])
                connection.commit()
                return {"customer_id": ident, "message": "Customer created"}
    except oracledb.IntegrityError:
        raise HTTPException(409, detail="Email already exists")
    except Exception:
        raise HTTPException(503, detail="Could not create customer")


@app.get("/api/accounts")
def accounts():
    try:
        with conn() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "select a.account_id,a.customer_id,a.account_number,a.account_type,"
                    "a.balance,a.status,a.created_at,c.full_name,c.email "
                    "from bank_accounts a join customers c on c.customer_id=a.customer_id "
                    "order by a.account_id desc"
                )
                return rows(cursor)
    except Exception:
        raise HTTPException(503, detail="Could not load accounts")


@app.get("/api/transactions")
def transactions():
    try:
        with conn() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "select t.transaction_id,t.account_id,a.account_number,c.full_name,"
                    "t.transaction_type,t.amount,t.description,t.reference_number,"
                    "t.related_account_id,t.created_at from bank_transactions t "
                    "join bank_accounts a on a.account_id=t.account_id "
                    "join customers c on c.customer_id=a.customer_id "
                    "order by t.created_at desc fetch first 200 rows only"
                )
                return rows(cursor)
    except Exception:
        raise HTTPException(503, detail="Could not load transactions")


@app.get("/api/audit")
def audit():
    try:
        with conn() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "select l.audit_id,l.account_id,a.account_number,l.old_balance,"
                    "l.new_balance,l.action_type,l.changed_at from balance_audit_log l "
                    "join bank_accounts a on a.account_id=l.account_id "
                    "order by l.changed_at desc fetch first 200 rows only"
                )
                return rows(cursor)
    except Exception:
        raise HTTPException(503, detail="Could not load audit history")


class Money(BaseModel):
    account_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    description: str | None = Field(default=None, max_length=250)


@app.post("/api/deposit")
def deposit(money: Money):
    return package_call(
        "begin banking_pkg.deposit(:a,:n,:d); end;",
        {"a": money.account_id, "n": money.amount, "d": money.description or "Deposit via FinTrust"},
    )


@app.post("/api/withdraw")
def withdraw(money: Money):
    return package_call(
        "begin banking_pkg.withdraw(:a,:n,:d); end;",
        {"a": money.account_id, "n": money.amount, "d": money.description or "Withdrawal via FinTrust"},
    )


class Transfer(BaseModel):
    from_account_id: int = Field(gt=0)
    to_account_id: int = Field(gt=0)
    amount: float = Field(gt=0, allow_inf_nan=False)
    description: str | None = Field(default=None, max_length=250)


@app.post("/api/transfer")
def transfer(transfer_request: Transfer):
    if transfer_request.from_account_id == transfer_request.to_account_id:
        raise HTTPException(400, detail="Accounts must be different")
    return package_call(
        "begin banking_pkg.transfer(:f,:t,:n,:d); end;",
        {
            "f": transfer_request.from_account_id,
            "t": transfer_request.to_account_id,
            "n": transfer_request.amount,
            "d": transfer_request.description or "Transfer via FinTrust",
        },
    )


def package_call(sql, params):
    try:
        with conn() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
            connection.commit()
        return {"message": "Operation committed"}
    except Exception:
        raise HTTPException(400, detail="The banking operation could not be completed")
