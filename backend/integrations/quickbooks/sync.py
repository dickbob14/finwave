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
        # Initialize client
        client = QuickBooksClient(
            access_token=integration.access_token,
            refresh_token=integration.refresh_token,
            realm_id=integration.metadata.get('realm_id'),
            environment='production' if 'sandbox' not in integration.metadata.get('realm_id', '') else 'sandbox'
        )
        
        records_processed = 0
        
        # 1. Sync P&L data
        logger.info("Fetching P&L report...")
        pl_data = client.get_profit_loss_report(
            start_date=(date.today().replace(day=1).replace(month=1)).isoformat(),
            end_date=date.today().isoformat()
        )
        
        if pl_data:
            # Extract metrics from P&L
            metrics_extracted = extract_pl_metrics(workspace_id, pl_data)
            records_processed += metrics_extracted
            logger.info(f"Extracted {metrics_extracted} P&L metrics")
        
        # 2. Sync Balance Sheet
        logger.info("Fetching Balance Sheet...")
        bs_data = client.get_balance_sheet_report(
            as_of_date=date.today().isoformat()
        )
        
        if bs_data:
            # Extract balance sheet metrics
            metrics_extracted = extract_balance_sheet_metrics(workspace_id, bs_data)
            records_processed += metrics_extracted
            logger.info(f"Extracted {metrics_extracted} balance sheet metrics")
        
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
        
        # Parse report data
        for row in pl_data.get('Rows', []):
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
    Extract balance sheet metrics
    """
    metrics_created = 0
    current_period = date.today().replace(day=1)
    
    with get_db_session() as db:
        # Map accounts
        metric_mappings = {
            'Total Bank Accounts': 'cash',
            'Total Current Assets': 'current_assets',
            'Total Fixed Assets': 'fixed_assets',
            'Total Assets': 'total_assets',
            'Total Current Liabilities': 'current_liabilities',
            'Total Liabilities': 'total_liabilities'
        }
        
        # Similar parsing logic as P&L
        # ... (implementation similar to extract_pl_metrics)
        
        db.commit()
    
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