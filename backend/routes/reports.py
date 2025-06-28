"""
FinWave Reports API Routes

Endpoints for generating board-ready PDF reports
"""

import asyncio
import json
import logging
from datetime import datetime, date
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Response, Depends
from fastapi.responses import StreamingResponse, FileResponse
from sse_starlette.sse import EventSourceResponse
from pathlib import Path

from reports.pdf_service import get_pdf_service
from auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["reports"])

# In-memory job tracking (use Redis in production)
report_jobs = {}


@router.get("/{workspace}/reports/board-pack.pdf")
async def generate_board_pack_sync(
    workspace: str,
    period: Optional[str] = Query(None, description="Period in YYYY-MM format"),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate board pack PDF synchronously (demo endpoint)
    
    Returns the PDF directly for immediate download
    """
    try:
        # Default to current month if not specified
        if not period:
            period = datetime.now().strftime("%Y-%m")
        
        # Validate period format
        try:
            datetime.strptime(period, "%Y-%m")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid period format. Use YYYY-MM"
            )
        
        logger.info(f"Generating board pack for {workspace}/{period}")
        
        # Generate PDF
        pdf_service = get_pdf_service()
        result = await pdf_service.build_pdf(
            workspace,
            period,
            template='board_pack',
            attach_variance=True
        )
        
        # Return file response
        return FileResponse(
            path=result['local_path'],
            media_type='application/pdf',
            filename=result['filename'],
            headers={
                'X-PDF-Pages': str(result.get('pages', 0)),
                'X-PDF-Size': str(result.get('size_bytes', 0))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Board pack generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed: {str(e)}"
        )


@router.post("/{workspace}/reports/board-pack/generate")
async def generate_board_pack_async(
    workspace: str,
    background_tasks: BackgroundTasks,
    period: Optional[str] = Query(None, description="Period in YYYY-MM format"),
    email_notification: bool = Query(False, description="Send email when complete"),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate board pack PDF asynchronously
    
    Returns job ID for tracking progress
    """
    try:
        # Default to current month
        if not period:
            period = datetime.now().strftime("%Y-%m")
        
        # Validate period
        try:
            datetime.strptime(period, "%Y-%m")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid period format. Use YYYY-MM"
            )
        
        # Create job
        job_id = f"job_{uuid4().hex[:8]}"
        report_jobs[job_id] = {
            'status': 'pending',
            'progress': 0,
            'message': 'Report generation queued',
            'workspace': workspace,
            'period': period,
            'created_at': datetime.utcnow().isoformat(),
            'created_by': current_user.get('email', 'system')
        }
        
        # Start background task
        background_tasks.add_task(
            _generate_pdf_background,
            job_id,
            workspace,
            period,
            email_notification,
            current_user.get('email')
        )
        
        return {
            'job_id': job_id,
            'status': 'accepted',
            'progress_url': f'/api/{workspace}/reports/progress/{job_id}',
            'message': 'Report generation started'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start report generation: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to start report generation"
        )


@router.get("/{workspace}/reports/progress/{job_id}")
async def get_job_progress_sse(
    workspace: str,
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Stream progress updates via Server-Sent Events
    """
    async def event_generator():
        # Initial check
        if job_id not in report_jobs:
            yield {
                'event': 'error',
                'data': json.dumps({'error': 'Job not found'})
            }
            return
        
        # Stream updates
        last_progress = -1
        while True:
            job = report_jobs.get(job_id)
            if not job:
                break
                
            # Only send if progress changed
            if job['progress'] != last_progress:
                yield {
                    'event': 'progress',
                    'data': json.dumps({
                        'progress': job['progress'],
                        'message': job['message'],
                        'status': job['status']
                    })
                }
                last_progress = job['progress']
            
            # Check if complete
            if job['status'] in ['complete', 'failed']:
                yield {
                    'event': 'complete',
                    'data': json.dumps(job)
                }
                break
            
            # Small delay to prevent overwhelming
            await asyncio.sleep(0.5)
    
    return EventSourceResponse(event_generator())


@router.get("/demo/reports/board-pack.pdf")
async def demo_board_pack():
    """
    Demo endpoint that doesn't require authentication
    
    Generates a sample board pack for the current month
    """
    try:
        period = datetime.now().strftime("%Y-%m")
        
        logger.info(f"Generating demo board pack for {period}")
        
        # Generate PDF with demo data
        pdf_service = get_pdf_service()
        result = await pdf_service.build_pdf(
            'demo',  # Demo workspace
            period,
            template='board_pack',
            attach_variance=True
        )
        
        # Return file
        return FileResponse(
            path=result['local_path'],
            media_type='application/pdf',
            filename=f"FinWave_Demo_Board_Pack_{period}.pdf"
        )
        
    except Exception as e:
        logger.error(f"Demo PDF generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate demo report"
        )


async def _generate_pdf_background(job_id: str, workspace: str, period: str,
                                  email_notification: bool, user_email: str):
    """
    Background task to generate PDF
    """
    try:
        # Update progress
        def update_progress(progress: int, message: str):
            if job_id in report_jobs:
                report_jobs[job_id].update({
                    'progress': progress,
                    'message': message,
                    'status': 'running' if progress < 100 else 'complete'
                })
        
        update_progress(10, "Initializing report generation...")
        
        # Generate PDF
        pdf_service = get_pdf_service()
        
        # Simulate progress updates during generation
        update_progress(20, "Loading financial data...")
        await asyncio.sleep(1)
        
        update_progress(40, "Generating charts and visualizations...")
        await asyncio.sleep(1)
        
        update_progress(60, "Building report sections...")
        await asyncio.sleep(1)
        
        update_progress(80, "Rendering PDF document...")
        
        # Actually generate the PDF
        result = await pdf_service.build_pdf(
            workspace,
            period,
            template='board_pack',
            attach_variance=True
        )
        
        update_progress(90, "Finalizing report...")
        
        # Update job with results
        report_jobs[job_id].update({
            'status': 'complete',
            'progress': 100,
            'message': 'Report generated successfully',
            'completed_at': datetime.utcnow().isoformat(),
            'result': {
                'filename': result['filename'],
                'size_bytes': result['size_bytes'],
                'pages': result['pages'],
                'download_url': f'/api/{workspace}/reports/download/{job_id}',
                's3_url': result.get('s3_url'),
                'presigned_url': result.get('download_url')
            }
        })
        
        # Send email notification if requested
        if email_notification and user_email:
            # TODO: Implement email notification
            logger.info(f"Would send email to {user_email} about completed report")
        
    except Exception as e:
        logger.error(f"Background PDF generation failed: {e}")
        if job_id in report_jobs:
            report_jobs[job_id].update({
                'status': 'failed',
                'progress': report_jobs[job_id].get('progress', 0),
                'message': f'Generation failed: {str(e)}',
                'error': str(e),
                'failed_at': datetime.utcnow().isoformat()
            })


@router.get("/{workspace}/reports/download/{job_id}")
async def download_generated_report(
    workspace: str,
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Download a previously generated report
    """
    job = report_jobs.get(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job['status'] != 'complete':
        raise HTTPException(
            status_code=400,
            detail=f"Report not ready. Status: {job['status']}"
        )
    
    if 'result' not in job or 'filename' not in job['result']:
        raise HTTPException(
            status_code=500,
            detail="Report metadata missing"
        )
    
    # Check if we have a presigned URL (for S3)
    if job['result'].get('presigned_url'):
        # Redirect to S3 presigned URL
        return Response(
            status_code=302,
            headers={'Location': job['result']['presigned_url']}
        )
    
    # Otherwise serve from local file
    local_path = Path(__file__).parent.parent / 'generated_reports' / job['result']['filename']
    
    if not local_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    
    return FileResponse(
        path=str(local_path),
        media_type='application/pdf',
        filename=job['result']['filename']
    )


# Include router in main app
__all__ = ['router']