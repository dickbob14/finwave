#!/usr/bin/env python3
"""
Test QuickBooks API connectivity and diagnose issues
"""
import os
import sys
import logging
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_quickbooks_connection():
    """Test QuickBooks API connection with detailed debugging"""
    
    # Import required modules
    from core.database import get_db_session
    from models.integration import IntegrationCredential
    from integrations.quickbooks.client import QuickBooksClient
    
    workspace_id = "default"  # or "demo"
    
    with get_db_session() as session:
        # Get QuickBooks integration
        integration = session.query(IntegrationCredential).filter_by(
            workspace_id=workspace_id,
            source="quickbooks"
        ).first()
        
        if not integration:
            logger.error(f"No QuickBooks integration found for workspace {workspace_id}")
            return
        
        logger.info(f"Integration status: {integration.status}")
        logger.info(f"Last synced: {integration.last_synced_at}")
        logger.info(f"Token expires at: {integration.expires_at}")
        
        # Check metadata - THIS IS THE KEY ISSUE
        metadata = integration.integration_metadata  # Not integration.metadata!
        logger.info(f"Metadata: {metadata}")
        
        realm_id = metadata.get('realm_id') if metadata else None
        logger.info(f"Realm ID: {realm_id}")
        
        if not realm_id:
            logger.error("NO REALM ID FOUND! This is why API calls fail!")
            return
        
        # Get OAuth credentials
        from core.oauth_config import get_oauth_credentials
        credentials = get_oauth_credentials(workspace_id, 'quickbooks')
        if not credentials:
            logger.error("OAuth credentials not configured")
            return
        
        client_id, client_secret = credentials
        
        # Initialize client
        client = QuickBooksClient(
            client_id=client_id,
            client_secret=client_secret,
            company_id=realm_id  # This is critical!
        )
        
        # Set tokens
        client.access_token = integration.access_token
        client.refresh_token_value = integration.refresh_token
        client.token_expiry = integration.expires_at or datetime.now()
        
        # Log the request URL that will be used
        test_endpoint = "companyinfo/" + realm_id
        expected_url = f"{client.base_url}/{realm_id}/{test_endpoint}"
        logger.info(f"Will request: {expected_url}")
        
        # Test API call
        try:
            logger.info("Making test API call to QuickBooks...")
            # Try a simple company info request
            response = client._make_request(f"companyinfo/{realm_id}")
            logger.info(f"Success! Company info: {response}")
            
            # Try to get some accounts
            logger.info("\nTrying to fetch accounts...")
            accounts = client.get_accounts()
            logger.info(f"Found {len(accounts)} accounts")
            if accounts:
                logger.info(f"First account: {accounts[0]}")
                
        except Exception as e:
            logger.error(f"API call failed: {type(e).__name__}: {e}")
            
            # If it's a 401, try refreshing token
            if "401" in str(e):
                logger.info("Attempting token refresh...")
                try:
                    client.refresh_token()
                    logger.info("Token refreshed successfully! Retrying...")
                    
                    # Update tokens in database
                    integration.access_token = client.access_token
                    integration.refresh_token = client.refresh_token_value
                    integration.expires_at = client.token_expiry
                    session.commit()
                    
                    # Retry the request
                    response = client._make_request(f"companyinfo/{realm_id}")
                    logger.info(f"Success after refresh! Company info: {response}")
                    
                except Exception as refresh_error:
                    logger.error(f"Token refresh failed: {refresh_error}")

if __name__ == "__main__":
    test_quickbooks_connection()