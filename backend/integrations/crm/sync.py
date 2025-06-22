"""
CRM data sync implementation (Salesforce/HubSpot)
"""

import logging
from datetime import datetime, date
from typing import Dict, Any

from models.integration import IntegrationCredential
from integrations.crm.client import create_crm_client
from core.database import get_db_session
from metrics.models import Metric

logger = logging.getLogger(__name__)


def sync_crm_data(workspace_id: str, integration: IntegrationCredential) -> Dict[str, Any]:
    """
    Sync CRM data to metric store
    """
    logger.info(f"Starting CRM sync for workspace {workspace_id} ({integration.source})")
    
    try:
        # Initialize appropriate client
        client = create_crm_client(
            integration.source,
            access_token=integration.access_token,
            refresh_token=integration.refresh_token,
            instance_url=integration.metadata.get('instance_url')  # For Salesforce
        )
        
        records_processed = 0
        current_period = date.today().replace(day=1)
        
        # 1. Sync pipeline/opportunities
        logger.info("Fetching opportunities...")
        opportunities = client.fetch_opportunities()
        
        if opportunities:
            # Calculate pipeline metrics
            pipeline_metrics = calculate_pipeline_metrics(
                workspace_id, opportunities, current_period
            )
            records_processed += pipeline_metrics
            logger.info(f"Calculated {pipeline_metrics} pipeline metrics")
        
        # 2. Sync accounts/companies
        logger.info("Fetching accounts...")
        accounts = client.fetch_accounts()
        
        if accounts:
            # Calculate account metrics
            account_metrics = calculate_account_metrics(
                workspace_id, accounts, current_period
            )
            records_processed += account_metrics
            logger.info(f"Calculated {account_metrics} account metrics")
        
        # 3. Sync activities
        logger.info("Fetching activities...")
        activities = client.fetch_activities()
        
        if activities:
            # Calculate activity metrics
            activity_metrics = calculate_activity_metrics(
                workspace_id, activities, current_period
            )
            records_processed += activity_metrics
            logger.info(f"Calculated {activity_metrics} activity metrics")
        
        return {
            'status': 'success',
            'records_processed': records_processed,
            'last_sync': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"CRM sync failed: {e}")
        raise


def calculate_pipeline_metrics(workspace_id: str, opportunities: list, 
                             period: date) -> int:
    """
    Calculate sales pipeline metrics
    """
    metrics_created = 0
    
    # Calculate pipeline value by stage
    pipeline_by_stage = {}
    total_pipeline = 0
    won_deals = 0
    lost_deals = 0
    
    for opp in opportunities:
        amount = float(opp.get('Amount', 0))
        stage = opp.get('StageName', 'Unknown')
        is_closed = opp.get('IsClosed', False)
        is_won = opp.get('IsWon', False)
        
        if not is_closed:
            pipeline_by_stage[stage] = pipeline_by_stage.get(stage, 0) + amount
            total_pipeline += amount
        elif is_won:
            won_deals += amount
        else:
            lost_deals += amount
    
    with get_db_session() as db:
        # Total pipeline
        metric = Metric(
            workspace_id=workspace_id,
            metric_id='sales_pipeline',
            period_date=period,
            value=total_pipeline,
            source_template='crm_sync',
            unit='dollars'
        )
        db.merge(metric)
        metrics_created += 1
        
        # Won deals (bookings)
        metric = Metric(
            workspace_id=workspace_id,
            metric_id='bookings',
            period_date=period,
            value=won_deals,
            source_template='crm_sync',
            unit='dollars'
        )
        db.merge(metric)
        metrics_created += 1
        
        # Win rate
        total_closed = won_deals + lost_deals
        if total_closed > 0:
            win_rate = (won_deals / total_closed) * 100
            metric = Metric(
                workspace_id=workspace_id,
                metric_id='win_rate',
                period_date=period,
                value=win_rate,
                source_template='crm_sync',
                unit='percentage'
            )
            db.merge(metric)
            metrics_created += 1
        
        db.commit()
    
    return metrics_created


def calculate_account_metrics(workspace_id: str, accounts: list, 
                            period: date) -> int:
    """
    Calculate account/customer metrics
    """
    metrics_created = 0
    
    # Count accounts by type
    total_accounts = len(accounts)
    customer_accounts = len([a for a in accounts if a.get('Type') == 'Customer'])
    prospect_accounts = len([a for a in accounts if a.get('Type') == 'Prospect'])
    
    # Calculate ARR if available
    total_arr = sum(float(a.get('AnnualRevenue', 0)) for a in accounts if a.get('AnnualRevenue'))
    
    with get_db_session() as db:
        # Total accounts
        metric = Metric(
            workspace_id=workspace_id,
            metric_id='crm_accounts',
            period_date=period,
            value=total_accounts,
            source_template='crm_sync',
            unit='count'
        )
        db.merge(metric)
        metrics_created += 1
        
        # Customer accounts
        metric = Metric(
            workspace_id=workspace_id,
            metric_id='crm_customers',
            period_date=period,
            value=customer_accounts,
            source_template='crm_sync',
            unit='count'
        )
        db.merge(metric)
        metrics_created += 1
        
        # ARR if available
        if total_arr > 0:
            metric = Metric(
                workspace_id=workspace_id,
                metric_id='arr',
                period_date=period,
                value=total_arr,
                source_template='crm_sync',
                unit='dollars'
            )
            db.merge(metric)
            metrics_created += 1
        
        db.commit()
    
    return metrics_created


def calculate_activity_metrics(workspace_id: str, activities: list, 
                             period: date) -> int:
    """
    Calculate sales activity metrics
    """
    metrics_created = 0
    
    # Count activities by type
    calls = len([a for a in activities if a.get('Type') == 'Call'])
    emails = len([a for a in activities if a.get('Type') == 'Email'])
    meetings = len([a for a in activities if a.get('Type') == 'Meeting'])
    
    with get_db_session() as db:
        # Total activities
        metric = Metric(
            workspace_id=workspace_id,
            metric_id='sales_activities',
            period_date=period,
            value=len(activities),
            source_template='crm_sync',
            unit='count'
        )
        db.merge(metric)
        metrics_created += 1
        
        # Calls
        if calls > 0:
            metric = Metric(
                workspace_id=workspace_id,
                metric_id='sales_calls',
                period_date=period,
                value=calls,
                source_template='crm_sync',
                unit='count'
            )
            db.merge(metric)
            metrics_created += 1
        
        db.commit()
    
    return metrics_created