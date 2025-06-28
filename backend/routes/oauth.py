"""
Unified OAuth callback and integration management routes
"""

import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import RedirectResponse, Response
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
from core.oauth_config import get_oauth_credentials

logger = logging.getLogger(__name__)

router = APIRouter(tags=["oauth"])

# Response model for integration list
class IntegrationResponse(BaseModel):
    id: str
    source: str
    status: str
    connected_at: datetime
    last_synced_at: Optional[datetime] = None
    last_sync_error: Optional[str] = None
    metadata: Dict[str, Any] = {}

# OAuth configuration per source (URLs and scopes only)
OAUTH_CONFIG = {
    IntegrationSource.QUICKBOOKS.value: {
        'auth_url': 'https://appcenter.intuit.com/connect/oauth2',
        'token_url': 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer',
        'scope': 'com.intuit.quickbooks.accounting'
    },
    IntegrationSource.SALESFORCE.value: {
        'auth_url': 'https://login.salesforce.com/services/oauth2/authorize',
        'token_url': 'https://login.salesforce.com/services/oauth2/token',
        'scope': 'api refresh_token'
    },
    IntegrationSource.HUBSPOT.value: {
        'auth_url': 'https://app.hubspot.com/oauth/authorize',
        'token_url': 'https://api.hubapi.com/oauth/v1/token',
        'scope': 'crm.objects.contacts.read crm.objects.companies.read crm.objects.deals.read'
    },
    IntegrationSource.GUSTO.value: {
        'auth_url': 'https://api.gusto.com/oauth/authorize',
        'token_url': 'https://api.gusto.com/oauth/token',
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


@router.post("/{workspace_id}/oauth/connect/{source}")
async def initiate_oauth_flow(
    workspace_id: str,
    source: str,
    user: dict = Depends(get_current_user)
):
    """
    Initiate OAuth flow for a data source
    """
    try:
        # Verify user has access to this workspace (skip in demo mode)
        if os.getenv("BYPASS_AUTH", "false").lower() != "true":
            if workspace_id != user.get('workspace_id'):
                raise HTTPException(status_code=403, detail="Access denied to workspace")
        # Validate source
        if source not in OAUTH_CONFIG:
            raise HTTPException(status_code=400, detail=f"Unsupported source: {source}")
        
        config = OAUTH_CONFIG[source]
        
        # Get credentials for this workspace
        credentials = get_oauth_credentials(workspace_id, source)
        if not credentials:
            raise HTTPException(
                status_code=400,
                detail=f"{source} OAuth not configured. Please configure OAuth credentials first."
            )
        
        client_id, client_secret = credentials
        
        # Create or get integration record
        from core.database import get_db_session
        with get_db_session() as db:
            from models.integration import IntegrationCredential, IntegrationStatus
            integration = db.query(IntegrationCredential).filter_by(
                workspace_id=workspace_id,
                source=source
            ).first()
            
            if not integration:
                integration = IntegrationCredential(
                    workspace_id=workspace_id,
                    source=source,
                    status=IntegrationStatus.PENDING.value,
                    connected_by=user.get('email', user.get('sub'))
                )
                db.add(integration)
                db.commit()
            
            integration_id = integration.id
        
        # Create secure state
        state = create_oauth_state(
            workspace_id,
            source,
            user.get('sub', user.get('email'))
        )
        
        # Build OAuth URL
        redirect_uri = f"{os.getenv('API_BASE_URL', 'http://localhost:8000')}/api/oauth/callback"
        
        params = {
            'client_id': client_id,
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
            'integration_id': integration_id
        }
        
    except Exception as e:
        logger.error(f"Error initiating OAuth for {source}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/oauth/callback")
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
            error_html = f"""
            <html>
            <head>
                <title>Connection Failed</title>
                <script>
                    setTimeout(function() {{
                        window.location.href = "http://localhost:3000/settings?oauth_error={error}&description={error_description or ''}";
                    }}, 2000);
                </script>
            </head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h2>❌ Connection Failed</h2>
                <p>Error: {error}</p>
                <p>{error_description or ''}</p>
                <p style="color: #666;">Redirecting back to FinWave...</p>
            </body>
            </html>
            """
            return Response(content=error_html, media_type="text/html")
        
        # Verify state
        if not state or not code:
            return RedirectResponse(
                url="http://localhost:3000/settings?oauth_error=invalid_request"
            )
        
        state_data = verify_oauth_state(state)
        if not state_data:
            return RedirectResponse(
                url="http://localhost:3000/settings?oauth_error=invalid_state"
            )
        
        workspace_id = state_data['workspace_id']
        source = state_data['source']
        user_id = state_data['user_id']
        
        # Get OAuth config
        config = OAUTH_CONFIG.get(source)
        if not config:
            return RedirectResponse(
                url="http://localhost:3000/settings?oauth_error=invalid_source"
            )
        
        # Get credentials for this workspace
        credentials = get_oauth_credentials(workspace_id, source)
        if not credentials:
            return RedirectResponse(
                url="http://localhost:3000/settings?oauth_error=oauth_not_configured"
            )
        
        # Exchange code for tokens
        redirect_uri = f"{os.getenv('API_BASE_URL', 'http://localhost:8000')}/api/oauth/callback"
        
        token_data = await exchange_code_for_tokens(
            source, code, redirect_uri, config, credentials
        )
        
        if not token_data:
            return RedirectResponse(
                url="http://localhost:3000/settings?oauth_error=token_exchange_failed"
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
        try:
            # Use our working sync service instead of broken job queue
            if source == 'quickbooks':
                from finwave_sync_service import FinWaveSyncService
                import threading
                
                def run_sync():
                    service = FinWaveSyncService(workspace_id)
                    result = service.run_sync()
                    logger.info(f"Initial sync completed: {result}")
                
                thread = threading.Thread(target=run_sync)
                thread.start()
                logger.info("Initial sync started in background")
            else:
                enqueue_initial_sync(workspace_id, source)
        except Exception as e:
            logger.error(f"Failed to start initial sync: {e}")
        
        # Redirect to success page (close tab and return to connections)
        success_html = f"""
        <html>
        <head>
            <title>Connection Successful</title>
            <script>
                // Try to close the tab/window
                window.close();
                // If it doesn't close, redirect to settings
                setTimeout(function() {{
                    window.location.href = "http://localhost:3000/settings?oauth_success=true&source={source}";
                }}, 1000);
            </script>
        </head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h2>✅ Successfully connected to {source.title()}!</h2>
            <p>You can close this tab and return to FinWave.</p>
            <p style="color: #666;">If this tab doesn't close automatically, <a href="http://localhost:3000/settings">click here</a>.</p>
        </body>
        </html>
        """
        return Response(content=success_html, media_type="text/html")
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return RedirectResponse(
            url=f"http://localhost:3000/settings?oauth_error=callback_failed&message={str(e)}"
        )


async def exchange_code_for_tokens(source: str, code: str, 
                                 redirect_uri: str, config: dict, 
                                 credentials: tuple[str, str]) -> Optional[dict]:
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
        client_id, client_secret = credentials
        
        if source in [IntegrationSource.QUICKBOOKS.value, IntegrationSource.GUSTO.value]:
            # Basic auth
            auth_str = f"{client_id}:{client_secret}"
            auth_bytes = base64.b64encode(auth_str.encode()).decode()
            headers['Authorization'] = f"Basic {auth_bytes}"
        else:
            # Client credentials in body
            data['client_id'] = client_id
            data['client_secret'] = client_secret
        
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


@router.get("/{workspace_id}/oauth/integrations", response_model=list[IntegrationResponse])
async def list_integrations(
    workspace_id: str,
    user: dict = Depends(get_current_user)
):
    """
    List all integrations for a workspace
    """
    try:
        # Verify user has access to this workspace (skip in demo mode)
        if os.getenv("BYPASS_AUTH", "false").lower() != "true":
            if workspace_id != user.get('workspace_id'):
                raise HTTPException(status_code=403, detail="Access denied to workspace")
        from core.database import get_db_session
        import json
        
        response = []
        with get_db_session() as db:
            integrations = db.query(IntegrationCredential).filter_by(
                workspace_id=workspace_id
            ).all()
            
            for integration in integrations:
                # Sanitize metadata (remove sensitive data)
                if integration.metadata:
                    try:
                        # Handle both dict and JSON string
                        if isinstance(integration.metadata, str):
                            safe_metadata = json.loads(integration.metadata)
                        elif isinstance(integration.metadata, dict):
                            safe_metadata = integration.metadata.copy()
                        else:
                            safe_metadata = {}
                    except:
                        safe_metadata = {}
                else:
                    safe_metadata = {}
                
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


@router.delete("/{workspace_id}/oauth/integrations/{source}")
async def disconnect_integration(
    workspace_id: str,
    source: str,
    user: dict = Depends(get_current_user)
):
    """
    Disconnect an integration
    """
    try:
        # Verify user has access to this workspace (skip in demo mode)
        if os.getenv("BYPASS_AUTH", "false").lower() != "true":
            if workspace_id != user.get('workspace_id'):
                raise HTTPException(status_code=403, detail="Access denied to workspace")
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


@router.post("/{workspace_id}/oauth/integrations/{source}/sync")
async def trigger_sync(
    workspace_id: str,
    source: str,
    user: dict = Depends(get_current_user)
):
    """
    Manually trigger a sync for an integration
    """
    try:
        # Verify user has access to this workspace (skip in demo mode)
        if os.getenv("BYPASS_AUTH", "false").lower() != "true":
            if workspace_id != user.get('workspace_id'):
                raise HTTPException(status_code=403, detail="Access denied to workspace")
        from core.database import get_db_session
        
        with get_db_session() as db:
            integration = db.query(IntegrationCredential).filter_by(
                workspace_id=workspace_id,
                source=source
            ).first()
            
            if not integration:
                raise HTTPException(status_code=404, detail="Integration not found")
            
            if integration.status != IntegrationStatus.CONNECTED.value:
                raise HTTPException(
                    status_code=400,
                    detail=f"Integration is {integration.status}, cannot sync"
                )
        
        # Run sync based on source
        if source == 'quickbooks':
            # Use our working sync service
            from finwave_sync_service import FinWaveSyncService
            service = FinWaveSyncService(workspace_id)
            result = service.run_sync()
            
            if result['status'] == 'success':
                job_id = f"sync_{source}_{datetime.utcnow().timestamp()}"
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Sync failed: {result.get('message')}"
                )
        else:
            # Use standard queue for other sources
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