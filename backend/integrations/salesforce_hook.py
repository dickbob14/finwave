"""
Salesforce CRM integration for enhanced financial analytics
Provides sales pipeline, opportunity, and customer data correlation with financial metrics
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
from models.financial import Customer, GeneralLedger, DataSource, IngestionHistory

logger = logging.getLogger(__name__)

class SalesforceIntegration:
    """Salesforce CRM integration for financial correlation analysis"""
    
    def __init__(self, instance_url: str, access_token: str, client_id: str, client_secret: str):
        """
        Initialize Salesforce integration
        
        Args:
            instance_url: Salesforce instance URL (e.g., https://company.salesforce.com)
            access_token: OAuth access token
            client_id: Connected app client ID
            client_secret: Connected app client secret
        """
        self.instance_url = instance_url.rstrip('/')
        self.access_token = access_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = f"{self.instance_url}/services/data/v59.0"
        
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
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make authenticated request to Salesforce API"""
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
            if e.response.status_code == 401:
                # Token expired, attempt refresh
                await self._refresh_token()
                # Retry the request
                response = await self.session.get(
                    url,
                    headers=self._get_headers(),
                    params=params or {}
                )
                response.raise_for_status()
                return response.json()
            else:
                logger.error(f"Salesforce API error for {endpoint}: {e.response.status_code} - {e.response.text}")
                raise
        except Exception as e:
            logger.error(f"Request failed for {endpoint}: {str(e)}")
            raise
    
    async def sync_opportunities(self, start_date: str, end_date: str) -> Dict[str, int]:
        """
        Sync Salesforce opportunities for financial pipeline analysis
        
        Args:
            start_date: YYYY-MM-DD format
            end_date: YYYY-MM-DD format
            
        Returns:
            Dictionary with sync statistics
        """
        with get_db_session() as db:
            # Create ingestion record
            ingestion_record = IngestionHistory(
                source='salesforce',
                entity_type='opportunities',
                period_start=datetime.fromisoformat(start_date),
                period_end=datetime.fromisoformat(end_date),
                status='pending'
            )
            db.add(ingestion_record)
            db.commit()
            
            try:
                # SOQL query for opportunities
                soql = f"""
                SELECT Id, Name, AccountId, Account.Name, Amount, StageName, 
                       Probability, CloseDate, CreatedDate, LastModifiedDate,
                       OwnerId, Owner.Name, Type, ForecastCategoryName
                FROM Opportunity 
                WHERE CreatedDate >= {start_date}T00:00:00Z 
                AND CreatedDate <= {end_date}T23:59:59Z
                ORDER BY CreatedDate DESC
                """
                
                response = await self._make_request("query", {"q": soql})
                opportunities = response.get('records', [])
                
                processed_count = 0
                for opp in opportunities:
                    await self._process_opportunity(db, opp)
                    processed_count += 1
                
                # Update ingestion record
                ingestion_record.status = 'completed'
                ingestion_record.records_count = processed_count
                db.commit()
                
                logger.info(f"Synced {processed_count} Salesforce opportunities")
                return {'opportunities': processed_count}
                
            except Exception as e:
                ingestion_record.status = 'failed'
                ingestion_record.error_message = str(e)
                db.commit()
                raise
    
    async def sync_accounts(self, start_date: str, end_date: str) -> Dict[str, int]:
        """
        Sync Salesforce accounts for customer correlation
        
        Args:
            start_date: YYYY-MM-DD format  
            end_date: YYYY-MM-DD format
            
        Returns:
            Dictionary with sync statistics
        """
        with get_db_session() as db:
            ingestion_record = IngestionHistory(
                source='salesforce',
                entity_type='accounts',
                period_start=datetime.fromisoformat(start_date),
                period_end=datetime.fromisoformat(end_date),
                status='pending'
            )
            db.add(ingestion_record)
            db.commit()
            
            try:
                # SOQL query for accounts
                soql = f"""
                SELECT Id, Name, Type, Industry, AnnualRevenue, 
                       NumberOfEmployees, BillingStreet, BillingCity, 
                       BillingState, BillingCountry, Phone, Website,
                       CreatedDate, LastModifiedDate
                FROM Account 
                WHERE LastModifiedDate >= {start_date}T00:00:00Z 
                AND LastModifiedDate <= {end_date}T23:59:59Z
                ORDER BY LastModifiedDate DESC
                """
                
                response = await self._make_request("query", {"q": soql})
                accounts = response.get('records', [])
                
                processed_count = 0
                for account in accounts:
                    await self._process_account(db, account)
                    processed_count += 1
                
                ingestion_record.status = 'completed'
                ingestion_record.records_count = processed_count
                db.commit()
                
                logger.info(f"Synced {processed_count} Salesforce accounts")
                return {'accounts': processed_count}
                
            except Exception as e:
                ingestion_record.status = 'failed'
                ingestion_record.error_message = str(e)
                db.commit()
                raise
    
    async def get_sales_pipeline_metrics(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Get sales pipeline metrics for financial correlation
        
        Args:
            start_date: YYYY-MM-DD format
            end_date: YYYY-MM-DD format
            
        Returns:
            Dictionary with pipeline metrics
        """
        # Pipeline by stage
        stage_soql = f"""
        SELECT StageName, COUNT(Id) OpportunityCount, SUM(Amount) TotalValue,
               AVG(Amount) AverageValue
        FROM Opportunity 
        WHERE CreatedDate >= {start_date}T00:00:00Z 
        AND CreatedDate <= {end_date}T23:59:59Z
        GROUP BY StageName
        """
        
        stage_response = await self._make_request("query", {"q": stage_soql})
        pipeline_by_stage = stage_response.get('records', [])
        
        # Won/Lost analysis
        outcome_soql = f"""
        SELECT IsWon, COUNT(Id) OpportunityCount, SUM(Amount) TotalValue
        FROM Opportunity 
        WHERE CloseDate >= {start_date} 
        AND CloseDate <= {end_date}
        AND IsClosed = true
        GROUP BY IsWon
        """
        
        outcome_response = await self._make_request("query", {"q": outcome_soql})
        win_loss_data = outcome_response.get('records', [])
        
        # Monthly trend
        monthly_soql = f"""
        SELECT CALENDAR_MONTH(CreatedDate) Month, 
               CALENDAR_YEAR(CreatedDate) Year,
               COUNT(Id) OpportunityCount, 
               SUM(Amount) TotalValue
        FROM Opportunity 
        WHERE CreatedDate >= {start_date}T00:00:00Z 
        AND CreatedDate <= {end_date}T23:59:59Z
        GROUP BY CALENDAR_YEAR(CreatedDate), CALENDAR_MONTH(CreatedDate)
        ORDER BY CALENDAR_YEAR(CreatedDate), CALENDAR_MONTH(CreatedDate)
        """
        
        monthly_response = await self._make_request("query", {"q": monthly_soql})
        monthly_trends = monthly_response.get('records', [])
        
        return {
            'pipeline_by_stage': [
                {
                    'stage': record['StageName'],
                    'count': record['OpportunityCount'],
                    'total_value': float(record['TotalValue'] or 0),
                    'average_value': float(record['AverageValue'] or 0)
                }
                for record in pipeline_by_stage
            ],
            'win_loss_analysis': [
                {
                    'outcome': 'Won' if record['IsWon'] else 'Lost',
                    'count': record['OpportunityCount'],
                    'total_value': float(record['TotalValue'] or 0)
                }
                for record in win_loss_data
            ],
            'monthly_trends': [
                {
                    'year': record['Year'],
                    'month': record['Month'],
                    'count': record['OpportunityCount'],
                    'total_value': float(record['TotalValue'] or 0)
                }
                for record in monthly_trends
            ]
        }
    
    async def correlate_sales_to_revenue(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Correlate Salesforce sales data with financial revenue data
        
        Args:
            start_date: YYYY-MM-DD format
            end_date: YYYY-MM-DD format
            
        Returns:
            Dictionary with correlation analysis
        """
        # Get won opportunities
        won_soql = f"""
        SELECT AccountId, Account.Name, SUM(Amount) TotalWon, COUNT(Id) OpportunityCount
        FROM Opportunity 
        WHERE CloseDate >= {start_date} 
        AND CloseDate <= {end_date}
        AND IsWon = true
        GROUP BY AccountId, Account.Name
        ORDER BY SUM(Amount) DESC
        """
        
        sf_response = await self._make_request("query", {"q": won_soql})
        sf_won_data = sf_response.get('records', [])
        
        # Get financial revenue data by customer
        with get_db_session() as db:
            revenue_data = db.query(
                GeneralLedger.customer_name,
                func.sum(GeneralLedger.credit_amount).label('revenue_amount')
            ).filter(
                and_(
                    GeneralLedger.transaction_date >= start_date,
                    GeneralLedger.transaction_date <= end_date,
                    GeneralLedger.account_type.in_(['Income', 'Revenue']),
                    GeneralLedger.customer_name.isnot(None)
                )
            ).group_by(GeneralLedger.customer_name).all()
        
        # Create correlation mapping
        correlations = []
        total_sf_amount = 0
        total_revenue_amount = 0
        matched_customers = 0
        
        for sf_record in sf_won_data:
            sf_account_name = sf_record['Account']['Name']
            sf_amount = float(sf_record['TotalWon'] or 0)
            total_sf_amount += sf_amount
            
            # Find matching customer in financial data
            matching_revenue = next(
                (r for r in revenue_data if self._fuzzy_match_customer(sf_account_name, r.customer_name)),
                None
            )
            
            if matching_revenue:
                revenue_amount = float(matching_revenue.revenue_amount or 0)
                total_revenue_amount += revenue_amount
                matched_customers += 1
                
                correlations.append({
                    'salesforce_account': sf_account_name,
                    'financial_customer': matching_revenue.customer_name,
                    'salesforce_amount': sf_amount,
                    'financial_revenue': revenue_amount,
                    'variance': revenue_amount - sf_amount,
                    'variance_percentage': ((revenue_amount - sf_amount) / sf_amount * 100) if sf_amount > 0 else 0,
                    'opportunity_count': sf_record['OpportunityCount']
                })
            else:
                correlations.append({
                    'salesforce_account': sf_account_name,
                    'financial_customer': None,
                    'salesforce_amount': sf_amount,
                    'financial_revenue': 0,
                    'variance': -sf_amount,
                    'variance_percentage': -100,
                    'opportunity_count': sf_record['OpportunityCount']
                })
        
        # Calculate overall correlation metrics
        coverage_percentage = (matched_customers / len(sf_won_data) * 100) if sf_won_data else 0
        total_variance = total_revenue_amount - total_sf_amount
        total_variance_pct = (total_variance / total_sf_amount * 100) if total_sf_amount > 0 else 0
        
        return {
            'correlations': correlations,
            'summary': {
                'total_salesforce_won': total_sf_amount,
                'total_financial_revenue': total_revenue_amount,
                'total_variance': total_variance,
                'total_variance_percentage': total_variance_pct,
                'customer_match_rate': coverage_percentage,
                'matched_customers': matched_customers,
                'total_sf_customers': len(sf_won_data)
            },
            'insights': self._generate_correlation_insights(correlations, total_variance_pct, coverage_percentage)
        }
    
    async def _process_opportunity(self, db: Session, opportunity: Dict):
        """Process and store opportunity data"""
        # In a full implementation, you'd create custom tables for SF data
        # For now, we'll log the key metrics that could be used for correlation
        logger.debug(f"Processing opportunity: {opportunity.get('Name')} - ${opportunity.get('Amount', 0)}")
        
        # This could be expanded to store in custom SF opportunity tables
        # or correlate with existing customer records
        
    async def _process_account(self, db: Session, account: Dict):
        """Process and store account data, correlating with existing customers"""
        sf_account_name = account.get('Name', '')
        
        # Try to find matching customer in financial data
        existing_customer = db.query(Customer).filter(
            Customer.name.ilike(f"%{sf_account_name}%")
        ).first()
        
        if existing_customer:
            # Update customer with Salesforce data
            if not existing_customer.raw_data:
                existing_customer.raw_data = {}
            
            existing_customer.raw_data['salesforce'] = {
                'sf_id': account.get('Id'),
                'industry': account.get('Industry'),
                'annual_revenue': account.get('AnnualRevenue'),
                'employee_count': account.get('NumberOfEmployees'),
                'account_type': account.get('Type'),
                'synced_at': datetime.now().isoformat()
            }
            
            # Update contact information if available
            if account.get('Phone') and not existing_customer.phone:
                existing_customer.phone = account.get('Phone')
            if account.get('Website') and not existing_customer.website:
                existing_customer.website = account.get('Website')
            
            db.commit()
            logger.debug(f"Updated customer {existing_customer.name} with Salesforce data")
    
    def _fuzzy_match_customer(self, sf_name: str, financial_name: str) -> bool:
        """Fuzzy match customer names between systems"""
        if not sf_name or not financial_name:
            return False
        
        sf_clean = sf_name.lower().strip()
        fin_clean = financial_name.lower().strip()
        
        # Exact match
        if sf_clean == fin_clean:
            return True
        
        # Contains match
        if sf_clean in fin_clean or fin_clean in sf_clean:
            return True
        
        # Remove common company suffixes for better matching
        suffixes = ['inc', 'llc', 'corp', 'ltd', 'company', 'co']
        for suffix in suffixes:
            sf_clean = sf_clean.replace(f' {suffix}', '').replace(f', {suffix}', '')
            fin_clean = fin_clean.replace(f' {suffix}', '').replace(f', {suffix}', '')
        
        # Check after suffix removal
        if sf_clean == fin_clean or sf_clean in fin_clean or fin_clean in sf_clean:
            return True
        
        return False
    
    def _generate_correlation_insights(self, correlations: List[Dict], total_variance_pct: float, coverage_pct: float) -> List[str]:
        """Generate insights from sales-to-revenue correlation"""
        insights = []
        
        if coverage_pct < 70:
            insights.append(f"Low customer matching rate ({coverage_pct:.1f}%) suggests need for improved data integration between Salesforce and financial systems.")
        
        if abs(total_variance_pct) > 20:
            if total_variance_pct > 0:
                insights.append(f"Financial revenue exceeds Salesforce won amounts by {total_variance_pct:.1f}%, indicating potential upselling or additional revenue streams.")
            else:
                insights.append(f"Salesforce won amounts exceed financial revenue by {abs(total_variance_pct):.1f}%, suggesting collection issues or revenue recognition timing differences.")
        
        # Identify customers with large variances
        large_variances = [c for c in correlations if abs(c.get('variance_percentage', 0)) > 50 and c.get('salesforce_amount', 0) > 1000]
        if large_variances:
            insights.append(f"{len(large_variances)} customers show significant variance between sales and financial data requiring investigation.")
        
        return insights
    
    async def _refresh_token(self):
        """Refresh OAuth token"""
        # Implementation would depend on your OAuth setup
        # This is a placeholder for token refresh logic
        logger.warning("Token refresh needed but not implemented")
    
    def _ensure_data_source(self):
        """Ensure Salesforce data source is registered"""
        with get_db_session() as db:
            existing = db.query(DataSource).filter(DataSource.name == 'salesforce').first()
            
            if not existing:
                data_source = DataSource(
                    name='salesforce',
                    type='crm',
                    status='active',
                    connection_config={
                        'instance_url': self.instance_url,
                        'api_version': 'v59.0'
                    },
                    sync_frequency='daily'
                )
                db.add(data_source)
                db.commit()
                logger.info("Registered Salesforce data source")


# Convenience functions
async def sync_salesforce_data(instance_url: str, access_token: str, client_id: str, 
                              client_secret: str, start_date: str, end_date: str) -> Dict[str, int]:
    """
    Sync Salesforce data for the given period
    
    Args:
        instance_url: Salesforce instance URL
        access_token: OAuth access token
        client_id: Connected app client ID
        client_secret: Connected app client secret
        start_date: YYYY-MM-DD format
        end_date: YYYY-MM-DD format
        
    Returns:
        Dictionary with sync statistics
    """
    async with SalesforceIntegration(instance_url, access_token, client_id, client_secret) as sf:
        # Sync opportunities and accounts
        opp_stats = await sf.sync_opportunities(start_date, end_date)
        account_stats = await sf.sync_accounts(start_date, end_date)
        
        # Combine statistics
        return {
            'opportunities': opp_stats.get('opportunities', 0),
            'accounts': account_stats.get('accounts', 0),
            'total_records': opp_stats.get('opportunities', 0) + account_stats.get('accounts', 0)
        }

async def get_sales_revenue_correlation(instance_url: str, access_token: str, client_id: str,
                                       client_secret: str, start_date: str, end_date: str) -> Dict[str, Any]:
    """Get sales to revenue correlation analysis"""
    async with SalesforceIntegration(instance_url, access_token, client_id, client_secret) as sf:
        return await sf.correlate_sales_to_revenue(start_date, end_date)


if __name__ == "__main__":
    # Example usage
    import asyncio
    import os
    
    async def main():
        # Configuration
        instance_url = os.getenv("SALESFORCE_INSTANCE_URL", "https://company.salesforce.com")
        access_token = os.getenv("SALESFORCE_ACCESS_TOKEN")
        client_id = os.getenv("SALESFORCE_CLIENT_ID")
        client_secret = os.getenv("SALESFORCE_CLIENT_SECRET")
        
        if not all([access_token, client_id, client_secret]):
            print("Salesforce credentials not configured in environment variables")
            return
        
        # Sync last 30 days
        end_date = datetime.now().date().isoformat()
        start_date = (datetime.now().date() - timedelta(days=30)).isoformat()
        
        print(f"Starting Salesforce sync for {start_date} to {end_date}")
        
        try:
            stats = await sync_salesforce_data(
                instance_url, access_token, client_id, client_secret,
                start_date, end_date
            )
            print(f"Sync completed: {stats}")
            
            # Get correlation analysis
            correlation = await get_sales_revenue_correlation(
                instance_url, access_token, client_id, client_secret,
                start_date, end_date
            )
            print(f"Correlation analysis completed. Match rate: {correlation['summary']['customer_match_rate']:.1f}%")
            
        except Exception as e:
            print(f"Salesforce sync failed: {e}")
    
    asyncio.run(main())