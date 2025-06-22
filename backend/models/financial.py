"""
SQLAlchemy models for financial data storage
"""
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Text, Boolean, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()

class IngestionHistory(Base):
    """Track data ingestion runs for idempotency"""
    __tablename__ = "ingestion_history"
    
    id = Column(Integer, primary_key=True)
    source = Column(String(50), nullable=False)  # 'quickbooks', 'salesforce', etc.
    entity_type = Column(String(50), nullable=False)  # 'invoice', 'account', etc.
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    records_count = Column(Integer, default=0)
    status = Column(String(20), default='pending')  # pending, completed, failed
    error_message = Column(Text, nullable=True)
    ingested_at = Column(DateTime, default=func.now())
    ingestion_metadata = Column(JSON, nullable=True)
    
    __table_args__ = (
        Index('idx_source_entity_period', 'source', 'entity_type', 'period_start', 'period_end'),
    )

class GeneralLedger(Base):
    """Core general ledger transactions"""
    __tablename__ = "general_ledger"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(100), nullable=False)  # Original QB ID
    source_type = Column(String(50), nullable=False)  # QB entity type
    
    # Core transaction fields
    transaction_date = Column(DateTime, nullable=False)
    posted_date = Column(DateTime, nullable=True)
    reference_number = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    
    # Account information
    account_id = Column(String(100), nullable=False)
    account_name = Column(String(200), nullable=False)
    account_type = Column(String(100), nullable=False)
    account_subtype = Column(String(100), nullable=True)
    
    # Amount fields
    debit_amount = Column(Numeric(15, 2), default=0)
    credit_amount = Column(Numeric(15, 2), default=0)
    amount = Column(Numeric(15, 2), nullable=False)  # Signed amount
    
    # Entity relationships
    customer_id = Column(String(100), nullable=True)
    customer_name = Column(String(200), nullable=True)
    vendor_id = Column(String(100), nullable=True) 
    vendor_name = Column(String(200), nullable=True)
    employee_id = Column(String(100), nullable=True)
    employee_name = Column(String(200), nullable=True)
    
    # Classifications
    class_id = Column(String(100), nullable=True)
    class_name = Column(String(200), nullable=True)
    department_id = Column(String(100), nullable=True)
    department_name = Column(String(200), nullable=True)
    location_id = Column(String(100), nullable=True)
    location_name = Column(String(200), nullable=True)
    
    # Metadata
    currency = Column(String(10), default='USD')
    is_reconciled = Column(Boolean, default=False)
    raw_data = Column(JSON, nullable=True)  # Store original QB response
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_transaction_date', 'transaction_date'),
        Index('idx_account_id', 'account_id'),
        Index('idx_source_id', 'source_id'),
        Index('idx_customer_vendor', 'customer_id', 'vendor_id'),
    )

class Account(Base):
    """Chart of accounts"""
    __tablename__ = "accounts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(100), nullable=False, unique=True)
    
    # Account details
    name = Column(String(200), nullable=False)
    fully_qualified_name = Column(String(500), nullable=True)
    account_type = Column(String(100), nullable=False)
    account_subtype = Column(String(100), nullable=True)
    classification = Column(String(50), nullable=True)  # Asset, Liability, Equity, Revenue, Expense
    
    # Hierarchy
    parent_account_id = Column(String(100), nullable=True)
    level = Column(Integer, default=1)
    
    # Properties
    is_active = Column(Boolean, default=True)
    current_balance = Column(Numeric(15, 2), default=0)
    currency = Column(String(10), default='USD')
    
    # Metadata
    raw_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Customer(Base):
    """Customer master data"""
    __tablename__ = "customers"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(100), nullable=False, unique=True)
    
    # Customer details
    name = Column(String(200), nullable=False)
    display_name = Column(String(200), nullable=True)
    company_name = Column(String(200), nullable=True)
    
    # Contact info
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    website = Column(String(200), nullable=True)
    
    # Financial
    balance = Column(Numeric(15, 2), default=0)
    credit_limit = Column(Numeric(15, 2), nullable=True)
    payment_terms = Column(String(100), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    raw_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Vendor(Base):
    """Vendor master data"""
    __tablename__ = "vendors"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(100), nullable=False, unique=True)
    
    # Vendor details
    name = Column(String(200), nullable=False)
    display_name = Column(String(200), nullable=True)
    company_name = Column(String(200), nullable=True)
    
    # Contact info
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    website = Column(String(200), nullable=True)
    
    # Financial
    balance = Column(Numeric(15, 2), default=0)
    payment_terms = Column(String(100), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    raw_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Item(Base):
    """Item/product master data"""
    __tablename__ = "items"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(100), nullable=False, unique=True)
    
    # Item details
    name = Column(String(200), nullable=False)
    sku = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    item_type = Column(String(50), nullable=False)  # Inventory, Service, NonInventory
    
    # Pricing
    unit_price = Column(Numeric(15, 4), nullable=True)
    cost = Column(Numeric(15, 4), nullable=True)
    
    # Inventory
    quantity_on_hand = Column(Numeric(15, 4), default=0)
    reorder_point = Column(Numeric(15, 4), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    raw_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class FinancialPeriod(Base):
    """Financial period definitions"""
    __tablename__ = "financial_periods"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)  # 'Q1 2024', 'Jan 2024', etc.
    period_type = Column(String(20), nullable=False)  # monthly, quarterly, annual
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_closed = Column(Boolean, default=False)
    fiscal_year = Column(Integer, nullable=False)
    
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_period_dates', 'start_date', 'end_date'),
    )

# Additional tables for data source integration
class DataSource(Base):
    """Track external data sources"""
    __tablename__ = "data_sources"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True)  # 'quickbooks', 'salesforce', etc.
    type = Column(String(50), nullable=False)  # 'erp', 'crm', 'payroll', etc.
    status = Column(String(20), default='inactive')  # active, inactive, error
    
    # Connection info (encrypted in production)
    connection_config = Column(JSON, nullable=True)
    last_sync = Column(DateTime, nullable=True)
    sync_frequency = Column(String(20), default='daily')  # hourly, daily, weekly
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())