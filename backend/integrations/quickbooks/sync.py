"""
QuickBooks data sync implementation
"""

import logging
from datetime import datetime, date
from typing import Dict, Any

from models.integration import IntegrationCredential
from integrations.quickbooks.client import QuickBooksClient
from metrics.ingest import ingest_metrics
from core.database import get_db_session
from metrics.models import Metric

logger = logging.getLogger(__name__)


def sync_quickbooks_data(workspace_id: str, integration: IntegrationCredential) -> Dict[str, Any]:
    """
    Sync QuickBooks data to metric store
    """
    logger.info(f"Starting QuickBooks sync for workspace {workspace_id}")
    
    try:
        # Get OAuth credentials for workspace
        from core.oauth_config import get_oauth_credentials
        credentials = get_oauth_credentials(workspace_id, 'quickbooks')
        if not credentials:
            raise ValueError("QuickBooks OAuth not configured for workspace")
        
        client_id, client_secret = credentials
        
        # Get realm_id from metadata
        metadata = {}
        if integration.integration_metadata:
            try:
                metadata = integration.integration_metadata
            except Exception as e:
                logger.warning(f"Failed to get integration metadata: {e}")
        
        # Initialize client with proper credentials
        realm_id = metadata.get('realm_id')
        logger.info(f"Initializing QuickBooks client with realm_id: {realm_id}")
        
        if not realm_id:
            logger.error("CRITICAL: No realm_id found in integration metadata!")
            logger.error(f"Metadata contents: {metadata}")
            raise ValueError("Missing realm_id in integration metadata")
        
        client = QuickBooksClient(
            client_id=client_id,
            client_secret=client_secret,
            company_id=realm_id
        )
        # Set tokens directly
        client.access_token = integration.access_token
        client.refresh_token_value = integration.refresh_token
        # Set token expiry if available
        if integration.expires_at:
            client.token_expiry = integration.expires_at
        else:
            # Set a default expiry (1 hour from last update)
            from datetime import timedelta
            client.token_expiry = integration.updated_at + timedelta(hours=1)
        
        records_processed = 0
        
        # 1. Sync P&L data
        logger.info("Fetching P&L report...")
        try:
            pl_data = client.get_profit_loss_report(
                start_date=(date.today().replace(day=1).replace(month=1)).isoformat(),
                end_date=date.today().isoformat()
            )
            logger.info(f"P&L data type: {type(pl_data)}")
            logger.info(f"P&L data: {pl_data if isinstance(pl_data, dict) else str(pl_data)[:200]}")
            
            if pl_data and isinstance(pl_data, dict):
                # Extract metrics from P&L
                metrics_extracted = extract_pl_metrics(workspace_id, pl_data)
                records_processed += metrics_extracted
                logger.info(f"Extracted {metrics_extracted} P&L metrics")
            else:
                logger.warning(f"P&L report returned non-dict data: {type(pl_data)}")
        except Exception as e:
            logger.error(f"Error fetching P&L report: {e}")
            logger.error(f"Error type: {type(e)}")
        
        # 2. Sync Balance Sheet
        logger.info("Fetching Balance Sheet...")
        try:
            bs_data = client.get_balance_sheet_report(
                as_of_date=date.today().isoformat()
            )
            logger.info(f"Balance Sheet data type: {type(bs_data)}")
            if isinstance(bs_data, dict):
                logger.info(f"Balance Sheet keys: {list(bs_data.keys())}")
            
            if bs_data and isinstance(bs_data, dict):
                # Extract balance sheet metrics
                metrics_extracted = extract_balance_sheet_metrics(workspace_id, bs_data)
                records_processed += metrics_extracted
                logger.info(f"Extracted {metrics_extracted} balance sheet metrics")
            else:
                logger.warning(f"Balance Sheet returned non-dict data: {type(bs_data)}")
        except Exception as e:
            logger.error(f"Error in Balance Sheet sync: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        # 3. Sync Customer data
        logger.info("Fetching customers...")
        customers = client.get_customers()
        if customers:
            # Calculate customer metrics
            customer_metrics = calculate_customer_metrics(workspace_id, customers)
            records_processed += customer_metrics
            logger.info(f"Calculated {customer_metrics} customer metrics")
        
        # 4. Sync Invoice data for AR
        logger.info("Fetching invoices...")
        invoices = client.get_invoices()
        if invoices:
            # Calculate AR metrics
            ar_metrics = calculate_ar_metrics(workspace_id, invoices)
            records_processed += ar_metrics
            logger.info(f"Calculated {ar_metrics} AR metrics")
        
        return {
            'status': 'success',
            'records_processed': records_processed,
            'last_sync': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"QuickBooks sync failed: {e}")
        raise


def extract_pl_metrics(workspace_id: str, pl_data: dict) -> int:
    """
    Extract P&L metrics from QuickBooks report
    """
    metrics_created = 0
    current_period = date.today().replace(day=1)
    
    with get_db_session() as db:
        # Map QB accounts to standard metrics
        metric_mappings = {
            'Total Income': 'revenue',
            'Total Cost of Goods Sold': 'cogs',
            'Gross Profit': 'gross_profit',
            'Total Expenses': 'opex',
            'Net Income': 'net_income'
        }
        
        # Parse report data - QuickBooks returns nested structure
        rows_data = pl_data.get('Rows', {})
        if isinstance(rows_data, dict) and 'Row' in rows_data:
            rows = rows_data['Row']
        else:
            rows = []
            
        for row in rows:
            if row.get('type') == 'Section':
                section_name = row.get('Summary', {}).get('ColData', [{}])[0].get('value')
                
                if section_name in metric_mappings:
                    metric_id = metric_mappings[section_name]
                    
                    # Get value from summary
                    value_data = row.get('Summary', {}).get('ColData', [])
                    if len(value_data) > 1:
                        value = float(value_data[1].get('value', 0))
                        
                        # Create or update metric
                        existing = db.query(Metric).filter_by(
                            workspace_id=workspace_id,
                            metric_id=metric_id,
                            period_date=current_period
                        ).first()
                        
                        if existing:
                            existing.value = value
                            existing.source_template = 'quickbooks_sync'
                            existing.updated_at = datetime.utcnow()
                        else:
                            metric = Metric(
                                workspace_id=workspace_id,
                                metric_id=metric_id,
                                period_date=current_period,
                                value=value,
                                source_template='quickbooks_sync',
                                unit='dollars'
                            )
                            db.add(metric)
                        
                        metrics_created += 1
        
        # Calculate derived metrics
        revenue = db.query(Metric).filter_by(
            workspace_id=workspace_id,
            metric_id='revenue',
            period_date=current_period
        ).first()
        
        if revenue and revenue.value > 0:
            # Gross margin %
            gross_profit = db.query(Metric).filter_by(
                workspace_id=workspace_id,
                metric_id='gross_profit',
                period_date=current_period
            ).first()
            
            if gross_profit:
                gross_margin = (gross_profit.value / revenue.value) * 100
                
                # Store gross margin
                gm_metric = Metric(
                    workspace_id=workspace_id,
                    metric_id='gross_margin',
                    period_date=current_period,
                    value=gross_margin,
                    source_template='quickbooks_sync',
                    unit='percentage'
                )
                db.merge(gm_metric)
                metrics_created += 1
        
        db.commit()
    
    return metrics_created


def extract_balance_sheet_metrics(workspace_id: str, bs_data: dict) -> int:
    """
    Extract balance sheet metrics from QuickBooks report
    """
    metrics_created = 0
    current_period = date.today().replace(day=1)
    
    with get_db_session() as db:
        # Process all rows recursively to find bank accounts and other metrics
        def process_rows(rows, parent_section=""):
            nonlocal metrics_created
            
            for row in rows:
                row_type = row.get('type', '')
                
                if row_type == 'Section':
                    # Get section name
                    section_data = row.get('Header', {}).get('ColData', [{}])
                    if section_data:
                        section_name = section_data[0].get('value', '')
                        
                        # Process nested rows in this section - handle dict structure
                        if 'Rows' in row:
                            nested_rows = row['Rows']
                            if isinstance(nested_rows, dict) and 'Row' in nested_rows:
                                process_rows(nested_rows['Row'], section_name)
                            elif isinstance(nested_rows, list):
                                process_rows(nested_rows, section_name)
                        
                        # Check if this section has a summary we care about
                        if 'Summary' in row:
                            summary_data = row['Summary'].get('ColData', [])
                            if len(summary_data) > 1:
                                summary_name = summary_data[0].get('value', '')
                                value_str = summary_data[1].get('value', '0')
                                # Handle empty strings
                                if value_str == '' or value_str is None:
                                    value_str = '0'
                                summary_value = float(value_str)
                                
                                # Map specific summaries to metrics
                                if summary_name == 'Total Bank Accounts' or (parent_section == 'Current Assets' and summary_name == 'Total Bank'):
                                    # This is the cash balance
                                    logger.info(f"Found cash balance: {summary_value}")
                                    save_metric(db, workspace_id, 'cash', summary_value, current_period)
                                    metrics_created += 1
                                elif summary_name == 'Total Accounts Receivable (A/R)':
                                    save_metric(db, workspace_id, 'accounts_receivable', summary_value, current_period)
                                    metrics_created += 1
                                elif summary_name == 'Total Current Assets':
                                    save_metric(db, workspace_id, 'current_assets', summary_value, current_period)
                                    metrics_created += 1
                                elif summary_name == 'Total Fixed Assets':
                                    save_metric(db, workspace_id, 'fixed_assets', summary_value, current_period)
                                    metrics_created += 1
                                elif summary_name == 'Total Assets':
                                    save_metric(db, workspace_id, 'total_assets', summary_value, current_period)
                                    metrics_created += 1
                                elif summary_name == 'Total Current Liabilities':
                                    save_metric(db, workspace_id, 'current_liabilities', summary_value, current_period)
                                    metrics_created += 1
                                elif summary_name == 'Total Liabilities':
                                    save_metric(db, workspace_id, 'total_liabilities', summary_value, current_period)
                                    metrics_created += 1
                
                elif row_type == 'Data':
                    # Individual account line items
                    col_data = row.get('ColData', [])
                    if len(col_data) > 1:
                        account_name = col_data[0].get('value', '')
                        value_str = col_data[1].get('value', '0')
                        # Handle empty strings
                        if value_str == '' or value_str is None:
                            value_str = '0'
                        account_value = float(value_str)
                        
                        # Log individual bank accounts for debugging
                        if parent_section == 'Bank Accounts' or 'bank' in account_name.lower():
                            logger.info(f"Found bank account: {account_name} = {account_value}")
        
        # Helper function to save/update metric
        def save_metric(db, workspace_id, metric_id, value, period):
            existing = db.query(Metric).filter_by(
                workspace_id=workspace_id,
                metric_id=metric_id,
                period_date=period
            ).first()
            
            if existing:
                existing.value = value
                existing.source_template = 'quickbooks_sync'
                existing.updated_at = datetime.utcnow()
            else:
                metric = Metric(
                    workspace_id=workspace_id,
                    metric_id=metric_id,
                    period_date=period,
                    value=value,
                    source_template='quickbooks_sync',
                    unit='dollars'
                )
                db.add(metric)
        
        # Start processing from top-level rows - QuickBooks returns nested structure
        rows_data = bs_data.get('Rows', {})
        if isinstance(rows_data, dict) and 'Row' in rows_data:
            rows = rows_data['Row']
        else:
            rows = []
        process_rows(rows)
        
        db.commit()
        logger.info(f"Extracted {metrics_created} balance sheet metrics")
    
    return metrics_created


def calculate_customer_metrics(workspace_id: str, customers: list) -> int:
    """
    Calculate customer-related metrics
    """
    current_period = date.today().replace(day=1)
    
    # Count active customers
    active_customers = len([c for c in customers if c.get('Active')])
    
    with get_db_session() as db:
        metric = Metric(
            workspace_id=workspace_id,
            metric_id='customer_count',
            period_date=current_period,
            value=active_customers,
            source_template='quickbooks_sync',
            unit='count'
        )
        db.merge(metric)
        db.commit()
    
    return 1


def calculate_ar_metrics(workspace_id: str, invoices: list) -> int:
    """
    Calculate accounts receivable metrics
    """
    current_period = date.today().replace(day=1)
    
    # Calculate total AR
    total_ar = sum(
        float(inv.get('Balance', 0)) 
        for inv in invoices 
        if inv.get('Balance', 0) > 0
    )
    
    with get_db_session() as db:
        metric = Metric(
            workspace_id=workspace_id,
            metric_id='accounts_receivable',
            period_date=current_period,
            value=total_ar,
            source_template='quickbooks_sync',
            unit='dollars'
        )
        db.merge(metric)
        db.commit()
    
    return 1