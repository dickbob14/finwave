#!/usr/bin/env python3
"""
Check QuickBooks integration status and debug sync issues
"""
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import get_db_session
from models.integration import IntegrationCredential
from metrics.models import Metric
from scheduler.models import ScheduledJob

def check_integration_status():
    """Check QuickBooks integration status"""
    with get_db_session() as db:
        print("=== QuickBooks Integration Status ===")
        
        # Check all integrations
        integrations = db.query(IntegrationCredential).all()
        
        for integration in integrations:
            print(f"\nIntegration: {integration.source}")
            print(f"  Workspace: {integration.workspace_id}")
            print(f"  Status: {integration.status}")
            print(f"  Connected at: {integration.created_at}")
            print(f"  Last synced: {integration.last_synced_at}")
            print(f"  Token expires: {integration.expires_at}")
            print(f"  Token expired: {integration.expires_at < datetime.utcnow() if integration.expires_at else 'No expiry set'}")
            
            if integration.last_sync_error:
                print(f"  Last error: {integration.last_sync_error[:200]}...")
            
            # Check metadata
            if integration.metadata:
                print(f"  Metadata: {integration.metadata}")
            
            # Check if tokens are set
            print(f"  Has access token: {bool(integration.access_token_encrypted)}")
            print(f"  Has refresh token: {bool(integration.refresh_token_encrypted)}")
        
        print("\n=== Sync Jobs ===")
        # Check sync jobs
        jobs = db.query(ScheduledJob).filter(
            ScheduledJob.job_name.like('sync_%')
        ).order_by(ScheduledJob.created_at.desc()).limit(5).all()
        
        for job in jobs:
            print(f"\nJob: {job.job_name}")
            print(f"  Status: {job.status}")
            print(f"  Started: {job.started_at}")
            print(f"  Completed: {job.completed_at}")
            print(f"  Records: {job.records_processed}")
            if job.error_message:
                print(f"  Error: {job.error_message[:200]}...")
        
        print("\n=== Metrics in Database ===")
        # Check metrics
        metric_count = db.query(Metric).count()
        print(f"Total metrics: {metric_count}")
        
        if metric_count > 0:
            # Get sample metrics
            sample_metrics = db.query(Metric).limit(10).all()
            print("\nSample metrics:")
            for m in sample_metrics:
                print(f"  {m.workspace_id} - {m.metric_id}: {m.value} ({m.period_date})")

if __name__ == "__main__":
    check_integration_status()