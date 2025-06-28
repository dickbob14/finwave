"""Add report history table

Revision ID: 008
Create Date: 2024-12-21
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    """Create report_history table"""
    op.create_table(
        'report_history',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(36), nullable=False),
        sa.Column('report_type', sa.String(50), nullable=False),
        sa.Column('period', sa.String(7), nullable=False),  # YYYY-MM format
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('s3_url', sa.String(500), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('pages', sa.Integer(), nullable=True),
        sa.Column('generated_by', sa.String(255), nullable=False),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Create indexes
    op.create_index('idx_report_history_workspace', 'report_history', ['workspace_id'])
    op.create_index('idx_report_history_period', 'report_history', ['period'])
    op.create_index('idx_report_history_type', 'report_history', ['report_type'])
    op.create_index('idx_report_history_generated_at', 'report_history', ['generated_at'])
    
    # Create foreign key to workspaces table (if it exists)
    # op.create_foreign_key(
    #     'fk_report_history_workspace',
    #     'report_history', 'workspaces',
    #     ['workspace_id'], ['id'],
    #     ondelete='CASCADE'
    # )


def downgrade():
    """Drop report_history table"""
    # Drop foreign key first if it exists
    # op.drop_constraint('fk_report_history_workspace', 'report_history', type_='foreignkey')
    
    # Drop indexes
    op.drop_index('idx_report_history_generated_at', 'report_history')
    op.drop_index('idx_report_history_type', 'report_history')
    op.drop_index('idx_report_history_period', 'report_history')
    op.drop_index('idx_report_history_workspace', 'report_history')
    
    # Drop table
    op.drop_table('report_history')