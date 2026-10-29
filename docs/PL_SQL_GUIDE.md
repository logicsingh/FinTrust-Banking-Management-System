# PL/SQL concepts
- **Package:** `BANKING_PKG` groups related banking logic.
- **Procedures:** `CREATE_ACCOUNT`, `DEPOSIT`, `WITHDRAW`, and `TRANSFER` implement banking operations.
- **Function:** `GET_BALANCE` returns an account balance.
- **Explicit cursor:** `REPORT_LOW_BALANCE` fetches accounts below a threshold and uses `DBMS_OUTPUT`.
- **Trigger:** `TRG_BALANCE_AUDIT` records old/new balances after balance updates.
- **Constraints:** primary/foreign keys, unique values, and check constraints protect data integrity.
- **Transactions:** caller commits on success and rolls back on error; transfer changes both accounts in one transaction.
Important: file creation is not proof of compilation. Check `USER_ERRORS` in Oracle.
