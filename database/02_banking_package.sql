CREATE OR REPLACE PACKAGE banking_pkg AS
 PROCEDURE create_account(p_customer_id IN customers.customer_id%TYPE,
  p_account_type IN bank_accounts.account_type%TYPE,p_opening_balance IN bank_accounts.balance%TYPE,
  p_account_number IN bank_accounts.account_number%TYPE,p_account_id OUT bank_accounts.account_id%TYPE);
 PROCEDURE deposit(p_account_id IN bank_accounts.account_id%TYPE,p_amount IN NUMBER,p_description IN VARCHAR2 DEFAULT 'Deposit');
 PROCEDURE withdraw(p_account_id IN bank_accounts.account_id%TYPE,p_amount IN NUMBER,p_description IN VARCHAR2 DEFAULT 'Withdrawal');
 PROCEDURE transfer(p_from_account_id IN NUMBER,p_to_account_id IN NUMBER,p_amount IN NUMBER,p_description IN VARCHAR2 DEFAULT 'Fund transfer');
 FUNCTION get_balance(p_account_id IN NUMBER) RETURN NUMBER;
 PROCEDURE report_low_balance(p_threshold IN NUMBER DEFAULT 2000);
END banking_pkg;
/
CREATE OR REPLACE PACKAGE BODY banking_pkg AS
 PROCEDURE create_account(p_customer_id IN customers.customer_id%TYPE,p_account_type IN bank_accounts.account_type%TYPE,
  p_opening_balance IN bank_accounts.balance%TYPE,p_account_number IN bank_accounts.account_number%TYPE,
  p_account_id OUT bank_accounts.account_id%TYPE) IS
  v_count NUMBER;
 BEGIN
  IF p_opening_balance < 0 THEN RAISE_APPLICATION_ERROR(-20001,'Opening balance cannot be negative.'); END IF;
  IF p_account_type NOT IN ('SAVINGS','CURRENT') THEN RAISE_APPLICATION_ERROR(-20002,'Invalid account type.'); END IF;
  SELECT COUNT(*) INTO v_count FROM customers WHERE customer_id=p_customer_id;
  IF v_count=0 THEN RAISE_APPLICATION_ERROR(-20003,'Customer does not exist.'); END IF;
  INSERT INTO bank_accounts(customer_id,account_type,balance,account_number,status)
  VALUES(p_customer_id,p_account_type,p_opening_balance,p_account_number,'ACTIVE')
  RETURNING account_id INTO p_account_id;
 END create_account;

 PROCEDURE deposit(p_account_id IN bank_accounts.account_id%TYPE,p_amount IN NUMBER,p_description IN VARCHAR2 DEFAULT 'Deposit') IS
  v_status bank_accounts.status%TYPE; v_ref VARCHAR2(40):=RAWTOHEX(SYS_GUID());
 BEGIN
  IF p_amount<=0 THEN RAISE_APPLICATION_ERROR(-20004,'Amount must be greater than zero.'); END IF;
  SELECT status INTO v_status FROM bank_accounts WHERE account_id=p_account_id FOR UPDATE;
  IF v_status<>'ACTIVE' THEN RAISE_APPLICATION_ERROR(-20005,'Account is not active.'); END IF;
  UPDATE bank_accounts SET balance=balance+p_amount WHERE account_id=p_account_id;
  INSERT INTO bank_transactions(account_id,transaction_type,amount,description,reference_number)
  VALUES(p_account_id,'DEPOSIT',p_amount,p_description,v_ref);
 EXCEPTION WHEN NO_DATA_FOUND THEN RAISE_APPLICATION_ERROR(-20006,'Account not found.');
 END deposit;

 PROCEDURE withdraw(p_account_id IN bank_accounts.account_id%TYPE,p_amount IN NUMBER,p_description IN VARCHAR2 DEFAULT 'Withdrawal') IS
  v_balance bank_accounts.balance%TYPE; v_status bank_accounts.status%TYPE; v_ref VARCHAR2(40):=RAWTOHEX(SYS_GUID());
 BEGIN
  IF p_amount<=0 THEN RAISE_APPLICATION_ERROR(-20007,'Amount must be greater than zero.'); END IF;
  SELECT balance,status INTO v_balance,v_status FROM bank_accounts WHERE account_id=p_account_id FOR UPDATE;
  IF v_status<>'ACTIVE' THEN RAISE_APPLICATION_ERROR(-20008,'Account is not active.'); END IF;
  IF v_balance<p_amount THEN RAISE_APPLICATION_ERROR(-20009,'Insufficient funds.'); END IF;
  UPDATE bank_accounts SET balance=balance-p_amount WHERE account_id=p_account_id;
  INSERT INTO bank_transactions(account_id,transaction_type,amount,description,reference_number)
  VALUES(p_account_id,'WITHDRAWAL',p_amount,p_description,v_ref);
 EXCEPTION WHEN NO_DATA_FOUND THEN RAISE_APPLICATION_ERROR(-20010,'Account not found.');
 END withdraw;

 PROCEDURE transfer(p_from_account_id IN NUMBER,p_to_account_id IN NUMBER,p_amount IN NUMBER,p_description IN VARCHAR2 DEFAULT 'Fund transfer') IS
  v_balance NUMBER; v_from_status VARCHAR2(10); v_to_status VARCHAR2(10);
  v_first NUMBER; v_second NUMBER; v_dummy NUMBER; v_ref VARCHAR2(40):=RAWTOHEX(SYS_GUID());
 BEGIN
  IF p_from_account_id=p_to_account_id THEN RAISE_APPLICATION_ERROR(-20011,'Accounts must be different.'); END IF;
  IF p_amount<=0 THEN RAISE_APPLICATION_ERROR(-20012,'Amount must be greater than zero.'); END IF;
  v_first:=LEAST(p_from_account_id,p_to_account_id); v_second:=GREATEST(p_from_account_id,p_to_account_id);
  SELECT account_id INTO v_dummy FROM bank_accounts WHERE account_id=v_first FOR UPDATE;
  SELECT account_id INTO v_dummy FROM bank_accounts WHERE account_id=v_second FOR UPDATE;
  SELECT balance,status INTO v_balance,v_from_status FROM bank_accounts WHERE account_id=p_from_account_id;
  SELECT status INTO v_to_status FROM bank_accounts WHERE account_id=p_to_account_id;
  IF v_from_status<>'ACTIVE' OR v_to_status<>'ACTIVE' THEN RAISE_APPLICATION_ERROR(-20013,'Both accounts must be active.'); END IF;
  IF v_balance<p_amount THEN RAISE_APPLICATION_ERROR(-20014,'Insufficient funds.'); END IF;
  UPDATE bank_accounts SET balance=balance-p_amount WHERE account_id=p_from_account_id;
  UPDATE bank_accounts SET balance=balance+p_amount WHERE account_id=p_to_account_id;
  INSERT INTO bank_transactions(account_id,transaction_type,amount,description,reference_number,related_account_id)
  VALUES(p_from_account_id,'TRANSFER_OUT',p_amount,p_description,v_ref,p_to_account_id);
  INSERT INTO bank_transactions(account_id,transaction_type,amount,description,reference_number,related_account_id)
  VALUES(p_to_account_id,'TRANSFER_IN',p_amount,p_description,v_ref,p_from_account_id);
 EXCEPTION WHEN NO_DATA_FOUND THEN RAISE_APPLICATION_ERROR(-20015,'Source or destination account not found.');
 END transfer;

 FUNCTION get_balance(p_account_id IN NUMBER) RETURN NUMBER IS v_balance NUMBER;
 BEGIN SELECT balance INTO v_balance FROM bank_accounts WHERE account_id=p_account_id; RETURN v_balance;
 EXCEPTION WHEN NO_DATA_FOUND THEN RAISE_APPLICATION_ERROR(-20016,'Account not found.'); END get_balance;

 PROCEDURE report_low_balance(p_threshold IN NUMBER DEFAULT 2000) IS
  CURSOR c_low IS SELECT a.account_number,c.full_name,a.balance FROM bank_accounts a JOIN customers c ON c.customer_id=a.customer_id
   WHERE a.status='ACTIVE' AND a.balance<p_threshold ORDER BY a.balance;
  v_row c_low%ROWTYPE;
 BEGIN
  DBMS_OUTPUT.PUT_LINE('Accounts below '||p_threshold);
  OPEN c_low; LOOP FETCH c_low INTO v_row; EXIT WHEN c_low%NOTFOUND;
   DBMS_OUTPUT.PUT_LINE(v_row.account_number||' | '||v_row.full_name||' | '||v_row.balance);
  END LOOP; CLOSE c_low;
 EXCEPTION WHEN OTHERS THEN IF c_low%ISOPEN THEN CLOSE c_low; END IF; RAISE;
 END report_low_balance;
END banking_pkg;
/
