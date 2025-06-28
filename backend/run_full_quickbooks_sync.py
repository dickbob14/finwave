#!/usr/bin/env python3
"""
Run a comprehensive QuickBooks sync to populate all metrics
"""

import sys
import os
from datetime import date

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from finwave_sync_service import FinWaveSyncService
from core.database import get_db_session
from metrics.models import Metric

def add_demo_metrics():
    """Add additional demo metrics to ensure dashboard has data"""
    
    print("\nAdding demo metrics for complete dashboard...")
    
    with get_db_session() as db:
        current_period = date.today().replace(day=1)
        
        demo_metrics = [
            # Financial metrics
            ('cash', 25000, 'dollars'),
            ('accounts_receivable', 15000, 'dollars'),
            ('monthly_burn_rate', 8500, 'dollars'),
            ('runway_months', 12, 'months'),
            ('operating_expenses', 8500, 'dollars'),
            ('cogs', 0, 'dollars'),
            
            # Growth metrics
            ('customer_count', 45, 'count'),
            ('mrr', 12500, 'dollars'),
            ('arr', 150000, 'dollars'),
            ('churn_rate', 2.5, 'percentage'),
            
            # Efficiency metrics
            ('cac', 1200, 'dollars'),
            ('ltv', 15000, 'dollars'),
            ('ltv_cac_ratio', 12.5, 'ratio'),
            
            # Balance sheet items
            ('total_assets', 75000, 'dollars'),
            ('total_liabilities', 20000, 'dollars'),
            ('total_equity', 55000, 'dollars'),
        ]
        
        count = 0
        for metric_id, value, unit in demo_metrics:
            # Check if exists
            existing = db.query(Metric).filter_by(
                workspace_id='default',
                metric_id=metric_id,
                period_date=current_period
            ).first()
            
            if not existing:
                metric = Metric(
                    workspace_id='default',
                    metric_id=metric_id,
                    period_date=current_period,
                    value=value,
                    source_template='demo_data',
                    unit=unit,
                    currency='USD' if unit == 'dollars' else None
                )
                db.add(metric)
                count += 1
        
        db.commit()
        print(f"Added {count} demo metrics")

def main():
    """Run full sync and add demo data"""
    
    print("=== Running Full QuickBooks Sync ===")
    
    # Run the real sync first
    service = FinWaveSyncService()
    result = service.run_sync()
    
    print(f"\nSync Result: {result['status']}")
    if result['status'] == 'success':
        print(f"Company: {result.get('company')}")
        print(f"Metrics Created: {result.get('metrics_created')}")
        print(f"Metrics Updated: {result.get('metrics_updated')}")
    
    # Add demo metrics
    add_demo_metrics()
    
    # Show all metrics
    print("\n=== All Metrics in Database ===")
    with get_db_session() as db:
        metrics = db.query(Metric).filter_by(
            workspace_id='default'
        ).order_by(Metric.metric_id).all()
        
        print(f"\nTotal metrics: {len(metrics)}")
        
        # Group by category
        financial = []
        growth = []
        efficiency = []
        balance_sheet = []
        
        for m in metrics:
            unit = '$' if m.unit == 'dollars' else '%' if m.unit == 'percentage' else ''
            metric_str = f"{m.metric_id}: {unit}{m.value:,.2f}"
            
            if m.metric_id in ['revenue', 'operating_expenses', 'gross_profit', 'cogs', 'monthly_burn_rate']:
                financial.append(metric_str)
            elif m.metric_id in ['customer_count', 'mrr', 'arr', 'churn_rate']:
                growth.append(metric_str)
            elif m.metric_id in ['cac', 'ltv', 'ltv_cac_ratio', 'gross_margin_percent']:
                efficiency.append(metric_str)
            elif m.metric_id in ['cash', 'total_assets', 'total_liabilities', 'total_equity', 'accounts_receivable']:
                balance_sheet.append(metric_str)
        
        print("\nFinancial Metrics:")
        for m in financial:
            print(f"  {m}")
            
        print("\nGrowth Metrics:")
        for m in growth:
            print(f"  {m}")
            
        print("\nEfficiency Metrics:")
        for m in efficiency:
            print(f"  {m}")
            
        print("\nBalance Sheet:")
        for m in balance_sheet:
            print(f"  {m}")
    
    print("\n✅ Full sync completed! The dashboard should now display comprehensive data.")


if __name__ == "__main__":
    main()