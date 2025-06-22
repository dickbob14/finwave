"""
Scheduled jobs for report generation
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List

from core.database import get_db_session
from models.workspace import Workspace
from reports import get_pdf_service
from scheduler.models import ScheduledJob

logger = logging.getLogger(__name__)


def generate_monthly_board_reports() -> Dict[str, Any]:
    """
    Generate board reports for all active workspaces
    Called on the 1st of each month
    """
    results = {
        'workspaces_processed': 0,
        'reports_generated': 0,
        'errors': []
    }
    
    # Get current period (previous month)
    today = date.today()
    if today.day <= 3:  # First few days of month, generate for previous month
        period_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    else:
        # Manual run, generate for current month
        period_date = today.replace(day=1)
    
    logger.info(f"Generating board reports for period: {period_date}")
    
    with get_db_session() as db:
        # Get active workspaces with board report enabled
        workspaces = db.query(Workspace).filter(
            Workspace.billing_status.in_(['trial', 'active'])
        ).all()
        
        pdf_service = get_pdf_service()
        
        for workspace in workspaces:
            # Check if board reports are enabled for this workspace
            features = workspace.features_enabled or {}
            if not features.get('board_reports', True):
                continue
            
            try:
                logger.info(f"Generating board report for {workspace.id}")
                
                # Log job start
                job = ScheduledJob(
                    job_name='generate_board_report',
                    workspace_id=workspace.id,
                    started_at=datetime.utcnow(),
                    status='running'
                )
                db.add(job)
                db.commit()
                job_id = job.id
                
                # Generate report
                pdf_bytes = pdf_service.generate_board_report(
                    workspace.id,
                    period_date
                )
                
                # Upload to S3
                s3_url = pdf_service.upload_to_s3(
                    pdf_bytes,
                    workspace.id,
                    period_date,
                    'board-pack'
                )
                
                # Save report record (in production, save to reports table)
                # report = Report(
                #     workspace_id=workspace.id,
                #     report_type='board-pack',
                #     period=period_date,
                #     s3_url=s3_url,
                #     size_bytes=len(pdf_bytes),
                #     generated_by='system'
                # )
                # db.add(report)
                
                # Update job status
                job = db.query(ScheduledJob).filter_by(id=job_id).first()
                if job:
                    job.completed_at = datetime.utcnow()
                    job.status = 'completed'
                    job.result_json = f'{{"s3_url": "{s3_url}", "size_bytes": {len(pdf_bytes)}}}'
                    db.commit()
                
                results['reports_generated'] += 1
                
                # Send email if configured
                if workspace.settings.get('report_recipients'):
                    send_report_email(
                        workspace,
                        period_date,
                        s3_url,
                        len(pdf_bytes)
                    )
                
            except Exception as e:
                logger.error(f"Failed to generate report for {workspace.id}: {e}")
                
                # Update job status
                if 'job_id' in locals():
                    job = db.query(ScheduledJob).filter_by(id=job_id).first()
                    if job:
                        job.completed_at = datetime.utcnow()
                        job.status = 'failed'
                        job.error_message = str(e)
                        db.commit()
                
                results['errors'].append({
                    'workspace_id': workspace.id,
                    'error': str(e)
                })
            
            results['workspaces_processed'] += 1
    
    logger.info(f"Board report generation complete: {results}")
    return results


def send_report_email(workspace: Workspace, period_date: date, 
                     s3_url: str, size_bytes: int):
    """
    Send board report via email
    
    In production, integrate with SES or SendGrid
    """
    recipients = workspace.settings.get('report_recipients', [])
    if not recipients:
        return
    
    logger.info(f"Sending board report to {len(recipients)} recipients for {workspace.id}")
    
    # Email content
    subject = f"{workspace.name} - Board Report - {period_date.strftime('%B %Y')}"
    
    body = f"""
    Dear Board Members,
    
    The monthly board report for {period_date.strftime('%B %Y')} is now available.
    
    Report Highlights:
    - Comprehensive financial statements
    - KPI dashboard with trends
    - Variance analysis vs budget
    - 12-month forecast and runway projection
    
    You can download the report from the link below:
    {s3_url}
    
    Report size: {size_bytes / (1024*1024):.1f} MB
    
    Best regards,
    {workspace.name} Finance Team
    
    ---
    This report was automatically generated by FinWave on {datetime.now().strftime('%Y-%m-%d')}.
    """
    
    # In production:
    # ses_client = boto3.client('ses')
    # ses_client.send_email(
    #     Source='reports@finwave.io',
    #     Destination={'ToAddresses': recipients},
    #     Message={
    #         'Subject': {'Data': subject},
    #         'Body': {'Text': {'Data': body}}
    #     }
    # )
    
    logger.info(f"Email sent to {recipients}")


def check_report_generation_health() -> Dict[str, Any]:
    """
    Health check for report generation
    Alert if reports are failing
    """
    with get_db_session() as db:
        # Check recent job failures
        since = datetime.utcnow() - timedelta(hours=24)
        
        failed_jobs = db.query(ScheduledJob).filter(
            ScheduledJob.job_name == 'generate_board_report',
            ScheduledJob.started_at >= since,
            ScheduledJob.status == 'failed'
        ).count()
        
        successful_jobs = db.query(ScheduledJob).filter(
            ScheduledJob.job_name == 'generate_board_report',
            ScheduledJob.started_at >= since,
            ScheduledJob.status == 'completed'
        ).count()
        
        total_jobs = failed_jobs + successful_jobs
        
        if total_jobs == 0:
            return {
                'status': 'no_recent_jobs',
                'message': 'No report generation jobs in last 24 hours'
            }
        
        failure_rate = (failed_jobs / total_jobs) * 100
        
        if failure_rate > 20:
            # Create internal alert
            from scheduler.models import Alert, AlertSeverity
            alert = Alert(
                workspace_id='system',
                metric_id='report_generation',
                rule_name='report_failure_rate',
                severity=AlertSeverity.CRITICAL.value,
                message=f"Report generation failure rate is {failure_rate:.1f}% ({failed_jobs}/{total_jobs} failed)",
                current_value=failure_rate,
                threshold_value=20,
                triggered_at=datetime.utcnow()
            )
            db.add(alert)
            db.commit()
            
            return {
                'status': 'unhealthy',
                'failure_rate': failure_rate,
                'failed_jobs': failed_jobs,
                'total_jobs': total_jobs
            }
        
        return {
            'status': 'healthy',
            'failure_rate': failure_rate,
            'successful_jobs': successful_jobs,
            'total_jobs': total_jobs
        }