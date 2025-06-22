"""Create metric metadata table and seed data

Revision ID: 002_metric_metadata
Revises: 001_metrics
Create Date: 2024-01-22 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_metric_metadata'
down_revision = '001_metrics'
branch_labels = None
depends_on = None

# Seed data for metrics
METRIC_SEEDS = [
    # Financial metrics
    {"metric_id": "revenue", "display_name": "Revenue", "unit": "dollars", "format_string": "$0.0a", "category": "financial"},
    {"metric_id": "cogs", "display_name": "Cost of Goods Sold", "unit": "dollars", "format_string": "$0.0a", "category": "financial"},
    {"metric_id": "gross_profit", "display_name": "Gross Profit", "unit": "dollars", "format_string": "$0.0a", "category": "financial"},
    {"metric_id": "opex", "display_name": "Operating Expenses", "unit": "dollars", "format_string": "$0.0a", "category": "financial"},
    {"metric_id": "ebitda", "display_name": "EBITDA", "unit": "dollars", "format_string": "$0.0a", "category": "financial"},
    {"metric_id": "net_income", "display_name": "Net Income", "unit": "dollars", "format_string": "$0.0a", "category": "financial"},
    {"metric_id": "cash", "display_name": "Cash", "unit": "dollars", "format_string": "$0.0a", "category": "financial"},
    {"metric_id": "total_assets", "display_name": "Total Assets", "unit": "dollars", "format_string": "$0.0a", "category": "financial"},
    {"metric_id": "total_liabilities", "display_name": "Total Liabilities", "unit": "dollars", "format_string": "$0.0a", "category": "financial"},
    {"metric_id": "total_equity", "display_name": "Total Equity", "unit": "dollars", "format_string": "$0.0a", "category": "financial"},
    
    # SaaS metrics
    {"metric_id": "mrr", "display_name": "Monthly Recurring Revenue", "unit": "dollars", "format_string": "$0.0a", "category": "saas"},
    {"metric_id": "arr", "display_name": "Annual Recurring Revenue", "unit": "dollars", "format_string": "$0.0a", "category": "saas"},
    {"metric_id": "new_customers", "display_name": "New Customers", "unit": "count", "format_string": "0", "category": "saas"},
    {"metric_id": "churn_rate", "display_name": "Churn Rate", "unit": "percentage", "format_string": "0.0%", "category": "saas"},
    {"metric_id": "net_revenue_retention", "display_name": "Net Revenue Retention", "unit": "percentage", "format_string": "0%", "category": "saas"},
    {"metric_id": "cac", "display_name": "Customer Acquisition Cost", "unit": "dollars", "format_string": "$0,0", "category": "saas"},
    {"metric_id": "ltv", "display_name": "Customer Lifetime Value", "unit": "dollars", "format_string": "$0,0", "category": "saas"},
    {"metric_id": "magic_number", "display_name": "Magic Number", "unit": "ratio", "format_string": "0.00", "category": "saas"},
    {"metric_id": "burn_rate", "display_name": "Monthly Burn Rate", "unit": "dollars", "format_string": "$0.0a", "category": "saas"},
    {"metric_id": "runway_months", "display_name": "Runway (Months)", "unit": "count", "format_string": "0", "category": "saas"},
    
    # Operational metrics
    {"metric_id": "headcount", "display_name": "Headcount", "unit": "count", "format_string": "0", "category": "operational"},
    {"metric_id": "revenue_per_employee", "display_name": "Revenue per Employee", "unit": "dollars", "format_string": "$0.0a", "category": "operational"},
    {"metric_id": "gross_margin", "display_name": "Gross Margin", "unit": "percentage", "format_string": "0.0%", "category": "operational"},
    {"metric_id": "ebitda_margin", "display_name": "EBITDA Margin", "unit": "percentage", "format_string": "0.0%", "category": "operational"},
    {"metric_id": "rule_of_40", "display_name": "Rule of 40", "unit": "percentage", "format_string": "0%", "category": "operational"},
]


def upgrade() -> None:
    # Create metric_metadata table
    metric_meta = op.create_table(
        'metric_metadata',
        sa.Column('metric_id', sa.String(), primary_key=True),
        sa.Column('display_name', sa.String(), nullable=False),
        sa.Column('unit', sa.String(), nullable=False),
        sa.Column('format_string', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('calculation_method', sa.Text(), nullable=True),
        sa.Column('is_calculated', sa.Boolean(), default=False),
        sa.Column('sort_order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    # Create index on category
    op.create_index('idx_metric_category', 'metric_metadata', ['category'])
    
    # Seed data
    op.bulk_insert(metric_meta, METRIC_SEEDS)


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_metric_category', table_name='metric_metadata')
    
    # Drop table
    op.drop_table('metric_metadata')