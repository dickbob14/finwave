#!/usr/bin/env python3
"""
Minimal test to sync QuickBooks data and populate metrics
"""

import sys
import os
import logging
from datetime import datetime, date, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import get_db_session
from models.integration import IntegrationCredential
from integrations.quickbooks.client import QuickBooksClient
from metrics.models import Metric
from core.oauth_config import get_oauth_credentials

def test_minimal_sync():
    """Test minimal sync - just pull a few invoices"""
    
    workspace_id = 'default'
    
    print("=== Minimal QuickBooks Sync Test ===")
    
    # Get integration and keep session open
    with get_db_session() as db:
        integration = db.query(IntegrationCredential).filter_by(
            workspace_id=workspace_id,
            source='quickbooks'
        ).first()
        
        if not integration:
            print("❌ No QuickBooks integration found")
            return
        
        print(f"✅ Found integration: {integration.status}")
        
        # Extract data while session is open
        access_token = integration.access_token
        refresh_token = integration.refresh_token
        expires_at = integration.expires_at
        metadata = integration.integration_metadata or {}
    
    # Initialize client
    print("\n1. Initializing QuickBooks client...")
    
    try:
        credentials = get_oauth_credentials(workspace_id, 'quickbooks')
        if not credentials:
            print("❌ No OAuth credentials configured")
            return
        
        client_id, client_secret = credentials
        
        # Get realm_id from previously extracted metadata
        realm_id = metadata.get('realm_id')
        
        if not realm_id:
            print("❌ No realm_id in metadata")
            return
        
        print(f"  Client ID: {client_id[:10]}...")
        print(f"  Realm ID: {realm_id}")
        
        # Create client
        client = QuickBooksClient(
            client_id=client_id,
            client_secret=client_secret,
            company_id=realm_id
        )
        
        # Set tokens from previously extracted data
        client.access_token = access_token
        client.refresh_token_value = refresh_token
        
        if expires_at:
            client.token_expiry = expires_at
        else:
            client.token_expiry = datetime.utcnow() + timedelta(hours=1)
        
        print("✅ Client initialized")
        
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test API connection
    print("\n2. Testing API connection...")
    try:
        company_info = client.fetch_company_info()
        print(f"✅ Connected to: {company_info.get('CompanyName', 'Unknown')}")
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return
    
    # Fetch some invoices
    print("\n3. Fetching recent invoices...")
    try:
        # Get last 30 days
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        query = f"SELECT * FROM Invoice WHERE TxnDate >= '{start_date}' AND TxnDate <= '{end_date}' MAXRESULTS 5"
        response = client._make_request('query', {'query': query})
        
        invoices = response.get('QueryResponse', {}).get('Invoice', [])
        print(f"✅ Found {len(invoices)} invoices")
        
        if invoices:
            # Show first invoice
            invoice = invoices[0]
            print(f"\nSample invoice:")
            print(f"  Date: {invoice.get('TxnDate')}")
            print(f"  Number: {invoice.get('DocNumber')}")
            print(f"  Amount: ${invoice.get('TotalAmt')}")
            print(f"  Customer: {invoice.get('CustomerRef', {}).get('name')}")
        
    except Exception as e:
        print(f"❌ Failed to fetch invoices: {e}")
        return
    
    # Store as metrics
    print("\n4. Storing as metrics...")
    try:
        with get_db_session() as db:
            # Calculate total revenue
            total_revenue = sum(float(inv.get('TotalAmt', 0)) for inv in invoices)
            current_period = date.today().replace(day=1)
            
            # Create revenue metric
            metric = Metric(
                workspace_id=workspace_id,
                metric_id='revenue',
                period_date=current_period,
                value=total_revenue,
                source_template='quickbooks_sync',
                unit='dollars',
                currency='USD'
            )
            
            # Use merge to update if exists
            db.merge(metric)
            db.commit()
            
            print(f"✅ Stored revenue metric: ${total_revenue}")
            
            # Also create a test metric
            test_metric = Metric(
                workspace_id=workspace_id,
                metric_id='test_metric',
                period_date=current_period,
                value=123.45,
                source_template='quickbooks_sync',
                unit='dollars',
                currency='USD'
            )
            db.merge(test_metric)
            db.commit()
            
            print("✅ Stored test metric")
            
    except Exception as e:
        print(f"❌ Failed to store metrics: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Verify metrics exist
    print("\n5. Verifying metrics...")
    with get_db_session() as db:
        metric_count = db.query(Metric).filter_by(
            workspace_id=workspace_id
        ).count()
        print(f"✅ Total metrics in database: {metric_count}")
        
        # Show metrics
        metrics = db.query(Metric).filter_by(
            workspace_id=workspace_id
        ).all()
        
        for m in metrics:
            print(f"  - {m.metric_id}: ${m.value} ({m.period_date})")
    
    # Update sync status
    print("\n6. Updating sync status...")
    try:
        from models.integration import mark_integration_synced
        mark_integration_synced(workspace_id, 'quickbooks')
        print("✅ Sync status updated")
    except Exception as e:
        print(f"❌ Failed to update sync status: {e}")
    
    print("\n✅ Minimal sync test completed!")
    print("Check the dashboard to see if data appears.")


if __name__ == "__main__":
    test_minimal_sync()