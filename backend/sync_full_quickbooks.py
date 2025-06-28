#!/usr/bin/env python3
"""Sync complete QuickBooks data"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from integrations.quickbooks.client import QuickBooksClient
from models.integration import IntegrationCredential
from core.database import get_db_session
from metrics.models import Metric
from datetime import date, datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_full_quickbooks_data():
    """Fetch comprehensive QuickBooks data"""
    with get_db_session() as db:
        integration = db.query(IntegrationCredential).filter_by(
            workspace_id='default',
            source='quickbooks'
        ).first()
        
        if not integration:
            print("No QuickBooks integration found")
            return
            
        metadata = integration.integration_metadata
        realm_id = metadata.get('realm_id')
        
        # Initialize client
        client = QuickBooksClient(
            company_id=realm_id,
            client_id=os.getenv('QB_CLIENT_ID'),
            client_secret=os.getenv('QB_CLIENT_SECRET')
        )
        # Set tokens directly
        client.access_token = integration.access_token
        client.refresh_token_value = integration.refresh_token
        if integration.expires_at:
            client.token_expiry = integration.expires_at
        
        current_period = date.today().replace(day=1)
        
        # Get P&L Report with more detail
        print("Fetching detailed P&L...")
        try:
            pl_data = client.get_profit_loss_report(
                start_date=current_period.isoformat(),
                end_date=date.today().isoformat()
            )
            
            if pl_data:
                # Extract all expense categories
                for row in pl_data.get('Rows', []):
                    if row.get('type') == 'Section' and 'Expenses' in str(row):
                        # Look for expense details
                        for expense_row in row.get('Rows', []):
                            if expense_row.get('type') == 'Data':
                                cols = expense_row.get('ColData', [])
                                if len(cols) >= 2:
                                    expense_name = cols[0].get('value', '')
                                    expense_value = float(cols[1].get('value', 0))
                                    
                                    if expense_value > 0:
                                        print(f"Expense: {expense_name} = ${expense_value}")
                                        
                                        # Store as operating_expenses (aggregate)
                                        existing = db.query(Metric).filter_by(
                                            workspace_id='default',
                                            metric_id='operating_expenses',
                                            period_date=current_period
                                        ).first()
                                        
                                        if existing:
                                            existing.value += expense_value
                                        else:
                                            metric = Metric(
                                                workspace_id='default',
                                                metric_id='operating_expenses',
                                                period_date=current_period,
                                                value=expense_value,
                                                source_template='quickbooks_sync',
                                                unit='dollars'
                                            )
                                            db.add(metric)
        
        except Exception as e:
            print(f"P&L Error: {e}")
        
        # Get Cash/Bank balance
        print("\nFetching account balances...")
        try:
            # Query bank accounts
            query = "SELECT * FROM Account WHERE AccountType = 'Bank' MAXRESULTS 10"
            accounts = client.query(query)
            
            total_cash = 0
            for account in accounts.get('QueryResponse', {}).get('Account', []):
                balance = float(account.get('CurrentBalance', 0))
                total_cash += balance
                print(f"Account: {account.get('Name')} = ${balance}")
            
            # Store cash metric
            cash_metric = db.query(Metric).filter_by(
                workspace_id='default',
                metric_id='cash',
                period_date=current_period
            ).first()
            
            if cash_metric:
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
                
        except Exception as e:
            print(f"Account query error: {e}")
        
        # Get AR balance
        print("\nFetching AR balance...")
        try:
            # Query AR account
            query = "SELECT * FROM Account WHERE AccountType = 'Accounts Receivable'"
            ar_accounts = client.query(query)
            
            total_ar = 0
            for account in ar_accounts.get('QueryResponse', {}).get('Account', []):
                balance = float(account.get('CurrentBalance', 0))
                total_ar += balance
                print(f"AR Account: {account.get('Name')} = ${balance}")
            
            # Store AR metric
            ar_metric = db.query(Metric).filter_by(
                workspace_id='default',
                metric_id='accounts_receivable',
                period_date=current_period
            ).first()
            
            if ar_metric:
                ar_metric.value = total_ar
                ar_metric.source_template = 'quickbooks_sync'
            else:
                ar_metric = Metric(
                    workspace_id='default',
                    metric_id='accounts_receivable',
                    period_date=current_period,
                    value=total_ar,
                    source_template='quickbooks_sync',
                    unit='dollars'
                )
                db.add(ar_metric)
                
        except Exception as e:
            print(f"AR query error: {e}")
        
        # Calculate additional metrics
        print("\nCalculating derived metrics...")
        
        # Get revenue and expenses for profit calculation
        revenue = db.query(Metric).filter_by(
            workspace_id='default',
            metric_id='revenue',
            period_date=current_period
        ).first()
        
        expenses = db.query(Metric).filter_by(
            workspace_id='default',
            metric_id='operating_expenses',
            period_date=current_period
        ).first()
        
        if revenue and expenses:
            # Net profit
            net_profit = revenue.value - expenses.value
            np_metric = Metric(
                workspace_id='default',
                metric_id='net_profit',
                period_date=current_period,
                value=net_profit,
                source_template='quickbooks_sync',
                unit='dollars'
            )
            db.merge(np_metric)
            
            # Profit margin
            if revenue.value > 0:
                profit_margin = (net_profit / revenue.value)
                pm_metric = Metric(
                    workspace_id='default',
                    metric_id='profit_margin',
                    period_date=current_period,
                    value=profit_margin,
                    source_template='quickbooks_sync',
                    unit='percentage'
                )
                db.merge(pm_metric)
        
        db.commit()
        
        # Show final metrics
        print("\n=== Final Metrics ===")
        metrics = db.query(Metric).filter_by(
            workspace_id='default',
            period_date=current_period,
            source_template='quickbooks_sync'
        ).all()
        
        for m in metrics:
            print(f"{m.metric_id}: {m.value} {m.unit or ''}")

if __name__ == "__main__":
    sync_full_quickbooks_data()