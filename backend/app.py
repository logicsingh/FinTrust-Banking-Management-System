import os
import oracledb
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
load_dotenv()
app=FastAPI(title="FinTrust API",version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"])
def conn():
    u,p,d=os.getenv("ORACLE_USER"),os.getenv("ORACLE_PASSWORD"),os.getenv("ORACLE_DSN")
    if not all([u,p,d]): raise RuntimeError("Configure ORACLE_USER, ORACLE_PASSWORD and ORACLE_DSN in .env")
    return oracledb.connect(user=u,password=p,dsn=d)
def rows(cur):
    names=[d[0].lower() for d in cur.description]
    return [dict(zip(names,r)) for r in cur.fetchall()]
@app.get("/api/health")
def health():
    try:
        with conn() as c:
            with c.cursor() as q:q.execute("select 'ok' from dual");q.fetchone()
        return {"status":"ok","database":"connected"}
    except Exception as e:return {"status":"not_connected","detail":str(e)}
@app.get("/api/dashboard")
def dashboard():
    try:
        with conn() as c:
            with c.cursor() as q:
                q.execute("""select (select count(*) from customers) total_customers,
                (select count(*) from bank_accounts where status='ACTIVE') active_accounts,
                (select nvl(sum(balance),0) from bank_accounts where status='ACTIVE') total_balance,
                (select count(*) from bank_transactions where created_at>=trunc(sysdate)) today_transactions,
                (select nvl(sum(amount),0) from bank_transactions where transaction_type='DEPOSIT' and created_at>=trunc(sysdate)) today_deposits,
                (select nvl(sum(amount),0) from bank_transactions where transaction_type='WITHDRAWAL' and created_at>=trunc(sysdate)) today_withdrawals from dual""")
                s=dict(zip([d[0].lower() for d in q.description],q.fetchone()))
                q.execute("""select t.transaction_id,t.account_id,a.account_number,c.full_name,t.transaction_type,t.amount,t.description,t.reference_number,t.created_at from bank_transactions t join bank_accounts a on a.account_id=t.account_id join customers c on c.customer_id=a.customer_id order by t.created_at desc fetch first 8 rows only""")
                return {"summary":s,"recent_transactions":rows(q)}
    except Exception as e:raise HTTPException(503,detail=str(e))
@app.get("/api/customers")
def customers():
    try:
        with conn() as c:
            with c.cursor() as q:q.execute("select customer_id,full_name,email,phone,created_at from customers order by customer_id desc");return rows(q)
    except Exception as e:raise HTTPException(503,detail=str(e))
class Customer(BaseModel):
    full_name:str=Field(min_length=2,max_length=120)
    email:EmailStr
    phone:str|None=None
@app.post("/api/customers",status_code=201)
def add_customer(x:Customer):
    try:
        with conn() as c:
            with c.cursor() as q:
                out=q.var(oracledb.NUMBER)
                q.execute("insert into customers(full_name,email,phone) values(:n,:e,:p) returning customer_id into :i",n=x.full_name.strip(),e=str(x.email).lower(),p=x.phone,i=out)
                ident=int(out.getvalue()[0]);c.commit();return {"customer_id":ident,"message":"Customer created"}
    except oracledb.IntegrityError:raise HTTPException(409,detail="Email already exists")
    except Exception as e:raise HTTPException(503,detail=str(e))
@app.get("/api/accounts")
def accounts():
    try:
        with conn() as c:
            with c.cursor() as q:q.execute("select a.account_id,a.customer_id,a.account_number,a.account_type,a.balance,a.status,a.created_at,c.full_name,c.email from bank_accounts a join customers c on c.customer_id=a.customer_id order by a.account_id desc");return rows(q)
    except Exception as e:raise HTTPException(503,detail=str(e))
@app.get("/api/transactions")
def transactions():
    try:
        with conn() as c:
            with c.cursor() as q:q.execute("select t.transaction_id,t.account_id,a.account_number,c.full_name,t.transaction_type,t.amount,t.description,t.reference_number,t.related_account_id,t.created_at from bank_transactions t join bank_accounts a on a.account_id=t.account_id join customers c on c.customer_id=a.customer_id order by t.created_at desc fetch first 200 rows only");return rows(q)
    except Exception as e:raise HTTPException(503,detail=str(e))
@app.get("/api/audit")
def audit():
    try:
        with conn() as c:
            with c.cursor() as q:q.execute("select l.audit_id,l.account_id,a.account_number,l.old_balance,l.new_balance,l.action_type,l.changed_at from balance_audit_log l join bank_accounts a on a.account_id=l.account_id order by l.changed_at desc fetch first 200 rows only");return rows(q)
    except Exception as e:raise HTTPException(503,detail=str(e))
class Money(BaseModel):
    account_id:int
    amount:float=Field(gt=0)
    description:str|None=None
@app.post("/api/deposit")
def deposit(x:Money):return package_call("begin banking_pkg.deposit(:a,:n,:d); end;",{"a":x.account_id,"n":x.amount,"d":x.description or "Deposit via FinTrust"})
@app.post("/api/withdraw")
def withdraw(x:Money):return package_call("begin banking_pkg.withdraw(:a,:n,:d); end;",{"a":x.account_id,"n":x.amount,"d":x.description or "Withdrawal via FinTrust"})
class Transfer(BaseModel):
    from_account_id:int
    to_account_id:int
    amount:float=Field(gt=0)
    description:str|None=None
@app.post("/api/transfer")
def transfer(x:Transfer):
    if x.from_account_id==x.to_account_id:raise HTTPException(400,detail="Accounts must be different")
    return package_call("begin banking_pkg.transfer(:f,:t,:n,:d); end;",{"f":x.from_account_id,"t":x.to_account_id,"n":x.amount,"d":x.description or "Transfer via FinTrust"})
def package_call(sql,b):
    try:
        with conn() as c:
            with c.cursor() as q:q.execute(sql,b)
            c.commit()
        return {"message":"Operation committed"}
    except Exception as e:raise HTTPException(400,detail=str(e))
