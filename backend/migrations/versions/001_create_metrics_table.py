"""Create metrics table

Revision ID: 001_metrics
Revises: 
Create Date: 2024-01-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_metrics'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create metrics table
    op.create_table(
        'metrics',
        sa.Column('workspace_id', sa.String(), nullable=False),
        sa.Column('metric_id', sa.String(), nullable=False),
        sa.Column('period_date', sa.Date(), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('source_template', sa.String(), nullable=False),
        sa.Column('currency', sa.String(), server_default='USD'),
        sa.Column('unit', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('workspace_id', 'metric_id', 'period_date'),
        sa.UniqueConstraint('workspace_id', 'metric_id', 'period_date', name='uq_metric_period')
    )
    
    # Create indexes
    op.create_index('idx_workspace_metric', 'metrics', ['workspace_id', 'metric_id'])
    op.create_index('idx_workspace_period', 'metrics', ['workspace_id', 'period_date'])
    op.create_index('idx_metric_period', 'metrics', ['metric_id', 'period_date'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_metric_period', table_name='metrics')
    op.drop_index('idx_workspace_period', table_name='metrics')
    op.drop_index('idx_workspace_metric', table_name='metrics')
    
    # Drop table
    op.drop_table('metrics')