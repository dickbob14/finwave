#!/usr/bin/env python3
"""
Fix QuickBooks connection issue by ensuring database and workspace are properly set up
"""
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set SQLite database URL
os.environ['DATABASE_URL'] = 'sqlite:///test_finwave.db'

def fix_quickbooks_connection():
    """Fix the QuickBooks connection issue"""
    print("🔧 Fixing QuickBooks Connection Issue")
    print("=" * 40)
    
    # Step 1: Initialize database if needed
    print("\n1. Checking database...")
    from sqlalchemy import create_engine, inspect
    from core.database import Base, engine
    from metrics.models import Base as MetricBase
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if len(tables) == 0:
        print("   Database is empty, initializing...")
        # Import all models to register them
        from models.workspace import Workspace
        from models.integration import IntegrationCredential
        from models.report import ReportConfig, ReportHistory
        from models.financial_data import FinancialStatement, AccountBalance
        from scheduler.models import ScheduledJob
        from metrics.models import Metric
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        MetricBase.metadata.create_all(bind=engine)
        print("   ✓ Database initialized with all tables")
    else:
        print(f"   ✓ Database exists with {len(tables)} tables")
    
    # Step 2: Create default workspace
    print("\n2. Creating default workspace...")
    from core.database import get_db_session
    from models.workspace import Workspace
    
    with get_db_session() as db:
        # Check if default workspace exists
        default_ws = db.query(Workspace).filter_by(id="default").first()
        if not default_ws:
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
            print("   ✓ Default workspace already exists")
        
        # Also ensure demo workspace exists
        demo_ws = db.query(Workspace).filter_by(id="demo").first()
        if not demo_ws:
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
            print("   ✓ Demo workspace already exists")
    
    # Step 3: Verify OAuth configuration
    print("\n3. Verifying OAuth configuration...")
    from core.oauth_config import get_oauth_credentials
    
    # Check for default workspace
    creds = get_oauth_credentials("default", "quickbooks")
    if creds:
        print("   ✓ QuickBooks OAuth credentials configured")
        print(f"   Client ID: {creds[0]}")
    else:
        print("   ✗ QuickBooks OAuth credentials NOT found")
        print("   Please ensure QB_CLIENT_ID and QB_CLIENT_SECRET are set in .env")
    
    # Step 4: Check environment
    print("\n4. Checking environment...")
    bypass_auth = os.getenv('BYPASS_AUTH', 'false').lower() == 'true'
    print(f"   BYPASS_AUTH: {bypass_auth}")
    print(f"   API_BASE_URL: {os.getenv('API_BASE_URL', 'http://localhost:8000')}")
    print(f"   QB_ENVIRONMENT: {os.getenv('QB_ENVIRONMENT', 'not set')}")
    
    print("\n✅ QuickBooks connection should now work!")
    print("\nNext steps:")
    print("1. Restart the backend server")
    print("2. Go to Settings > Data Sources")
    print("3. Click 'Connect' on QuickBooks")
    print("\nIf you still see errors, check backend/backend.log for details.")

if __name__ == "__main__":
    fix_quickbooks_connection()