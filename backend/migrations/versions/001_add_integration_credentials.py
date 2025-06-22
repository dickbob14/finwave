"""Add integration_credentials table

Revision ID: 001
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create integration_credentials table"""
    op.create_table(
        'integration_credentials',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('workspace_id', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('access_token_encrypted', sa.Text(), nullable=True),
        sa.Column('refresh_token_encrypted', sa.Text(), nullable=True),
        sa.Column('company_id', sa.String(), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('workspace_id', 'source', name='uq_workspace_source')
    )
    
    # Create index for faster lookups
    op.create_index('ix_integration_credentials_workspace_id', 'integration_credentials', ['workspace_id'])
    op.create_index('ix_integration_credentials_source', 'integration_credentials', ['source'])
    op.create_index('ix_integration_credentials_status', 'integration_credentials', ['status'])


def downgrade():
    """Drop integration_credentials table"""
    op.drop_index('ix_integration_credentials_status', table_name='integration_credentials')
    op.drop_index('ix_integration_credentials_source', table_name='integration_credentials')
    op.drop_index('ix_integration_credentials_workspace_id', table_name='integration_credentials')
    op.drop_table('integration_credentials')