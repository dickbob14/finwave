"""
QuickBooks Debug and Manual Sync Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging
from datetime import datetime

from core.database import get_db
from models.integration import IntegrationCredential
from integrations.quickbooks.sync import sync_quickbooks_data
from metrics.models import Metric

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{workspace_id}/quickbooks/status")
def get_quickbooks_status(
    workspace_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Check QuickBooks integration status and configuration"""
    
    # Get integration
    integration = db.query(IntegrationCredential).filter_by(
        workspace_id=workspace_id,
        source="quickbooks"
    ).first()
    
    if not integration:
        return {
            "status": "not_connected",
            "message": "QuickBooks not connected for this workspace"
        }
    
    # Get metadata
    metadata = integration.integration_metadata or {}
    
    return {
        "status": integration.status,
        "last_synced": integration.last_synced_at.isoformat() if integration.last_synced_at else None,
        "last_error": integration.last_sync_error,
        "realm_id": metadata.get('realm_id'),
        "token_expires": integration.expires_at.isoformat() if integration.expires_at else None,
        "token_valid": integration.expires_at > datetime.utcnow() if integration.expires_at else False,
        "metadata": metadata
    }


@router.post("/{workspace_id}/quickbooks/sync")
def trigger_manual_sync(
    workspace_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Manually trigger QuickBooks sync"""
    
    # Get integration
    integration = db.query(IntegrationCredential).filter_by(
        workspace_id=workspace_id,
        source="quickbooks"
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="QuickBooks not connected")
    
    if integration.status != "connected":
        raise HTTPException(status_code=400, detail=f"Integration status is {integration.status}")
    
    try:
        # Run sync
        logger.info(f"Starting manual sync for workspace {workspace_id}")
        result = sync_quickbooks_data(workspace_id, integration)
        
        # Update integration
        integration.last_synced_at = datetime.utcnow()
        integration.last_sync_error = None
        db.commit()
        
        return {
            "status": "success",
            "records_processed": result.get('records_processed', 0),
            "sync_time": datetime.utcnow().isoformat(),
            "details": result
        }
        
    except Exception as e:
        logger.error(f"Manual sync failed: {e}")
        
        # Update error
        integration.last_sync_error = str(e)
        db.commit()
        
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/{workspace_id}/metrics")
def get_workspace_metrics(
    workspace_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get all metrics for a workspace"""
    
    metrics = db.query(Metric).filter_by(workspace_id=workspace_id).all()
    
    if not metrics:
        return {
            "count": 0,
            "metrics": [],
            "message": "No metrics found. Run QuickBooks sync first."
        }
    
    # Group by metric_id
    metric_dict = {}
    for m in metrics:
        if m.metric_id not in metric_dict:
            metric_dict[m.metric_id] = []
        metric_dict[m.metric_id].append({
            "period": m.period_date.isoformat() if m.period_date else None,
            "value": float(m.value) if m.value else 0,
            "updated": m.updated_at.isoformat()
        })
    
    return {
        "count": len(metrics),
        "unique_metrics": len(metric_dict),
        "metrics": metric_dict
    }


@router.get("/{workspace_id}/dashboard/data")
def get_dashboard_data(
    workspace_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get simplified dashboard data"""
    
    # Get latest metrics
    from sqlalchemy import func, and_
    from datetime import date
    
    current_period = date.today().replace(day=1)
    
    # Get latest value for each metric
    subquery = db.query(
        Metric.metric_id,
        func.max(Metric.period_date).label('max_date')
    ).filter_by(
        workspace_id=workspace_id
    ).group_by(Metric.metric_id).subquery()
    
    metrics = db.query(Metric).join(
        subquery,
        and_(
            Metric.metric_id == subquery.c.metric_id,
            Metric.period_date == subquery.c.max_date,
            Metric.workspace_id == workspace_id
        )
    ).all()
    
    # Build response
    metric_dict = {m.metric_id: float(m.value) if m.value else 0 for m in metrics}
    
    revenue = metric_dict.get('revenue', 0)
    expenses = metric_dict.get('opex', 0) + metric_dict.get('cogs', 0)
    net_profit = metric_dict.get('net_income', 0)
    profit_margin = (net_profit / revenue * 100) if revenue > 0 else 0
    
    return {
        "summary": {
            "revenue": revenue,
            "expenses": expenses,
            "net_profit": net_profit,
            "profit_margin": profit_margin,
            "cash": metric_dict.get('cash', 0),
            "accounts_receivable": metric_dict.get('accounts_receivable', 0)
        },
        "metrics": metric_dict,
        "last_sync": max(m.updated_at for m in metrics).isoformat() if metrics else None,
        "has_data": len(metrics) > 0
    }


# Export router
__all__ = ['router']