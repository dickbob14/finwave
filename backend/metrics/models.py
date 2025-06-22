"""
Metric store models for time-series financial data
Supports both PostgreSQL and DuckDB backends
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Float, DateTime, Date, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Metric(Base):
    """
    Time-series metric storage
    Each row represents a single metric value for a specific period
    """
    __tablename__ = "metrics"
    
    # Primary fields
    workspace_id = Column(String, primary_key=True, nullable=False)
    metric_id = Column(String, primary_key=True, nullable=False)
    period_date = Column(Date, primary_key=True, nullable=False)
    
    # Value and metadata
    value = Column(Float, nullable=False)
    source_template = Column(String, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Additional context (optional)
    currency = Column(String, default="USD")
    unit = Column(String, nullable=True)  # e.g., "count", "percentage", "dollars"
    
    # Indexes for common queries
    __table_args__ = (
        # Unique constraint on composite key
        UniqueConstraint('workspace_id', 'metric_id', 'period_date', name='uq_metric_period'),
        
        # Performance indexes
        Index('idx_workspace_metric', 'workspace_id', 'metric_id'),
        Index('idx_workspace_period', 'workspace_id', 'period_date'),
        Index('idx_metric_period', 'metric_id', 'period_date'),
    )
    
    def __repr__(self):
        return f"<Metric({self.workspace_id}/{self.metric_id}@{self.period_date}={self.value})>"

# Standard metric identifiers
FINANCIAL_METRICS = [
    "revenue",
    "cogs",
    "gross_profit",
    "opex",
    "ebitda",
    "net_income",
    "cash",
    "total_assets",
    "total_liabilities",
    "total_equity"
]

SAAS_METRICS = [
    "mrr",
    "arr",
    "new_customers",
    "churn_rate",
    "net_revenue_retention",
    "cac",
    "ltv",
    "magic_number",
    "burn_rate",
    "runway_months"
]

OPERATIONAL_METRICS = [
    "headcount",
    "revenue_per_employee",
    "gross_margin",
    "ebitda_margin",
    "rule_of_40"
]

ALL_METRICS = FINANCIAL_METRICS + SAAS_METRICS + OPERATIONAL_METRICS

# Metric metadata for validation and display
METRIC_METADATA = {
    # Financial metrics
    "revenue": {"unit": "dollars", "display_name": "Revenue"},
    "cogs": {"unit": "dollars", "display_name": "Cost of Goods Sold"},
    "gross_profit": {"unit": "dollars", "display_name": "Gross Profit"},
    "opex": {"unit": "dollars", "display_name": "Operating Expenses"},
    "ebitda": {"unit": "dollars", "display_name": "EBITDA"},
    "net_income": {"unit": "dollars", "display_name": "Net Income"},
    "cash": {"unit": "dollars", "display_name": "Cash"},
    "total_assets": {"unit": "dollars", "display_name": "Total Assets"},
    "total_liabilities": {"unit": "dollars", "display_name": "Total Liabilities"},
    "total_equity": {"unit": "dollars", "display_name": "Total Equity"},
    
    # SaaS metrics
    "mrr": {"unit": "dollars", "display_name": "Monthly Recurring Revenue"},
    "arr": {"unit": "dollars", "display_name": "Annual Recurring Revenue"},
    "new_customers": {"unit": "count", "display_name": "New Customers"},
    "churn_rate": {"unit": "percentage", "display_name": "Churn Rate"},
    "net_revenue_retention": {"unit": "percentage", "display_name": "Net Revenue Retention"},
    "cac": {"unit": "dollars", "display_name": "Customer Acquisition Cost"},
    "ltv": {"unit": "dollars", "display_name": "Customer Lifetime Value"},
    "magic_number": {"unit": "ratio", "display_name": "Magic Number"},
    "burn_rate": {"unit": "dollars", "display_name": "Monthly Burn Rate"},
    "runway_months": {"unit": "count", "display_name": "Runway (Months)"},
    
    # Operational metrics
    "headcount": {"unit": "count", "display_name": "Headcount"},
    "revenue_per_employee": {"unit": "dollars", "display_name": "Revenue per Employee"},
    "gross_margin": {"unit": "percentage", "display_name": "Gross Margin"},
    "ebitda_margin": {"unit": "percentage", "display_name": "EBITDA Margin"},
    "rule_of_40": {"unit": "percentage", "display_name": "Rule of 40"}
}