#!/usr/bin/env python3
"""
Test the complete QuickBooks flow
"""
import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set SQLite database URL
os.environ['DATABASE_URL'] = 'sqlite:///finwave.db'

print("=== Testing QuickBooks Integration ===\n")

# 1. Check database tables
print("1. Checking database tables...")
from sqlalchemy import inspect
from core.database import engine

inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"   Found {len(tables)} tables")
required_tables = ['workspaces', 'integration_credentials', 'metrics', 'scheduled_jobs']
for table in required_tables:
    if table in tables:
        print(f"   ✓ {table}")
    else:
        print(f"   ✗ {table} MISSING")

# 2. Check workspace
print("\n2. Checking workspace...")
from core.database import get_db_session
from models.workspace import Workspace

with get_db_session() as db:
    workspace = db.query(Workspace).filter_by(id="demo").first()
    if workspace:
        print(f"   ✓ Demo workspace exists: {workspace.name}")
    else:
        print("   ✗ Demo workspace missing")

# 3. Test sync with mock data
print("\n3. Testing sync process...")
from models.integration import IntegrationCredential, IntegrationStatus
from datetime import datetime, timedelta
from core.crypto import encrypt

with get_db_session() as db:
    # Create mock integration
    integration = IntegrationCredential(
        workspace_id="demo",
        source="quickbooks",
        status=IntegrationStatus.CONNECTED.value,
        access_token_encrypted=encrypt("mock_token"),
        refresh_token_encrypted=encrypt("mock_refresh"),
        expires_at=datetime.utcnow() + timedelta(hours=1),
        metadata_encrypted=encrypt('{"realm_id": "test123"}'),
        connected_by="test@example.com"
    )
    
    # Don't save - just use for testing
    print("   Created mock integration")
    
    # Test sync
    from integrations.quickbooks.sync_v2 import sync_quickbooks_data
    
    try:
        result = sync_quickbooks_data("demo", integration)
        print(f"   Sync result: {result['status']}")
        print(f"   Records processed: {result['records_processed']}")
        if 'errors' in result:
            print(f"   Errors: {result['errors']}")
    except Exception as e:
        print(f"   ✗ Sync failed: {e}")

# 4. Check metrics
print("\n4. Checking metrics...")
from metrics.models import Metric

with get_db_session() as db:
    metric_count = db.query(Metric).filter_by(workspace_id="demo").count()
    print(f"   Found {metric_count} metrics")
    
    if metric_count > 0:
        metrics = db.query(Metric).filter_by(workspace_id="demo").limit(5).all()
        for m in metrics:
            print(f"   - {m.metric_id}: ${m.value:,.0f}")

# 5. Test API endpoint
print("\n5. Testing API endpoint...")
try:
    # Import FastAPI test client
    from app.main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    response = client.get("/api/demo/insights")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ API endpoint works")
        print(f"   Summary: {data.get('summary', 'N/A')}")
        print(f"   Revenue: {data.get('key_metrics', {}).get('total_revenue', 'N/A')}")
    else:
        print(f"   ✗ API error: {response.status_code}")
except Exception as e:
    print(f"   ✗ API test failed: {e}")

print("\n=== Test Complete ===")
print("\nTo fully test:")
print("1. Start the backend: uvicorn app.main:app --reload")
print("2. Start the frontend: cd frontend && npm run dev")
print("3. Go to Settings > Data Sources")
print("4. Connect QuickBooks")
print("5. Check the Dashboard for data")