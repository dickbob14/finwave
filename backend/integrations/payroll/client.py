"""
Payroll API Client for Gusto and ADP
Provides unified interface for fetching employee and compensation data
"""

import json
import logging
import time
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Union
from functools import wraps
import os
from abc import ABC, abstractmethod

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class PayrollAPIError(Exception):
    """Base exception for Payroll API errors"""
    pass

class RateLimitError(PayrollAPIError):
    """Raised when rate limit is exceeded"""
    pass

class AuthenticationError(PayrollAPIError):
    """Raised when authentication fails"""
    pass

def retry_with_backoff(max_retries=3, backoff_factor=1.0):
    """Decorator for retry with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except RateLimitError as e:
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(f"Rate limit hit, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                    time.sleep(wait_time)
                    last_exception = e
                except AuthenticationError as e:
                    if hasattr(args[0], 'refresh_auth'):
                        logger.info("Authentication failed, refreshing...")
                        args[0].refresh_auth()
                    else:
                        raise
                except Exception as e:
                    logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                    last_exception = e
                    if attempt == max_retries - 1:
                        raise
            raise last_exception
        return wrapper
    return decorator

class PayrollClient(ABC):
    """Abstract base class for payroll clients"""
    
    @abstractmethod
    def fetch_employees(self, as_of_date: Optional[str] = None) -> pd.DataFrame:
        """Fetch employee roster"""
        pass
    
    @abstractmethod
    def fetch_payroll_runs(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch payroll run data"""
        pass
    
    @abstractmethod
    def fetch_departments(self) -> pd.DataFrame:
        """Fetch department list"""
        pass
    
    @abstractmethod
    def get_headcount_summary(self, as_of_date: Optional[str] = None) -> Dict[str, Any]:
        """Get headcount metrics summary"""
        pass

class GustoClient(PayrollClient):
    """Gusto API client implementation"""
    
    def __init__(self, api_token: str = None, company_id: str = None):
        self.api_token = api_token or os.getenv('GUSTO_API_TOKEN')
        self.company_id = company_id or os.getenv('GUSTO_COMPANY_ID')
        self.base_url = 'https://api.gusto.com/v1'
        
        # Session with retry
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        return {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
    
    @retry_with_backoff(max_retries=3)
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make API request with error handling"""
        url = f"{self.base_url}/{endpoint}"
        
        response = self.session.get(
            url,
            headers=self._get_headers(),
            params=params
        )
        
        if response.status_code == 429:
            retry_after = int(response.headers.get('X-Rate-Limit-Retry-After', 60))
            raise RateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds")
        
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed")
        
        if response.status_code != 200:
            raise PayrollAPIError(f"API request failed: {response.status_code} - {response.text}")
        
        return response.json()
    
    def fetch_employees(self, as_of_date: Optional[str] = None) -> pd.DataFrame:
        """Fetch employee roster from Gusto"""
        
        endpoint = f"companies/{self.company_id}/employees"
        params = {}
        if as_of_date:
            params['terminated'] = 'true'  # Include terminated employees
        
        response = self._make_request(endpoint, params)
        
        employees = []
        for emp in response:
            # Extract relevant fields
            employee = {
                'employee_id': emp['uuid'],
                'first_name': emp['first_name'],
                'last_name': emp['last_name'],
                'email': emp['email'],
                'department': emp.get('department'),
                'job_title': emp.get('job_title'),
                'employment_type': 'FTE' if emp.get('employment_type') == 'full_time' else 'Contractor',
                'hire_date': emp.get('hire_date'),
                'termination_date': emp.get('termination_date'),
                'status': 'Active' if not emp.get('termination_date') else 'Terminated',
                'location': emp.get('work_location', {}).get('city')
            }
            
            # Filter by date if specified
            if as_of_date:
                as_of = pd.to_datetime(as_of_date)
                hire = pd.to_datetime(employee['hire_date']) if employee['hire_date'] else None
                term = pd.to_datetime(employee['termination_date']) if employee['termination_date'] else None
                
                # Include if hired before as_of and not terminated or terminated after as_of
                if hire and hire <= as_of:
                    if not term or term > as_of:
                        employee['status'] = 'Active'
                        employees.append(employee)
            else:
                employees.append(employee)
        
        return pd.DataFrame(employees)
    
    def fetch_payroll_runs(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch payroll runs from Gusto"""
        
        endpoint = f"companies/{self.company_id}/payrolls"
        params = {
            'start_date': start_date,
            'end_date': end_date,
            'include': 'employee_compensations'
        }
        
        response = self._make_request(endpoint, params)
        
        payroll_data = []
        for payroll in response:
            pay_date = payroll['pay_date']
            
            # Extract compensation by employee
            for comp in payroll.get('employee_compensations', []):
                data = {
                    'pay_date': pay_date,
                    'employee_id': comp['employee_uuid'],
                    'employee_name': f"{comp['first_name']} {comp['last_name']}",
                    'gross_pay': float(comp['gross_pay']),
                    'net_pay': float(comp['net_pay']),
                    'employer_taxes': float(comp.get('employer_taxes', 0)),
                    'benefits_employer_paid': float(comp.get('benefits_employer_paid', 0)),
                    'total_employer_cost': float(comp['gross_pay']) + float(comp.get('employer_taxes', 0)) + float(comp.get('benefits_employer_paid', 0))
                }
                payroll_data.append(data)
        
        return pd.DataFrame(payroll_data)
    
    def fetch_departments(self) -> pd.DataFrame:
        """Fetch departments from Gusto"""
        
        endpoint = f"companies/{self.company_id}/departments"
        response = self._make_request(endpoint)
        
        departments = []
        for dept in response:
            departments.append({
                'department_id': dept['uuid'],
                'department_name': dept['name'],
                'employee_count': dept.get('employee_count', 0)
            })
        
        return pd.DataFrame(departments)
    
    def get_headcount_summary(self, as_of_date: Optional[str] = None) -> Dict[str, Any]:
        """Get headcount metrics summary"""
        
        employees_df = self.fetch_employees(as_of_date)
        
        if employees_df.empty:
            return {
                'total_headcount': 0,
                'fte_count': 0,
                'contractor_count': 0,
                'by_department': {},
                'new_hires_mtd': 0,
                'terminations_mtd': 0
            }
        
        # Active employees only
        active_df = employees_df[employees_df['status'] == 'Active']
        
        summary = {
            'total_headcount': len(active_df),
            'fte_count': len(active_df[active_df['employment_type'] == 'FTE']),
            'contractor_count': len(active_df[active_df['employment_type'] == 'Contractor']),
            'by_department': active_df.groupby('department').size().to_dict() if 'department' in active_df.columns else {}
        }
        
        # Calculate monthly changes
        if as_of_date:
            as_of = pd.to_datetime(as_of_date)
            month_start = as_of.replace(day=1)
            
            # New hires this month
            employees_df['hire_date_parsed'] = pd.to_datetime(employees_df['hire_date'])
            new_hires = employees_df[
                (employees_df['hire_date_parsed'] >= month_start) & 
                (employees_df['hire_date_parsed'] <= as_of)
            ]
            summary['new_hires_mtd'] = len(new_hires)
            
            # Terminations this month
            employees_df['term_date_parsed'] = pd.to_datetime(employees_df['termination_date'])
            terminations = employees_df[
                (employees_df['term_date_parsed'] >= month_start) & 
                (employees_df['term_date_parsed'] <= as_of)
            ]
            summary['terminations_mtd'] = len(terminations)
        else:
            summary['new_hires_mtd'] = 0
            summary['terminations_mtd'] = 0
        
        return summary

class ADPClient(PayrollClient):
    """ADP API client implementation"""
    
    def __init__(self, client_id: str = None, client_secret: str = None, 
                 cert_path: str = None, key_path: str = None):
        self.client_id = client_id or os.getenv('ADP_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('ADP_CLIENT_SECRET')
        self.cert_path = cert_path or os.getenv('ADP_CERT_PATH')
        self.key_path = key_path or os.getenv('ADP_KEY_PATH')
        self.base_url = 'https://api.adp.com'
        self.access_token = None
        
        # Session setup
        self.session = requests.Session()
        if self.cert_path and self.key_path:
            self.session.cert = (self.cert_path, self.key_path)
    
    def refresh_auth(self):
        """Get ADP OAuth token"""
        auth_url = f"{self.base_url}/auth/oauth/v2/token"
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        response = requests.post(auth_url, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access_token']
            logger.info("Successfully refreshed ADP token")
        else:
            raise AuthenticationError(f"Token refresh failed: {response.text}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        if not self.access_token:
            self.refresh_auth()
        
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def fetch_employees(self, as_of_date: Optional[str] = None) -> pd.DataFrame:
        """Fetch employees from ADP"""
        # Implementation would follow ADP's Worker API
        # This is a stub showing the expected structure
        
        logger.warning("ADP client not fully implemented - returning sample data")
        
        return pd.DataFrame([
            {
                'employee_id': 'ADP001',
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@company.com',
                'department': 'Engineering',
                'job_title': 'Software Engineer',
                'employment_type': 'FTE',
                'hire_date': '2023-01-15',
                'termination_date': None,
                'status': 'Active',
                'location': 'San Francisco'
            }
        ])
    
    def fetch_payroll_runs(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch payroll data from ADP"""
        logger.warning("ADP payroll fetch not implemented - returning empty DataFrame")
        return pd.DataFrame()
    
    def fetch_departments(self) -> pd.DataFrame:
        """Fetch departments from ADP"""
        logger.warning("ADP departments fetch not implemented - returning empty DataFrame")
        return pd.DataFrame()
    
    def get_headcount_summary(self, as_of_date: Optional[str] = None) -> Dict[str, Any]:
        """Get headcount summary from ADP"""
        return {
            'total_headcount': 0,
            'fte_count': 0,
            'contractor_count': 0,
            'by_department': {},
            'new_hires_mtd': 0,
            'terminations_mtd': 0
        }

# Factory function to create appropriate client
def create_payroll_client(payroll_type: str) -> PayrollClient:
    """Create a payroll client based on type"""
    
    if payroll_type.lower() == 'gusto':
        return GustoClient()
    elif payroll_type.lower() == 'adp':
        return ADPClient()
    else:
        raise ValueError(f"Unsupported payroll type: {payroll_type}")

# Convenience function for testing
def test_payroll_connection(payroll_type: str) -> bool:
    """Test payroll connection"""
    try:
        client = create_payroll_client(payroll_type)
        
        # Try to fetch current headcount
        summary = client.get_headcount_summary()
        
        logger.info(f"Connected to {payroll_type}: {summary.get('total_headcount', 0)} employees")
        return True
        
    except Exception as e:
        logger.error(f"{payroll_type} connection failed: {e}")
        return False