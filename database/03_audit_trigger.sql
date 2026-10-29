CREATE OR REPLACE TRIGGER trg_balance_audit
AFTER UPDATE OF balance ON bank_accounts
FOR EACH ROW WHEN (OLD.balance <> NEW.balance)
BEGIN
 INSERT INTO balance_audit_log(account_id,old_balance,new_balance,action_type,changed_at)
 VALUES(:NEW.account_id,:OLD.balance,:NEW.balance,
  CASE WHEN :NEW.balance>:OLD.balance THEN 'BALANCE_INCREASE' ELSE 'BALANCE_DECREASE' END,SYSTIMESTAMP);
END;
/
