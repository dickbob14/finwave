#!/usr/bin/env python3
"""
FinWave QuickBooks Sync Service
Handles sync execution with proper error handling and schema workarounds
"""

import sys
import os
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import get_db_session
from models.integration import IntegrationCredential, mark_integration_synced
from metrics.models import Metric
from integrations.quickbooks.client import QuickBooksClient
from core.oauth_config import get_oauth_credentials


class FinWaveSyncService:
    """Handles QuickBooks sync with database workarounds"""
    
    def __init__(self, workspace_id: str = 'default'):
        self.workspace_id = workspace_id
        self.metrics_created = 0
        self.metrics_updated = 0
        
    def run_sync(self) -> Dict[str, Any]:
        """Execute complete sync process"""
        logger.info(f"Starting FinWave sync for workspace {self.workspace_id}")
        
        try:
            # Get integration
            integration_data = self._get_integration_data()
            if not integration_data:
                return {'status': 'error', 'message': 'No QuickBooks integration found'}
            
            # Initialize client
            client = self._initialize_client(integration_data)
            
            # Test connection
            company_info = client.fetch_company_info()
            logger.info(f"Connected to: {company_info.get('CompanyName', 'Unknown')}")
            
            # Sync data based on last sync time
            if integration_data['last_synced_at']:
                result = self._incremental_sync(client, integration_data['last_synced_at'])
            else:
                result = self._full_sync(client)
            
            # Update sync status
            mark_integration_synced(self.workspace_id, 'quickbooks')
            
            return {
                'status': 'success',
                'company': company_info.get('CompanyName'),
                'metrics_created': self.metrics_created,
                'metrics_updated': self.metrics_updated,
                **result
            }
            
        except Exception as e:
            logger.error(f"Sync failed: {e}", exc_info=True)
            mark_integration_synced(self.workspace_id, 'quickbooks', error=str(e))
            return {'status': 'error', 'message': str(e)}
    
    def _get_integration_data(self) -> Optional[Dict[str, Any]]:
        """Get integration data from database"""
        with get_db_session() as db:
            integration = db.query(IntegrationCredential).filter_by(
                workspace_id=self.workspace_id,
                source='quickbooks'
            ).first()
            
            if not integration:
                return None
            
            # Extract all data while session is open
            return {
                'access_token': integration.access_token,
                'refresh_token': integration.refresh_token,
                'expires_at': integration.expires_at,
                'metadata': integration.integration_metadata or {},
                'last_synced_at': integration.last_synced_at
            }
    
    def _initialize_client(self, integration_data: Dict[str, Any]) -> QuickBooksClient:
        """Initialize QuickBooks client"""
        credentials = get_oauth_credentials(self.workspace_id, 'quickbooks')
        if not credentials:
            raise ValueError("QuickBooks OAuth not configured")
        
        client_id, client_secret = credentials
        realm_id = integration_data['metadata'].get('realm_id')
        
        if not realm_id:
            raise ValueError("No realm_id found in integration metadata")
        
        client = QuickBooksClient(
            client_id=client_id,
            client_secret=client_secret,
            company_id=realm_id
        )
        
        # Set tokens
        client.access_token = integration_data['access_token']
        client.refresh_token_value = integration_data['refresh_token']
        client.token_expiry = integration_data['expires_at'] or (datetime.utcnow() + timedelta(hours=1))
        
        return client
    
    def _full_sync(self, client: QuickBooksClient) -> Dict[str, Any]:
        """Perform full sync of all data"""
        logger.info("Performing full sync...")
        
        # Sync financial data
        self._sync_invoices(client)
        self._sync_bills(client)
        self._sync_accounts(client)
        self._sync_reports(client)
        
        # Calculate KPIs
        self._calculate_kpis()
        
        return {
            'sync_type': 'full',
            'records_processed': self.metrics_created + self.metrics_updated
        }
    
    def _incremental_sync(self, client: QuickBooksClient, last_sync: datetime) -> Dict[str, Any]:
        """Perform incremental sync of changed data"""
        logger.info(f"Performing incremental sync since {last_sync}")
        
        # For now, just sync current month data
        self._sync_current_month(client)
        self._calculate_kpis()
        
        return {
            'sync_type': 'incremental',
            'records_processed': self.metrics_created + self.metrics_updated
        }
    
    def _sync_invoices(self, client: QuickBooksClient):
        """Sync invoice data"""
        try:
            # Get last 12 months of invoices
            end_date = date.today()
            start_date = end_date - timedelta(days=365)
            
            invoices = client._fetch_invoices(start_date.isoformat(), end_date.isoformat())
            logger.info(f"Found {len(invoices)} invoices")
            
            # Group by month
            monthly_revenue = {}
            for invoice in invoices:
                invoice_date = datetime.strptime(invoice['TxnDate'], '%Y-%m-%d').date()
                month_key = invoice_date.replace(day=1)
                amount = float(invoice.get('TotalAmt', 0))
                
                if month_key not in monthly_revenue:
                    monthly_revenue[month_key] = 0
                monthly_revenue[month_key] += amount
            
            # Store metrics
            for period_date, revenue in monthly_revenue.items():
                self._upsert_metric('revenue', period_date, revenue)
                
        except Exception as e:
            logger.error(f"Error syncing invoices: {e}")
    
    def _sync_bills(self, client: QuickBooksClient):
        """Sync bill data"""
        try:
            # Get last 12 months of bills
            end_date = date.today()
            start_date = end_date - timedelta(days=365)
            
            bills = client.get_bills(start_date.isoformat(), end_date.isoformat())
            logger.info(f"Found {len(bills)} bills")
            
            # Group by month
            monthly_expenses = {}
            for bill in bills:
                bill_date = datetime.strptime(bill['TxnDate'], '%Y-%m-%d').date()
                month_key = bill_date.replace(day=1)
                amount = float(bill.get('TotalAmt', 0))
                
                if month_key not in monthly_expenses:
                    monthly_expenses[month_key] = 0
                monthly_expenses[month_key] += amount
            
            # Store metrics
            for period_date, expenses in monthly_expenses.items():
                self._upsert_metric('operating_expenses', period_date, expenses)
                
        except Exception as e:
            logger.error(f"Error syncing bills: {e}")
    
    def _sync_accounts(self, client: QuickBooksClient):
        """Sync account balances"""
        try:
            response = client.get_accounts()
            accounts = response.get('Account', [])
            logger.info(f"Found {len(accounts)} accounts")
            
            current_period = date.today().replace(day=1)
            
            # Aggregate by type
            account_totals = {}
            for account in accounts:
                account_type = account.get('AccountType', '')
                balance = float(account.get('CurrentBalance', 0))
                
                metric_id = self._map_account_type_to_metric(account_type)
                if metric_id and balance != 0:
                    if metric_id not in account_totals:
                        account_totals[metric_id] = 0
                    account_totals[metric_id] += abs(balance)
            
            # Store metrics
            for metric_id, value in account_totals.items():
                self._upsert_metric(metric_id, current_period, value)
                
        except Exception as e:
            logger.error(f"Error syncing accounts: {e}")
    
    def _sync_reports(self, client: QuickBooksClient):
        """Sync P&L and Balance Sheet reports"""
        try:
            current_period = date.today().replace(day=1)
            end_date = date.today()
            
            # Try to get P&L report
            try:
                pl_report = client.get_profit_loss_report(
                    current_period.isoformat(),
                    end_date.isoformat()
                )
                # Basic parsing - just look for total revenue/expenses
                logger.info("Retrieved P&L report")
            except Exception as e:
                logger.error(f"Error fetching P&L report: {e}")
            
            # Try to get Balance Sheet
            try:
                bs_report = client.get_balance_sheet_report(end_date.isoformat())
                logger.info("Retrieved Balance Sheet")
            except Exception as e:
                logger.error(f"Error fetching Balance Sheet: {e}")
                
        except Exception as e:
            logger.error(f"Error syncing reports: {e}")
    
    def _sync_current_month(self, client: QuickBooksClient):
        """Sync only current month data"""
        current_period = date.today().replace(day=1)
        end_date = date.today()
        
        # Sync current month invoices
        try:
            query = f"SELECT * FROM Invoice WHERE TxnDate >= '{current_period}' AND TxnDate <= '{end_date}'"
            response = client._make_request('query', {'query': query})
            invoices = response.get('QueryResponse', {}).get('Invoice', [])
            
            total_revenue = sum(float(inv.get('TotalAmt', 0)) for inv in invoices)
            if total_revenue > 0:
                self._upsert_metric('revenue', current_period, total_revenue)
                
        except Exception as e:
            logger.error(f"Error syncing current month invoices: {e}")
    
    def _calculate_kpis(self):
        """Calculate KPI metrics from base metrics"""
        try:
            current_period = date.today().replace(day=1)
            
            with get_db_session() as db:
                # Get base metrics
                metrics = db.query(Metric).filter(
                    Metric.workspace_id == self.workspace_id,
                    Metric.period_date == current_period
                ).all()
                
                metric_values = {m.metric_id: m.value for m in metrics}
                
                # Calculate gross margin if we have revenue
                if 'revenue' in metric_values and metric_values['revenue'] > 0:
                    revenue = metric_values['revenue']
                    cogs = metric_values.get('cogs', 0)
                    gross_profit = revenue - cogs
                    gross_margin = (gross_profit / revenue) * 100
                    
                    self._upsert_metric('gross_profit', current_period, gross_profit)
                    self._upsert_metric('gross_margin_percent', current_period, gross_margin)
                
                # Calculate burn rate
                if 'operating_expenses' in metric_values:
                    monthly_burn = metric_values['operating_expenses']
                    self._upsert_metric('monthly_burn_rate', current_period, monthly_burn)
                    
        except Exception as e:
            logger.error(f"Error calculating KPIs: {e}")
    
    def _upsert_metric(self, metric_id: str, period_date: date, value: float):
        """Insert or update a metric"""
        with get_db_session() as db:
            # Check if metric exists
            existing = db.query(Metric).filter_by(
                workspace_id=self.workspace_id,
                metric_id=metric_id,
                period_date=period_date
            ).first()
            
            if existing:
                existing.value = value
                existing.updated_at = datetime.utcnow()
                self.metrics_updated += 1
            else:
                metric = Metric(
                    workspace_id=self.workspace_id,
                    metric_id=metric_id,
                    period_date=period_date,
                    value=value,
                    source_template='quickbooks_sync',
                    unit='dollars' if 'percent' not in metric_id else 'percentage',
                    currency='USD'
                )
                db.add(metric)
                self.metrics_created += 1
            
            db.commit()
    
    def _map_account_type_to_metric(self, account_type: str) -> Optional[str]:
        """Map QuickBooks account type to metric ID"""
        mapping = {
            'Bank': 'cash',
            'Accounts Receivable': 'accounts_receivable',
            'Other Current Asset': 'current_assets',
            'Fixed Asset': 'fixed_assets',
            'Accounts Payable': 'accounts_payable',
            'Credit Card': 'credit_card_debt',
            'Other Current Liability': 'current_liabilities',
            'Long Term Liability': 'long_term_debt'
        }
        return mapping.get(account_type)


def main():
    """Run sync from command line"""
    print("=== FinWave QuickBooks Sync Service ===")
    print(f"Timestamp: {datetime.now()}")
    
    service = FinWaveSyncService()
    result = service.run_sync()
    
    print(f"\nSync Result: {result['status']}")
    if result['status'] == 'success':
        print(f"Company: {result.get('company')}")
        print(f"Metrics Created: {result.get('metrics_created')}")
        print(f"Metrics Updated: {result.get('metrics_updated')}")
        print(f"Sync Type: {result.get('sync_type')}")
    else:
        print(f"Error: {result.get('message')}")
    
    # Show current metrics
    print("\n=== Current Metrics ===")
    with get_db_session() as db:
        metrics = db.query(Metric).filter_by(
            workspace_id='default'
        ).order_by(Metric.period_date.desc(), Metric.metric_id).limit(20).all()
        
        for m in metrics:
            unit = '$' if m.unit == 'dollars' else '%' if m.unit == 'percentage' else ''
            print(f"{m.metric_id}: {unit}{m.value:,.2f} ({m.period_date})")


if __name__ == "__main__":
    main()