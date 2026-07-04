import os
import sys
import shutil
from pathlib import Path

# Directories
root = Path(r"c:\D_volume\FYP\Projects\AI-Empowered-Fintech-Fraud-Detection-and-Control-Automation-System")
os.chdir(root)

# 1. Fix Directories & Files
(root / "n8n" / "workflows").mkdir(parents=True, exist_ok=True)
(root / "docs").mkdir(exist_ok=True)
(root / "frontend").mkdir(exist_ok=True)

workflow_json = root / "FraudAlertWorkflow.json"
if workflow_json.exists():
    shutil.move(str(workflow_json), str(root / "n8n" / "workflows" / "FraudAlertWorkflow.json"))

with open(root / ".gitignore", "a") as f:
    f.write("\nnode_modules/\nfraud_engine.db\n*.db\n.env\n")


# 3. Read models.py and rewrite the Transaction class
models_file = root / "backend" / "models.py"
content = models_file.read_text("utf-8")

# Refactoring the Transaction class to match main.py
# First replace the user_id nullable=False to nullable=True
content = content.replace(
    'user_id        = Column(Integer,   ForeignKey("users.id"), nullable=False)',
    'user_id        = Column(Integer,   ForeignKey("users.id"), nullable=True)'
)

# Insert the missing columns after reason_codes
missing_cols = """    reason_codes       = Column(Text,    nullable=True)   # JSON string
    risk_level         = Column(String(20),   nullable=True)
    risk_score         = Column(Float,        nullable=True)
    transaction_type   = Column(String(50),   nullable=True)
    country            = Column(String(50),   nullable=True)
    user_email         = Column(String(255),  nullable=True)
    verification_token = Column(String(100),  nullable=True)"""
content = content.replace('    reason_codes       = Column(Text,    nullable=True)   # JSON string', missing_cols)

models_file.write_text(content, "utf-8")
print("models.py patched.")

# 4. Read main.py and rewrite references to models.transaction and models.FraudLog
main_file = root / "backend" / "main.py"
main_content = main_file.read_text("utf-8")

# Fix 1: change FraudLog to AuditLog
main_content = main_content.replace('models.FraudLog', 'models.AuditLog')

# Fix 2: the kwargs in predict_transaction
# We need to change id=transaction_id to transaction_id=transaction_id
# And add user_id=None
transaction_create_old = '''        db_transaction = models.Transaction(
            id                = transaction_id,'''
transaction_create_new = '''        db_transaction = models.Transaction(
            transaction_id    = transaction_id,
            user_id           = None,'''
if transaction_create_old in main_content:
    main_content = main_content.replace(transaction_create_old, transaction_create_new)

# Fix 3: In the audit log entry, AuditLog expects transaction_id to be an Integer, but we only have UUID atm.
# Wait, AuditLog has: transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
# `db_transaction.id` will be populated after `db.add(db_transaction) \n db.flush()`
# So we need to insert a db.flush() before creating the log_entry and use db_transaction.id
log_entry_old = '''        db.add(db_transaction)

        # ── Step 8: Write audit log ────────────────────────────────────────
        action = "AUTO_APPROVED" if not fraud_flag else (
            "EMAIL_QUEUED" if transaction.user_email else "FLAGGED"
        )
        log_entry = models.AuditLog(
            transaction_id = transaction_id,'''
log_entry_new = '''        db.add(db_transaction)
        db.flush()

        # ── Step 8: Write audit log ────────────────────────────────────────
        action = "AUTO_APPROVED" if not fraud_flag else (
            "EMAIL_QUEUED" if transaction.user_email else "FLAGGED"
        )
        log_entry = models.AuditLog(
            transaction_id = db_transaction.id,'''
if log_entry_old in main_content:
    main_content = main_content.replace(log_entry_old, log_entry_new)

# Fix 4: Transaction retrieval in lists and status.
# Models.py defines `transaction_id = ...String(50)...`
# main.py does: `filter(models.Transaction.id == transaction_id)`
# We need to change `.id == transaction_id` to `.transaction_id == transaction_id`
main_content = main_content.replace(
    '.filter(models.Transaction.id == transaction_id)',
    '.filter(models.Transaction.transaction_id == transaction_id)'
)
# And the API needs to return `transaction_id = tx.transaction_id` instead of `tx.id`
main_content = main_content.replace(
    'transaction_id    = tx.id,',
    'transaction_id    = tx.transaction_id,'
)

main_file.write_text(main_content, "utf-8")
print("main.py patched.")

print("All fixes applied!")
