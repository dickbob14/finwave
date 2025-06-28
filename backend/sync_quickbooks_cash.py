#!/usr/bin/env python3
"""Direct sync of QuickBooks cash/bank accounts"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.integration import IntegrationCredential
from integrations.quickbooks.client import QuickBooksClient
from core.database import get_db_session
from metrics.models import Metric
from datetime import date, datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_cash_directly():
    """Fetch bank accounts directly using query API"""
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
        
        current_period = date.today().replace(day=1)
        
        try:
            # Method 1: Query bank accounts directly
            print("\n=== Method 1: Direct Account Query ===")
            query = "SELECT * FROM Account WHERE AccountType = 'Bank' MAXRESULTS 20"
            response = client.query(query)
            
            accounts = response.get('QueryResponse', {}).get('Account', [])
            print(f"Found {len(accounts)} bank accounts")
            
            total_cash = 0
            for account in accounts:
                balance = float(account.get('CurrentBalance', 0))
                total_cash += balance
                print(f"  {account.get('Name')}: ${balance:,.2f}")
            
            print(f"\nTotal Cash (from accounts): ${total_cash:,.2f}")
            
            # Store cash metric
            existing = db.query(Metric).filter_by(
                workspace_id='default',
                metric_id='cash',
                period_date=current_period
            ).first()
            
            if existing:
                print(f"Updating cash from ${existing.value:,.2f} to ${total_cash:,.2f}")
                existing.value = total_cash
                existing.source_template = 'quickbooks_sync'
                existing.updated_at = datetime.utcnow()
            else:
                metric = Metric(
                    workspace_id='default',
                    metric_id='cash',
                    period_date=current_period,
                    value=total_cash,
                    source_template='quickbooks_sync',
                    unit='dollars'
                )
                db.add(metric)
                print(f"Created cash metric: ${total_cash:,.2f}")
            
            # Method 2: Get Balance Sheet Report
            print("\n=== Method 2: Balance Sheet Report ===")
            bs_data = client.get_balance_sheet_report(
                as_of_date=date.today().isoformat()
            )
            
            # Import and use the new extraction function
            from integrations.quickbooks.sync import extract_balance_sheet_metrics
            metrics_extracted = extract_balance_sheet_metrics('default', bs_data)
            print(f"Extracted {metrics_extracted} metrics from balance sheet")
            
            db.commit()
            
            # Show all metrics
            print("\n=== Current Metrics ===")
            metrics = db.query(Metric).filter_by(
                workspace_id='default',
                period_date=current_period
            ).order_by(Metric.metric_id).all()
            
            for m in metrics:
                print(f"{m.metric_id}: ${m.value:,.2f} (source: {m.source_template})")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    sync_cash_directly()