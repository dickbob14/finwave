"""
Payroll data sync implementation (Gusto/ADP)
"""

import logging
from datetime import datetime, date
from typing import Dict, Any

from models.integration import IntegrationCredential
from integrations.payroll.client import create_payroll_client
from core.database import get_db_session
from metrics.models import Metric

logger = logging.getLogger(__name__)


def sync_payroll_data(workspace_id: str, integration: IntegrationCredential) -> Dict[str, Any]:
    """
    Sync payroll data to metric store
    """
    logger.info(f"Starting payroll sync for workspace {workspace_id} ({integration.source})")
    
    try:
        # Initialize appropriate client
        client = create_payroll_client(
            integration.source,
            access_token=integration.access_token,
            refresh_token=integration.refresh_token
        )
        
        records_processed = 0
        current_period = date.today().replace(day=1)
        
        # 1. Sync employee data
        logger.info("Fetching employees...")
        employees = client.fetch_employees()
        
        if employees:
            # Calculate headcount metrics
            headcount_metrics = calculate_headcount_metrics(
                workspace_id, employees, current_period
            )
            records_processed += headcount_metrics
            logger.info(f"Calculated {headcount_metrics} headcount metrics")
        
        # 2. Sync payroll runs
        logger.info("Fetching payroll runs...")
        start_date = current_period.replace(month=1).isoformat()
        end_date = date.today().isoformat()
        
        payroll_runs = client.fetch_payroll_runs(start_date, end_date)
        
        if payroll_runs:
            # Calculate compensation metrics
            comp_metrics = calculate_compensation_metrics(
                workspace_id, payroll_runs, current_period
            )
            records_processed += comp_metrics
            logger.info(f"Calculated {comp_metrics} compensation metrics")
        
        # 3. Sync departments
        logger.info("Fetching departments...")
        departments = client.fetch_departments()
        
        if departments:
            # Calculate department metrics
            dept_metrics = calculate_department_metrics(
                workspace_id, departments, employees, current_period
            )
            records_processed += dept_metrics
            logger.info(f"Calculated {dept_metrics} department metrics")
        
        return {
            'status': 'success',
            'records_processed': records_processed,
            'last_sync': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Payroll sync failed: {e}")
        raise


def calculate_headcount_metrics(workspace_id: str, employees: list, 
                              period: date) -> int:
    """
    Calculate headcount and employee metrics
    """
    metrics_created = 0
    
    # Count employees by status and type
    active_employees = [e for e in employees if e.get('status') == 'Active']
    fte_count = len([e for e in active_employees if e.get('employment_type') == 'FTE'])
    contractor_count = len([e for e in active_employees if e.get('employment_type') == 'Contractor'])
    
    # Calculate hiring metrics
    current_month = period.month
    current_year = period.year
    
    new_hires = len([
        e for e in employees 
        if e.get('hire_date') and 
        datetime.fromisoformat(e['hire_date']).year == current_year and
        datetime.fromisoformat(e['hire_date']).month == current_month
    ])
    
    terminations = len([
        e for e in employees 
        if e.get('termination_date') and 
        datetime.fromisoformat(e['termination_date']).year == current_year and
        datetime.fromisoformat(e['termination_date']).month == current_month
    ])
    
    with get_db_session() as db:
        # Total headcount
        metric = Metric(
            workspace_id=workspace_id,
            metric_id='total_headcount',
            period_date=period,
            value=len(active_employees),
            source_template='payroll_sync',
            unit='count'
        )
        db.merge(metric)
        metrics_created += 1
        
        # FTE count
        metric = Metric(
            workspace_id=workspace_id,
            metric_id='fte_count',
            period_date=period,
            value=fte_count,
            source_template='payroll_sync',
            unit='count'
        )
        db.merge(metric)
        metrics_created += 1
        
        # Contractor count
        if contractor_count > 0:
            metric = Metric(
                workspace_id=workspace_id,
                metric_id='contractor_count',
                period_date=period,
                value=contractor_count,
                source_template='payroll_sync',
                unit='count'
            )
            db.merge(metric)
            metrics_created += 1
        
        # New hires
        metric = Metric(
            workspace_id=workspace_id,
            metric_id='new_hires',
            period_date=period,
            value=new_hires,
            source_template='payroll_sync',
            unit='count'
        )
        db.merge(metric)
        metrics_created += 1
        
        # Terminations
        metric = Metric(
            workspace_id=workspace_id,
            metric_id='terminations',
            period_date=period,
            value=terminations,
            source_template='payroll_sync',
            unit='count'
        )
        db.merge(metric)
        metrics_created += 1
        
        db.commit()
    
    return metrics_created


def calculate_compensation_metrics(workspace_id: str, payroll_runs: list, 
                                 period: date) -> int:
    """
    Calculate compensation and payroll cost metrics
    """
    metrics_created = 0
    
    # Sum payroll costs for the period
    total_gross_pay = 0
    total_employer_cost = 0
    
    for run in payroll_runs:
        pay_date = datetime.fromisoformat(run['pay_date']).date()
        if pay_date.year == period.year and pay_date.month == period.month:
            total_gross_pay += float(run.get('gross_pay', 0))
            total_employer_cost += float(run.get('total_employer_cost', run.get('gross_pay', 0)))
    
    # Calculate benefits load
    benefits_cost = total_employer_cost - total_gross_pay
    benefits_load_pct = (benefits_cost / total_gross_pay * 100) if total_gross_pay > 0 else 0
    
    with get_db_session() as db:
        # Gross payroll
        metric = Metric(
            workspace_id=workspace_id,
            metric_id='gross_payroll',
            period_date=period,
            value=total_gross_pay,
            source_template='payroll_sync',
            unit='dollars'
        )
        db.merge(metric)
        metrics_created += 1
        
        # Total payroll cost
        metric = Metric(
            workspace_id=workspace_id,
            metric_id='total_payroll_cost',
            period_date=period,
            value=total_employer_cost,
            source_template='payroll_sync',
            unit='dollars'
        )
        db.merge(metric)
        metrics_created += 1
        
        # Benefits load %
        metric = Metric(
            workspace_id=workspace_id,
            metric_id='benefits_load_pct',
            period_date=period,
            value=benefits_load_pct,
            source_template='payroll_sync',
            unit='percentage'
        )
        db.merge(metric)
        metrics_created += 1
        
        # Payroll as % of revenue (if revenue exists)
        revenue = db.query(Metric).filter_by(
            workspace_id=workspace_id,
            metric_id='revenue',
            period_date=period
        ).first()
        
        if revenue and revenue.value > 0:
            payroll_pct = (total_employer_cost / revenue.value) * 100
            metric = Metric(
                workspace_id=workspace_id,
                metric_id='payroll_as_pct_revenue',
                period_date=period,
                value=payroll_pct,
                source_template='payroll_sync',
                unit='percentage'
            )
            db.merge(metric)
            metrics_created += 1
        
        db.commit()
    
    return metrics_created


def calculate_department_metrics(workspace_id: str, departments: list, 
                               employees: list, period: date) -> int:
    """
    Calculate department-level metrics
    """
    metrics_created = 0
    
    # Count employees by department
    dept_headcount = {}
    for emp in employees:
        if emp.get('status') == 'Active' and emp.get('department'):
            dept = emp['department']
            dept_headcount[dept] = dept_headcount.get(dept, 0) + 1
    
    with get_db_session() as db:
        # Store headcount for major departments
        for dept_name, count in dept_headcount.items():
            if count > 0:
                # Normalize department names
                dept_id = dept_name.lower().replace(' ', '_').replace('&', 'and')
                metric_id = f"headcount_{dept_id}"
                
                metric = Metric(
                    workspace_id=workspace_id,
                    metric_id=metric_id,
                    period_date=period,
                    value=count,
                    source_template='payroll_sync',
                    unit='count'
                )
                db.merge(metric)
                metrics_created += 1
        
        db.commit()
    
    return metrics_created