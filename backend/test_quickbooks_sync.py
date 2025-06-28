#!/usr/bin/env python3
"""
Test QuickBooks sync manually
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import get_db_session
from models.integration import get_integration
from integrations.quickbooks.sync_v2 import sync_quickbooks_data

def test_sync(workspace_id: str = 'default'):
    """Test QuickBooks sync for a workspace"""
    print(f"\n🔄 Testing QuickBooks sync for workspace: {workspace_id}")
    print("=" * 50)
    
    # Get integration
    integration = get_integration(workspace_id, 'quickbooks')
    
    if not integration:
        print("❌ No QuickBooks integration found")
        print("   Please connect QuickBooks first in the UI")
        return
    
    print(f"✅ Found integration:")
    print(f"   Status: {integration.status}")
    print(f"   Last synced: {integration.last_synced_at}")
    print(f"   Has access token: {'Yes' if integration.access_token else 'No'}")
    
    if integration.status != 'connected':
        print("⚠️  Integration status is not 'connected'")
        print("   You may need to reconnect")
        return
    
    # Run sync
    print("\n🚀 Starting sync...")
    try:
        result = sync_quickbooks_data(workspace_id, integration)
        
        print("\n✅ Sync completed!")
        print(f"   Status: {result.get('status')}")
        print(f"   Records processed: {result.get('records_processed')}")
        
        if 'details' in result:
            print("\n📊 Details:")
            for key, value in result['details'].items():
                print(f"   {key}: {value}")
                
    except Exception as e:
        print(f"\n❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Check metrics
    print("\n📈 Checking metrics in database...")
    with get_db_session() as db:
        from metrics.models import Metric
        from datetime import date
        
        current_period = date.today().replace(day=1)
        metrics = db.query(Metric).filter(
            Metric.workspace_id == workspace_id,
            Metric.period_date == current_period
        ).all()
        
        if metrics:
            print(f"   Found {len(metrics)} metrics for current period:")
            for metric in metrics[:10]:  # Show first 10
                print(f"   - {metric.metric_id}: ${metric.value:,.2f}")
        else:
            print("   No metrics found for current period")


if __name__ == "__main__":
    workspace_id = sys.argv[1] if len(sys.argv) > 1 else 'default'
    test_sync(workspace_id)