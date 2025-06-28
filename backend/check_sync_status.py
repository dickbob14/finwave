#!/usr/bin/env python3
"""
Check QuickBooks sync status and identify issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import get_db_session
from models.integration import IntegrationCredential
from scheduler.models import ScheduledJob
from metrics.models import Metric

def check_sync_status():
    """Check sync status and identify issues"""
    
    with get_db_session() as db:
        # Check integration status
        print("=== QuickBooks Integration Status ===")
        integration = db.query(IntegrationCredential).filter_by(
            workspace_id='default',
            source='quickbooks'
        ).first()
        
        if integration:
            print(f'Status: {integration.status}')
            print(f'Last Synced: {integration.last_synced_at}')
            print(f'Last Error: {integration.last_sync_error}')
            print(f'Has Access Token: {bool(integration.access_token)}')
            print(f'Has Refresh Token: {bool(integration.refresh_token)}')
            print(f'Expires At: {integration.expires_at}')
            print(f'Metadata: {integration.integration_metadata}')
        else:
            print('❌ No QuickBooks integration found')
            return
        
        # Check recent sync jobs
        print('\n=== Recent Sync Jobs ===')
        jobs = db.query(ScheduledJob).filter(
            ScheduledJob.job_name.like('sync_quickbooks%')
        ).order_by(ScheduledJob.started_at.desc()).limit(5).all()
        
        if not jobs:
            print('❌ No sync jobs found')
        else:
            for job in jobs:
                print(f'\nJob {job.id}:')
                print(f'  Status: {job.status}')
                print(f'  Started: {job.started_at}')
                print(f'  Completed: {job.completed_at}')
                print(f'  Records Processed: {job.records_processed}')
                if job.error_message:
                    print(f'  ❌ Error: {job.error_message[:300]}')
        
        # Check if any metrics exist
        print('\n=== Metrics Status ===')
        metric_count = db.query(Metric).filter_by(
            workspace_id='default'
        ).count()
        print(f'Total metrics in database: {metric_count}')
        
        if metric_count > 0:
            # Show sample metrics
            recent_metrics = db.query(Metric).filter_by(
                workspace_id='default'
            ).order_by(Metric.updated_at.desc()).limit(5).all()
            
            print('\nRecent metrics:')
            for metric in recent_metrics:
                print(f'  - {metric.metric_id}: {metric.value} {metric.unit} ({metric.period_date})')


if __name__ == "__main__":
    check_sync_status()