"""
CRM API Client for Salesforce and HubSpot
Provides unified interface for fetching sales and marketing data
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from functools import wraps
import os
from abc import ABC, abstractmethod

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class CRMAPIError(Exception):
    """Base exception for CRM API errors"""
    pass

class RateLimitError(CRMAPIError):
    """Raised when rate limit is exceeded"""
    pass

class AuthenticationError(CRMAPIError):
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
                    # Try to refresh token
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

class CRMClient(ABC):
    """Abstract base class for CRM clients"""
    
    @abstractmethod
    def fetch_opportunities(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch opportunities/deals in date range"""
        pass
    
    @abstractmethod
    def fetch_accounts(self, modified_since: Optional[str] = None) -> pd.DataFrame:
        """Fetch accounts/companies"""
        pass
    
    @abstractmethod
    def fetch_contacts(self, modified_since: Optional[str] = None) -> pd.DataFrame:
        """Fetch contacts"""
        pass
    
    @abstractmethod
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get high-level metrics summary"""
        pass

class SalesforceClient(CRMClient):
    """Salesforce API client implementation"""
    
    def __init__(self, instance_url: str = None, access_token: str = None,
                 refresh_token: str = None, client_id: str = None, 
                 client_secret: str = None):
        self.instance_url = instance_url or os.getenv('SF_INSTANCE_URL')
        self.access_token = access_token or os.getenv('SF_ACCESS_TOKEN')
        self.refresh_token = refresh_token or os.getenv('SF_REFRESH_TOKEN')
        self.client_id = client_id or os.getenv('SF_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('SF_CLIENT_SECRET')
        
        self.api_version = 'v59.0'
        self.base_url = f"{self.instance_url}/services/data/{self.api_version}"
        
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
    
    def refresh_auth(self):
        """Refresh Salesforce OAuth token"""
        if not self.refresh_token:
            raise AuthenticationError("No refresh token available")
        
        token_url = f"{self.instance_url}/services/oauth2/token"
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        response = requests.post(token_url, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.instance_url = token_data['instance_url']
            self.base_url = f"{self.instance_url}/services/data/{self.api_version}"
            logger.info("Successfully refreshed Salesforce token")
        else:
            raise AuthenticationError(f"Token refresh failed: {response.text}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        return {
            'Authorization': f'Bearer {self.access_token}',
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
            retry_after = int(response.headers.get('Retry-After', 60))
            raise RateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds")
        
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed")
        
        if response.status_code != 200:
            raise CRMAPIError(f"API request failed: {response.status_code} - {response.text}")
        
        return response.json()
    
    def fetch_opportunities(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch opportunities in date range"""
        
        # SOQL query for opportunities
        query = f"""
        SELECT Id, Name, AccountId, Amount, StageName, CloseDate,
               Probability, Type, LeadSource, OwnerId, CreatedDate,
               IsClosed, IsWon, ExpectedRevenue
        FROM Opportunity
        WHERE CloseDate >= {start_date} AND CloseDate <= {end_date}
        ORDER BY CloseDate DESC
        """
        
        response = self._make_request('query', {'q': query})
        
        records = response.get('records', [])
        
        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        if not df.empty:
            # Clean up data types
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
            df['CloseDate'] = pd.to_datetime(df['CloseDate'])
            df['CreatedDate'] = pd.to_datetime(df['CreatedDate'])
            df['ExpectedRevenue'] = pd.to_numeric(df['ExpectedRevenue'], errors='coerce').fillna(0)
            
            # Add calculated fields
            df['Quarter'] = df['CloseDate'].dt.to_period('Q')
            df['Month'] = df['CloseDate'].dt.to_period('M')
        
        return df
    
    def fetch_accounts(self, modified_since: Optional[str] = None) -> pd.DataFrame:
        """Fetch accounts"""
        
        query = """
        SELECT Id, Name, Type, Industry, AnnualRevenue, NumberOfEmployees,
               BillingCountry, CreatedDate, LastModifiedDate, OwnerId
        FROM Account
        WHERE IsDeleted = false
        """
        
        if modified_since:
            query += f" AND LastModifiedDate >= {modified_since}"
        
        query += " ORDER BY LastModifiedDate DESC LIMIT 2000"
        
        response = self._make_request('query', {'q': query})
        records = response.get('records', [])
        
        return pd.DataFrame(records)
    
    def fetch_contacts(self, modified_since: Optional[str] = None) -> pd.DataFrame:
        """Fetch contacts"""
        
        query = """
        SELECT Id, FirstName, LastName, Email, AccountId, Title,
               Department, LeadSource, CreatedDate, LastModifiedDate
        FROM Contact
        WHERE IsDeleted = false
        """
        
        if modified_since:
            query += f" AND LastModifiedDate >= {modified_since}"
        
        query += " ORDER BY LastModifiedDate DESC LIMIT 2000"
        
        response = self._make_request('query', {'q': query})
        records = response.get('records', [])
        
        return pd.DataFrame(records)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get high-level Salesforce metrics"""
        
        today = datetime.now()
        month_start = today.replace(day=1)
        quarter_start = today.replace(month=((today.month-1)//3)*3+1, day=1)
        year_start = today.replace(month=1, day=1)
        
        metrics = {}
        
        # Pipeline metrics
        pipeline_query = f"""
        SELECT StageName, COUNT(Id) as Count, SUM(Amount) as Total
        FROM Opportunity
        WHERE IsClosed = false
        AND CloseDate >= '{month_start.strftime('%Y-%m-%d')}'
        GROUP BY StageName
        """
        
        pipeline_response = self._make_request('query', {'q': pipeline_query})
        pipeline_data = pipeline_response.get('records', [])
        
        total_pipeline = sum(float(stage.get('Total', 0) or 0) for stage in pipeline_data)
        metrics['pipeline_value'] = total_pipeline
        metrics['pipeline_count'] = sum(int(stage.get('Count', 0)) for stage in pipeline_data)
        
        # Closed-Won metrics
        won_query = f"""
        SELECT 
            SUM(Amount) as Total,
            COUNT(Id) as Count
        FROM Opportunity
        WHERE IsWon = true
        AND CloseDate >= '{month_start.strftime('%Y-%m-%d')}'
        """
        
        won_response = self._make_request('query', {'q': won_query})
        won_data = won_response.get('records', [{}])[0]
        
        metrics['bookings_mtd'] = float(won_data.get('Total', 0) or 0)
        metrics['deals_won_mtd'] = int(won_data.get('Count', 0))
        
        return metrics

class HubSpotClient(CRMClient):
    """HubSpot API client implementation"""
    
    def __init__(self, api_key: str = None, access_token: str = None):
        self.api_key = api_key or os.getenv('HUBSPOT_API_KEY')
        self.access_token = access_token or os.getenv('HUBSPOT_ACCESS_TOKEN')
        self.base_url = 'https://api.hubapi.com'
        
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
        if self.access_token:
            return {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
        else:
            return {
                'Content-Type': 'application/json'
            }
    
    def _get_auth_params(self) -> Dict[str, str]:
        """Get auth parameters for API key auth"""
        if self.api_key and not self.access_token:
            return {'hapikey': self.api_key}
        return {}
    
    @retry_with_backoff(max_retries=3)
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make API request with error handling"""
        url = f"{self.base_url}/{endpoint}"
        
        # Merge auth params if using API key
        if self.api_key and not self.access_token:
            params = {**params, **self._get_auth_params()} if params else self._get_auth_params()
        
        response = self.session.get(
            url,
            headers=self._get_headers(),
            params=params
        )
        
        if response.status_code == 429:
            retry_after = int(response.headers.get('X-HubSpot-RateLimit-Interval-Milliseconds', 10000)) / 1000
            raise RateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds")
        
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed")
        
        if response.status_code != 200:
            raise CRMAPIError(f"API request failed: {response.status_code} - {response.text}")
        
        return response.json()
    
    def fetch_opportunities(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch deals from HubSpot"""
        
        # Convert dates to timestamps
        start_ts = int(datetime.fromisoformat(start_date).timestamp() * 1000)
        end_ts = int(datetime.fromisoformat(end_date).timestamp() * 1000)
        
        endpoint = 'crm/v3/objects/deals'
        params = {
            'limit': 100,
            'properties': 'dealname,amount,dealstage,closedate,pipeline,hs_object_id,createdate'
        }
        
        all_deals = []
        after = None
        
        while True:
            if after:
                params['after'] = after
            
            response = self._make_request(endpoint, params)
            deals = response.get('results', [])
            
            # Filter by close date
            for deal in deals:
                close_date = deal.get('properties', {}).get('closedate')
                if close_date:
                    close_ts = int(datetime.fromisoformat(close_date).timestamp() * 1000)
                    if start_ts <= close_ts <= end_ts:
                        all_deals.append(deal['properties'])
            
            # Check for more pages
            paging = response.get('paging', {})
            if 'next' in paging:
                after = paging['next']['after']
            else:
                break
        
        # Convert to DataFrame
        df = pd.DataFrame(all_deals)
        
        if not df.empty:
            # Rename columns to match Salesforce schema
            df = df.rename(columns={
                'dealname': 'Name',
                'amount': 'Amount',
                'dealstage': 'StageName',
                'closedate': 'CloseDate',
                'hs_object_id': 'Id',
                'createdate': 'CreatedDate'
            })
            
            # Clean up data types
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
            df['CloseDate'] = pd.to_datetime(df['CloseDate'])
            df['CreatedDate'] = pd.to_datetime(df['CreatedDate'])
            
            # Add calculated fields
            df['Quarter'] = df['CloseDate'].dt.to_period('Q')
            df['Month'] = df['CloseDate'].dt.to_period('M')
            
            # Map HubSpot stages to standard stages
            stage_mapping = {
                'closedwon': 'Closed Won',
                'closedlost': 'Closed Lost',
                'contractsent': 'Negotiation',
                'decisionmakerboughtin': 'Proposal',
                'presentationscheduled': 'Demo',
                'appointmentscheduled': 'Discovery',
                'qualifiedtobuy': 'Qualified'
            }
            df['StageName'] = df['StageName'].map(stage_mapping).fillna(df['StageName'])
            
            # Add IsWon flag
            df['IsWon'] = df['StageName'] == 'Closed Won'
            df['IsClosed'] = df['StageName'].isin(['Closed Won', 'Closed Lost'])
        
        return df
    
    def fetch_accounts(self, modified_since: Optional[str] = None) -> pd.DataFrame:
        """Fetch companies from HubSpot"""
        
        endpoint = 'crm/v3/objects/companies'
        params = {
            'limit': 100,
            'properties': 'name,industry,annualrevenue,numberofemployees,country,createdate,hs_lastmodifieddate'
        }
        
        all_companies = []
        after = None
        
        while True:
            if after:
                params['after'] = after
            
            response = self._make_request(endpoint, params)
            companies = response.get('results', [])
            
            for company in companies:
                props = company['properties']
                if modified_since:
                    last_modified = props.get('hs_lastmodifieddate')
                    if last_modified and last_modified < modified_since:
                        continue
                all_companies.append(props)
            
            # Check for more pages
            paging = response.get('paging', {})
            if 'next' in paging and len(all_companies) < 2000:  # Limit to 2000
                after = paging['next']['after']
            else:
                break
        
        df = pd.DataFrame(all_companies)
        
        if not df.empty:
            # Rename to match Salesforce schema
            df = df.rename(columns={
                'name': 'Name',
                'industry': 'Industry',
                'annualrevenue': 'AnnualRevenue',
                'numberofemployees': 'NumberOfEmployees',
                'country': 'BillingCountry',
                'createdate': 'CreatedDate',
                'hs_lastmodifieddate': 'LastModifiedDate'
            })
        
        return df
    
    def fetch_contacts(self, modified_since: Optional[str] = None) -> pd.DataFrame:
        """Fetch contacts from HubSpot"""
        
        endpoint = 'crm/v3/objects/contacts'
        params = {
            'limit': 100,
            'properties': 'firstname,lastname,email,jobtitle,hs_lead_status,createdate,lastmodifieddate'
        }
        
        all_contacts = []
        after = None
        
        while True:
            if after:
                params['after'] = after
            
            response = self._make_request(endpoint, params)
            contacts = response.get('results', [])
            
            for contact in contacts:
                props = contact['properties']
                if modified_since:
                    last_modified = props.get('lastmodifieddate')
                    if last_modified and last_modified < modified_since:
                        continue
                all_contacts.append(props)
            
            # Check for more pages
            paging = response.get('paging', {})
            if 'next' in paging and len(all_contacts) < 2000:
                after = paging['next']['after']
            else:
                break
        
        df = pd.DataFrame(all_contacts)
        
        if not df.empty:
            # Rename to match Salesforce schema
            df = df.rename(columns={
                'firstname': 'FirstName',
                'lastname': 'LastName',
                'email': 'Email',
                'jobtitle': 'Title',
                'createdate': 'CreatedDate',
                'lastmodifieddate': 'LastModifiedDate'
            })
        
        return df
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get high-level HubSpot metrics"""
        
        today = datetime.now()
        month_start = today.replace(day=1)
        
        # Fetch deals for metrics
        deals_df = self.fetch_opportunities(
            month_start.strftime('%Y-%m-%d'),
            today.strftime('%Y-%m-%d')
        )
        
        metrics = {}
        
        if not deals_df.empty:
            # Pipeline metrics
            open_deals = deals_df[~deals_df['IsClosed']]
            metrics['pipeline_value'] = open_deals['Amount'].sum()
            metrics['pipeline_count'] = len(open_deals)
            
            # Closed-Won metrics
            won_deals = deals_df[deals_df['IsWon']]
            metrics['bookings_mtd'] = won_deals['Amount'].sum()
            metrics['deals_won_mtd'] = len(won_deals)
        else:
            metrics = {
                'pipeline_value': 0,
                'pipeline_count': 0,
                'bookings_mtd': 0,
                'deals_won_mtd': 0
            }
        
        return metrics

# Factory function to create appropriate client
def create_crm_client(crm_type: str) -> CRMClient:
    """Create a CRM client based on type"""
    
    if crm_type.lower() == 'salesforce':
        return SalesforceClient()
    elif crm_type.lower() == 'hubspot':
        return HubSpotClient()
    else:
        raise ValueError(f"Unsupported CRM type: {crm_type}")

# Convenience function for testing
def test_crm_connection(crm_type: str) -> bool:
    """Test CRM connection"""
    try:
        client = create_crm_client(crm_type)
        
        # Try to fetch recent opportunities
        today = datetime.now()
        start = today - timedelta(days=30)
        
        df = client.fetch_opportunities(
            start.strftime('%Y-%m-%d'),
            today.strftime('%Y-%m-%d')
        )
        
        logger.info(f"Connected to {crm_type}: Found {len(df)} opportunities")
        return True
        
    except Exception as e:
        logger.error(f"{crm_type} connection failed: {e}")
        return False