"""
Integration manager for coordinating multiple data source syncs
Provides centralized control and orchestration for all external integrations
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

from sqlalchemy.orm import Session
from database import get_db_session
from models.financial import DataSource, IngestionHistory

from .salesforce_hook import sync_salesforce_data, get_sales_revenue_correlation
from .hubspot_hook import sync_hubspot_data, get_marketing_revenue_correlation
from .nue_hook import sync_nue_data, get_payroll_correlation

logger = logging.getLogger(__name__)

class IntegrationManager:
    """Centralized manager for all external data source integrations"""
    
    def __init__(self):
        """Initialize integration manager"""
        self.available_integrations = {
            'salesforce': {
                'sync_function': sync_salesforce_data,
                'correlation_function': get_sales_revenue_correlation,
                'required_env_vars': ['SALESFORCE_INSTANCE_URL', 'SALESFORCE_ACCESS_TOKEN', 
                                    'SALESFORCE_CLIENT_ID', 'SALESFORCE_CLIENT_SECRET']
            },
            'hubspot': {
                'sync_function': sync_hubspot_data,
                'correlation_function': get_marketing_revenue_correlation,
                'required_env_vars': ['HUBSPOT_API_KEY']
            },
            'nue': {
                'sync_function': sync_nue_data,
                'correlation_function': get_payroll_correlation,
                'required_env_vars': ['NUE_API_KEY']
            }
        }
    
    async def sync_all_active_sources(self, start_date: str, end_date: str, 
                                    parallel: bool = True) -> Dict[str, Any]:
        """
        Sync all active data sources
        
        Args:
            start_date: YYYY-MM-DD format
            end_date: YYYY-MM-DD format
            parallel: Whether to run syncs in parallel
            
        Returns:
            Dictionary with sync results for all sources
        """
        active_sources = self._get_active_sources()
        sync_results = {}
        
        if parallel:
            # Run all syncs in parallel
            tasks = []
            for source_name in active_sources:
                if source_name in self.available_integrations:
                    task = self._sync_single_source(source_name, start_date, end_date)
                    tasks.append((source_name, task))
            
            # Wait for all tasks to complete
            for source_name, task in tasks:
                try:
                    result = await task
                    sync_results[source_name] = {
                        'status': 'success',
                        'data': result,
                        'synced_at': datetime.now().isoformat()
                    }
                except Exception as e:
                    logger.error(f"Sync failed for {source_name}: {e}")
                    sync_results[source_name] = {
                        'status': 'failed',
                        'error': str(e),
                        'synced_at': datetime.now().isoformat()
                    }
        else:
            # Run syncs sequentially
            for source_name in active_sources:
                if source_name in self.available_integrations:
                    try:
                        result = await self._sync_single_source(source_name, start_date, end_date)
                        sync_results[source_name] = {
                            'status': 'success',
                            'data': result,
                            'synced_at': datetime.now().isoformat()
                        }
                    except Exception as e:
                        logger.error(f"Sync failed for {source_name}: {e}")
                        sync_results[source_name] = {
                            'status': 'failed',
                            'error': str(e),
                            'synced_at': datetime.now().isoformat()
                        }
        
        # Update last sync timestamps
        self._update_sync_timestamps(sync_results)
        
        return {
            'sync_results': sync_results,
            'total_sources': len(active_sources),
            'successful_syncs': len([r for r in sync_results.values() if r['status'] == 'success']),
            'failed_syncs': len([r for r in sync_results.values() if r['status'] == 'failed']),
            'period': {'start_date': start_date, 'end_date': end_date}
        }
    
    async def get_comprehensive_correlation_analysis(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Get correlation analysis from all active sources
        
        Args:
            start_date: YYYY-MM-DD format
            end_date: YYYY-MM-DD format
            
        Returns:
            Dictionary with correlation data from all sources
        """
        active_sources = self._get_active_sources()
        correlation_results = {}
        
        # Run correlation analysis for each active source
        for source_name in active_sources:
            if source_name in self.available_integrations:
                try:
                    correlation_func = self.available_integrations[source_name]['correlation_function']
                    
                    # Get credentials for this source
                    credentials = self._get_source_credentials(source_name)
                    if not credentials:
                        logger.warning(f"No credentials found for {source_name}, skipping correlation")
                        continue
                    
                    # Call correlation function with appropriate parameters
                    if source_name == 'salesforce':
                        result = await correlation_func(
                            credentials['instance_url'],
                            credentials['access_token'],
                            credentials['client_id'],
                            credentials['client_secret'],
                            start_date,
                            end_date
                        )
                    elif source_name == 'hubspot':
                        result = await correlation_func(
                            credentials['api_key'],
                            start_date,
                            end_date
                        )
                    elif source_name == 'nue':
                        result = await correlation_func(
                            credentials['api_key'],
                            start_date,
                            end_date
                        )
                    
                    correlation_results[source_name] = {
                        'status': 'success',
                        'data': result,
                        'analyzed_at': datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    logger.error(f"Correlation analysis failed for {source_name}: {e}")
                    correlation_results[source_name] = {
                        'status': 'failed',
                        'error': str(e),
                        'analyzed_at': datetime.now().isoformat()
                    }
        
        # Generate comprehensive insights
        insights = self._generate_cross_platform_insights(correlation_results)
        
        return {
            'correlation_results': correlation_results,
            'cross_platform_insights': insights,
            'sources_analyzed': len(correlation_results),
            'period': {'start_date': start_date, 'end_date': end_date}
        }
    
    async def sync_specific_source(self, source_name: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Sync a specific data source
        
        Args:
            source_name: Name of the source to sync
            start_date: YYYY-MM-DD format
            end_date: YYYY-MM-DD format
            
        Returns:
            Dictionary with sync results
        """
        if source_name not in self.available_integrations:
            raise ValueError(f"Unknown integration: {source_name}")
        
        try:
            result = await self._sync_single_source(source_name, start_date, end_date)
            
            # Update sync timestamp
            self._update_sync_timestamps({source_name: {'status': 'success', 'data': result}})
            
            return {
                'source': source_name,
                'status': 'success',
                'data': result,
                'synced_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Sync failed for {source_name}: {e}")
            return {
                'source': source_name,
                'status': 'failed',
                'error': str(e),
                'synced_at': datetime.now().isoformat()
            }
    
    def get_integration_status(self) -> Dict[str, Any]:
        """
        Get status of all integrations
        
        Returns:
            Dictionary with integration status information
        """
        with get_db_session() as db:
            data_sources = db.query(DataSource).all()
            
            status_info = {}
            for source in data_sources:
                # Check if credentials are available
                credentials_available = bool(self._get_source_credentials(source.name))
                
                # Get last sync info
                last_sync = db.query(IngestionHistory).filter(
                    IngestionHistory.source == source.name
                ).order_by(IngestionHistory.ingested_at.desc()).first()
                
                status_info[source.name] = {
                    'type': source.type,
                    'status': source.status,
                    'credentials_configured': credentials_available,
                    'sync_frequency': source.sync_frequency,
                    'last_sync': last_sync.ingested_at.isoformat() if last_sync else None,
                    'last_sync_status': last_sync.status if last_sync else None,
                    'last_sync_records': last_sync.records_count if last_sync else 0,
                    'connection_config': source.connection_config or {}
                }
        
        return {
            'integrations': status_info,
            'total_configured': len([s for s in status_info.values() if s['credentials_configured']]),
            'total_active': len([s for s in status_info.values() if s['status'] == 'active']),
            'checked_at': datetime.now().isoformat()
        }
    
    def configure_integration(self, source_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Configure an integration with connection details
        
        Args:
            source_name: Name of the integration
            config: Configuration parameters
            
        Returns:
            Dictionary with configuration status
        """
        if source_name not in self.available_integrations:
            raise ValueError(f"Unknown integration: {source_name}")
        
        with get_db_session() as db:
            # Get or create data source
            data_source = db.query(DataSource).filter(DataSource.name == source_name).first()
            
            if not data_source:
                data_source = DataSource(
                    name=source_name,
                    type=config.get('type', 'external'),
                    status='inactive'
                )
                db.add(data_source)
            
            # Update configuration
            data_source.connection_config = config.get('connection_config', {})
            data_source.sync_frequency = config.get('sync_frequency', 'daily')
            data_source.status = config.get('status', 'active')
            
            db.commit()
            
            return {
                'source': source_name,
                'status': 'configured',
                'message': f"Integration {source_name} configured successfully"
            }
    
    async def _sync_single_source(self, source_name: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Sync a single data source"""
        sync_func = self.available_integrations[source_name]['sync_function']
        credentials = self._get_source_credentials(source_name)
        
        if not credentials:
            raise ValueError(f"No credentials configured for {source_name}")
        
        # Call sync function with appropriate parameters
        if source_name == 'salesforce':
            return await sync_func(
                credentials['instance_url'],
                credentials['access_token'],
                credentials['client_id'],
                credentials['client_secret'],
                start_date,
                end_date
            )
        elif source_name == 'hubspot':
            return await sync_func(
                credentials['api_key'],
                start_date,
                end_date
            )
        elif source_name == 'nue':
            return await sync_func(
                credentials['api_key'],
                start_date,
                end_date
            )
        else:
            raise ValueError(f"Unknown sync function for {source_name}")
    
    def _get_active_sources(self) -> List[str]:
        """Get list of active data sources"""
        with get_db_session() as db:
            active_sources = db.query(DataSource).filter(
                DataSource.status == 'active'
            ).all()
            
            return [source.name for source in active_sources]
    
    def _get_source_credentials(self, source_name: str) -> Optional[Dict[str, str]]:
        """Get credentials for a specific source from environment variables"""
        import os
        
        required_vars = self.available_integrations[source_name]['required_env_vars']
        credentials = {}
        
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                return None  # Missing required credential
            
            # Map env var names to credential keys
            if var == 'SALESFORCE_INSTANCE_URL':
                credentials['instance_url'] = value
            elif var == 'SALESFORCE_ACCESS_TOKEN':
                credentials['access_token'] = value
            elif var == 'SALESFORCE_CLIENT_ID':
                credentials['client_id'] = value
            elif var == 'SALESFORCE_CLIENT_SECRET':
                credentials['client_secret'] = value
            elif var == 'HUBSPOT_API_KEY':
                credentials['api_key'] = value
            elif var == 'NUE_API_KEY':
                credentials['api_key'] = value
        
        return credentials if credentials else None
    
    def _update_sync_timestamps(self, sync_results: Dict[str, Any]):
        """Update last sync timestamps for data sources"""
        with get_db_session() as db:
            for source_name, result in sync_results.items():
                if result['status'] == 'success':
                    data_source = db.query(DataSource).filter(DataSource.name == source_name).first()
                    if data_source:
                        data_source.last_sync = datetime.now()
                        db.commit()
    
    def _generate_cross_platform_insights(self, correlation_results: Dict[str, Any]) -> List[str]:
        """Generate insights across multiple platform correlations"""
        insights = []
        
        successful_correlations = {
            name: result['data'] for name, result in correlation_results.items()
            if result['status'] == 'success'
        }
        
        if not successful_correlations:
            return ["No successful correlations to analyze"]
        
        # Analyze data quality across platforms
        match_rates = {}
        for platform, data in successful_correlations.items():
            if 'summary' in data and 'company_match_rate' in data['summary']:
                match_rates[platform] = data['summary']['company_match_rate']
        
        if match_rates:
            avg_match_rate = sum(match_rates.values()) / len(match_rates)
            if avg_match_rate > 80:
                insights.append(f"Excellent data integration quality with {avg_match_rate:.1f}% average customer matching across platforms.")
            elif avg_match_rate > 60:
                insights.append(f"Good data integration with {avg_match_rate:.1f}% average matching - opportunities for improvement in data standardization.")
            else:
                insights.append(f"Data integration challenges detected with {avg_match_rate:.1f}% average matching - recommend data cleansing initiative.")
        
        # Revenue attribution analysis
        if 'salesforce' in successful_correlations and 'hubspot' in successful_correlations:
            sf_revenue = successful_correlations['salesforce']['summary'].get('total_financial_revenue', 0)
            hs_revenue = successful_correlations['hubspot']['summary'].get('total_financial_revenue', 0)
            
            if sf_revenue > 0 and hs_revenue > 0:
                overlap_percentage = min(sf_revenue, hs_revenue) / max(sf_revenue, hs_revenue) * 100
                insights.append(f"Sales and marketing platforms show {overlap_percentage:.1f}% revenue overlap - validate attribution models.")
        
        # Cost correlation analysis
        if 'nue' in successful_correlations:
            nue_data = successful_correlations['nue']
            accuracy = nue_data['correlation'].get('accuracy_rate', 0)
            
            if accuracy > 95:
                insights.append("Excellent payroll data accuracy - compensation costs align closely with financial records.")
            elif accuracy > 85:
                insights.append("Good payroll alignment with minor variances - monitor for timing differences.")
            else:
                insights.append("Payroll data inconsistencies detected - investigate missing entries or timing issues.")
        
        return insights


# Convenience functions
async def sync_all_sources(start_date: str, end_date: str, parallel: bool = True) -> Dict[str, Any]:
    """
    Sync all active data sources
    
    Args:
        start_date: YYYY-MM-DD format
        end_date: YYYY-MM-DD format
        parallel: Whether to run syncs in parallel
        
    Returns:
        Dictionary with sync results
    """
    manager = IntegrationManager()
    return await manager.sync_all_active_sources(start_date, end_date, parallel)

async def get_all_correlations(start_date: str, end_date: str) -> Dict[str, Any]:
    """Get correlation analysis from all sources"""
    manager = IntegrationManager()
    return await manager.get_comprehensive_correlation_analysis(start_date, end_date)

def get_integration_health() -> Dict[str, Any]:
    """Get health status of all integrations"""
    manager = IntegrationManager()
    return manager.get_integration_status()


if __name__ == "__main__":
    # Example usage
    import asyncio
    import os
    
    async def main():
        manager = IntegrationManager()
        
        # Get integration status
        status = manager.get_integration_status()
        print(f"Integration Status: {status['total_active']}/{status['total_configured']} active")
        
        # Sync last 30 days for all sources
        end_date = datetime.now().date().isoformat()
        start_date = (datetime.now().date() - timedelta(days=30)).isoformat()
        
        print(f"Starting comprehensive sync for {start_date} to {end_date}")
        
        try:
            # Sync all sources
            sync_results = await manager.sync_all_active_sources(start_date, end_date)
            print(f"Sync completed: {sync_results['successful_syncs']}/{sync_results['total_sources']} successful")
            
            # Get correlation analysis
            correlations = await manager.get_comprehensive_correlation_analysis(start_date, end_date)
            print(f"Correlation analysis: {correlations['sources_analyzed']} sources analyzed")
            
            # Print insights
            for insight in correlations['cross_platform_insights']:
                print(f"Insight: {insight}")
                
        except Exception as e:
            print(f"Integration manager failed: {e}")
    
    asyncio.run(main())