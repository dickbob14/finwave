"""
Scheduled insight generation tasks
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

from core.database import get_db_session
from models.workspace import Workspace
from insights.client import InsightEngine

logger = logging.getLogger(__name__)


def generate_scheduled_insights() -> Dict[str, Any]:
    """
    Generate insights for all active workspaces
    Called by scheduler periodically
    """
    results = {
        'workspaces_processed': 0,
        'insights_generated': 0,
        'errors': []
    }
    
    with get_db_session() as db:
        # Get active workspaces
        workspaces = db.query(Workspace).filter(
            Workspace.billing_status.in_(['trial', 'active'])
        ).all()
        
        for workspace in workspaces:
            try:
                logger.info(f"Generating insights for workspace: {workspace.id}")
                
                engine = InsightEngine(workspace.id)
                
                # Generate different types of insights
                insight_types = [
                    'executive_summary',
                    'kpi_dashboard',
                    'variance_analysis'
                ]
                
                for insight_type in insight_types:
                    try:
                        result = engine.generate_insights(
                            template_name=insight_type,
                            force_regenerate=True
                        )
                        results['insights_generated'] += 1
                    except Exception as e:
                        logger.error(f"Failed to generate {insight_type} for {workspace.id}: {e}")
                        results['errors'].append({
                            'workspace_id': workspace.id,
                            'insight_type': insight_type,
                            'error': str(e)
                        })
                
                results['workspaces_processed'] += 1
                
            except Exception as e:
                logger.error(f"Failed to process workspace {workspace.id}: {e}")
                results['errors'].append({
                    'workspace_id': workspace.id,
                    'error': str(e)
                })
    
    logger.info(f"Scheduled insights complete: {results['workspaces_processed']} workspaces, "
               f"{results['insights_generated']} insights generated")
    
    return results