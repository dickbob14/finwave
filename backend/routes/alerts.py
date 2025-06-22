"""
Alert API routes for variance monitoring
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy import and_, or_

from core.database import get_db_session
from scheduler.models import Alert, AlertSeverity, AlertStatus
from scheduler.variance_watcher import VarianceWatcher
from auth import get_current_user, require_workspace

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["alerts"])


# Response models
class AlertResponse(BaseModel):
    id: str
    workspace_id: str
    metric_id: str
    rule_name: str
    severity: str
    status: str
    message: str
    current_value: Optional[float] = None
    threshold_value: Optional[float] = None
    comparison_value: Optional[float] = None
    triggered_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    notes: Optional[str] = None

class AlertSummary(BaseModel):
    total: int
    active: int
    acknowledged: int
    resolved: int
    by_severity: Dict[str, int]
    recent_24h: int

class AlertUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


@router.get("/", response_model=List[AlertResponse])
async def get_alerts(
    workspace_id: str = Depends(require_workspace),
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    metric_id: Optional[str] = Query(None, description="Filter by metric"),
    days: int = Query(7, description="Number of days to look back"),
    limit: int = Query(100, description="Maximum results"),
    user: dict = Depends(get_current_user)
):
    """
    Get alerts for workspace with optional filters
    """
    try:
        with get_db_session() as db:
            query = db.query(Alert).filter(
                Alert.workspace_id == workspace_id
            )
            
            # Apply filters
            if status:
                query = query.filter(Alert.status == status)
            
            if severity:
                query = query.filter(Alert.severity == severity)
            
            if metric_id:
                query = query.filter(Alert.metric_id == metric_id)
            
            # Time filter
            since = datetime.utcnow() - timedelta(days=days)
            query = query.filter(Alert.triggered_at >= since)
            
            # Order and limit
            alerts = query.order_by(Alert.triggered_at.desc()).limit(limit).all()
            
            return [AlertResponse(
                id=alert.id,
                workspace_id=alert.workspace_id,
                metric_id=alert.metric_id,
                rule_name=alert.rule_name,
                severity=alert.severity,
                status=alert.status,
                message=alert.message,
                current_value=alert.current_value,
                threshold_value=alert.threshold_value,
                comparison_value=alert.comparison_value,
                triggered_at=alert.triggered_at,
                acknowledged_at=alert.acknowledged_at,
                resolved_at=alert.resolved_at,
                acknowledged_by=alert.acknowledged_by,
                notes=alert.notes
            ) for alert in alerts]
            
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=AlertSummary)
async def get_alert_summary(
    workspace_id: str = Depends(require_workspace),
    user: dict = Depends(get_current_user)
):
    """
    Get alert summary statistics for workspace
    """
    try:
        with get_db_session() as db:
            # Get all alerts
            all_alerts = db.query(Alert).filter(
                Alert.workspace_id == workspace_id
            ).all()
            
            # Calculate stats
            total = len(all_alerts)
            active = len([a for a in all_alerts if a.status == AlertStatus.ACTIVE.value])
            acknowledged = len([a for a in all_alerts if a.status == AlertStatus.ACKNOWLEDGED.value])
            resolved = len([a for a in all_alerts if a.status == AlertStatus.RESOLVED.value])
            
            # By severity
            by_severity = {
                AlertSeverity.INFO.value: 0,
                AlertSeverity.WARNING.value: 0,
                AlertSeverity.CRITICAL.value: 0
            }
            
            for alert in all_alerts:
                if alert.severity in by_severity:
                    by_severity[alert.severity] += 1
            
            # Recent 24h
            cutoff = datetime.utcnow() - timedelta(hours=24)
            recent = len([a for a in all_alerts if a.triggered_at >= cutoff])
            
            return AlertSummary(
                total=total,
                active=active,
                acknowledged=acknowledged,
                resolved=resolved,
                by_severity=by_severity,
                recent_24h=recent
            )
            
    except Exception as e:
        logger.error(f"Error getting alert summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    workspace_id: str = Depends(require_workspace),
    user: dict = Depends(get_current_user)
):
    """
    Get specific alert details
    """
    try:
        with get_db_session() as db:
            alert = db.query(Alert).filter(
                Alert.id == alert_id,
                Alert.workspace_id == workspace_id
            ).first()
            
            if not alert:
                raise HTTPException(status_code=404, detail="Alert not found")
            
            return AlertResponse(
                id=alert.id,
                workspace_id=alert.workspace_id,
                metric_id=alert.metric_id,
                rule_name=alert.rule_name,
                severity=alert.severity,
                status=alert.status,
                message=alert.message,
                current_value=alert.current_value,
                threshold_value=alert.threshold_value,
                comparison_value=alert.comparison_value,
                triggered_at=alert.triggered_at,
                acknowledged_at=alert.acknowledged_at,
                resolved_at=alert.resolved_at,
                acknowledged_by=alert.acknowledged_by,
                notes=alert.notes
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: str,
    update: AlertUpdate,
    workspace_id: str = Depends(require_workspace),
    user: dict = Depends(get_current_user)
):
    """
    Update alert status or add notes
    """
    try:
        with get_db_session() as db:
            alert = db.query(Alert).filter(
                Alert.id == alert_id,
                Alert.workspace_id == workspace_id
            ).first()
            
            if not alert:
                raise HTTPException(status_code=404, detail="Alert not found")
            
            # Update status
            if update.status:
                if update.status not in [s.value for s in AlertStatus]:
                    raise HTTPException(status_code=400, detail="Invalid status")
                
                alert.status = update.status
                
                # Set timestamps
                if update.status == AlertStatus.ACKNOWLEDGED.value:
                    alert.acknowledged_at = datetime.utcnow()
                    alert.acknowledged_by = user.get('email', user.get('sub'))
                elif update.status == AlertStatus.RESOLVED.value:
                    alert.resolved_at = datetime.utcnow()
                    alert.resolved_by = user.get('email', user.get('sub'))
            
            # Update notes
            if update.notes is not None:
                alert.notes = update.notes
            
            db.commit()
            db.refresh(alert)
            
            return AlertResponse(
                id=alert.id,
                workspace_id=alert.workspace_id,
                metric_id=alert.metric_id,
                rule_name=alert.rule_name,
                severity=alert.severity,
                status=alert.status,
                message=alert.message,
                current_value=alert.current_value,
                threshold_value=alert.threshold_value,
                comparison_value=alert.comparison_value,
                triggered_at=alert.triggered_at,
                acknowledged_at=alert.acknowledged_at,
                resolved_at=alert.resolved_at,
                acknowledged_by=alert.acknowledged_by,
                notes=alert.notes
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-now")
async def trigger_variance_check(
    workspace_id: str = Depends(require_workspace),
    user: dict = Depends(get_current_user)
):
    """
    Manually trigger variance check for workspace
    """
    try:
        watcher = VarianceWatcher()
        alerts = watcher.check_workspace(workspace_id)
        
        return {
            'status': 'completed',
            'workspace_id': workspace_id,
            'alerts_generated': len(alerts),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error running variance check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/active")
async def get_active_rules(
    workspace_id: str = Depends(require_workspace),
    user: dict = Depends(get_current_user)
):
    """
    Get list of active variance rules
    """
    try:
        watcher = VarianceWatcher()
        
        # Filter rules that apply to this workspace's metrics
        active_rules = []
        
        for rule in watcher.rules:
            active_rules.append({
                'metric_id': rule['metric_id'],
                'comparison': rule['comparison'],
                'threshold_type': rule['threshold_type'],
                'threshold_value': rule['threshold_value'],
                'direction': rule['direction'],
                'severity': rule.get('severity', 'warning'),
                'message_template': rule.get('message', ''),
                'cooldown_hours': rule.get('cooldown_hours', 24)
            })
        
        # Add compound rules
        compound_rules = []
        for rule in watcher.compound_rules:
            compound_rules.append({
                'name': rule['name'],
                'conditions': len(rule['conditions']),
                'severity': rule.get('severity', 'warning'),
                'message_template': rule.get('message', ''),
                'cooldown_hours': rule.get('cooldown_hours', 48)
            })
        
        return {
            'simple_rules': active_rules,
            'compound_rules': compound_rules,
            'total': len(active_rules) + len(compound_rules),
            'check_frequency_minutes': watcher.settings.get('check_frequency_minutes', 60)
        }
        
    except Exception as e:
        logger.error(f"Error fetching rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))