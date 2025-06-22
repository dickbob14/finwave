"""
Unified OAuth callback and integration management routes
"""

import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Depends, Query, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from auth import get_current_user, require_workspace
from core.crypto import create_oauth_state, verify_oauth_state
from models.integration import (
    IntegrationSource, IntegrationStatus, IntegrationCredential,
    create_integration, get_integration, update_integration_tokens,
    list_workspace_integrations
)
from integrations.quickbooks.client import QuickBooksClient
from integrations.crm.client import create_crm_client
from integrations.payroll.client import create_payroll_client
from scheduler.sync_jobs import enqueue_initial_sync

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/oauth", tags=["oauth"])

# OAuth configuration per source
OAUTH_CONFIG = {
    IntegrationSource.QUICKBOOKS.value: {
        'auth_url': 'https://appcenter.intuit.com/connect/oauth2',
        'token_url': 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer',
        'client_id': os.getenv('QB_CLIENT_ID'),
        'client_secret': os.getenv('QB_CLIENT_SECRET'),
        'scope': 'com.intuit.quickbooks.accounting'
    },
    IntegrationSource.SALESFORCE.value: {
        'auth_url': 'https://login.salesforce.com/services/oauth2/authorize',
        'token_url': 'https://login.salesforce.com/services/oauth2/token',
        'client_id': os.getenv('SALESFORCE_CLIENT_ID'),
        'client_secret': os.getenv('SALESFORCE_CLIENT_SECRET'),
        'scope': 'api refresh_token'
    },
    IntegrationSource.HUBSPOT.value: {
        'auth_url': 'https://app.hubspot.com/oauth/authorize',
        'token_url': 'https://api.hubapi.com/oauth/v1/token',
        'client_id': os.getenv('HUBSPOT_CLIENT_ID'),
        'client_secret': os.getenv('HUBSPOT_CLIENT_SECRET'),
        'scope': 'crm.objects.contacts.read crm.objects.companies.read crm.objects.deals.read'
    },
    IntegrationSource.GUSTO.value: {
        'auth_url': 'https://api.gusto.com/oauth/authorize',
        'token_url': 'https://api.gusto.com/oauth/token',
        'client_id': os.getenv('GUSTO_CLIENT_ID'),
        'client_secret': os.getenv('GUSTO_CLIENT_SECRET'),
        'scope': 'public'
    }
}

# Response models
class IntegrationResponse(BaseModel):
    id: str
    source: str
    status: str
    connected_at: datetime
    last_synced_at: Optional[datetime]
    last_sync_error: Optional[str]
    metadata: Dict[str, Any]

class ConnectRequest(BaseModel):
    source: str
    workspace_id: str


@router.post("/connect/{source}")
async def initiate_oauth_flow(
    source: str,
    workspace_id: str = Depends(require_workspace),
    user: dict = Depends(get_current_user)
):
    """
    Initiate OAuth flow for a data source
    """
    try:
        # Validate source
        if source not in OAUTH_CONFIG:
            raise HTTPException(status_code=400, detail=f"Unsupported source: {source}")
        
        config = OAUTH_CONFIG[source]
        if not config['client_id']:
            raise HTTPException(
                status_code=500,
                detail=f"{source} OAuth not configured"
            )
        
        # Create or get integration record
        integration = get_integration(workspace_id, source)
        if not integration:
            integration = create_integration(
                workspace_id, source, user.get('email', user.get('sub'))
            )
        
        # Create secure state
        state = create_oauth_state(
            workspace_id,
            source,
            user.get('sub', user.get('email'))
        )
        
        # Build OAuth URL
        redirect_uri = f"{os.getenv('API_BASE_URL', 'http://localhost:8000')}/api/oauth/callback"
        
        params = {
            'client_id': config['client_id'],
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': config['scope'],
            'state': state
        }
        
        # Add source-specific parameters
        if source == IntegrationSource.QUICKBOOKS.value:
            params['access_type'] = 'offline'
        elif source == IntegrationSource.SALESFORCE.value:
            params['prompt'] = 'consent'
        elif source == IntegrationSource.HUBSPOT.value:
            params['optional_scope'] = 'crm.objects.line_items.read'
        
        auth_url = f"{config['auth_url']}?{urlencode(params)}"
        
        return {
            'auth_url': auth_url,
            'integration_id': integration.id
        }
        
    except Exception as e:
        logger.error(f"Error initiating OAuth for {source}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/callback")
async def oauth_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
    realmId: Optional[str] = Query(None),  # QuickBooks specific
    request: Request = None
):
    """
    Unified OAuth callback endpoint
    """
    try:
        # Check for errors
        if error:
            logger.error(f"OAuth error: {error} - {error_description}")
            return RedirectResponse(
                url=f"/connect/error?error={error}&description={error_description}"
            )
        
        # Verify state
        if not state or not code:
            return RedirectResponse(
                url="/connect/error?error=invalid_request"
            )
        
        state_data = verify_oauth_state(state)
        if not state_data:
            return RedirectResponse(
                url="/connect/error?error=invalid_state"
            )
        
        workspace_id = state_data['workspace_id']
        source = state_data['source']
        user_id = state_data['user_id']
        
        # Get OAuth config
        config = OAUTH_CONFIG.get(source)
        if not config:
            return RedirectResponse(
                url="/connect/error?error=invalid_source"
            )
        
        # Exchange code for tokens
        redirect_uri = f"{os.getenv('API_BASE_URL', 'http://localhost:8000')}/api/oauth/callback"
        
        token_data = await exchange_code_for_tokens(
            source, code, redirect_uri, config
        )
        
        if not token_data:
            return RedirectResponse(
                url="/connect/error?error=token_exchange_failed"
            )
        
        # Store tokens
        metadata = {
            'user_id': user_id,
            'connected_at': datetime.utcnow().isoformat()
        }
        
        # Add source-specific metadata
        if source == IntegrationSource.QUICKBOOKS.value and realmId:
            metadata['realm_id'] = realmId
        elif source == IntegrationSource.SALESFORCE.value:
            metadata['instance_url'] = token_data.get('instance_url')
        
        integration = update_integration_tokens(
            workspace_id,
            source,
            access_token=token_data['access_token'],
            refresh_token=token_data.get('refresh_token'),
            expires_in=token_data.get('expires_in'),
            metadata=metadata
        )
        
        # Enqueue initial sync
        enqueue_initial_sync(workspace_id, source)
        
        # Redirect to success page
        return RedirectResponse(
            url=f"/connect/success?source={source}"
        )
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return RedirectResponse(
            url=f"/connect/error?error=callback_failed&message={str(e)}"
        )


async def exchange_code_for_tokens(source: str, code: str, 
                                 redirect_uri: str, config: dict) -> Optional[dict]:
    """
    Exchange authorization code for tokens
    """
    import aiohttp
    import base64
    
    try:
        # Prepare token request
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri
        }
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Add authentication
        if source in [IntegrationSource.QUICKBOOKS.value, IntegrationSource.GUSTO.value]:
            # Basic auth
            auth_str = f"{config['client_id']}:{config['client_secret']}"
            auth_bytes = base64.b64encode(auth_str.encode()).decode()
            headers['Authorization'] = f"Basic {auth_bytes}"
        else:
            # Client credentials in body
            data['client_id'] = config['client_id']
            data['client_secret'] = config['client_secret']
        
        # Make token request
        async with aiohttp.ClientSession() as session:
            async with session.post(
                config['token_url'],
                data=data,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Token exchange failed: {error_text}")
                    return None
                
                return await response.json()
                
    except Exception as e:
        logger.error(f"Token exchange error for {source}: {e}")
        return None


@router.get("/integrations", response_model=list[IntegrationResponse])
async def list_integrations(
    workspace_id: str = Depends(require_workspace),
    user: dict = Depends(get_current_user)
):
    """
    List all integrations for a workspace
    """
    try:
        integrations = list_workspace_integrations(workspace_id)
        
        response = []
        for integration in integrations:
            # Sanitize metadata (remove sensitive data)
            safe_metadata = integration.metadata or {}
            safe_metadata.pop('access_token', None)
            safe_metadata.pop('refresh_token', None)
            
            response.append(IntegrationResponse(
                id=integration.id,
                source=integration.source,
                status=integration.status,
                connected_at=integration.created_at,
                last_synced_at=integration.last_synced_at,
                last_sync_error=integration.last_sync_error,
                metadata=safe_metadata
            ))
        
        return response
        
    except Exception as e:
        logger.error(f"Error listing integrations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/integrations/{source}")
async def disconnect_integration(
    source: str,
    workspace_id: str = Depends(require_workspace),
    user: dict = Depends(get_current_user)
):
    """
    Disconnect an integration
    """
    try:
        integration = get_integration(workspace_id, source)
        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")
        
        # Revoke tokens if possible
        if source == IntegrationSource.QUICKBOOKS.value:
            # QB token revocation
            pass
        elif source == IntegrationSource.SALESFORCE.value:
            # Salesforce token revocation
            pass
        
        # Update status
        from core.database import get_db_session
        with get_db_session() as db:
            db_integration = db.query(IntegrationCredential).filter_by(
                workspace_id=workspace_id,
                source=source
            ).first()
            
            if db_integration:
                db_integration.status = IntegrationStatus.EXPIRED.value
                db_integration.access_token = None
                db_integration.refresh_token = None
                db_integration.updated_at = datetime.utcnow()
                db.commit()
        
        return {"status": "disconnected", "source": source}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting {source}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/integrations/{source}/sync")
async def trigger_sync(
    source: str,
    workspace_id: str = Depends(require_workspace),
    user: dict = Depends(get_current_user)
):
    """
    Manually trigger a sync for an integration
    """
    try:
        integration = get_integration(workspace_id, source)
        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")
        
        if integration.status != IntegrationStatus.CONNECTED.value:
            raise HTTPException(
                status_code=400,
                detail=f"Integration is {integration.status}, cannot sync"
            )
        
        # Enqueue sync job
        job_id = enqueue_initial_sync(workspace_id, source, priority='high')
        
        return {
            'status': 'sync_queued',
            'source': source,
            'job_id': job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering sync for {source}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dev/quick_setup")
async def dev_quick_setup():
    """
    Development endpoint for quick demo setup
    Creates demo workspace and triggers sync
    """
    if os.getenv('QB_ENVIRONMENT') != 'sandbox':
        raise HTTPException(status_code=403, detail="Only available in sandbox mode")
    
    # Run seed script
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    
    try:
        from scripts.seed_demo import main as seed_main
        seed_main()
        return {"ok": True, "message": "Demo workspace created and QuickBooks sync triggered"}
    except Exception as e:
        logger.error(f"Quick setup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))