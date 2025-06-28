#!/usr/bin/env python3
"""
Execute full QuickBooks sync bypassing ScheduledJob issues
"""

import sys
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import get_db_session
from models.integration import IntegrationCredential, mark_integration_synced
from integrations.quickbooks.sync_v2 import sync_quickbooks_data

def execute_full_sync():
    """Execute full QuickBooks sync"""
    
    workspace_id = 'default'
    
    print("=== Executing Full QuickBooks Sync ===")
    print(f"Timestamp: {datetime.now()}")
    
    # Get integration
    with get_db_session() as db:
        integration = db.query(IntegrationCredential).filter_by(
            workspace_id=workspace_id,
            source='quickbooks'
        ).first()
        
        if not integration:
            print("❌ No QuickBooks integration found")
            return
        
        print(f"✅ Found integration: {integration.status}")
        
        # Extract all needed data while session is open
        integration_data = {
            'access_token': integration.access_token,
            'refresh_token': integration.refresh_token,
            'expires_at': integration.expires_at,
            'metadata': integration.integration_metadata or {},
            'last_synced_at': integration.last_synced_at
        }
    
    # Create a minimal integration object for sync
    class IntegrationProxy:
        def __init__(self, data):
            self.access_token = data['access_token']
            self.refresh_token = data['refresh_token']
            self.expires_at = data['expires_at']
            self.integration_metadata = data['metadata']
            self.last_synced_at = data['last_synced_at']
        
        def is_expired(self):
            if not self.expires_at:
                return True
            return datetime.utcnow() > self.expires_at
    
    integration_proxy = IntegrationProxy(integration_data)
    
    # Execute sync
    print("\nStarting sync...")
    try:
        result = sync_quickbooks_data(workspace_id, integration_proxy)
        print(f"\n✅ Sync completed successfully!")
        print(f"Result: {result}")
        
        # Update sync status
        mark_integration_synced(workspace_id, 'quickbooks')
        
    except Exception as e:
        print(f"\n❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Update with error
        mark_integration_synced(workspace_id, 'quickbooks', error=str(e))
    
    # Check metrics
    print("\n=== Checking Metrics ===")
    from metrics.models import Metric
    
    with get_db_session() as db:
        metric_count = db.query(Metric).filter_by(
            workspace_id=workspace_id
        ).count()
        
        print(f"Total metrics: {metric_count}")
        
        # Show recent metrics
        metrics = db.query(Metric).filter_by(
            workspace_id=workspace_id
        ).order_by(Metric.updated_at.desc()).limit(10).all()
        
        if metrics:
            print("\nRecent metrics:")
            for m in metrics:
                print(f"  {m.metric_id}: ${m.value:,.2f} ({m.period_date})")
        else:
            print("No metrics found")


if __name__ == "__main__":
    execute_full_sync()