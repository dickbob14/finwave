#!/usr/bin/env python3
"""
Initialize SQLite database with all required tables
"""
import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set SQLite database URL
os.environ['DATABASE_URL'] = 'sqlite:///finwave.db'

from core.database import Base, engine, init_db

# Import all models to register them
from models.workspace import Workspace
from models.integration import IntegrationCredential
from models.financial_data import (
    FinancialStatement, AccountBalance, Transaction,
    Customer, Vendor, KPIMetric, SyncLog
)
from scheduler.models import ScheduledJob

# Import Metric model separately (it has its own Base)
from metrics.models import Metric, Base as MetricBase

print("Creating database tables...")

try:
    # Create all tables from main Base
    Base.metadata.create_all(bind=engine)
    
    # Create metrics table from MetricBase
    MetricBase.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")
    
    # List tables
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\nCreated {len(tables)} tables:")
    for table in sorted(tables):
        print(f"  - {table}")
        
except Exception as e:
    print(f"❌ Error creating database: {e}")
    sys.exit(1)