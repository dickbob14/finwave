#!/usr/bin/env python3
"""
Simulate QuickBooks connection to test the flow
"""
import os
import sys
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set SQLite database URL
os.environ['DATABASE_URL'] = 'sqlite:///finwave.db'

from core.database import get_db_session
from models.integration import IntegrationCredential, IntegrationStatus
from core.crypto import encrypt

with get_db_session() as db:
    # Create a QuickBooks integration
    qb = IntegrationCredential(
        workspace_id="demo",
        source="quickbooks",
        status=IntegrationStatus.CONNECTED.value,
        access_token_encrypted=encrypt("fake_access_token"),
        refresh_token_encrypted=encrypt("fake_refresh_token"),
        expires_at=datetime.utcnow() + timedelta(hours=1),
        metadata_encrypted=encrypt('{"realm_id": "123456789"}'),
        connected_by="test@example.com"
    )
    db.add(qb)
    db.commit()
    
    print("✅ Created QuickBooks integration")
    print(f"Status: {qb.status}")
    print(f"Expires at: {qb.expires_at}")
    
    # Now simulate a sync error
    from scheduler.sync_jobs import enqueue_initial_sync
    from models.integration import mark_integration_synced
    
    # Mark as error
    mark_integration_synced("demo", "quickbooks", error="Test sync error: Unable to fetch data from QuickBooks API")
    
    # Check status
    db.refresh(qb)
    print(f"\nAfter sync error:")
    print(f"Status: {qb.status}")
    print(f"Last sync error: {qb.last_sync_error}")