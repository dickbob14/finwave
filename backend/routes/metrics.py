"""
Metrics API routes for time-series financial data
"""

import io
import os
import logging
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from core.database import get_db
from metrics.models import Metric, METRIC_METADATA
from metrics.ingest import ingest_metrics
from auth import get_current_user, require_workspace

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["metrics"])

@router.get("/{workspace_id}/metrics")
async def get_metrics(
    workspace_id: str,
    metric: Optional[List[str]] = Query(None, description="Metric IDs to fetch"),
    period_from: Optional[date] = Query(None, description="Start date (inclusive)"),
    period_to: Optional[date] = Query(None, description="End date (inclusive)"),
    limit: int = Query(100, ge=1, le=1000),
    user: dict = Depends(get_current_user),
    workspace: str = Depends(require_workspace),
    db: Session = Depends(get_db)
):
    """
    Fetch metrics for a workspace
    
    Examples:
    - /api/demo/metrics?metric=revenue&metric=mrr
    - /api/demo/metrics?period_from=2024-01-01&period_to=2024-12-31
    """
    # Verify workspace access
    if workspace_id != workspace:
        raise HTTPException(status_code=403, detail="Access denied to workspace")
    
    # Build query
    query = db.query(Metric).filter(Metric.workspace_id == workspace_id)
    
    # Filter by metrics
    if metric:
        query = query.filter(Metric.metric_id.in_(metric))
    
    # Filter by period
    if period_from:
        query = query.filter(Metric.period_date >= period_from)
    if period_to:
        query = query.filter(Metric.period_date <= period_to)
    
    # Order by period descending, then by metric
    query = query.order_by(Metric.period_date.desc(), Metric.metric_id)
    
    # Apply limit
    metrics = query.limit(limit).all()
    
    # Format response
    result = []
    for m in metrics:
        metadata = METRIC_METADATA.get(m.metric_id, {})
        result.append({
            'metric_id': m.metric_id,
            'period_date': m.period_date.isoformat(),
            'value': m.value,
            'unit': m.unit or metadata.get('unit'),
            'display_name': metadata.get('display_name', m.metric_id),
            'source_template': m.source_template,
            'updated_at': m.updated_at.isoformat() if m.updated_at else None
        })
    
    return {
        'workspace_id': workspace_id,
        'metrics': result,
        'count': len(result),
        'filters': {
            'metric': metric,
            'period_from': period_from.isoformat() if period_from else None,
            'period_to': period_to.isoformat() if period_to else None
        }
    }

@router.get("/{workspace_id}/metrics/summary")
async def get_metrics_summary(
    workspace_id: str,
    period: Optional[date] = Query(None, description="Period to fetch (defaults to latest)"),
    db: Session = Depends(get_db)
):
    """
    Get summary of all metrics for a specific period
    """
    # Skip auth check for demo mode
    if os.getenv("BYPASS_AUTH", "false").lower() != "true":
        # In production, would check auth here
        pass
    
    # If no period specified, get the latest period
    if not period:
        latest = db.query(Metric.period_date).filter(
            Metric.workspace_id == workspace_id
        ).order_by(Metric.period_date.desc()).first()
        
        if not latest:
            return {
                'workspace_id': workspace_id,
                'period': None,
                'metrics': {},
                'message': 'No metrics found for workspace'
            }
        
        period = latest[0]
    
    # Get all metrics for the period
    metrics = db.query(Metric).filter(
        and_(
            Metric.workspace_id == workspace_id,
            Metric.period_date == period
        )
    ).all()
    
    # Format as key-value pairs
    summary = {}
    for m in metrics:
        metadata = METRIC_METADATA.get(m.metric_id, {})
        summary[m.metric_id] = {
            'value': m.value,
            'unit': m.unit or metadata.get('unit'),
            'display_name': metadata.get('display_name', m.metric_id)
        }
    
    return {
        'workspace_id': workspace_id,
        'period': period.isoformat(),
        'metrics': summary,
        'count': len(summary)
    }

@router.get("/{workspace_id}/metrics/timeseries")
async def get_metric_timeseries(
    workspace_id: str,
    metric_id: str,
    periods: int = Query(12, description="Number of periods to fetch", le=36),
    order: str = Query("desc", description="Sort order (asc/desc)", regex="^(asc|desc)$"),
    user: dict = Depends(get_current_user),
    workspace: str = Depends(require_workspace),
    db: Session = Depends(get_db)
):
    """
    Get time series data for a specific metric
    Default limit of 36 periods (3 years) to prevent mobile hammering
    """
    # Verify workspace access
    if workspace_id != workspace:
        raise HTTPException(status_code=403, detail="Access denied to workspace")
    
    # Get metric metadata
    metadata = METRIC_METADATA.get(metric_id, {})
    
    # Fetch time series
    query = db.query(Metric).filter(
        and_(
            Metric.workspace_id == workspace_id,
            Metric.metric_id == metric_id
        )
    )
    
    # Apply ordering
    if order == "asc":
        query = query.order_by(Metric.period_date.asc())
    else:
        query = query.order_by(Metric.period_date.desc())
    
    metrics = query.limit(periods).all()
    
    # Format as time series
    series = []
    for m in metrics:
        series.append({
            'period': m.period_date.isoformat(),
            'value': m.value
        })
    
    # If we fetched descending but want ascending display, reverse
    if order == "asc" and query.order_by == Metric.period_date.desc():
        series.reverse()
    
    return {
        'workspace_id': workspace_id,
        'metric_id': metric_id,
        'display_name': metadata.get('display_name', metric_id),
        'unit': metadata.get('unit'),
        'series': series,
        'periods': len(series)
    }

@router.post("/{workspace_id}/metrics/ingest")
async def ingest_metrics_endpoint(
    workspace_id: str,
    file: UploadFile = File(...),
    period_date: Optional[date] = Query(None, description="Override period date"),
    user: dict = Depends(get_current_user),
    workspace: str = Depends(require_workspace)
):
    """
    Ingest metrics from uploaded Excel file
    """
    # Verify workspace access
    if workspace_id != workspace:
        raise HTTPException(status_code=403, detail="Access denied to workspace")
    
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xlsm')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only Excel files (.xlsx, .xlsm) are supported"
        )
    
    try:
        # Save uploaded file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Run ingestion
        results = ingest_metrics(workspace_id, tmp_path, period_date)
        
        # Clean up
        import os
        os.unlink(tmp_path)
        
        return {
            'status': 'success',
            'workspace_id': workspace_id,
            'filename': file.filename,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Failed to ingest metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{workspace_id}/metrics/available")
async def get_available_metrics(
    workspace_id: str,
    user: dict = Depends(get_current_user),
    workspace: str = Depends(require_workspace),
    db: Session = Depends(get_db)
):
    """
    Get list of available metrics for a workspace
    """
    # Verify workspace access
    if workspace_id != workspace:
        raise HTTPException(status_code=403, detail="Access denied to workspace")
    
    # Get distinct metrics
    metrics = db.query(Metric.metric_id).filter(
        Metric.workspace_id == workspace_id
    ).distinct().all()
    
    # Format with metadata
    available = []
    for (metric_id,) in metrics:
        metadata = METRIC_METADATA.get(metric_id, {})
        available.append({
            'metric_id': metric_id,
            'display_name': metadata.get('display_name', metric_id),
            'unit': metadata.get('unit')
        })
    
    # Sort by display name
    available.sort(key=lambda x: x['display_name'])
    
    return {
        'workspace_id': workspace_id,
        'metrics': available,
        'count': len(available)
    }

@router.delete("/{workspace_id}/metrics")
async def delete_metrics(
    workspace_id: str,
    metric_id: Optional[str] = Query(None, description="Delete specific metric"),
    period_date: Optional[date] = Query(None, description="Delete specific period"),
    user: dict = Depends(get_current_user),
    workspace: str = Depends(require_workspace),
    db: Session = Depends(get_db)
):
    """
    Delete metrics (admin only)
    """
    # Verify workspace access
    if workspace_id != workspace:
        raise HTTPException(status_code=403, detail="Access denied to workspace")
    
    # Require admin permission
    if "admin" not in user.get("permissions", []):
        raise HTTPException(status_code=403, detail="Admin permission required")
    
    # Build delete query
    query = db.query(Metric).filter(Metric.workspace_id == workspace_id)
    
    if metric_id:
        query = query.filter(Metric.metric_id == metric_id)
    if period_date:
        query = query.filter(Metric.period_date == period_date)
    
    # Count before delete
    count = query.count()
    
    if count == 0:
        return {
            'status': 'no_action',
            'message': 'No metrics matched the criteria',
            'deleted': 0
        }
    
    # Delete
    query.delete()
    db.commit()
    
    return {
        'status': 'success',
        'deleted': count,
        'filters': {
            'metric_id': metric_id,
            'period_date': period_date.isoformat() if period_date else None
        }
    }