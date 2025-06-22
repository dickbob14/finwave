"""Add cohort and payroll metrics to catalog

Revision ID: 003_cohort_metrics
Revises: 002_metric_metadata
Create Date: 2024-01-22 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_cohort_metrics'
down_revision = '002_metric_metadata'
branch_labels = None
depends_on = None

# New metrics to add
COHORT_METRICS = [
    # Payroll metrics
    {"metric_id": "total_headcount", "display_name": "Total Headcount", "unit": "count", "format_string": "0", "category": "payroll"},
    {"metric_id": "fte_count", "display_name": "Full-Time Employees", "unit": "count", "format_string": "0", "category": "payroll"},
    {"metric_id": "contractor_count", "display_name": "Contractors", "unit": "count", "format_string": "0", "category": "payroll"},
    {"metric_id": "new_hires_mtd", "display_name": "New Hires (MTD)", "unit": "count", "format_string": "0", "category": "payroll"},
    {"metric_id": "terminations_mtd", "display_name": "Terminations (MTD)", "unit": "count", "format_string": "0", "category": "payroll"},
    {"metric_id": "total_payroll_cost", "display_name": "Total Payroll Cost", "unit": "dollars", "format_string": "$0.0a", "category": "payroll"},
    {"metric_id": "average_cost_fte", "display_name": "Average Cost per FTE", "unit": "dollars", "format_string": "$0,0", "category": "payroll"},
    {"metric_id": "benefits_load_pct", "display_name": "Benefits Load %", "unit": "percentage", "format_string": "0.0%", "category": "payroll"},
    {"metric_id": "payroll_as_pct_revenue", "display_name": "Payroll as % of Revenue", "unit": "percentage", "format_string": "0.0%", "category": "payroll"},
    
    # Cohort metrics
    {"metric_id": "new_mrr_cohort", "display_name": "New MRR (Cohort)", "unit": "dollars", "format_string": "$0.0a", "category": "cohort"},
    {"metric_id": "retained_mrr_cohort", "display_name": "Retained MRR (Cohort)", "unit": "dollars", "format_string": "$0.0a", "category": "cohort"},
    {"metric_id": "gross_churn_rate", "display_name": "Gross Churn Rate", "unit": "percentage", "format_string": "0.0%", "category": "cohort"},
    {"metric_id": "net_churn_rate", "display_name": "Net Churn Rate", "unit": "percentage", "format_string": "0.0%", "category": "cohort"},
    {"metric_id": "gross_retention_rate", "display_name": "Gross Retention Rate", "unit": "percentage", "format_string": "0.0%", "category": "cohort"},
    {"metric_id": "net_retention_rate", "display_name": "Net Retention Rate", "unit": "percentage", "format_string": "0.0%", "category": "cohort"},
    {"metric_id": "cohort_ltv", "display_name": "Cohort LTV", "unit": "dollars", "format_string": "$0,0", "category": "cohort"},
    {"metric_id": "payback_period", "display_name": "CAC Payback Period", "unit": "count", "format_string": "0.0", "category": "cohort"},
    
    # Employee retention cohorts
    {"metric_id": "employee_30d_retention", "display_name": "30-Day Employee Retention", "unit": "percentage", "format_string": "0%", "category": "cohort"},
    {"metric_id": "employee_90d_retention", "display_name": "90-Day Employee Retention", "unit": "percentage", "format_string": "0%", "category": "cohort"},
    {"metric_id": "employee_180d_retention", "display_name": "180-Day Employee Retention", "unit": "percentage", "format_string": "0%", "category": "cohort"},
    {"metric_id": "employee_365d_retention", "display_name": "1-Year Employee Retention", "unit": "percentage", "format_string": "0%", "category": "cohort"},
    
    # Productivity metrics
    {"metric_id": "revenue_per_fte", "display_name": "Revenue per FTE", "unit": "dollars", "format_string": "$0.0a", "category": "productivity"},
    {"metric_id": "gross_profit_per_fte", "display_name": "Gross Profit per FTE", "unit": "dollars", "format_string": "$0.0a", "category": "productivity"},
    {"metric_id": "customers_per_fte", "display_name": "Customers per FTE", "unit": "ratio", "format_string": "0.0", "category": "productivity"},
    
    # Advanced CAC/LTV
    {"metric_id": "cac_by_channel", "display_name": "CAC by Channel", "unit": "dollars", "format_string": "$0,0", "category": "saas"},
    {"metric_id": "ltv_to_cac_ratio", "display_name": "LTV:CAC Ratio", "unit": "ratio", "format_string": "0.0x", "category": "saas"},
    {"metric_id": "months_to_recover_cac", "display_name": "Months to Recover CAC", "unit": "count", "format_string": "0.0", "category": "saas"},
]


def upgrade() -> None:
    # Get the metadata table
    metric_meta = sa.table('metric_metadata',
        sa.column('metric_id', sa.String()),
        sa.column('display_name', sa.String()),
        sa.column('unit', sa.String()),
        sa.column('format_string', sa.String()),
        sa.column('category', sa.String()),
        sa.column('description', sa.Text()),
        sa.column('calculation_method', sa.Text()),
        sa.column('is_calculated', sa.Boolean()),
        sa.column('sort_order', sa.Integer())
    )
    
    # Insert new metrics
    op.bulk_insert(metric_meta, COHORT_METRICS)
    
    # Add cohort analysis table for storing cohort data
    op.create_table(
        'cohort_analysis',
        sa.Column('workspace_id', sa.String(), nullable=False),
        sa.Column('cohort_type', sa.String(), nullable=False),  # 'customer' or 'employee'
        sa.Column('cohort_period', sa.Date(), nullable=False),  # Month of cohort
        sa.Column('analysis_period', sa.Date(), nullable=False),  # Month being analyzed
        sa.Column('periods_since_start', sa.Integer(), nullable=False),  # 0, 1, 2, 3... months
        sa.Column('cohort_size', sa.Integer(), nullable=False),  # Initial size
        sa.Column('retained_count', sa.Integer(), nullable=False),  # Still active
        sa.Column('retained_value', sa.Float(), nullable=True),  # MRR or payroll cost
        sa.Column('churn_count', sa.Integer(), nullable=False),
        sa.Column('churn_value', sa.Float(), nullable=True),
        sa.Column('retention_rate', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('workspace_id', 'cohort_type', 'cohort_period', 'analysis_period')
    )
    
    # Create indexes
    op.create_index('idx_cohort_workspace_type', 'cohort_analysis', ['workspace_id', 'cohort_type'])
    op.create_index('idx_cohort_period', 'cohort_analysis', ['cohort_period'])


def downgrade() -> None:
    # Drop cohort analysis table
    op.drop_index('idx_cohort_period', table_name='cohort_analysis')
    op.drop_index('idx_cohort_workspace_type', table_name='cohort_analysis')
    op.drop_table('cohort_analysis')
    
    # Remove added metrics
    metric_ids = [m['metric_id'] for m in COHORT_METRICS]
    op.execute(
        f"DELETE FROM metric_metadata WHERE metric_id IN ({','.join(['%s'] * len(metric_ids))})",
        metric_ids
    )