"""
OAuth configuration management
"""

import os
import json
from typing import Optional
from sqlalchemy import text

from core.database import get_db_session
from core.crypto import decrypt
from models.integration import IntegrationSource


def get_oauth_credentials(workspace_id: str, source: str) -> Optional[tuple[str, str]]:
    """
    Get OAuth credentials for a workspace/source combination
    Returns (client_id, client_secret) or None
    """
    # First check database for workspace-specific credentials
    try:
        with get_db_session() as db:
            result = db.execute(
                text("""
                SELECT client_id, client_secret_encrypted
                FROM oauth_app_configs
                WHERE workspace_id = :workspace_id AND source = :source
                """),
                {"workspace_id": workspace_id, "source": source}
            ).fetchone()
            
            if result and result[0] and result[1]:
                return result[0], decrypt(result[1])
    except Exception:
        # Table might not exist yet
        pass
    
    # Fall back to environment variables
    if source == IntegrationSource.QUICKBOOKS.value:
        client_id = os.getenv('QB_CLIENT_ID')
        client_secret = os.getenv('QB_CLIENT_SECRET')
    elif source == IntegrationSource.SALESFORCE.value:
        client_id = os.getenv('SALESFORCE_CLIENT_ID')
        client_secret = os.getenv('SALESFORCE_CLIENT_SECRET')
    elif source == IntegrationSource.HUBSPOT.value:
        client_id = os.getenv('HUBSPOT_CLIENT_ID')
        client_secret = os.getenv('HUBSPOT_CLIENT_SECRET')
    elif source == IntegrationSource.GUSTO.value:
        client_id = os.getenv('GUSTO_CLIENT_ID')
        client_secret = os.getenv('GUSTO_CLIENT_SECRET')
    else:
        return None
    
    if client_id and client_secret:
        return client_id, client_secret
    
    return None