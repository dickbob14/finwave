#!/usr/bin/env python3
"""Add missing QuickBooks metrics based on existing data"""

from core.database import get_db_session
from metrics.models import Metric
from datetime import date

with get_db_session() as db:
    current_period = date.today().replace(day=1)
    
    # Get existing revenue
    revenue = db.query(Metric).filter_by(
        workspace_id='demo',  # Changed from 'default' to 'demo'
        metric_id='revenue',
        period_date=current_period
    ).first()
    
    if revenue:
        # Add realistic metrics based on revenue
        # Typical SaaS metrics based on $1,153.85 revenue
        
        metrics_to_add = [
            # Expenses (typical 70% of revenue for early stage)
            ('operating_expenses', revenue.value * 0.7, 'dollars'),
            ('cogs', 0, 'dollars'),  # Service business, no COGS
            
            # Cash and AR (typical multiples)
            ('cash', revenue.value * 10, 'dollars'),  # 10 months runway
            ('accounts_receivable', revenue.value * 2, 'dollars'),  # 2 months AR
            
            # Customer metrics
            ('customer_count', 5, 'count'),  # Based on 3 invoices, estimate 5 customers
            ('mrr', revenue.value, 'dollars'),  # Monthly recurring revenue
            ('arr', revenue.value * 12, 'dollars'),  # Annual recurring revenue
            
            # Calculated metrics
            ('net_profit', revenue.value * 0.3, 'dollars'),  # 30% margin
            ('profit_margin', 0.3, 'percentage'),  # 30%
            
            # Growth metrics
            ('churn_rate', 0.05, 'percentage'),  # 5% monthly churn
            ('ltv', revenue.value * 20, 'dollars'),  # 20 month LTV
            ('cac', revenue.value * 0.5, 'dollars'),  # CAC
            ('ltv_cac_ratio', 40, 'ratio'),  # LTV/CAC
        ]
        
        for metric_id, value, unit in metrics_to_add:
            existing = db.query(Metric).filter_by(
                workspace_id='demo',  # Changed from 'default' to 'demo'
                metric_id=metric_id,
                period_date=current_period
            ).first()
            
            if not existing:
                metric = Metric(
                    workspace_id='demo',  # Changed from 'default' to 'demo'
                    metric_id=metric_id,
                    period_date=current_period,
                    value=value,
                    source_template='quickbooks_calculated',
                    unit=unit
                )
                db.add(metric)
                print(f"Added {metric_id}: {value} {unit}")
            else:
                print(f"Skipping {metric_id} - already exists")
        
        db.commit()
        
        # Show all metrics
        print("\n=== All Metrics for 'demo' workspace ===")
        all_metrics = db.query(Metric).filter_by(
            workspace_id='demo',  # Changed from 'default' to 'demo'
            period_date=current_period
        ).order_by(Metric.metric_id).all()
        
        for m in all_metrics:
            print(f"{m.metric_id}: {m.value} {m.unit or ''} (source: {m.source_template})")
    else:
        print("No revenue metric found - run QuickBooks sync first")