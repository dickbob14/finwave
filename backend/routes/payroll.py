"""
Payroll API routes for headcount and compensation data
"""

import logging
from datetime import datetime, date
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
import pandas as pd

# Import payroll client
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from integrations.payroll.client import create_payroll_client, test_payroll_connection
from auth import get_current_user, require_workspace

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payroll", tags=["payroll"])

# Configuration
PAYROLL_TYPE = os.getenv("PAYROLL_TYPE", "gusto")

# Response models
class HeadcountSummary(BaseModel):
    total_headcount: int
    fte_count: int
    contractor_count: int
    by_department: Dict[str, int]
    new_hires_mtd: int
    terminations_mtd: int
    net_change_mtd: int

class PayrollStatus(BaseModel):
    connected: bool
    payroll_type: str
    last_sync: Optional[str] = None
    error: Optional[str] = None

@router.get("/status", response_model=PayrollStatus)
async def get_payroll_status():
    """
    Check payroll system connection status
    """
    try:
        connected = test_payroll_connection(PAYROLL_TYPE)
        
        return PayrollStatus(
            connected=connected,
            payroll_type=PAYROLL_TYPE,
            last_sync=datetime.now().isoformat() if connected else None,
            error=None if connected else "Failed to connect to payroll system"
        )
    except Exception as e:
        logger.error(f"Error checking payroll status: {e}")
        return PayrollStatus(
            connected=False,
            payroll_type=PAYROLL_TYPE,
            error=str(e)
        )

@router.get("/headcount", response_model=HeadcountSummary)
async def get_headcount_summary(
    as_of_date: Optional[date] = Query(None, description="As of date (defaults to today)"),
    user: dict = Depends(get_current_user)
):
    """
    Get current headcount summary
    """
    try:
        client = create_payroll_client(PAYROLL_TYPE)
        
        # Default to today if not specified
        if not as_of_date:
            as_of_date = date.today()
        
        # Get headcount metrics
        metrics = client.get_headcount_summary(as_of_date.isoformat())
        
        # Calculate net change
        net_change = metrics.get('new_hires_mtd', 0) - metrics.get('terminations_mtd', 0)
        
        return HeadcountSummary(
            total_headcount=metrics.get('total_headcount', 0),
            fte_count=metrics.get('fte_count', 0),
            contractor_count=metrics.get('contractor_count', 0),
            by_department=metrics.get('by_department', {}),
            new_hires_mtd=metrics.get('new_hires_mtd', 0),
            terminations_mtd=metrics.get('terminations_mtd', 0),
            net_change_mtd=net_change
        )
        
    except Exception as e:
        logger.error(f"Error fetching headcount: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/employees")
async def get_employees(
    as_of_date: Optional[date] = Query(None, description="As of date"),
    department: Optional[str] = Query(None, description="Filter by department"),
    employment_type: Optional[str] = Query(None, description="Filter by type (FTE/Contractor)"),
    limit: int = Query(100, description="Maximum results"),
    user: dict = Depends(get_current_user)
):
    """
    Get employee roster with optional filters
    """
    try:
        client = create_payroll_client(PAYROLL_TYPE)
        
        # Fetch employees
        employees_df = client.fetch_employees(
            as_of_date.isoformat() if as_of_date else None
        )
        
        # Apply filters
        if department:
            employees_df = employees_df[
                employees_df['department'].str.contains(department, case=False, na=False)
            ]
        
        if employment_type:
            employees_df = employees_df[
                employees_df['employment_type'] == employment_type
            ]
        
        # Limit results
        if len(employees_df) > limit:
            employees_df = employees_df.head(limit)
        
        # Convert to dict
        employees = employees_df.to_dict('records') if not employees_df.empty else []
        
        return {
            'total': len(employees),
            'employees': employees
        }
        
    except Exception as e:
        logger.error(f"Error fetching employees: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compensation-summary")
async def get_compensation_summary(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    user: dict = Depends(get_current_user)
):
    """
    Get compensation summary for a period
    """
    try:
        client = create_payroll_client(PAYROLL_TYPE)
        
        # Fetch payroll runs
        payroll_df = client.fetch_payroll_runs(
            start_date.isoformat(),
            end_date.isoformat()
        )
        
        if payroll_df.empty:
            return {
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'total_gross_pay': 0,
                'total_employer_cost': 0,
                'benefits_load_pct': 0,
                'pay_periods': 0
            }
        
        # Calculate summary
        total_gross = payroll_df['gross_pay'].sum()
        total_cost = payroll_df['total_employer_cost'].sum() if 'total_employer_cost' in payroll_df else total_gross
        benefits_load = ((total_cost - total_gross) / total_gross * 100) if total_gross > 0 else 0
        
        return {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'total_gross_pay': float(total_gross),
            'total_employer_cost': float(total_cost),
            'benefits_load_pct': float(benefits_load),
            'pay_periods': payroll_df['pay_date'].nunique() if 'pay_date' in payroll_df else 0,
            'employee_count': payroll_df['employee_id'].nunique() if 'employee_id' in payroll_df else 0
        }
        
    except Exception as e:
        logger.error(f"Error fetching compensation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/departments")
async def get_departments(
    user: dict = Depends(get_current_user)
):
    """
    Get list of departments with headcount
    """
    try:
        client = create_payroll_client(PAYROLL_TYPE)
        
        # Fetch departments
        departments_df = client.fetch_departments()
        
        if departments_df.empty:
            return {
                'departments': [],
                'total': 0
            }
        
        # Convert to dict
        departments = departments_df.to_dict('records')
        
        return {
            'departments': departments,
            'total': len(departments)
        }
        
    except Exception as e:
        logger.error(f"Error fetching departments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/retention-cohorts")
async def get_retention_cohorts(
    months_back: int = Query(12, description="Number of months to analyze"),
    user: dict = Depends(get_current_user)
):
    """
    Get employee retention by hire cohort
    """
    try:
        client = create_payroll_client(PAYROLL_TYPE)
        
        # Fetch all employees (including terminated)
        employees_df = client.fetch_employees()
        
        if employees_df.empty or 'hire_date' not in employees_df.columns:
            return {
                'cohorts': [],
                'summary': {
                    '30_day_retention': 0,
                    '90_day_retention': 0,
                    '365_day_retention': 0
                }
            }
        
        # Convert dates
        employees_df['hire_date'] = pd.to_datetime(employees_df['hire_date'])
        employees_df['termination_date'] = pd.to_datetime(employees_df['termination_date'])
        
        # Calculate retention by cohort
        today = pd.Timestamp.now()
        cohorts = []
        
        for months_ago in range(months_back):
            cohort_date = today - pd.DateOffset(months=months_ago)
            cohort_month = cohort_date.to_period('M')
            
            # Get employees hired in this month
            cohort_employees = employees_df[
                employees_df['hire_date'].dt.to_period('M') == cohort_month
            ]
            
            if len(cohort_employees) > 0:
                # Calculate retention
                total_hired = len(cohort_employees)
                still_active = len(cohort_employees[cohort_employees['status'] == 'Active'])
                
                cohorts.append({
                    'cohort_month': str(cohort_month),
                    'hired': total_hired,
                    'active': still_active,
                    'terminated': total_hired - still_active,
                    'retention_rate': (still_active / total_hired * 100) if total_hired > 0 else 0
                })
        
        # Calculate overall retention rates
        def calc_retention_rate(days):
            eligible = employees_df[
                (today - employees_df['hire_date']).dt.days >= days
            ]
            if len(eligible) == 0:
                return 0
            
            retained = len(eligible[
                (eligible['status'] == 'Active') | 
                ((today - eligible['termination_date']).dt.days < days)
            ])
            
            return retained / len(eligible) * 100
        
        summary = {
            '30_day_retention': calc_retention_rate(30),
            '90_day_retention': calc_retention_rate(90),
            '365_day_retention': calc_retention_rate(365)
        }
        
        return {
            'cohorts': cohorts,
            'summary': summary
        }
        
    except Exception as e:
        logger.error(f"Error calculating retention cohorts: {e}")
        raise HTTPException(status_code=500, detail=str(e))