#!/usr/bin/env python3
"""
Run scheduled jobs for FinWave
This script can be executed by cron or a scheduler service
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_db_session
from scheduler.models import ScheduledJob
from scheduler.variance_watcher import run_variance_check
from forecast.engine import forecast_metrics_task
from insights.scheduled import generate_scheduled_insights

logger = logging.getLogger(__name__)

# Available jobs
JOBS = {
    'variance_check': {
        'function': run_variance_check,
        'description': 'Check variance rules and generate alerts',
        'default_frequency': 'hourly'
    },
    'forecast_update': {
        'function': lambda: run_forecast_for_all_workspaces(),
        'description': 'Update metric forecasts',
        'default_frequency': 'daily'
    },
    'insight_refresh': {
        'function': generate_scheduled_insights,
        'description': 'Refresh AI-generated insights',
        'default_frequency': 'daily'
    }
}


def log_job_execution(job_name: str, workspace_id: str = None) -> ScheduledJob:
    """Create a job execution record"""
    job = ScheduledJob(
        job_name=job_name,
        workspace_id=workspace_id,
        started_at=datetime.utcnow(),
        status='running'
    )
    
    with get_db_session() as db:
        db.add(job)
        db.commit()
        db.refresh(job)
    
    return job


def update_job_status(job_id: str, status: str, records_processed: int = None,
                     error_message: str = None, result_json: str = None):
    """Update job execution status"""
    with get_db_session() as db:
        job = db.query(ScheduledJob).filter_by(id=job_id).first()
        if job:
            job.status = status
            job.completed_at = datetime.utcnow()
            if records_processed is not None:
                job.records_processed = records_processed
            if error_message:
                job.error_message = error_message
            if result_json:
                job.result_json = result_json
            db.commit()


def run_forecast_for_all_workspaces():
    """Run forecast updates for all active workspaces"""
    from models.workspace import Workspace
    
    results = {}
    
    with get_db_session() as db:
        workspaces = db.query(Workspace).filter(
            Workspace.billing_status.in_(['trial', 'active'])
        ).all()
        
        for workspace in workspaces:
            try:
                result = forecast_metrics_task(workspace.id, periods_ahead=12)
                results[workspace.id] = result
            except Exception as e:
                logger.error(f"Forecast failed for {workspace.id}: {e}")
                results[workspace.id] = {'error': str(e)}
    
    return results


def run_job(job_name: str, dry_run: bool = False) -> Dict[str, Any]:
    """Execute a scheduled job"""
    if job_name not in JOBS:
        raise ValueError(f"Unknown job: {job_name}")
    
    job_config = JOBS[job_name]
    logger.info(f"Starting job: {job_name} - {job_config['description']}")
    
    if dry_run:
        logger.info("DRY RUN - not executing job")
        return {'status': 'dry_run', 'job': job_name}
    
    # Log job start
    job_record = log_job_execution(job_name)
    
    try:
        # Execute job
        result = job_config['function']()
        
        # Calculate records processed
        records = 0
        if isinstance(result, dict):
            for key, value in result.items():
                if isinstance(value, list):
                    records += len(value)
                elif isinstance(value, dict) and 'count' in value:
                    records += value['count']
        
        # Update job status
        update_job_status(
            job_record.id,
            status='completed',
            records_processed=records,
            result_json=str(result) if result else None
        )
        
        logger.info(f"Job {job_name} completed successfully")
        return {
            'status': 'success',
            'job': job_name,
            'records_processed': records,
            'result': result
        }
        
    except Exception as e:
        logger.error(f"Job {job_name} failed: {e}")
        
        # Update job status
        update_job_status(
            job_record.id,
            status='failed',
            error_message=str(e)
        )
        
        return {
            'status': 'error',
            'job': job_name,
            'error': str(e)
        }


def main():
    parser = argparse.ArgumentParser(description='Run FinWave scheduled jobs')
    parser.add_argument('job', choices=list(JOBS.keys()) + ['all'],
                       help='Job to run (or "all" for all jobs)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without executing')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run job(s)
    if args.job == 'all':
        logger.info("Running all scheduled jobs")
        results = {}
        for job_name in JOBS:
            results[job_name] = run_job(job_name, args.dry_run)
        
        # Print summary
        print("\n=== Job Execution Summary ===")
        for job_name, result in results.items():
            status = result.get('status', 'unknown')
            print(f"{job_name}: {status}")
            if status == 'error':
                print(f"  Error: {result.get('error', 'Unknown error')}")
            elif status == 'success':
                print(f"  Records: {result.get('records_processed', 0)}")
    else:
        result = run_job(args.job, args.dry_run)
        
        # Print result
        print(f"\n=== {args.job} ===")
        print(f"Status: {result.get('status', 'unknown')}")
        if result.get('status') == 'error':
            print(f"Error: {result.get('error', 'Unknown error')}")
        elif result.get('status') == 'success':
            print(f"Records processed: {result.get('records_processed', 0)}")


if __name__ == "__main__":
    main()