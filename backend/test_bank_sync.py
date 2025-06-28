#!/usr/bin/env python3
"""Test fetching real bank account data from QuickBooks"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.integration import IntegrationCredential
from core.database import get_db_session
from metrics.models import Metric
from datetime import date
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_bank_sync():
    """Test fetching bank accounts from QuickBooks"""
    with get_db_session() as db:
        # Get QuickBooks integration
        integration = db.query(IntegrationCredential).filter_by(
            workspace_id='default',
            source='quickbooks'
        ).first()
        
        if not integration:
            print("No QuickBooks integration found")
            return
            
        metadata = integration.integration_metadata
        realm_id = metadata.get('realm_id')
        print(f"Using realm_id: {realm_id}")
        
        # Import here to avoid pandas dependency at module level
        from integrations.quickbooks.client import QuickBooksClient
        
        # Initialize client
        client = QuickBooksClient(
            company_id=realm_id,
            client_id=os.getenv('QB_CLIENT_ID'),
            client_secret=os.getenv('QB_CLIENT_SECRET')
        )
        
        # Set tokens
        client.access_token = integration.access_token
        client.refresh_token_value = integration.refresh_token
        if integration.expires_at:
            client.token_expiry = integration.expires_at
        
        print("\nFetching bank accounts...")
        try:
            # Query bank accounts using the new query method
            query = "SELECT * FROM Account WHERE AccountType = 'Bank' MAXRESULTS 10"
            response = client.query(query)
            
            accounts = response.get('QueryResponse', {}).get('Account', [])
            print(f"Found {len(accounts)} bank accounts")
            
            total_cash = 0
            for account in accounts:
                balance = float(account.get('CurrentBalance', 0))
                total_cash += balance
                print(f"  {account.get('Name')}: ${balance:,.2f}")
            
            print(f"\nTotal Cash Balance: ${total_cash:,.2f}")
            
            # Store in metrics
            current_period = date.today().replace(day=1)
            
            cash_metric = db.query(Metric).filter_by(
                workspace_id='default',
                metric_id='cash',
                period_date=current_period
            ).first()
            
            if cash_metric:
                print(f"\nUpdating cash metric from ${cash_metric.value:,.2f} to ${total_cash:,.2f}")
                cash_metric.value = total_cash
                cash_metric.source_template = 'quickbooks_sync'
            else:
                cash_metric = Metric(
                    workspace_id='default',
                    metric_id='cash',
                    period_date=current_period,
                    value=total_cash,
                    source_template='quickbooks_sync',
                    unit='dollars'
                )
                db.add(cash_metric)
                print(f"\nCreated new cash metric: ${total_cash:,.2f}")
            
            db.commit()
            print("\nCash metric updated successfully!")
            
        except Exception as e:
            print(f"Error fetching bank accounts: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_bank_sync()