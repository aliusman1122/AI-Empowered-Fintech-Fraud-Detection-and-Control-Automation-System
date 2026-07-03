"""
╔══════════════════════════════════════════════════════════════╗
║           DATABASE CONNECTION SETUP                          ║
║   Connect the SQLite database with SQLAlchemy                ║
║                                                              ║
║   Why to choose SQLite:                                      ║
║     ✔ No need to Installation (built-in in python)           ║
║     ✔ There is complete database in a simple .db file        ║
║     ✔ Easy to update in PostgreSQL later                     ║
╚══════════════════════════════════════════════════════════════╝
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# ─────────────────────────────────────────────────────────────
# DATABASE URL — define the location of the database file
# ─────────────────────────────────────────────────────────────
#
# Default: SQLite file "fraud_system.db" project root    
# Production: Set the environment variable DATABASE_URL for PostgreSQL 
#
# SQLite format  : sqlite:///./fraud_system.db
# PostgreSQL format: postgresql://user:password@localhost:5432/fraud_db
#
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fraud_system.db")


# ─────────────────────────────────────────────────────────────
# ENGINE — Actual database connection
# ─────────────────────────────────────────────────────────────
#
# Engine = method to connect to the database
# connect_args: Allow the multi-threading for SQLite
#               (FastAPI hendle with multiple requests)
#
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Only require for SQLite 
    echo=False   # debug
)


# ─────────────────────────────────────────────────────────────
# SESSION FACTORY — Tools for working with Database
# ─────────────────────────────────────────────────────────────
#
# Session = 1 "conversation" with database
# Every API makes a new session for every request
# Request end → session automatically close
#
SessionLocal = sessionmaker(
    autocommit=False,   # commit manually (for safety )
    autoflush=False,    # flush manually (for control )
    bind=engine
)


# ─────────────────────────────────────────────────────────────
# BASE CLASS — Every database table class will inherit from this
# ─────────────────────────────────────────────────────────────
#
# when you create a new table class, make sure
# it inherits from Base, like:
# class User(Base):
# it will automatically register the table with SQLAlchemy

Base = declarative_base()


# ─────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def get_db():
    """
    FastAPI Dependency Injection function.

    How it works:
      - For every request, a new database session is created
      - Request handler gets the session object (db) via 'yield'
      - Request ends → session is automatically closed (cleanup)
      - 'yield' is used to provide the session to the request handler

    Example usage in FastAPI route:
      @app.get("/transactions")
      def get_transactions(db: Session = Depends(get_db)):
          return db.query(Transaction).all()
    """
    db = SessionLocal()
    try:
        yield db          # ← Session object is provided to the request handler
    finally:
        db.close()        # ← Session is closed after the request is completed


def create_tables():
    """
    Create the tables in database.

    On first run:
      - Create the SQLite file "fraud_system.db" in project root
      - Create 5 tables inside the database file

    On subsequent runs:
      - No changes will be made if tables already exist
    Note:
      - SQLAlchemy use the "CREATE TABLE IF NOT EXISTS" 

    When to call this function:
      - only once, when the application is first deployed
      - Run: python -m backend.init_db
    """
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully!")
    print(f"   Database file: fraud_system.db")