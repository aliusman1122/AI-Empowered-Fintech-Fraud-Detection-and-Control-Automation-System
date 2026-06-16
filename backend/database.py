# =============================================================================
# backend/database.py
# =============================================================================
# PURPOSE:
#   This file sets up our database connection using SQLAlchemy.
#   SQLAlchemy is a tool that lets us talk to a database using Python
#   objects instead of raw SQL queries.
#
# DATABASE CHOICE:
#   We use SQLite for now. SQLite stores the entire database in ONE file
#   (fraud_engine.db) on your computer. No separate database server needed.
#   Later (Phase 6) we will switch to PostgreSQL for production.
#
# HOW IT WORKS:
#   1. engine      → The actual connection to the database file
#   2. SessionLocal → A "session" is like a temporary workspace for one request
#   3. Base        → A base class that our database table models inherit from
#   4. get_db()    → A function that opens a session, gives it to the API,
#                    then closes it when the request is done
# =============================================================================

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ─── DATABASE URL ─────────────────────────────────────────────────────────────
# "sqlite:///./fraud_engine.db" means:
#   - Use SQLite driver
#   - Create/open a file named "fraud_engine.db" in the current folder
# When you run the server, this file appears automatically in your project root.
SQLALCHEMY_DATABASE_URL = "sqlite:///./fraud_engine.db"

# ─── ENGINE ──────────────────────────────────────────────────────────────────
# The "engine" is the actual database connection.
# connect_args={"check_same_thread": False} is REQUIRED for SQLite when using
# FastAPI (FastAPI uses multiple threads, SQLite needs this flag to allow it).
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# ─── SESSION FACTORY ─────────────────────────────────────────────────────────
# SessionLocal is a factory (a class) that creates database sessions.
# autocommit=False → We must manually call db.commit() to save changes.
# autoflush=False  → Changes are not automatically sent to DB before queries.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ─── BASE CLASS ───────────────────────────────────────────────────────────────
# All our database table models (in models.py) will inherit from this Base.
# This Base keeps track of all the table definitions so SQLAlchemy can
# create the tables automatically.
Base = declarative_base()


# ─── DEPENDENCY FUNCTION ─────────────────────────────────────────────────────
def get_db():
    """
    FastAPI dependency that provides a database session per request.

    HOW TO USE:
        In any FastAPI route, add this as a parameter:
        async def my_route(db: Session = Depends(get_db)):
            ...

    The "yield" keyword makes this a generator:
        1. Code BEFORE yield: runs at the START of each request (opens session)
        2. yield db: gives the session to the route function
        3. Code AFTER yield: runs at the END of each request (closes session)

    The try/finally ensures the session is ALWAYS closed, even if an error occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
