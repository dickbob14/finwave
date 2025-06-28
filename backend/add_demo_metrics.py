#!/usr/bin/env python3
"""Add demo metrics to database"""

from core.database import get_db_session
from metrics.models import Metric
from datetime import date

with get_db_session() as db:
    # Add some demo metrics
    metrics = [
        Metric(workspace_id='demo', metric_id='revenue', period_date=date.today().replace(day=1), value=567890, unit='dollars', source_template='quickbooks'),
        Metric(workspace_id='demo', metric_id='expenses', period_date=date.today().replace(day=1), value=432100, unit='dollars', source_template='quickbooks'),
        Metric(workspace_id='demo', metric_id='profit_margin', period_date=date.today().replace(day=1), value=0.238, unit='percentage', source_template='quickbooks'),
        Metric(workspace_id='demo', metric_id='customer_count', period_date=date.today().replace(day=1), value=1847, unit='count', source_template='quickbooks'),
    ]
    for m in metrics:
        existing = db.query(Metric).filter_by(
            workspace_id=m.workspace_id,
            metric_id=m.metric_id,
            period_date=m.period_date
        ).first()
        if not existing:
            db.add(m)
    db.commit()
    print('Demo metrics added')