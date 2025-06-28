#!/usr/bin/env python3
"""Populate demo metrics data for testing"""

import sys
sys.path.append('.')

from datetime import date, timedelta
from core.database import get_db_session
from metrics.models import Metric
import random

# Demo metrics for the default workspace
def populate_demo_metrics():
    """Add demo metrics to the database"""
    
    # Generate data for the last 6 months
    end_date = date.today()
    start_date = end_date - timedelta(days=180)
    
    metrics_config = {
        'revenue': {'base': 150000, 'growth': 0.05},
        'expenses': {'base': 120000, 'growth': 0.03},
        'mrr': {'base': 50000, 'growth': 0.08},
        'arr': {'base': 600000, 'growth': 0.08},
        'customers': {'base': 150, 'growth': 0.04},
        'churn_rate': {'base': 0.05, 'growth': -0.002},
        'cash_burn': {'base': 30000, 'growth': -0.01},
        'runway_months': {'base': 18, 'growth': 0.02},
    }
    
    with get_db_session() as db:
        # Clear existing metrics for default workspace
        db.query(Metric).filter_by(workspace_id='default').delete()
        
        current_date = start_date
        while current_date <= end_date:
            # Only add data for month-end dates
            if current_date.day == 1 or current_date == end_date:
                for metric_id, config in metrics_config.items():
                    # Calculate value with some randomness
                    days_from_start = (current_date - start_date).days
                    growth_factor = 1 + (config['growth'] * days_from_start / 30)
                    random_factor = random.uniform(0.95, 1.05)
                    
                    value = config['base'] * growth_factor * random_factor
                    
                    metric = Metric(
                        workspace_id='default',
                        metric_id=metric_id,
                        period_date=current_date,
                        value=round(value, 2),
                        source_template='demo_data'
                    )
                    db.add(metric)
            
            current_date += timedelta(days=1)
        
        db.commit()
        print(f"✅ Added demo metrics for default workspace")
        
        # Show summary
        count = db.query(Metric).filter_by(workspace_id='default').count()
        print(f"Total metrics: {count}")

if __name__ == "__main__":
    populate_demo_metrics()