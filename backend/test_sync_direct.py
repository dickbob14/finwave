#!/usr/bin/env python3
"""
Test QuickBooks sync directly without job logging
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import get_db_session
from models.integration import IntegrationCredential
from integrations.quickbooks.sync_v2 import sync_quickbooks_data

def test_direct_sync():
    """Test sync directly"""
    workspace_id = 'default'
    
    print(f"Testing direct sync for workspace: {workspace_id}")
    print("=" * 50)
    
    with get_db_session() as db:
        # Get integration
        integration = db.query(IntegrationCredential).filter_by(
            workspace_id=workspace_id,
            source='quickbooks'
        ).first()
        
        if not integration:
            print("❌ No QuickBooks integration found")
            return
        
        print(f"✅ Found integration")
        print(f"   Status: {integration.status}")
        print(f"   Has token: {bool(integration.access_token)}")
        
        # Make a copy of integration data before session closes
        integration_data = {
            'id': integration.id,
            'workspace_id': integration.workspace_id,
            'source': integration.source,
            'access_token': integration.access_token,
            'refresh_token': integration.refresh_token,
            'expires_at': integration.expires_at,
            'integration_metadata': integration.integration_metadata,  # Use the property
            'last_synced_at': integration.last_synced_at
        }
    
    # Create a new integration object outside the session
    integration_obj = IntegrationCredential()
    for key, value in integration_data.items():
        if key == 'integration_metadata':
            # Handle metadata specially
            integration_obj.integration_metadata = value
        else:
            setattr(integration_obj, key, value)
    
    print("\n🚀 Starting sync...")
    try:
        result = sync_quickbooks_data(workspace_id, integration_obj)
        print("\n✅ Sync completed!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"\n❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_direct_sync()