-- Run manually after schema/package/seed scripts. Adjust IDs to match your schema.
SET SERVEROUTPUT ON;
DECLARE v_account_id NUMBER;
BEGIN
 banking_pkg.create_account(1,'SAVINGS',1000,'FT-DEMO-TEST-2001',v_account_id);
 DBMS_OUTPUT.PUT_LINE('Created account ID: '||v_account_id);
 ROLLBACK;
END;
/
-- Deposit example (run separately and ROLLBACK if you do not want to keep the test):
-- BEGIN banking_pkg.deposit(1, 100, 'PL/SQL test deposit'); ROLLBACK; END;
-- /
-- Low-balance cursor:
-- BEGIN banking_pkg.report_low_balance(5000); END;
-- /
