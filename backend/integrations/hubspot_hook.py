"""
HubSpot CRM integration for marketing and sales attribution analysis
Provides marketing campaign, contact, and deal data correlation with financial performance
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

class HubSpotIntegration:
    """HubSpot CRM integration for marketing attribution and financial correlation"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.hubapi.com"):
        """
        Initialize HubSpot integration
        
        Args:
            api_key: HubSpot API key
            base_url: HubSpot API base URL
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
    
    async def _make_request(self, endpoint: str, params: Dict = None, method: str = "GET") -> Dict:
        """Make authenticated request to HubSpot API"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = await self.session.get(
                    url,
                    headers=self._get_headers(),
                    params=params or {}
                )
            else:
                response = await self.session.request(
                    method,
                    url,
                    headers=self._get_headers(),
                    json=params or {}
                )
            
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HubSpot API error for {endpoint}: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Request failed for {endpoint}: {str(e)}")
            raise
    
    async def sync_deals(self, start_date: str, end_date: str) -> Dict[str, int]:
        """
        Sync HubSpot deals for financial pipeline analysis
        
        Args:
            start_date: YYYY-MM-DD format
            end_date: YYYY-MM-DD format
            
        Returns:
            Dictionary with sync statistics
        """
        with get_db_session() as db:
            # Create ingestion record
            ingestion_record = IngestionHistory(
                source='hubspot',
                entity_type='deals',
                period_start=datetime.fromisoformat(start_date),
                period_end=datetime.fromisoformat(end_date),
                status='pending'
            )
            db.add(ingestion_record)
            db.commit()
            
            try:
                # Convert dates to timestamps for HubSpot API
                start_timestamp = int(datetime.fromisoformat(start_date).timestamp() * 1000)
                end_timestamp = int(datetime.fromisoformat(end_date).timestamp() * 1000)
                
                # Get deals created in the date range
                deals_data = await self._get_deals_batch(start_timestamp, end_timestamp)
                
                processed_count = 0
                for deal in deals_data:
                    await self._process_deal(db, deal)
                    processed_count += 1
                
                # Update ingestion record
                ingestion_record.status = 'completed'
                ingestion_record.records_count = processed_count
                db.commit()
                
                logger.info(f"Synced {processed_count} HubSpot deals")
                return {'deals': processed_count}
                
            except Exception as e:
                ingestion_record.status = 'failed'
                ingestion_record.error_message = str(e)
                db.commit()
                raise
    
    async def sync_companies(self, start_date: str, end_date: str) -> Dict[str, int]:
        """
        Sync HubSpot companies for customer correlation
        
        Args:
            start_date: YYYY-MM-DD format
            end_date: YYYY-MM-DD format
            
        Returns:
            Dictionary with sync statistics
        """
        with get_db_session() as db:
            ingestion_record = IngestionHistory(
                source='hubspot',
                entity_type='companies',
                period_start=datetime.fromisoformat(start_date),
                period_end=datetime.fromisoformat(end_date),
                status='pending'
            )
            db.add(ingestion_record)
            db.commit()
            
            try:
                # Convert dates for HubSpot API
                start_timestamp = int(datetime.fromisoformat(start_date).timestamp() * 1000)
                end_timestamp = int(datetime.fromisoformat(end_date).timestamp() * 1000)
                
                # Get companies
                companies_data = await self._get_companies_batch(start_timestamp, end_timestamp)
                
                processed_count = 0
                for company in companies_data:
                    await self._process_company(db, company)
                    processed_count += 1
                
                ingestion_record.status = 'completed'
                ingestion_record.records_count = processed_count
                db.commit()
                
                logger.info(f"Synced {processed_count} HubSpot companies")
                return {'companies': processed_count}
                
            except Exception as e:
                ingestion_record.status = 'failed'
                ingestion_record.error_message = str(e)
                db.commit()
                raise
    
    async def sync_marketing_campaigns(self, start_date: str, end_date: str) -> Dict[str, int]:
        """
        Sync HubSpot marketing campaign data
        
        Args:
            start_date: YYYY-MM-DD format
            end_date: YYYY-MM-DD format
            
        Returns:
            Dictionary with sync statistics
        """
        with get_db_session() as db:
            ingestion_record = IngestionHistory(
                source='hubspot',
                entity_type='campaigns',
                period_start=datetime.fromisoformat(start_date),
                period_end=datetime.fromisoformat(end_date),
                status='pending'
            )
            db.add(ingestion_record)
            db.commit()
            
            try:
                # Get marketing campaigns
                campaigns_data = await self._get_campaigns_batch(start_date, end_date)
                
                processed_count = len(campaigns_data)
                
                # Store campaign data for later correlation
                # In a full implementation, you'd create custom tables for campaign data
                
                ingestion_record.status = 'completed'
                ingestion_record.records_count = processed_count
                ingestion_record.ingestion_metadata = {'campaigns': campaigns_data}
                db.commit()
                
                logger.info(f"Synced {processed_count} HubSpot campaigns")
                return {'campaigns': processed_count}
                
            except Exception as e:
                ingestion_record.status = 'failed'
                ingestion_record.error_message = str(e)
                db.commit()
                raise
    
    async def get_sales_attribution_metrics(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Get sales attribution metrics from HubSpot
        
        Args:
            start_date: YYYY-MM-DD format
            end_date: YYYY-MM-DD format
            
        Returns:
            Dictionary with attribution metrics
        """
        # Get deals with attribution data
        start_timestamp = int(datetime.fromisoformat(start_date).timestamp() * 1000)
        end_timestamp = int(datetime.fromisoformat(end_date).timestamp() * 1000)
        
        deals = await self._get_deals_batch(start_timestamp, end_timestamp, include_attribution=True)
        
        # Analyze attribution sources
        attribution_analysis = self._analyze_deal_attribution(deals)
        
        # Get campaign performance
        campaigns = await self._get_campaigns_batch(start_date, end_date)
        campaign_analysis = self._analyze_campaign_performance(campaigns, deals)
        
        return {
            'attribution_sources': attribution_analysis,
            'campaign_performance': campaign_analysis,
            'total_deals_analyzed': len(deals),
            'period': {'start_date': start_date, 'end_date': end_date}
        }
    
    async def correlate_marketing_to_revenue(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Correlate HubSpot marketing data with financial revenue
        
        Args:
            start_date: YYYY-MM-DD format
            end_date: YYYY-MM-DD format
            
        Returns:
            Dictionary with marketing-to-revenue correlation
        """
        # Get HubSpot won deals
        start_timestamp = int(datetime.fromisoformat(start_date).timestamp() * 1000)
        end_timestamp = int(datetime.fromisoformat(end_date).timestamp() * 1000)
        
        won_deals = await self._get_won_deals(start_timestamp, end_timestamp)
        
        # Get financial revenue data
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
        
        # Create correlation analysis
        correlations = []
        total_hs_amount = 0
        total_revenue_amount = 0
        matched_companies = 0
        
        for deal in won_deals:
            company_name = deal.get('properties', {}).get('dealname', '')
            deal_amount = float(deal.get('properties', {}).get('amount', 0))
            total_hs_amount += deal_amount
            
            # Find matching customer in financial data
            matching_revenue = next(
                (r for r in revenue_data if self._fuzzy_match_customer(company_name, r.customer_name)),
                None
            )
            
            if matching_revenue:
                revenue_amount = float(matching_revenue.revenue_amount or 0)
                total_revenue_amount += revenue_amount
                matched_companies += 1
                
                correlations.append({
                    'hubspot_deal': company_name,
                    'financial_customer': matching_revenue.customer_name,
                    'hubspot_amount': deal_amount,
                    'financial_revenue': revenue_amount,
                    'variance': revenue_amount - deal_amount,
                    'variance_percentage': ((revenue_amount - deal_amount) / deal_amount * 100) if deal_amount > 0 else 0,
                    'attribution_source': deal.get('properties', {}).get('hs_analytics_source', 'Unknown'),
                    'campaign': deal.get('properties', {}).get('hs_campaign', 'Unknown')
                })
        
        # Calculate metrics
        coverage_percentage = (matched_companies / len(won_deals) * 100) if won_deals else 0
        total_variance = total_revenue_amount - total_hs_amount
        total_variance_pct = (total_variance / total_hs_amount * 100) if total_hs_amount > 0 else 0
        
        # Attribution source analysis
        attribution_revenue = {}
        for correlation in correlations:
            source = correlation['attribution_source']
            if source not in attribution_revenue:
                attribution_revenue[source] = {'count': 0, 'hubspot_total': 0, 'revenue_total': 0}
            
            attribution_revenue[source]['count'] += 1
            attribution_revenue[source]['hubspot_total'] += correlation['hubspot_amount']
            attribution_revenue[source]['revenue_total'] += correlation['financial_revenue']
        
        return {
            'correlations': correlations,
            'summary': {
                'total_hubspot_deals': total_hs_amount,
                'total_financial_revenue': total_revenue_amount,
                'total_variance': total_variance,
                'total_variance_percentage': total_variance_pct,
                'company_match_rate': coverage_percentage,
                'matched_companies': matched_companies,
                'total_hs_deals': len(won_deals)
            },
            'attribution_analysis': [
                {
                    'source': source,
                    'deal_count': data['count'],
                    'hubspot_total': data['hubspot_total'],
                    'revenue_total': data['revenue_total'],
                    'roi': ((data['revenue_total'] - data['hubspot_total']) / data['hubspot_total'] * 100) if data['hubspot_total'] > 0 else 0
                }
                for source, data in attribution_revenue.items()
            ],
            'insights': self._generate_marketing_insights(correlations, attribution_revenue, total_variance_pct, coverage_percentage)
        }
    
    async def _get_deals_batch(self, start_timestamp: int, end_timestamp: int, include_attribution: bool = False) -> List[Dict]:
        """Get deals in batches from HubSpot API"""
        all_deals = []
        after = None
        
        properties = [
            'dealname', 'amount', 'dealstage', 'pipeline', 'closedate', 
            'createdate', 'hs_deal_stage_probability', 'dealtype'
        ]
        
        if include_attribution:
            properties.extend([
                'hs_analytics_source', 'hs_campaign', 'hs_analytics_source_data_1',
                'hs_analytics_source_data_2', 'hs_latest_source'
            ])
        
        while True:
            params = {
                'properties': properties,
                'limit': 100
            }
            
            if after:
                params['after'] = after
            
            # Add date filtering
            params['filterGroups'] = [{
                'filters': [{
                    'propertyName': 'createdate',
                    'operator': 'BETWEEN',
                    'value': start_timestamp,
                    'highValue': end_timestamp
                }]
            }]
            
            response = await self._make_request("crm/v3/objects/deals/search", params, "POST")
            
            deals = response.get('results', [])
            all_deals.extend(deals)
            
            paging = response.get('paging', {})
            if not paging.get('next'):
                break
                
            after = paging['next']['after']
        
        return all_deals
    
    async def _get_companies_batch(self, start_timestamp: int, end_timestamp: int) -> List[Dict]:
        """Get companies in batches from HubSpot API"""
        all_companies = []
        after = None
        
        properties = [
            'name', 'domain', 'industry', 'annualrevenue', 'numberofemployees',
            'city', 'state', 'country', 'phone', 'website', 'createdate',
            'hs_lastmodifieddate', 'lifecyclestage'
        ]
        
        while True:
            params = {
                'properties': properties,
                'limit': 100
            }
            
            if after:
                params['after'] = after
            
            # Add date filtering for recently modified companies
            params['filterGroups'] = [{
                'filters': [{
                    'propertyName': 'hs_lastmodifieddate',
                    'operator': 'BETWEEN',
                    'value': start_timestamp,
                    'highValue': end_timestamp
                }]
            }]
            
            response = await self._make_request("crm/v3/objects/companies/search", params, "POST")
            
            companies = response.get('results', [])
            all_companies.extend(companies)
            
            paging = response.get('paging', {})
            if not paging.get('next'):
                break
                
            after = paging['next']['after']
        
        return all_companies
    
    async def _get_campaigns_batch(self, start_date: str, end_date: str) -> List[Dict]:
        """Get marketing campaigns from HubSpot"""
        # This would use the Marketing Events API or Campaigns API
        # For now, return mock data structure
        return [
            {
                'id': '12345',
                'name': 'Q4 Email Campaign',
                'type': 'EMAIL',
                'startDate': start_date,
                'endDate': end_date,
                'budget': 5000,
                'impressions': 15000,
                'clicks': 750,
                'conversions': 45
            },
            {
                'id': '12346',
                'name': 'Social Media Push',
                'type': 'SOCIAL',
                'startDate': start_date,
                'endDate': end_date,
                'budget': 3000,
                'impressions': 25000,
                'clicks': 1200,
                'conversions': 38
            }
        ]
    
    async def _get_won_deals(self, start_timestamp: int, end_timestamp: int) -> List[Dict]:
        """Get won deals from HubSpot"""
        params = {
            'properties': [
                'dealname', 'amount', 'closedate', 'hs_analytics_source',
                'hs_campaign', 'hs_analytics_source_data_1', 'pipeline'
            ],
            'filterGroups': [{
                'filters': [
                    {
                        'propertyName': 'closedate',
                        'operator': 'BETWEEN',
                        'value': start_timestamp,
                        'highValue': end_timestamp
                    },
                    {
                        'propertyName': 'dealstage',
                        'operator': 'EQ',
                        'value': 'closedwon'
                    }
                ]
            }],
            'limit': 100
        }
        
        response = await self._make_request("crm/v3/objects/deals/search", params, "POST")
        return response.get('results', [])
    
    async def _process_deal(self, db: Session, deal: Dict):
        """Process and store deal data"""
        # In a full implementation, you'd create custom tables for HubSpot data
        logger.debug(f"Processing deal: {deal.get('properties', {}).get('dealname')} - ${deal.get('properties', {}).get('amount', 0)}")
    
    async def _process_company(self, db: Session, company: Dict):
        """Process and store company data, correlating with existing customers"""
        company_name = company.get('properties', {}).get('name', '')
        
        # Try to find matching customer in financial data
        existing_customer = db.query(Customer).filter(
            Customer.name.ilike(f"%{company_name}%")
        ).first()
        
        if existing_customer:
            # Update customer with HubSpot data
            if not existing_customer.raw_data:
                existing_customer.raw_data = {}
            
            existing_customer.raw_data['hubspot'] = {
                'hs_id': company.get('id'),
                'domain': company.get('properties', {}).get('domain'),
                'industry': company.get('properties', {}).get('industry'),
                'annual_revenue': company.get('properties', {}).get('annualrevenue'),
                'employee_count': company.get('properties', {}).get('numberofemployees'),
                'lifecycle_stage': company.get('properties', {}).get('lifecyclestage'),
                'synced_at': datetime.now().isoformat()
            }
            
            # Update contact information
            props = company.get('properties', {})
            if props.get('phone') and not existing_customer.phone:
                existing_customer.phone = props.get('phone')
            if props.get('website') and not existing_customer.website:
                existing_customer.website = props.get('website')
            
            db.commit()
            logger.debug(f"Updated customer {existing_customer.name} with HubSpot data")
    
    def _analyze_deal_attribution(self, deals: List[Dict]) -> List[Dict]:
        """Analyze deal attribution sources"""
        attribution_summary = {}
        
        for deal in deals:
            props = deal.get('properties', {})
            source = props.get('hs_analytics_source', 'Unknown')
            amount = float(props.get('amount', 0))
            
            if source not in attribution_summary:
                attribution_summary[source] = {'count': 0, 'total_value': 0, 'deals': []}
            
            attribution_summary[source]['count'] += 1
            attribution_summary[source]['total_value'] += amount
            attribution_summary[source]['deals'].append({
                'name': props.get('dealname', ''),
                'amount': amount,
                'stage': props.get('dealstage', ''),
                'campaign': props.get('hs_campaign', 'Unknown')
            })
        
        return [
            {
                'source': source,
                'deal_count': data['count'],
                'total_value': data['total_value'],
                'average_deal_size': data['total_value'] / data['count'] if data['count'] > 0 else 0,
                'sample_deals': data['deals'][:3]  # Top 3 deals
            }
            for source, data in attribution_summary.items()
        ]
    
    def _analyze_campaign_performance(self, campaigns: List[Dict], deals: List[Dict]) -> List[Dict]:
        """Analyze campaign performance with deal correlation"""
        campaign_performance = []
        
        for campaign in campaigns:
            # Calculate basic metrics
            ctr = (campaign['clicks'] / campaign['impressions'] * 100) if campaign['impressions'] > 0 else 0
            conversion_rate = (campaign['conversions'] / campaign['clicks'] * 100) if campaign['clicks'] > 0 else 0
            cpc = (campaign['budget'] / campaign['clicks']) if campaign['clicks'] > 0 else 0
            
            # Find related deals (simplified matching by campaign name)
            related_deals = [
                d for d in deals 
                if campaign['name'].lower() in d.get('properties', {}).get('hs_campaign', '').lower()
            ]
            
            deal_value = sum(float(d.get('properties', {}).get('amount', 0)) for d in related_deals)
            roi = ((deal_value - campaign['budget']) / campaign['budget'] * 100) if campaign['budget'] > 0 else 0
            
            campaign_performance.append({
                'campaign_id': campaign['id'],
                'campaign_name': campaign['name'],
                'campaign_type': campaign['type'],
                'budget': campaign['budget'],
                'impressions': campaign['impressions'],
                'clicks': campaign['clicks'],
                'conversions': campaign['conversions'],
                'ctr': ctr,
                'conversion_rate': conversion_rate,
                'cpc': cpc,
                'attributed_deals': len(related_deals),
                'attributed_deal_value': deal_value,
                'roi': roi
            })
        
        return campaign_performance
    
    def _fuzzy_match_customer(self, hs_name: str, financial_name: str) -> bool:
        """Fuzzy match customer names between HubSpot and financial systems"""
        if not hs_name or not financial_name:
            return False
        
        hs_clean = hs_name.lower().strip()
        fin_clean = financial_name.lower().strip()
        
        # Exact match
        if hs_clean == fin_clean:
            return True
        
        # Contains match
        if hs_clean in fin_clean or fin_clean in hs_clean:
            return True
        
        # Remove common company suffixes
        suffixes = ['inc', 'llc', 'corp', 'ltd', 'company', 'co']
        for suffix in suffixes:
            hs_clean = hs_clean.replace(f' {suffix}', '').replace(f', {suffix}', '')
            fin_clean = fin_clean.replace(f' {suffix}', '').replace(f', {suffix}', '')
        
        # Check after suffix removal
        if hs_clean == fin_clean or hs_clean in fin_clean or fin_clean in hs_clean:
            return True
        
        return False
    
    def _generate_marketing_insights(self, correlations: List[Dict], attribution_revenue: Dict, 
                                   total_variance_pct: float, coverage_pct: float) -> List[str]:
        """Generate insights from marketing-to-revenue correlation"""
        insights = []
        
        if coverage_pct < 70:
            insights.append(f"Company matching rate of {coverage_pct:.1f}% indicates need for better integration between HubSpot and financial systems.")
        
        # ROI analysis by attribution source
        high_roi_sources = [
            source for source, data in attribution_revenue.items()
            if data['revenue_total'] > data['hubspot_total'] * 1.5  # 150% ROI
        ]
        
        if high_roi_sources:
            insights.append(f"High-performing attribution sources: {', '.join(high_roi_sources)} - consider increased investment.")
        
        # Variance analysis
        if abs(total_variance_pct) > 15:
            if total_variance_pct > 0:
                insights.append(f"Financial revenue exceeds HubSpot deal values by {total_variance_pct:.1f}%, suggesting effective upselling or additional revenue streams.")
            else:
                insights.append(f"HubSpot deal values exceed financial revenue by {abs(total_variance_pct):.1f}%, indicating potential collection or recognition issues.")
        
        return insights
    
    def _ensure_data_source(self):
        """Ensure HubSpot data source is registered"""
        with get_db_session() as db:
            existing = db.query(DataSource).filter(DataSource.name == 'hubspot').first()
            
            if not existing:
                data_source = DataSource(
                    name='hubspot',
                    type='crm',
                    status='active',
                    connection_config={
                        'api_version': 'v3',
                        'base_url': self.base_url
                    },
                    sync_frequency='daily'
                )
                db.add(data_source)
                db.commit()
                logger.info("Registered HubSpot data source")


# Convenience functions
async def sync_hubspot_data(api_key: str, start_date: str, end_date: str) -> Dict[str, int]:
    """
    Sync HubSpot data for the given period
    
    Args:
        api_key: HubSpot API key
        start_date: YYYY-MM-DD format
        end_date: YYYY-MM-DD format
        
    Returns:
        Dictionary with sync statistics
    """
    async with HubSpotIntegration(api_key) as hs:
        # Sync deals, companies, and campaigns
        deal_stats = await hs.sync_deals(start_date, end_date)
        company_stats = await hs.sync_companies(start_date, end_date)
        campaign_stats = await hs.sync_marketing_campaigns(start_date, end_date)
        
        return {
            'deals': deal_stats.get('deals', 0),
            'companies': company_stats.get('companies', 0),
            'campaigns': campaign_stats.get('campaigns', 0),
            'total_records': (deal_stats.get('deals', 0) + 
                            company_stats.get('companies', 0) + 
                            campaign_stats.get('campaigns', 0))
        }

async def get_marketing_attribution_analysis(api_key: str, start_date: str, end_date: str) -> Dict[str, Any]:
    """Get marketing attribution analysis"""
    async with HubSpotIntegration(api_key) as hs:
        return await hs.get_sales_attribution_metrics(start_date, end_date)

async def get_marketing_revenue_correlation(api_key: str, start_date: str, end_date: str) -> Dict[str, Any]:
    """Get marketing to revenue correlation analysis"""
    async with HubSpotIntegration(api_key) as hs:
        return await hs.correlate_marketing_to_revenue(start_date, end_date)


if __name__ == "__main__":
    # Example usage
    import asyncio
    import os
    
    async def main():
        api_key = os.getenv("HUBSPOT_API_KEY")
        
        if not api_key:
            print("HUBSPOT_API_KEY not configured in environment variables")
            return
        
        # Sync last 30 days
        end_date = datetime.now().date().isoformat()
        start_date = (datetime.now().date() - timedelta(days=30)).isoformat()
        
        print(f"Starting HubSpot sync for {start_date} to {end_date}")
        
        try:
            stats = await sync_hubspot_data(api_key, start_date, end_date)
            print(f"Sync completed: {stats}")
            
            # Get attribution analysis
            attribution = await get_marketing_attribution_analysis(api_key, start_date, end_date)
            print(f"Attribution analysis: {len(attribution['attribution_sources'])} sources found")
            
            # Get correlation analysis
            correlation = await get_marketing_revenue_correlation(api_key, start_date, end_date)
            print(f"Marketing correlation: {correlation['summary']['company_match_rate']:.1f}% match rate")
            
        except Exception as e:
            print(f"HubSpot sync failed: {e}")
    
    asyncio.run(main())