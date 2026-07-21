import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 1. Import our models and engine
import sys
import os

# Env variables load karne ke liye taake direct .env file read ho sakay
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.database import Base
from backend.models import User, Transaction, FraudAlert, VerificationToken, AuditLog, RefreshToken

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Sab se pehle check karein ke terminal/env mein kya url para hai, warna .env file se uthayein
ENV_DATABASE_URL = os.getenv("DATABASE_URL")

x_args = context.get_x_argument(as_dictionary=True)
if 'db_url' in x_args:
    config.set_main_option("sqlalchemy.url", x_args['db_url'])
elif ENV_DATABASE_URL:
    # Agay backend/database.py mein galti ho bhi, toh yeh .env wala path force apply karega
    config.set_main_option("sqlalchemy.url", ENV_DATABASE_URL)
else:
    # Fallback backup ke taur par agar kuch na mile
    from backend.database import DATABASE_URL
    config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# target metadata for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()