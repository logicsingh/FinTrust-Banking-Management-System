DECLARE v_count NUMBER;
BEGIN
 SELECT COUNT(*) INTO v_count FROM customers;
 IF v_count=0 THEN
  INSERT INTO customers(full_name,email,phone) VALUES('Aarav Sharma','aarav.sharma@example.test','9000000001');
  INSERT INTO customers(full_name,email,phone) VALUES('Meera Kapoor','meera.kapoor@example.test','9000000002');
  INSERT INTO customers(full_name,email,phone) VALUES('Kabir Singh','kabir.singh@example.test','9000000003');
  INSERT INTO customers(full_name,email,phone) VALUES('Anaya Verma','anaya.verma@example.test','9000000004');
  INSERT INTO bank_accounts(customer_id,account_number,account_type,balance,status)
   SELECT customer_id,'FT-DEMO-1001','SAVINGS',11600,'ACTIVE' FROM customers WHERE email='aarav.sharma@example.test';
  INSERT INTO bank_accounts(customer_id,account_number,account_type,balance,status)
   SELECT customer_id,'FT-DEMO-1002','SAVINGS',9000,'ACTIVE' FROM customers WHERE email='meera.kapoor@example.test';
  INSERT INTO bank_accounts(customer_id,account_number,account_type,balance,status)
   SELECT customer_id,'FT-DEMO-1003','CURRENT',23500,'ACTIVE' FROM customers WHERE email='kabir.singh@example.test';
  INSERT INTO bank_accounts(customer_id,account_number,account_type,balance,status)
   SELECT customer_id,'FT-DEMO-1004','SAVINGS',4200,'ACTIVE' FROM customers WHERE email='anaya.verma@example.test';
  COMMIT;
 END IF;
END;
/
