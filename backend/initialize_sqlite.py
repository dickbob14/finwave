#!/usr/bin/env python3
"""
Initialize SQLite database for FinWave with proper schema
"""
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Force SQLite database URL
os.environ['DATABASE_URL'] = 'sqlite:///test_finwave.db'

print("🔧 Initializing FinWave SQLite Database")
print("=" * 40)

# Import all models to register them with SQLAlchemy
print("\n1. Loading models...")
from core.database import Base, engine
from models.workspace import Workspace
from models.integration import IntegrationCredential
from models.report import ReportConfig, ReportHistory  
from models.financial_data import FinancialStatement, AccountBalance
from scheduler.models import ScheduledJob
from metrics.models import Base as MetricBase, Metric

# Create all tables
print("\n2. Creating database tables...")
Base.metadata.create_all(bind=engine)
MetricBase.metadata.create_all(bind=engine)
print("   ✓ All tables created")

# Create default workspace
print("\n3. Creating workspaces...")
from core.database import get_db_session

with get_db_session() as db:
    # Create 'default' workspace for frontend compatibility
    default_ws = db.query(Workspace).filter_by(id="default").first()
    if not default_ws:
        # First check what columns exist by looking at the model
        print("   Creating 'default' workspace...")
        workspace = Workspace(
            id="default",
            name="Default Workspace",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(workspace)
        db.commit()
        print("   ✓ Created 'default' workspace")
    else:
        print("   ✓ 'default' workspace already exists")
    
    # Also create 'demo' workspace
    demo_ws = db.query(Workspace).filter_by(id="demo").first()
    if not demo_ws:
        print("   Creating 'demo' workspace...")
        workspace = Workspace(
            id="demo", 
            name="Demo Workspace",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(workspace)
        db.commit()
        print("   ✓ Created 'demo' workspace")
    else:
        print("   ✓ 'demo' workspace already exists")

print("\n✅ Database initialization complete!")
print("\nQuickBooks connection should now work:")
print("1. Make sure the backend server is restarted")
print("2. Go to Settings > Data Sources")  
print("3. Click 'Connect' on QuickBooks")
print("\nIf you see any errors, check backend/backend.log")