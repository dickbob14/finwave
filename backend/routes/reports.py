"""
Report generation API routes
"""

import asyncio
import logging
from datetime import datetime, date
from typing import Optional, Dict, Any
import json

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import StreamingResponse, Response
from sse_starlette.sse import EventSourceResponse

from auth import get_current_user, require_workspace
from reports import get_pdf_service
from core.database import get_db_session
from models.workspace import Workspace

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])

# In-memory progress tracking (in production, use Redis)
report_progress = {}


@router.get("/board-pack.pdf")
async def generate_board_report(
    period: Optional[str] = Query(None, description="Period in YYYY-MM format"),
    workspace_id: str = Depends(require_workspace),
    user: dict = Depends(get_current_user)
):
    """
    Generate board pack PDF report
    
    Returns PDF file stream
    """
    try:
        # Parse period
        if period:
            try:
                period_date = datetime.strptime(period, "%Y-%m").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid period format. Use YYYY-MM")
        else:
            period_date = date.today().replace(day=1)
        
        # Get workspace name for filename
        with get_db_session() as db:
            workspace = db.query(Workspace).filter_by(id=workspace_id).first()
            if not workspace:
                raise HTTPException(status_code=404, detail="Workspace not found")
        
        # Generate PDF
        pdf_service = get_pdf_service()
        
        # Generate synchronously for now (could make async with progress)
        pdf_bytes = pdf_service.generate_board_report(workspace_id, period_date)
        
        # Generate filename
        filename = f"{workspace.name.replace(' ', '_')}_Board_Report_{period_date.strftime('%Y_%m')}.pdf"
        
        # Return PDF stream
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate board report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate report")


@router.get("/board-pack/progress")
async def board_report_progress(
    workspace_id: str = Depends(require_workspace),
    user: dict = Depends(get_current_user)
):
    """
    Stream progress updates for board report generation
    
    Uses Server-Sent Events (SSE)
    """
    async def generate():
        progress_key = f"{workspace_id}_board_report"
        
        # Initial message
        yield {
            "event": "start",
            "data": json.dumps({"progress": 0, "message": "Starting report generation..."})
        }
        
        # Simulate progress updates
        stages = [
            (10, "Loading financial data..."),
            (30, "Generating charts..."),
            (50, "Building report sections..."),
            (70, "Rendering PDF..."),
            (90, "Finalizing document..."),
            (100, "Complete!")
        ]
        
        for progress, message in stages:
            await asyncio.sleep(1)  # Simulate work
            
            yield {
                "event": "progress",
                "data": json.dumps({"progress": progress, "message": message})
            }
        
        # Final message with download URL
        yield {
            "event": "complete",
            "data": json.dumps({
                "progress": 100,
                "message": "Report ready!",
                "download_url": f"/api/{workspace_id}/reports/board-pack.pdf"
            })
        }
    
    return EventSourceResponse(generate())


@router.post("/board-pack/generate")
async def generate_board_report_async(
    background_tasks: BackgroundTasks,
    period: Optional[str] = Query(None, description="Period in YYYY-MM format"),
    workspace_id: str = Depends(require_workspace),
    user: dict = Depends(get_current_user)
):
    """
    Generate board report asynchronously
    
    Returns job ID for tracking progress
    """
    try:
        # Parse period
        if period:
            try:
                period_date = datetime.strptime(period, "%Y-%m").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid period format. Use YYYY-MM")
        else:
            period_date = date.today().replace(day=1)
        
        # Create job ID
        job_id = f"{workspace_id}_{period_date.strftime('%Y%m')}_{datetime.utcnow().timestamp()}"
        
        # Start background generation
        background_tasks.add_task(
            generate_report_background,
            workspace_id,
            period_date,
            job_id,
            user.get('email', user.get('sub'))
        )
        
        return {
            "job_id": job_id,
            "status": "started",
            "progress_url": f"/api/{workspace_id}/reports/status/{job_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start report generation: {e}")
        raise HTTPException(status_code=500, detail="Failed to start report generation")


async def generate_report_background(workspace_id: str, period_date: date, 
                                   job_id: str, user_email: str):
    """Background task to generate report"""
    try:
        # Update progress
        def update_progress(progress: int, message: str):
            report_progress[job_id] = {
                "progress": progress,
                "message": message,
                "status": "running" if progress < 100 else "complete"
            }
        
        # Generate report
        pdf_service = get_pdf_service()
        pdf_bytes = pdf_service.generate_board_report(
            workspace_id, 
            period_date,
            progress_callback=update_progress
        )
        
        # Save to storage (S3 in production)
        s3_url = pdf_service.upload_to_s3(
            pdf_bytes,
            workspace_id,
            period_date
        )
        
        # Update final status
        report_progress[job_id] = {
            "progress": 100,
            "message": "Report generated successfully",
            "status": "complete",
            "download_url": s3_url,
            "size_bytes": len(pdf_bytes)
        }
        
        # TODO: Send email notification if configured
        
    except Exception as e:
        logger.error(f"Background report generation failed: {e}")
        report_progress[job_id] = {
            "progress": 0,
            "message": f"Generation failed: {str(e)}",
            "status": "failed"
        }


@router.get("/status/{job_id}")
async def get_report_status(
    job_id: str,
    workspace_id: str = Depends(require_workspace),
    user: dict = Depends(get_current_user)
):
    """Get status of report generation job"""
    status = report_progress.get(job_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return status


@router.get("/history")
async def get_report_history(
    limit: int = Query(10, description="Number of reports to return"),
    workspace_id: str = Depends(require_workspace),
    user: dict = Depends(get_current_user)
):
    """
    Get history of generated reports
    
    In production, this would query a reports table
    """
    # Mock data for now
    history = [
        {
            "id": f"report_{i}",
            "period": f"2024-{12-i:02d}",
            "generated_at": datetime(2024, 12-i, 1).isoformat(),
            "generated_by": user.get('email', 'system'),
            "size_bytes": 1024 * 1024 * (i + 1),  # 1-10 MB
            "download_url": f"/api/{workspace_id}/reports/board-pack.pdf?period=2024-{12-i:02d}"
        }
        for i in range(min(limit, 6))
    ]
    
    return {
        "reports": history,
        "total": len(history)
    }


@router.get("/templates")
async def list_report_templates(
    workspace_id: str = Depends(require_workspace),
    user: dict = Depends(get_current_user)
):
    """List available report templates"""
    return {
        "templates": [
            {
                "id": "board-pack",
                "name": "Board Report Pack",
                "description": "Comprehensive monthly board report with financials, KPIs, and analysis",
                "sections": [
                    "Executive Summary",
                    "KPI Dashboard", 
                    "Financial Statements",
                    "Variance Analysis",
                    "Forecast & Outlook"
                ]
            },
            {
                "id": "investor-update",
                "name": "Investor Update",
                "description": "Quarterly investor update with highlights and metrics",
                "sections": [
                    "Highlights",
                    "Key Metrics",
                    "Product Updates",
                    "Financial Summary"
                ]
            },
            {
                "id": "variance-report",
                "name": "Variance Report",
                "description": "Detailed variance analysis vs budget and prior period",
                "sections": [
                    "Executive Summary",
                    "Revenue Variances",
                    "Expense Variances",
                    "Action Items"
                ]
            }
        ]
    }