"""
External data source integration hooks for CRM, sales, and other business systems
"""

from .salesforce_hook import SalesforceIntegration, sync_salesforce_data
from .hubspot_hook import HubSpotIntegration, sync_hubspot_data  
from .nue_hook import NueIntegration, sync_nue_data
from .integration_manager import IntegrationManager, sync_all_sources

__all__ = [
    'SalesforceIntegration',
    'sync_salesforce_data',
    'HubSpotIntegration', 
    'sync_hubspot_data',
    'NueIntegration',
    'sync_nue_data',
    'IntegrationManager',
    'sync_all_sources'
]