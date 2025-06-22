"""Initial financial data models

Revision ID: rev_20250617_221122
Revises: 
Create Date: 2025-06-17T22:11:22.184863

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'rev_20250617_221122'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create ingestion_history table
    op.create_table('ingestion_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('source', sa.String(length=50), nullable=False),
    sa.Column('entity_type', sa.String(length=50), nullable=False),
    sa.Column('period_start', sa.DateTime(), nullable=False),
    sa.Column('period_end', sa.DateTime(), nullable=False),
    sa.Column('records_count', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('ingested_at', sa.DateTime(), nullable=True),
    sa.Column('ingestion_metadata', sa.JSON(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_source_entity_period', 'ingestion_history', ['source', 'entity_type', 'period_start', 'period_end'], unique=False)

    # Create general_ledger table
    op.create_table('general_ledger',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('source_id', sa.String(length=100), nullable=False),
    sa.Column('source_type', sa.String(length=50), nullable=False),
    sa.Column('transaction_date', sa.DateTime(), nullable=False),
    sa.Column('posted_date', sa.DateTime(), nullable=True),
    sa.Column('reference_number', sa.String(length=100), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('account_id', sa.String(length=100), nullable=False),
    sa.Column('account_name', sa.String(length=200), nullable=False),
    sa.Column('account_type', sa.String(length=100), nullable=False),
    sa.Column('account_subtype', sa.String(length=100), nullable=True),
    sa.Column('debit_amount', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('credit_amount', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('customer_id', sa.String(length=100), nullable=True),
    sa.Column('customer_name', sa.String(length=200), nullable=True),
    sa.Column('vendor_id', sa.String(length=100), nullable=True),
    sa.Column('vendor_name', sa.String(length=200), nullable=True),
    sa.Column('employee_id', sa.String(length=100), nullable=True),
    sa.Column('employee_name', sa.String(length=200), nullable=True),
    sa.Column('class_id', sa.String(length=100), nullable=True),
    sa.Column('class_name', sa.String(length=200), nullable=True),
    sa.Column('department_id', sa.String(length=100), nullable=True),
    sa.Column('department_name', sa.String(length=200), nullable=True),
    sa.Column('location_id', sa.String(length=100), nullable=True),
    sa.Column('location_name', sa.String(length=200), nullable=True),
    sa.Column('currency', sa.String(length=10), nullable=True),
    sa.Column('is_reconciled', sa.Boolean(), nullable=True),
    sa.Column('raw_data', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_account_id', 'general_ledger', ['account_id'], unique=False)
    op.create_index('idx_customer_vendor', 'general_ledger', ['customer_id', 'vendor_id'], unique=False)
    op.create_index('idx_source_id', 'general_ledger', ['source_id'], unique=False)
    op.create_index('idx_transaction_date', 'general_ledger', ['transaction_date'], unique=False)

    # Create accounts table
    op.create_table('accounts',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('source_id', sa.String(length=100), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('fully_qualified_name', sa.String(length=500), nullable=True),
    sa.Column('account_type', sa.String(length=100), nullable=False),
    sa.Column('account_subtype', sa.String(length=100), nullable=True),
    sa.Column('classification', sa.String(length=50), nullable=True),
    sa.Column('parent_account_id', sa.String(length=100), nullable=True),
    sa.Column('level', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('current_balance', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('currency', sa.String(length=10), nullable=True),
    sa.Column('raw_data', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('source_id')
    )

    # Create customers table
    op.create_table('customers',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('source_id', sa.String(length=100), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('display_name', sa.String(length=200), nullable=True),
    sa.Column('company_name', sa.String(length=200), nullable=True),
    sa.Column('email', sa.String(length=200), nullable=True),
    sa.Column('phone', sa.String(length=50), nullable=True),
    sa.Column('website', sa.String(length=200), nullable=True),
    sa.Column('balance', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('credit_limit', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('payment_terms', sa.String(length=100), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('raw_data', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('source_id')
    )

    # Create vendors table
    op.create_table('vendors',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('source_id', sa.String(length=100), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('display_name', sa.String(length=200), nullable=True),
    sa.Column('company_name', sa.String(length=200), nullable=True),
    sa.Column('email', sa.String(length=200), nullable=True),
    sa.Column('phone', sa.String(length=50), nullable=True),
    sa.Column('website', sa.String(length=200), nullable=True),
    sa.Column('balance', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('payment_terms', sa.String(length=100), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('raw_data', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('source_id')
    )

    # Create items table
    op.create_table('items',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('source_id', sa.String(length=100), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('sku', sa.String(length=100), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('item_type', sa.String(length=50), nullable=False),
    sa.Column('unit_price', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('cost', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('quantity_on_hand', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('reorder_point', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('raw_data', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('source_id')
    )

    # Create financial_periods table
    op.create_table('financial_periods',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('period_type', sa.String(length=20), nullable=False),
    sa.Column('start_date', sa.DateTime(), nullable=False),
    sa.Column('end_date', sa.DateTime(), nullable=False),
    sa.Column('is_closed', sa.Boolean(), nullable=True),
    sa.Column('fiscal_year', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_period_dates', 'financial_periods', ['start_date', 'end_date'], unique=False)

    # Create data_sources table
    op.create_table('data_sources',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('type', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('connection_config', sa.JSON(), nullable=True),
    sa.Column('last_sync', sa.DateTime(), nullable=True),
    sa.Column('sync_frequency', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('data_sources')
    op.drop_table('financial_periods')
    op.drop_table('items')
    op.drop_table('vendors')
    op.drop_table('customers')
    op.drop_table('accounts')
    op.drop_table('general_ledger')
    op.drop_table('ingestion_history')
