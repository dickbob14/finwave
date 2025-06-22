"""
Background sync jobs for integrations
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4

from core.database import get_db_session
from models.integration import (
    IntegrationCredential, IntegrationStatus, IntegrationSource,
    get_integration, mark_integration_synced
)
from models.workspace import Workspace
from scheduler.models import ScheduledJob
from metrics.ingest import ingest_metrics
from integrations.quickbooks.sync import sync_quickbooks_data
from integrations.crm.sync import sync_crm_data
from integrations.payroll.sync import sync_payroll_data

logger = logging.getLogger(__name__)

# In production, use Celery/RQ/etc. For now, simple in-memory queue
SYNC_QUEUE = []


def enqueue_initial_sync(workspace_id: str, source: str, 
                        priority: str = 'normal') -> str:
    """
    Enqueue an initial sync job after OAuth connection
    """
    job_id = f"sync_{uuid4().hex[:8]}"
    
    job = {
        'id': job_id,
        'workspace_id': workspace_id,
        'source': source,
        'type': 'initial_sync',
        'priority': priority,
        'created_at': datetime.utcnow()
    }
    
    # In production, use proper queue
    SYNC_QUEUE.append(job)
    
    # For demo, execute immediately in background
    import threading
    thread = threading.Thread(
        target=execute_sync_job,
        args=(job,)
    )
    thread.start()
    
    return job_id


def execute_sync_job(job: dict) -> Dict[str, Any]:
    """
    Execute a sync job
    """
    workspace_id = job['workspace_id']
    source = job['source']
    
    logger.info(f"Starting sync job {job['id']} for {workspace_id}/{source}")
    
    # Log job start
    with get_db_session() as db:
        job_record = ScheduledJob(
            job_name=f"sync_{source}",
            workspace_id=workspace_id,
            started_at=datetime.utcnow(),
            status='running'
        )
        db.add(job_record)
        db.commit()
        job_record_id = job_record.id
    
    try:
        # Get integration
        integration = get_integration(workspace_id, source)
        if not integration:
            raise ValueError(f"Integration not found: {workspace_id}/{source}")
        
        # Check token validity
        if integration.is_expired():
            # Try to refresh
            refreshed = refresh_integration_token(integration)
            if not refreshed:
                raise ValueError("Token expired and refresh failed")
        
        # Execute source-specific sync
        if source == IntegrationSource.QUICKBOOKS.value:
            result = sync_quickbooks_data(workspace_id, integration)
        elif source in [IntegrationSource.SALESFORCE.value, IntegrationSource.HUBSPOT.value]:
            result = sync_crm_data(workspace_id, integration)
        elif source in [IntegrationSource.GUSTO.value, IntegrationSource.ADP.value]:
            result = sync_payroll_data(workspace_id, integration)
        else:
            raise ValueError(f"Unknown source: {source}")
        
        # Mark success
        mark_integration_synced(workspace_id, source)
        
        # Update job record
        with get_db_session() as db:
            job_record = db.query(ScheduledJob).filter_by(id=job_record_id).first()
            if job_record:
                job_record.completed_at = datetime.utcnow()
                job_record.status = 'completed'
                job_record.records_processed = result.get('records_processed', 0)
                job_record.result_json = str(result)
                db.commit()
        
        logger.info(f"Sync job {job['id']} completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Sync job {job['id']} failed: {e}")
        
        # Mark error
        mark_integration_synced(workspace_id, source, error=str(e))
        
        # Update job record
        with get_db_session() as db:
            job_record = db.query(ScheduledJob).filter_by(id=job_record_id).first()
            if job_record:
                job_record.completed_at = datetime.utcnow()
                job_record.status = 'failed'
                job_record.error_message = str(e)
                db.commit()
        
        return {'error': str(e)}


def refresh_integration_token(integration: IntegrationCredential) -> bool:
    """
    Refresh OAuth token for an integration
    """
    if not integration.refresh_token:
        logger.error(f"No refresh token for {integration.workspace_id}/{integration.source}")
        return False
    
    try:
        # Source-specific refresh logic
        if integration.source == IntegrationSource.QUICKBOOKS.value:
            from integrations.quickbooks.auth import refresh_quickbooks_token
            new_tokens = refresh_quickbooks_token(
                integration.refresh_token,
                integration.metadata.get('realm_id')
            )
        elif integration.source == IntegrationSource.SALESFORCE.value:
            from integrations.crm.auth import refresh_salesforce_token
            new_tokens = refresh_salesforce_token(
                integration.refresh_token,
                integration.metadata.get('instance_url')
            )
        else:
            logger.warning(f"Token refresh not implemented for {integration.source}")
            return False
        
        if new_tokens:
            # Update tokens
            from models.integration import update_integration_tokens
            update_integration_tokens(
                integration.workspace_id,
                integration.source,
                access_token=new_tokens['access_token'],
                refresh_token=new_tokens.get('refresh_token', integration.refresh_token),
                expires_in=new_tokens.get('expires_in')
            )
            return True
            
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
    
    return False


def process_sync_queue():
    """
    Process pending sync jobs (called by scheduler)
    """
    if not SYNC_QUEUE:
        return
    
    # Process up to 5 jobs
    jobs_to_process = SYNC_QUEUE[:5]
    SYNC_QUEUE[:5] = []
    
    for job in jobs_to_process:
        try:
            execute_sync_job(job)
        except Exception as e:
            logger.error(f"Failed to process sync job: {e}")


def get_sync_status(workspace_id: str, source: str) -> Dict[str, Any]:
    """
    Get sync status for an integration
    """
    integration = get_integration(workspace_id, source)
    if not integration:
        return {'status': 'not_connected'}
    
    # Check for running jobs
    with get_db_session() as db:
        running_job = db.query(ScheduledJob).filter(
            ScheduledJob.workspace_id == workspace_id,
            ScheduledJob.job_name == f"sync_{source}",
            ScheduledJob.status == 'running'
        ).first()
        
        if running_job:
            return {
                'status': 'syncing',
                'started_at': running_job.started_at,
                'progress': 50  # Placeholder
            }
    
    # Get last sync info
    return {
        'status': integration.status,
        'last_synced_at': integration.last_synced_at,
        'last_error': integration.last_sync_error,
        'next_sync_in_minutes': 60  # Based on sync frequency
    }