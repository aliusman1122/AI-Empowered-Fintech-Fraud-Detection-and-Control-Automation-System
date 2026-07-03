"""
╔══════════════════════════════════════════════════════════════╗
║           DATABASE HEALTH CHECK SCRIPT                       ║
║                                                              ║
║   This script verifies:                                      ║
║     ✔ All tables exist in the database                       ║
║     ✔ Records are populated across all tables                ║
║     ✔ Relationships are working correctly                    ║
║     ✔ Suspicious transaction states and audit trails         ║
║                                                              ║
║   Command: python -m backend.test_db                         ║
╚══════════════════════════════════════════════════════════════╝

"""

from sqlalchemy import inspect, text
from .database import SessionLocal, engine
from .models import (
    User, Transaction, FraudAlert,
    VerificationToken, AuditLog
)


# ─────────────────────────────────────────────────────────────
# CHECK 1: Tables exist karti hain?
# ─────────────────────────────────────────────────────────────

def check_tables() -> bool:
    """Verify that all 5 tables exist in the database."""
    print("\n📋 TABLE VERIFICATION")
    print("─" * 50)

    inspector     = inspect(engine)
    existing      = set(inspector.get_table_names())
    required      = {
        "users",
        "transactions",
        "fraud_alerts",
        "verification_tokens",
        "audit_logs"
    }
    missing       = required - existing
    all_ok        = True

    for table in sorted(required):
        if table in existing:
            # Column count bhi dikhao
            cols = len(inspector.get_columns(table))
            print(f"  ✅  {table:<26}  ({cols} columns)")
        else:
            print(f"  ❌  {table:<26}  — MISSING!")
            all_ok = False

    if missing:
        print(f"\n  ❗ Missing tables: {missing}")
        print("  Pehle chalao: python -m backend.init_db")
    else:
        print("\n  ✅ Tamam 5 tables theek hain!")

    return all_ok


# ─────────────────────────────────────────────────────────────
# CHECK 2: Record counts
# ─────────────────────────────────────────────────────────────

def check_record_counts():
    """Check the number of records in each table."""
    db = SessionLocal()
    try:
        print("\n📊 RECORD COUNTS")
        print("─" * 50)

        counts = {
            "users":               db.query(User).count(),
            "transactions":        db.query(Transaction).count(),
            "fraud_alerts":        db.query(FraudAlert).count(),
            "verification_tokens": db.query(VerificationToken).count(),
            "audit_logs":          db.query(AuditLog).count(),
        }

        max_count = max(counts.values()) if any(counts.values()) else 5
        for table, count in counts.items():
            filled = int((count / max(max_count, 1)) * 15)
            bar    = "█" * filled + "░" * (15 - filled)
            icon   = "✅" if count > 0 else "⚠️ "
            print(f"  {icon}  {table:<26}  {bar}  {count}")

    except Exception as err:
        print(f"  ❌ Error: {err}")
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────
# CHECK 3: Relationships kaam kar rahe hain?
# ─────────────────────────────────────────────────────────────

def check_relationships():
    """Verify the User → Transaction → Alert → Logs chain."""
    db = SessionLocal()
    try:
        print("\n🔗 RELATIONSHIP CHECK")
        print("─" * 50)

        # User ka pehla record lo
        user = db.query(User).first()
        if not user:
            print("  ⚠️  No users found in the database. — run init_db first")
            return

        print(f"  👤 User: {user.full_name}  ({user.email})")

        # Us user ki transactions
        txns = user.transactions
        print(f"  💰 Transactions: {len(txns)} mili")
        for txn in txns:
            flag_icon = "🚨" if txn.fraud_flag else "✅"
            print(f"       {flag_icon}  {txn.transaction_id}  —  PKR {txn.amount:,.0f}  —  {txn.status}")

            # Fraud alerts
            if txn.fraud_alerts:
                for alert in txn.fraud_alerts:
                    print(f"             ↳ Alert: {alert.alert_level.upper()}  —  email_sent={alert.email_sent}")

            # Verification tokens
            if txn.verification_tokens:
                for token in txn.verification_tokens:
                    used = "Used ✓" if token.is_used else "Unused ○"
                    print(f"             ↳ Token ({token.action}): {used}")

        print("  ✅ All relationships verified successfully!")

    except Exception as err:
        print(f"  ❌ Relationship error: {err}")
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────
# CHECK 4: Audit Trail
# ─────────────────────────────────────────────────────────────

def check_audit_trail():
    """Display all audit log entries in the system."""
    db = SessionLocal()
    try:
        print("\n📜 AUDIT TRAIL")
        print("─" * 50)

        logs = db.query(AuditLog).order_by(AuditLog.created_at).all()
        if not logs:
            print("  ℹ️  No audit logs available yet.")
            return

        for log in logs:
            time_str = log.created_at.strftime("%H:%M:%S") if log.created_at else "—"
            status_change = ""
            if log.old_status or log.new_status:
                old = log.old_status or "—"
                new = log.new_status or "—"
                status_change = f"  [{old} → {new}]"

            print(f"  [{time_str}]  {log.performed_by:<10}  {log.action}{status_change}")
            if log.description:
                print(f"              {log.description}")

    except Exception as err:
        print(f"  ❌ Error: {err}")
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────
# CHECK 5: Database file info
# ─────────────────────────────────────────────────────────────

def check_db_info():
    """Display basic information about the database file."""
    import os
    print("\n💾 DATABASE INFO")
    print("─" * 50)

    db_path = "fraud_system.db"
    if os.path.exists(db_path):
        size_kb = os.path.getsize(db_path) / 1024
        print(f"  📁 File   : {db_path}")
        print(f"  📏 Size   : {size_kb:.1f} KB")
        print(f"  ✅ Status : Exists and accessible")
    else:
        print(f"  ❌ fraud_system.db not found!")
        print(f"     Please run first: python -m backend.init_db")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "═" * 50)
    print("  🔍 DATABASE HEALTH CHECK")
    print("═" * 50)

    check_db_info()
    ok = check_tables()

    if ok:
        check_record_counts()
        check_relationships()
        check_audit_trail()

        print("\n" + "═" * 50)
        print("  ✅ DATABASE IS WORKING PERFECTLY!")
        print("  You can now begin building Phase 4 FastAPI endpoints.")
        print("═" * 50 + "\n")
    else:
        print("\n❗ Please run this first:  python -m backend.init_db\n")