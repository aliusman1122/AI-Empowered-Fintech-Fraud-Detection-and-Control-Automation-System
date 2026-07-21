"""sync schema with fixes

Revision ID: 002_schema_sync
Revises: 5eca4c7ae2fb
Create Date: 2026-07-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_schema_sync'
down_revision = '5eca4c7ae2fb'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # ── TRANSACTION TYPE CHANGES ────────────────────────────────────
    op.alter_column('transactions', 'user_id', existing_type=sa.INTEGER(), nullable=True)

    # Removed redundant op.add_column steps for 'risk_level', 'risk_score', etc., as they are 
    # already created in the '5eca4c7ae2fb_initial_schema.py' migration.

    # ── 3-STEP REASON_CODES MIGRATION (TRANSACTIONS) ───────────────
    # (1) Add new reason_codes_jsonb JSONB column
    op.add_column('transactions', sa.Column('reason_codes_jsonb', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    
    # (2) Migrate existing text data to JSONB representation where it exists
    # If the table is completely empty, this UPDATE affects 0 rows gracefully
    op.execute(
        "UPDATE transactions "
        "SET reason_codes_jsonb = reason_codes::jsonb "
        "WHERE reason_codes IS NOT NULL;"
    )

    # (3) Drop old column and rename new one
    op.drop_column('transactions', 'reason_codes')
    op.alter_column('transactions', 'reason_codes_jsonb', new_column_name='reason_codes')


    # ── 3-STEP REASON_CODES MIGRATION (FRAUD ALERTS) ───────────────
    op.add_column('fraud_alerts', sa.Column('reason_codes_jsonb', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    
    op.execute(
        "UPDATE fraud_alerts "
        "SET reason_codes_jsonb = reason_codes::jsonb "
        "WHERE reason_codes IS NOT NULL;"
    )

    op.drop_column('fraud_alerts', 'reason_codes')
    op.alter_column('fraud_alerts', 'reason_codes_jsonb', new_column_name='reason_codes')

def downgrade() -> None:
    # Reverse everything
    op.add_column('fraud_alerts', sa.Column('reason_codes_text', sa.TEXT(), nullable=True))
    op.execute("UPDATE fraud_alerts SET reason_codes_text = reason_codes::text;")
    op.drop_column('fraud_alerts', 'reason_codes')
    op.alter_column('fraud_alerts', 'reason_codes_text', new_column_name='reason_codes')

    op.add_column('transactions', sa.Column('reason_codes_text', sa.TEXT(), nullable=True))
    op.execute("UPDATE transactions SET reason_codes_text = reason_codes::text;")
    op.drop_column('transactions', 'reason_codes')
    op.alter_column('transactions', 'reason_codes_text', new_column_name='reason_codes')

    # Removed redundant op.drop_column steps for 'verification_token', 'user_email', etc.
    op.alter_column('transactions', 'user_id', existing_type=sa.INTEGER(), nullable=False)
