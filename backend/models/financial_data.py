"""
Financial data models for storing QuickBooks sync data
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Float, DateTime, JSON, Boolean, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from core.database import Base


class FinancialStatement(Base):
    """Store financial statements from QuickBooks"""
    __tablename__ = "qb_financial_statements"
    
    id = Column(String, primary_key=True)
    company_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    statement_type = Column(String, nullable=False)  # P&L, Balance Sheet, Cash Flow
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    data = Column(JSON, nullable=False)  # Full statement data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_financial_statements_company_type', 'company_id', 'statement_type'),
        Index('idx_financial_statements_period', 'company_id', 'period_start', 'period_end'),
    )
    
    # workspace = relationship("Workspace", back_populates="financial_statements")


class AccountBalance(Base):
    """Store individual account balances for detailed tracking"""
    __tablename__ = "qb_account_balances"
    
    id = Column(String, primary_key=True)
    company_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    account_id = Column(String, nullable=False)  # QuickBooks account ID
    account_name = Column(String, nullable=False)
    account_type = Column(String, nullable=False)  # Asset, Liability, Equity, Revenue, Expense
    account_subtype = Column(String)
    balance = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    as_of_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_account_balances_company_account', 'company_id', 'account_id'),
        Index('idx_account_balances_date', 'company_id', 'as_of_date'),
        Index('idx_account_balances_type', 'company_id', 'account_type'),
    )
    
    # workspace = relationship("Workspace", back_populates="account_balances")


class Transaction(Base):
    """Store transaction-level data from QuickBooks"""
    __tablename__ = "qb_transactions"
    
    id = Column(String, primary_key=True)
    company_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    quickbooks_id = Column(String, nullable=False)
    transaction_type = Column(String, nullable=False)  # Invoice, Payment, Bill, etc.
    transaction_date = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    customer_id = Column(String)
    vendor_id = Column(String)
    account_id = Column(String)
    description = Column(String)
    transaction_metadata = Column(JSON)  # Additional transaction details
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_transactions_company_type', 'company_id', 'transaction_type'),
        Index('idx_transactions_date', 'company_id', 'transaction_date'),
        Index('idx_transactions_quickbooks', 'company_id', 'quickbooks_id'),
    )
    
    # workspace = relationship("Workspace", back_populates="transactions")


class Customer(Base):
    """Store customer data from QuickBooks"""
    __tablename__ = "qb_customers"
    
    id = Column(String, primary_key=True)
    company_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    quickbooks_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String)
    phone = Column(String)
    first_transaction_date = Column(DateTime)
    last_transaction_date = Column(DateTime)
    total_revenue = Column(Float, default=0)
    transaction_count = Column(Integer, default=0)
    status = Column(String, default="active")  # active, churned
    churn_date = Column(DateTime)
    customer_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_customers_company', 'company_id'),
        Index('idx_customers_quickbooks', 'company_id', 'quickbooks_id'),
        Index('idx_customers_status', 'company_id', 'status'),
    )
    
    # workspace = relationship("Workspace", back_populates="customers")


class Vendor(Base):
    """Store vendor data from QuickBooks"""
    __tablename__ = "qb_vendors"
    
    id = Column(String, primary_key=True)
    company_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    quickbooks_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String)
    phone = Column(String)
    total_spend = Column(Float, default=0)
    transaction_count = Column(Integer, default=0)
    vendor_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_vendors_company', 'company_id'),
        Index('idx_vendors_quickbooks', 'company_id', 'quickbooks_id'),
    )
    
    # workspace = relationship("Workspace", back_populates="vendors")


class KPIMetric(Base):
    """Store calculated KPI metrics"""
    __tablename__ = "kpi_metrics"
    
    id = Column(String, primary_key=True)
    company_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String)  # percentage, currency, ratio, etc.
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    calculation_method = Column(String)  # How the metric was calculated
    kpi_metadata = Column(JSON)  # Additional context or breakdown
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_kpi_metrics_company_metric', 'company_id', 'metric_name'),
        Index('idx_kpi_metrics_period', 'company_id', 'period_start', 'period_end'),
    )
    
    # workspace = relationship("Workspace", back_populates="kpi_metrics")


class SyncLog(Base):
    """Track sync operations for audit and debugging"""
    __tablename__ = "sync_logs"
    
    id = Column(String, primary_key=True)
    company_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    sync_type = Column(String, nullable=False)  # full, incremental
    sync_status = Column(String, nullable=False)  # started, completed, failed
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    records_synced = Column(Integer, default=0)
    error_message = Column(String)
    sync_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_sync_logs_company', 'company_id'),
        Index('idx_sync_logs_status', 'company_id', 'sync_status'),
    )
    
    # workspace = relationship("Workspace", back_populates="sync_logs")


# Update Workspace model relationships
def update_workspace_model():
    """This function should be called to update the Workspace model with new relationships"""
    from models.workspace import Workspace
    
    # Add relationships if they don't exist
    if not hasattr(Workspace, 'financial_statements'):
        Workspace.financial_statements = relationship("FinancialStatement", back_populates="workspace", cascade="all, delete-orphan")
    if not hasattr(Workspace, 'account_balances'):
        Workspace.account_balances = relationship("AccountBalance", back_populates="workspace", cascade="all, delete-orphan")
    if not hasattr(Workspace, 'transactions'):
        Workspace.transactions = relationship("Transaction", back_populates="workspace", cascade="all, delete-orphan")
    if not hasattr(Workspace, 'customers'):
        Workspace.customers = relationship("Customer", back_populates="workspace", cascade="all, delete-orphan")
    if not hasattr(Workspace, 'vendors'):
        Workspace.vendors = relationship("Vendor", back_populates="workspace", cascade="all, delete-orphan")
    if not hasattr(Workspace, 'kpi_metrics'):
        Workspace.kpi_metrics = relationship("KPIMetric", back_populates="workspace", cascade="all, delete-orphan")
    if not hasattr(Workspace, 'sync_logs'):
        Workspace.sync_logs = relationship("SyncLog", back_populates="workspace", cascade="all, delete-orphan")