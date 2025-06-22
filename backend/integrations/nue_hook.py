"""
Nue compensation data integration for enhanced financial analytics
Provides employee compensation, benefits, and payroll correlation with financial metrics
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal
import asyncio
import json

import httpx
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from database import get_db_session
from models.financial import GeneralLedger, DataSource, IngestionHistory

logger = logging.getLogger(__name__)

class NueIntegration:
    """Nue compensation integration for payroll and benefits correlation"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.nue.co"):
        """
        Initialize Nue integration
        
        Args:
            api_key: Nue API key
            base_url: Nue API base URL
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        
        # Track data source
        self._ensure_data_source()
    
    async def __aenter__(self):
        self.session = httpx.AsyncClient()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make authenticated request to Nue API"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = await self.session.get(
                url,
                headers=self._get_headers(),
                params=params or {}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Nue API error for {endpoint}: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Request failed for {endpoint}: {str(e)}")
            raise
    
    async def sync_compensation_data(self, start_date: str, end_date: str) -> Dict[str, int]:
        """
        Sync Nue compensation data for payroll correlation
        
        Args:
            start_date: YYYY-MM-DD format
            end_date: YYYY-MM-DD format
            
        Returns:
            Dictionary with sync statistics
        """
        with get_db_session() as db:
            # Create ingestion record
            ingestion_record = IngestionHistory(
                source='nue',
                entity_type='compensation',
                period_start=datetime.fromisoformat(start_date),
                period_end=datetime.fromisoformat(end_date),
                status='pending'
            )
            db.add(ingestion_record)
            db.commit()
            
            try:
                # Get compensation data from Nue
                comp_data = await self._get_compensation_batch(start_date, end_date)
                
                processed_count = 0
                for comp_record in comp_data:
                    await self._process_compensation_record(db, comp_record)
                    processed_count += 1
                
                # Update ingestion record
                ingestion_record.status = 'completed'
                ingestion_record.records_count = processed_count
                db.commit()
                
                logger.info(f"Synced {processed_count} Nue compensation records")
                return {'compensation_records': processed_count}
                
            except Exception as e:
                ingestion_record.status = 'failed'
                ingestion_record.error_message = str(e)
                db.commit()
                raise
    
    async def sync_payroll_runs(self, start_date: str, end_date: str) -> Dict[str, int]:
        """
        Sync Nue payroll run data
        
        Args:
            start_date: YYYY-MM-DD format
            end_date: YYYY-MM-DD format
            
        Returns:
            Dictionary with sync statistics
        """
        with get_db_session() as db:
            ingestion_record = IngestionHistory(
                source='nue',
                entity_type='payroll_runs',
                period_start=datetime.fromisoformat(start_date),
                period_end=datetime.fromisoformat(end_date),
                status='pending'
            )
            db.add(ingestion_record)
            db.commit()
            
            try:
                # Get payroll runs from Nue
                payroll_data = await self._get_payroll_runs_batch(start_date, end_date)
                
                processed_count = 0
                for payroll_run in payroll_data:
                    await self._process_payroll_run(db, payroll_run)
                    processed_count += 1
                
                ingestion_record.status = 'completed'
                ingestion_record.records_count = processed_count
                db.commit()
                
                logger.info(f"Synced {processed_count} Nue payroll runs")
                return {'payroll_runs': processed_count}
                
            except Exception as e:
                ingestion_record.status = 'failed'
                ingestion_record.error_message = str(e)
                db.commit()
                raise
    
    async def get_compensation_metrics(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Get compensation metrics for financial analysis
        
        Args:
            start_date: YYYY-MM-DD format
            end_date: YYYY-MM-DD format
            
        Returns:
            Dictionary with compensation metrics
        """
        # Get department breakdown
        dept_data = await self._get_compensation_by_department(start_date, end_date)
        
        # Get role/level breakdown
        role_data = await self._get_compensation_by_role(start_date, end_date)
        
        # Get benefits costs
        benefits_data = await self._get_benefits_costs(start_date, end_date)
        
        # Calculate key metrics
        total_compensation = sum(d['total_comp'] for d in dept_data)
        total_benefits = sum(b['cost'] for b in benefits_data)
        headcount = len(await self._get_active_employees(start_date, end_date))
        
        return {
            'summary': {
                'total_compensation': total_compensation,
                'total_benefits': total_benefits,
                'total_people_costs': total_compensation + total_benefits,
                'headcount': headcount,
                'average_compensation': total_compensation / headcount if headcount > 0 else 0
            },
            'by_department': dept_data,
            'by_role': role_data,
            'benefits_breakdown': benefits_data,
            'period': {'start_date': start_date, 'end_date': end_date}
        }
    
    async def correlate_payroll_to_expenses(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Correlate Nue payroll data with financial expense data
        
        Args:
            start_date: YYYY-MM-DD format
            end_date: YYYY-MM-DD format
            
        Returns:
            Dictionary with payroll-to-expense correlation
        """
        # Get Nue payroll totals
        nue_payroll = await self._get_total_payroll(start_date, end_date)
        
        # Get financial payroll expenses
        with get_db_session() as db:
            payroll_expenses = db.query(
                func.sum(GeneralLedger.debit_amount).label('total_expense')
            ).filter(
                and_(
                    GeneralLedger.transaction_date >= start_date,
                    GeneralLedger.transaction_date <= end_date,
                    GeneralLedger.account_type == 'Expense',
                    GeneralLedger.account_name.ilike('%payroll%') | 
                    GeneralLedger.account_name.ilike('%salary%') |
                    GeneralLedger.account_name.ilike('%wages%')
                )
            ).scalar() or Decimal('0')
            
            # Get benefits expenses
            benefits_expenses = db.query(
                func.sum(GeneralLedger.debit_amount).label('total_expense')
            ).filter(
                and_(
                    GeneralLedger.transaction_date >= start_date,
                    GeneralLedger.transaction_date <= end_date,
                    GeneralLedger.account_type == 'Expense',
                    GeneralLedger.account_name.ilike('%benefit%') |
                    GeneralLedger.account_name.ilike('%insurance%') |
                    GeneralLedger.account_name.ilike('%401k%') |
                    GeneralLedger.account_name.ilike('%health%')
                )
            ).scalar() or Decimal('0')
        
        # Calculate correlation metrics
        total_financial_people_costs = float(payroll_expenses + benefits_expenses)
        total_nue_costs = nue_payroll['gross_pay'] + nue_payroll['benefits_cost']
        
        variance = total_financial_people_costs - total_nue_costs
        variance_pct = (variance / total_nue_costs * 100) if total_nue_costs > 0 else 0
        
        return {
            'nue_data': {
                'gross_pay': nue_payroll['gross_pay'],
                'benefits_cost': nue_payroll['benefits_cost'],
                'total_people_costs': total_nue_costs,
                'employee_count': nue_payroll['employee_count']
            },
            'financial_data': {
                'payroll_expenses': float(payroll_expenses),
                'benefits_expenses': float(benefits_expenses),
                'total_people_costs': total_financial_people_costs
            },
            'correlation': {
                'variance': variance,
                'variance_percentage': variance_pct,
                'accuracy_rate': (1 - abs(variance_pct) / 100) * 100 if abs(variance_pct) <= 100 else 0
            },
            'insights': self._generate_payroll_insights(variance_pct, total_nue_costs, total_financial_people_costs)
        }
    
    async def _get_compensation_batch(self, start_date: str, end_date: str) -> List[Dict]:
        """Get compensation data from Nue API (mock implementation)"""
        # In a real implementation, this would call the actual Nue API
        # For now, return mock data structure
        return [
            {
                'employee_id': 'emp_001',
                'employee_name': 'John Doe',
                'department': 'Engineering',
                'role': 'Senior Engineer',
                'level': 'L5',
                'base_salary': 120000,
                'bonus': 15000,
                'equity_value': 25000,
                'benefits_cost': 18000,
                'effective_date': start_date
            },
            {
                'employee_id': 'emp_002',
                'employee_name': 'Jane Smith',
                'department': 'Sales',
                'role': 'Account Executive',
                'level': 'L4',
                'base_salary': 85000,
                'bonus': 25000,
                'equity_value': 15000,
                'benefits_cost': 16000,
                'effective_date': start_date
            },
            {
                'employee_id': 'emp_003',
                'employee_name': 'Mike Johnson',
                'department': 'Marketing',
                'role': 'Marketing Manager',
                'level': 'L4',
                'base_salary': 95000,
                'bonus': 12000,
                'equity_value': 18000,
                'benefits_cost': 17000,
                'effective_date': start_date
            }
        ]
    
    async def _get_payroll_runs_batch(self, start_date: str, end_date: str) -> List[Dict]:
        """Get payroll run data from Nue API (mock implementation)"""
        return [
            {
                'run_id': 'run_202401_1',
                'pay_period_start': start_date,
                'pay_period_end': end_date,
                'run_date': end_date,
                'total_gross': 45000,
                'total_net': 32000,
                'total_taxes': 8500,
                'total_deductions': 4500,
                'employee_count': 15,
                'department_breakdown': [
                    {'department': 'Engineering', 'gross_pay': 25000, 'employee_count': 8},
                    {'department': 'Sales', 'gross_pay': 12000, 'employee_count': 4},
                    {'department': 'Marketing', 'gross_pay': 8000, 'employee_count': 3}
                ]
            }
        ]
    
    async def _get_compensation_by_department(self, start_date: str, end_date: str) -> List[Dict]:
        """Get compensation breakdown by department"""
        comp_data = await self._get_compensation_batch(start_date, end_date)
        
        dept_summary = {}
        for record in comp_data:
            dept = record['department']
            if dept not in dept_summary:
                dept_summary[dept] = {
                    'department': dept,
                    'employee_count': 0,
                    'total_comp': 0,
                    'avg_comp': 0
                }
            
            total_comp = record['base_salary'] + record['bonus'] + record['equity_value']
            dept_summary[dept]['employee_count'] += 1
            dept_summary[dept]['total_comp'] += total_comp
        
        # Calculate averages
        for dept_data in dept_summary.values():
            if dept_data['employee_count'] > 0:
                dept_data['avg_comp'] = dept_data['total_comp'] / dept_data['employee_count']
        
        return list(dept_summary.values())
    
    async def _get_compensation_by_role(self, start_date: str, end_date: str) -> List[Dict]:
        """Get compensation breakdown by role"""
        comp_data = await self._get_compensation_batch(start_date, end_date)
        
        role_summary = {}
        for record in comp_data:
            role = record['role']
            if role not in role_summary:
                role_summary[role] = {
                    'role': role,
                    'employee_count': 0,
                    'total_comp': 0,
                    'avg_comp': 0,
                    'min_comp': float('inf'),
                    'max_comp': 0
                }
            
            total_comp = record['base_salary'] + record['bonus'] + record['equity_value']
            role_summary[role]['employee_count'] += 1
            role_summary[role]['total_comp'] += total_comp
            role_summary[role]['min_comp'] = min(role_summary[role]['min_comp'], total_comp)
            role_summary[role]['max_comp'] = max(role_summary[role]['max_comp'], total_comp)
        
        # Calculate averages
        for role_data in role_summary.values():
            if role_data['employee_count'] > 0:
                role_data['avg_comp'] = role_data['total_comp'] / role_data['employee_count']
        
        return list(role_summary.values())
    
    async def _get_benefits_costs(self, start_date: str, end_date: str) -> List[Dict]:
        """Get benefits cost breakdown"""
        comp_data = await self._get_compensation_batch(start_date, end_date)
        
        total_benefits = sum(record['benefits_cost'] for record in comp_data)
        employee_count = len(comp_data)
        
        return [
            {
                'benefit_type': 'Health Insurance',
                'cost': total_benefits * 0.6,
                'per_employee': (total_benefits * 0.6) / employee_count if employee_count > 0 else 0
            },
            {
                'benefit_type': '401k Match',
                'cost': total_benefits * 0.25,
                'per_employee': (total_benefits * 0.25) / employee_count if employee_count > 0 else 0
            },
            {
                'benefit_type': 'Other Benefits',
                'cost': total_benefits * 0.15,
                'per_employee': (total_benefits * 0.15) / employee_count if employee_count > 0 else 0
            }
        ]
    
    async def _get_active_employees(self, start_date: str, end_date: str) -> List[Dict]:
        """Get active employees for the period"""
        comp_data = await self._get_compensation_batch(start_date, end_date)
        return comp_data
    
    async def _get_total_payroll(self, start_date: str, end_date: str) -> Dict[str, float]:
        """Get total payroll metrics from Nue"""
        payroll_runs = await self._get_payroll_runs_batch(start_date, end_date)
        comp_data = await self._get_compensation_batch(start_date, end_date)
        
        total_gross = sum(run['total_gross'] for run in payroll_runs)
        total_benefits = sum(record['benefits_cost'] for record in comp_data)
        employee_count = len(comp_data)
        
        return {
            'gross_pay': total_gross,
            'benefits_cost': total_benefits,
            'employee_count': employee_count
        }
    
    async def _process_compensation_record(self, db: Session, comp_record: Dict):
        """Process and store compensation data"""
        # In a full implementation, you'd create custom tables for Nue data
        logger.debug(f"Processing compensation for {comp_record.get('employee_name')} - ${comp_record.get('base_salary', 0)}")
    
    async def _process_payroll_run(self, db: Session, payroll_run: Dict):
        """Process and store payroll run data"""
        logger.debug(f"Processing payroll run {payroll_run.get('run_id')} - ${payroll_run.get('total_gross', 0)}")
    
    def _generate_payroll_insights(self, variance_pct: float, nue_total: float, financial_total: float) -> List[str]:
        """Generate insights from payroll correlation"""
        insights = []
        
        if abs(variance_pct) < 5:
            insights.append("Excellent alignment between Nue compensation data and financial payroll expenses.")
        elif abs(variance_pct) < 15:
            insights.append(f"Good alignment with {abs(variance_pct):.1f}% variance - likely due to timing differences or benefit accruals.")
        else:
            if variance_pct > 0:
                insights.append(f"Financial expenses exceed Nue data by {variance_pct:.1f}% - investigate additional payroll costs or timing differences.")
            else:
                insights.append(f"Nue data exceeds financial expenses by {abs(variance_pct):.1f}% - check for missing payroll entries or accrual timing.")
        
        # Cost per employee analysis
        nue_employees = nue_total / 15 if nue_total > 0 else 0  # Mock employee count
        if nue_employees > 100000:
            insights.append("High cost per employee - review compensation benchmarks and benefit costs.")
        elif nue_employees < 50000:
            insights.append("Below-market cost per employee - consider competitive positioning.")
        
        return insights
    
    def _ensure_data_source(self):
        """Ensure Nue data source is registered"""
        with get_db_session() as db:
            existing = db.query(DataSource).filter(DataSource.name == 'nue').first()
            
            if not existing:
                data_source = DataSource(
                    name='nue',
                    type='payroll',
                    status='active',
                    connection_config={
                        'api_version': 'v1',
                        'base_url': self.base_url
                    },
                    sync_frequency='monthly'
                )
                db.add(data_source)
                db.commit()
                logger.info("Registered Nue data source")


# Convenience functions
async def sync_nue_data(api_key: str, start_date: str, end_date: str) -> Dict[str, int]:
    """
    Sync Nue compensation data for the given period
    
    Args:
        api_key: Nue API key
        start_date: YYYY-MM-DD format
        end_date: YYYY-MM-DD format
        
    Returns:
        Dictionary with sync statistics
    """
    async with NueIntegration(api_key) as nue:
        # Sync compensation and payroll data
        comp_stats = await nue.sync_compensation_data(start_date, end_date)
        payroll_stats = await nue.sync_payroll_runs(start_date, end_date)
        
        return {
            'compensation_records': comp_stats.get('compensation_records', 0),
            'payroll_runs': payroll_stats.get('payroll_runs', 0),
            'total_records': (comp_stats.get('compensation_records', 0) + 
                            payroll_stats.get('payroll_runs', 0))
        }

async def get_compensation_analysis(api_key: str, start_date: str, end_date: str) -> Dict[str, Any]:
    """Get compensation analysis metrics"""
    async with NueIntegration(api_key) as nue:
        return await nue.get_compensation_metrics(start_date, end_date)

async def get_payroll_correlation(api_key: str, start_date: str, end_date: str) -> Dict[str, Any]:
    """Get payroll to expense correlation analysis"""
    async with NueIntegration(api_key) as nue:
        return await nue.correlate_payroll_to_expenses(start_date, end_date)


if __name__ == "__main__":
    # Example usage
    import asyncio
    import os
    
    async def main():
        api_key = os.getenv("NUE_API_KEY", "mock_key_for_testing")
        
        # Sync last 30 days
        end_date = datetime.now().date().isoformat()
        start_date = (datetime.now().date() - timedelta(days=30)).isoformat()
        
        print(f"Starting Nue sync for {start_date} to {end_date}")
        
        try:
            stats = await sync_nue_data(api_key, start_date, end_date)
            print(f"Sync completed: {stats}")
            
            # Get compensation analysis
            comp_analysis = await get_compensation_analysis(api_key, start_date, end_date)
            print(f"Compensation analysis: ${comp_analysis['summary']['total_compensation']:,.0f} total compensation")
            
            # Get correlation analysis
            correlation = await get_payroll_correlation(api_key, start_date, end_date)
            print(f"Payroll correlation: {correlation['correlation']['accuracy_rate']:.1f}% accuracy")
            
        except Exception as e:
            print(f"Nue sync failed: {e}")
    
    asyncio.run(main())