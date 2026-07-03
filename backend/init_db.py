"""
╔══════════════════════════════════════════════════════════════╗
║           DATABASE INITIALIZATION SCRIPT                     ║
║                                                              ║
║   This Script do 3 things:                                   ║
║     1. Create the Database tables                            ║ 
║     2. Insert Test data (seed data)                          ║
║     3. Print the Status report                               ║
║                                                              ║
║   Command: python -m backend.init_db                         ║
║                                                              ║
║   Only runs once                                             ║
╚══════════════════════════════════════════════════════════════╝
"""

import uuid
from datetime import datetime, timedelta, timezone

from .database import create_tables, SessionLocal
from .models import (
    User, Transaction, FraudAlert,
    VerificationToken, AuditLog,
    TransactionStatus, AlertLevel
)


# ─────────────────────────────────────────────────────────────
# Helper function: Alert level decide karna probability se
# ─────────────────────────────────────────────────────────────

def get_alert_level(probability: float) -> str:
    """Return alert level according to Fraud probability."""
    if probability >= 0.90:
        return AlertLevel.CRITICAL.value
    elif probability >= 0.70:
        return AlertLevel.HIGH.value
    elif probability >= 0.50:
        return AlertLevel.MEDIUM.value
    else:
        return AlertLevel.LOW.value


# ─────────────────────────────────────────────────────────────
# Seed Data
# ─────────────────────────────────────────────────────────────

def seed_test_data():
    """
    Database mein .

    Which things are inserted:
      ✔ 1 test user
      ✔ 1 suspicious transaction (status: pending)
      ✔ 1 normal transaction (status: auto_approved)
      ✔ 1 fraud alert (for the suspicious)
      ✔ 2 verification tokens (approve + reject)
      ✔ 3 audit log entries
    """
    db = SessionLocal()

    try:
        print("\n" + "═" * 60)
        print("  SEED DATA INSERTING ...")
        print("═" * 60 + "\n")

        # ──────────────────────────────────────────────────────
        # STEP 1: Creating test user
        # ──────────────────────────────────────────────────────
        print("👤 STEP 1: Creating test user ...")

        existing = db.query(User).filter(User.email == "ali.usman@test.com").first()
        if existing:
            print(f"   ⚠️  User already exist (id={existing.id}) — skip")
            user = existing
        else:
            user = User(
                email     = "ali.usman@test.com",
                full_name = "Ali Usman",
                phone     = "+92-300-1234567"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"   ✅ Create User!  id={user.id}  email={user.email}")

        # ──────────────────────────────────────────────────────
        # STEP 2:  Creating suspicious transaction 
        # ──────────────────────────────────────────────────────
        print("\n🚨 STEP 2: Creating suspicious transaction ...")

        fraud_txn_id = f"TXN-{str(uuid.uuid4())[:8].upper()}"
        fraud_txn = Transaction(
            transaction_id    = fraud_txn_id,
            user_id           = user.id,
            amount            = 85_000.00,            # PKR 85,000 — bari raqam
            merchant_category = "international_wire",  # International wire = high risk
            transaction_hour  = 3,                    # Raat 3 baje — suspicious!
            device_risk_score = 0.91,                 # Bohot zyada risky device
            ip_risk_score     = 0.87,                 # Risky IP address
            fraud_probability = 0.89,                 # ML ne 89% fraud bola
            fraud_flag        = True,                  # Fraud suspected = True
            status            = TransactionStatus.PENDING.value,
            reason_codes      = (
                '["High device risk score (0.91)", '
                '"Unusual transaction hour (3 AM)", '
                '"High IP risk score (0.87)", '
                '"International wire transfer"]'
            )
        )
        db.add(fraud_txn)
        db.commit()
        db.refresh(fraud_txn)
        print(f"   ✅ Create Suspicious transaction!")
        print(f"      ID     : {fraud_txn.transaction_id}")
        print(f"      Amount : PKR {fraud_txn.amount:,.0f}")
        print(f"      Score  : {fraud_txn.fraud_probability:.0%} fraud probability")
        print(f"      Status : {fraud_txn.status}")

        # ──────────────────────────────────────────────────────
        # STEP 3: Creating fraud alert 
        # ──────────────────────────────────────────────────────
        print("\n🔔 STEP 3: Creating fraud alert ...")

        alert = FraudAlert(
            transaction_id      = fraud_txn.id,
            alert_level         = get_alert_level(fraud_txn.fraud_probability),
            reason_codes        = fraud_txn.reason_codes,
            n8n_webhook_sent    = False,     # Abhi n8n ko signal nahi gaya
            n8n_webhook_sent_at = None,
            n8n_response_status = None,
            email_sent          = False,     # Abhi email nahi gayi
            email_sent_at       = None,
            email_recipient     = user.email
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        print(f"   ✅ Creating fraud alert!")
        print(f"      Level   : {alert.alert_level.upper()}")
        print(f"      To      : {alert.email_recipient}")
        print(f"      Webhook : {'Sent' if alert.n8n_webhook_sent else '(Enabled)'}")

        # ──────────────────────────────────────────────────────
        # STEP 4: Verification Tokens banana
        # ──────────────────────────────────────────────────────
        print("\n🔑 STEP 4: Creating Verification tokens ...")

        now = datetime.now(timezone.utc)
        expire_time = now + timedelta(hours=24)  # 24/7 validity

        approve_token = VerificationToken(
            transaction_id = fraud_txn.id,
            token          = str(uuid.uuid4()),
            action         = "approve",
            expires_at     = expire_time,
            is_used        = False
        )
        reject_token = VerificationToken(
            transaction_id = fraud_txn.id,
            token          = str(uuid.uuid4()),
            action         = "reject",
            expires_at     = expire_time,
            is_used        = False
        )
        db.add_all([approve_token, reject_token])
        db.commit()
        print(f"   ✅ Create two tokens!")
        print(f"      Approve token: {approve_token.token[:20]}...")
        print(f"      Reject  token: {reject_token.token[:20]}...")
        print(f"      Expire  at   : {expire_time.strftime('%Y-%m-%d %H:%M UTC')}")

        # ──────────────────────────────────────────────────────
        # STEP 5: Creating normal transaction
        # ──────────────────────────────────────────────────────
        print("\n✅ STEP 5: Creating Normal (safe) transaction ...")

        normal_txn_id = f"TXN-{str(uuid.uuid4())[:8].upper()}"
        normal_txn = Transaction(
            transaction_id    = normal_txn_id,
            user_id           = user.id,
            amount            = 1_200.00,        # PKR 1,200 — normal amount
            merchant_category = "grocery",        # Grocery = low risk
            transaction_hour  = 14,               # Dopahar 2 baje — normal time
            device_risk_score = 0.05,             # Safe device
            ip_risk_score     = 0.03,             # Safe IP
            fraud_probability = 0.08,             # Sirf 8% fraud probability
            fraud_flag        = False,             # Safe = False
            status            = TransactionStatus.AUTO_APPROVED.value,
            reason_codes      = '[]'
        )
        db.add(normal_txn)
        db.commit()
        db.refresh(normal_txn)
        print(f"   ✅ Creating normal transaction!")
        print(f"      ID     : {normal_txn.transaction_id}")
        print(f"      Amount : PKR {normal_txn.amount:,.0f}")
        print(f"      Score  : {normal_txn.fraud_probability:.0%} fraud probability")
        print(f"      Status : {normal_txn.status}")

        # ──────────────────────────────────────────────────────
        # STEP 6: Audit Logs banana
        # ──────────────────────────────────────────────────────
        print("\n📋 STEP 6: Creating Audit log entries ...")

        audit_entries = [
            AuditLog(
                transaction_id = fraud_txn.id,
                action         = "TRANSACTION_CREATED",
                description    = "New transaction submit from dashboard",
                old_status     = None,
                new_status     = TransactionStatus.PENDING.value,
                performed_by   = "system",
                ip_address     = "192.168.1.1"
            ),
            AuditLog(
                transaction_id = fraud_txn.id,
                action         = "ML_SCORE_ASSIGNED",
                description    = f"Fraud probability assign by ML model: 89%",
                old_status     = TransactionStatus.PENDING.value,
                new_status     = TransactionStatus.PENDING.value,
                performed_by   = "ml_model",
            ),
            AuditLog(
                transaction_id = fraud_txn.id,
                action         = "FRAUD_ALERT_TRIGGERED",
                description    = "Score >= threshold — fraud alert creation, n8n webhook pending",
                old_status     = TransactionStatus.PENDING.value,
                new_status     = TransactionStatus.PENDING.value,
                performed_by   = "ml_model"
            ),
            AuditLog(
                transaction_id = normal_txn.id,
                action         = "TRANSACTION_AUTO_APPROVED",
                description    = "ML score < 0.35 threshold — automatically approved",
                old_status     = None,
                new_status     = TransactionStatus.AUTO_APPROVED.value,
                performed_by   = "ml_model"
            ),
        ]

        db.add_all(audit_entries)
        db.commit()
        print(f"   ✅ {len(audit_entries)} audit log entries bane!")

        # ──────────────────────────────────────────────────────
        # FINAL SUMMARY
        # ──────────────────────────────────────────────────────
        print("\n" + "═" * 60)
        print("  🎉 DATABASE SEED COMPLETE!")
        print("═" * 60)
        print(f"  👤  Users:               1")
        print(f"  💰  Transactions:        2  (1 suspicious | 1 normal)")
        print(f"  🚨  Fraud Alerts:        1  (CRITICAL level)")
        print(f"  🔑  Verification Tokens: 2  (approve + reject)")
        print(f"  📋  Audit Logs:          {len(audit_entries)}")
        print("═" * 60)
        print("\n  Now run the: python -m backend.test_db")
        print("  Moves to: streamlit run app.py\n")

    except Exception as err:
        print(f"\n❌ Error: {err}")
        db.rollback()
        raise
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────
# MAIN — Run the: python -m backend.init_db
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n🚀 INITIALIZING DATABASE ...")
    create_tables()
    seed_test_data()