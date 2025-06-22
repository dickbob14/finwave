"""
QuickBooks API Client with OAuth refresh and rate limit handling
Provides a clean interface for fetching financial data
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from functools import wraps
import os

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class QuickBooksAPIError(Exception):
    """Custom exception for QuickBooks API errors"""
    pass

class RateLimitError(QuickBooksAPIError):
    """Raised when rate limit is exceeded"""
    pass

class TokenExpiredError(QuickBooksAPIError):
    """Raised when OAuth token needs refresh"""
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
                except TokenExpiredError as e:
                    # Let token refresh happen
                    logger.info("Token expired, refreshing...")
                    if hasattr(args[0], 'refresh_token'):
                        args[0].refresh_token()
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

class QuickBooksClient:
    """
    Reusable QuickBooks API client with OAuth management
    """
    
    def __init__(self, client_id: str = None, client_secret: str = None, 
                 company_id: str = None, token_store_path: str = None):
        self.client_id = client_id or os.getenv('QB_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('QB_CLIENT_SECRET')
        self.company_id = company_id or os.getenv('QB_COMPANY_ID')
        self.token_store_path = token_store_path or 'qb_tokens.json'
        
        # API configuration
        environment = os.getenv('QB_ENVIRONMENT', 'sandbox')
        if environment == 'production':
            self.base_url = 'https://quickbooks.api.intuit.com/v3/company'
        else:
            self.base_url = 'https://sandbox-quickbooks.api.intuit.com/v3/company'
        self.auth_url = 'https://appcenter.intuit.com/connect/oauth2'
        
        # Session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        # Load tokens
        self.access_token = None
        self.refresh_token_value = None
        self.token_expiry = None
        self._load_tokens()
    
    def _load_tokens(self):
        """Load tokens from storage"""
        if os.path.exists(self.token_store_path):
            try:
                with open(self.token_store_path, 'r') as f:
                    tokens = json.load(f)
                    self.access_token = tokens.get('access_token')
                    self.refresh_token_value = tokens.get('refresh_token')
                    self.token_expiry = datetime.fromisoformat(tokens.get('expiry', '1970-01-01'))
                    logger.info("Loaded existing OAuth tokens")
            except Exception as e:
                logger.error(f"Error loading tokens: {e}")
    
    def _save_tokens(self):
        """Save tokens to storage"""
        tokens = {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token_value,
            'expiry': self.token_expiry.isoformat() if self.token_expiry else None,
            'company_id': self.company_id
        }
        with open(self.token_store_path, 'w') as f:
            json.dump(tokens, f, indent=2)
        logger.info("Saved OAuth tokens")
    
    def is_token_valid(self) -> bool:
        """Check if current token is valid"""
        if not self.access_token or not self.token_expiry:
            return False
        return datetime.now() < self.token_expiry - timedelta(minutes=5)  # 5 min buffer
    
    def refresh_token(self):
        """Refresh the OAuth token"""
        if not self.refresh_token_value:
            raise QuickBooksAPIError("No refresh token available")
        
        token_url = f"{self.auth_url}/tokens/bearer"
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token_value
        }
        
        response = requests.post(
            token_url,
            auth=(self.client_id, self.client_secret),
            data=data,
            headers={'Accept': 'application/json'}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.refresh_token_value = token_data['refresh_token']
            # Token expires in 3600 seconds (1 hour)
            self.token_expiry = datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600))
            self._save_tokens()
            logger.info("Successfully refreshed OAuth token")
        else:
            raise QuickBooksAPIError(f"Token refresh failed: {response.text}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with current token"""
        if not self.is_token_valid():
            self.refresh_token()
        
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    @retry_with_backoff(max_retries=3)
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make API request with error handling"""
        url = f"{self.base_url}/{self.company_id}/{endpoint}"
        
        response = self.session.get(
            url,
            headers=self._get_headers(),
            params=params
        )
        
        # Handle rate limiting
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            raise RateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds")
        
        # Handle token expiry
        if response.status_code == 401:
            raise TokenExpiredError("Access token expired")
        
        # Handle other errors
        if response.status_code != 200:
            raise QuickBooksAPIError(f"API request failed: {response.status_code} - {response.text}")
        
        return response.json()
    
    def fetch_gl(self, start_date: str, end_date: str, include_prior_year: bool = False) -> pd.DataFrame:
        """
        Fetch general ledger entries for date range
        Returns a pandas DataFrame ready for template population
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            include_prior_year: If True, also fetches prior year data
        """
        logger.info(f"Fetching GL entries from {start_date} to {end_date}")
        
        # QuickBooks uses different endpoints for different transaction types
        # We'll aggregate data from multiple sources
        
        all_transactions = []
        
        # Fetch invoices (revenue)
        invoices = self._fetch_invoices(start_date, end_date)
        all_transactions.extend(self._transform_invoices_to_gl(invoices))
        
        # Fetch bills (expenses)
        bills = self._fetch_bills(start_date, end_date)
        all_transactions.extend(self._transform_bills_to_gl(bills))
        
        # Fetch journal entries
        journal_entries = self._fetch_journal_entries(start_date, end_date)
        all_transactions.extend(self._transform_journal_entries_to_gl(journal_entries))
        
        # Convert to DataFrame
        df = pd.DataFrame(all_transactions)
        
        if df.empty:
            logger.warning("No GL entries found for date range")
            return pd.DataFrame(columns=['Date', 'Account', 'Account_Name', 'Debit', 'Credit', 
                                       'Description', 'Entity', 'Department', 'Class'])
        
        # Ensure proper data types
        df['Date'] = pd.to_datetime(df['Date'])
        df['Debit'] = pd.to_numeric(df['Debit'], errors='coerce').fillna(0)
        df['Credit'] = pd.to_numeric(df['Credit'], errors='coerce').fillna(0)
        
        # Sort by date
        df = df.sort_values('Date')
        
        logger.info(f"Fetched {len(df)} GL entries")
        
        # Fetch prior year data if requested
        if include_prior_year:
            from datetime import datetime, timedelta
            
            # Calculate prior year dates
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            
            py_start = (start_dt - timedelta(days=365)).strftime('%Y-%m-%d')
            py_end = (end_dt - timedelta(days=365)).strftime('%Y-%m-%d')
            
            logger.info(f"Fetching prior year GL entries from {py_start} to {py_end}")
            
            # Recursive call for prior year
            py_df = self.fetch_gl(py_start, py_end, include_prior_year=False)
            
            # Add year indicator
            df['Year'] = 'Current'
            py_df['Year'] = 'Prior'
            
            # Combine dataframes
            df = pd.concat([df, py_df], ignore_index=True)
            logger.info(f"Total with prior year: {len(df)} GL entries")
        
        return df
    
    def _fetch_invoices(self, start_date: str, end_date: str) -> List[Dict]:
        """Fetch all invoices in date range"""
        query = f"SELECT * FROM Invoice WHERE TxnDate >= '{start_date}' AND TxnDate <= '{end_date}'"
        response = self._make_request('query', {'query': query})
        return response.get('QueryResponse', {}).get('Invoice', [])
    
    def _fetch_bills(self, start_date: str, end_date: str) -> List[Dict]:
        """Fetch all bills in date range"""
        query = f"SELECT * FROM Bill WHERE TxnDate >= '{start_date}' AND TxnDate <= '{end_date}'"
        response = self._make_request('query', {'query': query})
        return response.get('QueryResponse', {}).get('Bill', [])
    
    def _fetch_journal_entries(self, start_date: str, end_date: str) -> List[Dict]:
        """Fetch all journal entries in date range"""
        query = f"SELECT * FROM JournalEntry WHERE TxnDate >= '{start_date}' AND TxnDate <= '{end_date}'"
        response = self._make_request('query', {'query': query})
        return response.get('QueryResponse', {}).get('JournalEntry', [])
    
    def _transform_invoices_to_gl(self, invoices: List[Dict]) -> List[Dict]:
        """Transform invoices to GL entries"""
        gl_entries = []
        
        for invoice in invoices:
            date = invoice['TxnDate']
            total = float(invoice.get('TotalAmt', 0))
            customer_name = invoice.get('CustomerRef', {}).get('name', 'Unknown')
            
            # Debit AR
            gl_entries.append({
                'Date': date,
                'Account': '1200',  # AR account
                'Account_Name': 'Accounts Receivable',
                'Debit': total,
                'Credit': 0,
                'Description': f"Invoice #{invoice.get('DocNumber', 'N/A')} - {customer_name}",
                'Entity': 'Main',
                'Department': 'Sales',
                'Class': invoice.get('ClassRef', {}).get('name', '')
            })
            
            # Credit Revenue (by line item)
            for line in invoice.get('Line', []):
                if line.get('DetailType') == 'SalesItemLineDetail':
                    amount = float(line.get('Amount', 0))
                    item_name = line.get('SalesItemLineDetail', {}).get('ItemRef', {}).get('name', 'Sales')
                    
                    gl_entries.append({
                        'Date': date,
                        'Account': '4000',  # Revenue account
                        'Account_Name': f'Revenue - {item_name}',
                        'Debit': 0,
                        'Credit': amount,
                        'Description': f"Invoice #{invoice.get('DocNumber', 'N/A')} - {item_name}",
                        'Entity': 'Main',
                        'Department': 'Sales',
                        'Class': invoice.get('ClassRef', {}).get('name', '')
                    })
        
        return gl_entries
    
    def _transform_bills_to_gl(self, bills: List[Dict]) -> List[Dict]:
        """Transform bills to GL entries"""
        gl_entries = []
        
        for bill in bills:
            date = bill['TxnDate']
            total = float(bill.get('TotalAmt', 0))
            vendor_name = bill.get('VendorRef', {}).get('name', 'Unknown')
            
            # Credit AP
            gl_entries.append({
                'Date': date,
                'Account': '2000',  # AP account
                'Account_Name': 'Accounts Payable',
                'Debit': 0,
                'Credit': total,
                'Description': f"Bill - {vendor_name}",
                'Entity': 'Main',
                'Department': 'Operations',
                'Class': bill.get('ClassRef', {}).get('name', '')
            })
            
            # Debit Expense (by line item)
            for line in bill.get('Line', []):
                if line.get('DetailType') == 'AccountBasedExpenseLineDetail':
                    amount = float(line.get('Amount', 0))
                    account_ref = line.get('AccountBasedExpenseLineDetail', {}).get('AccountRef', {})
                    
                    gl_entries.append({
                        'Date': date,
                        'Account': account_ref.get('value', '5000'),
                        'Account_Name': account_ref.get('name', 'Operating Expense'),
                        'Debit': amount,
                        'Credit': 0,
                        'Description': line.get('Description', f"Bill - {vendor_name}"),
                        'Entity': 'Main',
                        'Department': 'Operations',
                        'Class': bill.get('ClassRef', {}).get('name', '')
                    })
        
        return gl_entries
    
    def _transform_journal_entries_to_gl(self, journal_entries: List[Dict]) -> List[Dict]:
        """Transform journal entries to GL entries"""
        gl_entries = []
        
        for je in journal_entries:
            date = je['TxnDate']
            
            for line in je.get('Line', []):
                if line.get('DetailType') == 'JournalEntryLineDetail':
                    detail = line.get('JournalEntryLineDetail', {})
                    account_ref = detail.get('AccountRef', {})
                    posting_type = detail.get('PostingType', 'Debit')
                    amount = float(line.get('Amount', 0))
                    
                    gl_entries.append({
                        'Date': date,
                        'Account': account_ref.get('value', ''),
                        'Account_Name': account_ref.get('name', ''),
                        'Debit': amount if posting_type == 'Debit' else 0,
                        'Credit': amount if posting_type == 'Credit' else 0,
                        'Description': line.get('Description', f"JE #{je.get('DocNumber', 'N/A')}"),
                        'Entity': detail.get('Entity', {}).get('name', 'Main'),
                        'Department': detail.get('DepartmentRef', {}).get('name', ''),
                        'Class': detail.get('ClassRef', {}).get('name', '')
                    })
        
        return gl_entries
    
    def fetch_trial_balance(self, as_of_date: str) -> pd.DataFrame:
        """Fetch trial balance as of specific date"""
        report_url = f"{self.base_url}/{self.company_id}/reports/TrialBalance"
        
        params = {
            'date': as_of_date,
            'summarize_column_by': 'Total'
        }
        
        response = self._make_request('reports/TrialBalance', params)
        
        # Parse the report structure
        # QuickBooks reports have a specific nested structure
        # This is simplified - actual implementation would need proper parsing
        
        rows = []
        for row in response.get('Rows', []):
            if row.get('type') == 'Data':
                cols = row.get('ColData', [])
                if len(cols) >= 3:
                    account = cols[0].get('value', '')
                    debit = float(cols[1].get('value', '0') or 0)
                    credit = float(cols[2].get('value', '0') or 0)
                    
                    rows.append({
                        'Account': account,
                        'Debit': debit,
                        'Credit': credit,
                        'Balance': debit - credit
                    })
        
        return pd.DataFrame(rows)
    
    def fetch_company_info(self) -> Dict[str, Any]:
        """Fetch company information"""
        response = self._make_request('companyinfo/1')
        return response.get('CompanyInfo', {})


# Convenience functions for testing
def create_client() -> QuickBooksClient:
    """Create a QuickBooks client with environment configuration"""
    return QuickBooksClient()

def test_connection() -> bool:
    """Test QuickBooks connection"""
    try:
        client = create_client()
        info = client.fetch_company_info()
        logger.info(f"Connected to QuickBooks: {info.get('CompanyName', 'Unknown')}")
        return True
    except Exception as e:
        logger.error(f"QuickBooks connection failed: {e}")
        return False