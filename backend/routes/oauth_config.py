"""
OAuth configuration management routes
Allows users to configure their own OAuth app credentials
"""

import logging
import os
import json
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from auth import get_current_user, require_workspace
from core.database import get_db_session
from core.crypto import encrypt, decrypt
from models.integration import IntegrationSource

logger = logging.getLogger(__name__)

router = APIRouter(tags=["oauth-config"])

class OAuthConfig(BaseModel):
    """OAuth app configuration"""
    source: str
    client_id: str
    client_secret: str
    environment: Optional[str] = "production"
    additional_settings: Optional[Dict[str, Any]] = {}

class OAuthConfigResponse(BaseModel):
    """OAuth config response (without secrets)"""
    source: str
    client_id: str
    is_configured: bool
    environment: str
    last_updated: Optional[datetime]

# Store OAuth configs in database
class OAuthAppConfig:
    """Database model for OAuth app configurations"""
    __tablename__ = "oauth_app_configs"
    
    def __init__(self, workspace_id: str, source: str):
        self.workspace_id = workspace_id
        self.source = source
        self.client_id = None
        self.client_secret_encrypted = None
        self.environment = "production"
        self.settings = {}
        self.updated_at = datetime.utcnow()

@router.post("/{workspace_id}/oauth/config/configure")
async def configure_oauth_app(
    workspace_id: str,
    config: OAuthConfig,
    user: dict = Depends(get_current_user)
):
    """
    Configure OAuth app credentials for a workspace
    """
    try:
        # Verify user has access to this workspace
        if workspace_id != user.get('workspace_id'):
            raise HTTPException(status_code=403, detail="Access denied to workspace")
        # Validate source
        if config.source not in [s.value for s in IntegrationSource]:
            raise HTTPException(status_code=400, detail=f"Invalid source: {config.source}")
        
        # Store configuration
        from sqlalchemy import text
        
        with get_db_session() as db:
            # Check if config exists
            result = db.execute(
                text("""
                SELECT COUNT(*) FROM oauth_app_configs 
                WHERE workspace_id = :workspace_id AND source = :source
                """),
                {"workspace_id": workspace_id, "source": config.source}
            ).fetchone()
            
            if result[0] > 0:
                # Update existing
                db.execute(
                    text("""
                    UPDATE oauth_app_configs 
                    SET client_id = :client_id,
                        client_secret_encrypted = :secret,
                        environment = :env,
                        settings = :settings,
                        updated_at = :updated_at,
                        updated_by = :user
                    WHERE workspace_id = :workspace_id AND source = :source
                    """),
                    {
                        "workspace_id": workspace_id,
                        "source": config.source,
                        "client_id": config.client_id,
                        "secret": encrypt(config.client_secret),
                        "env": config.environment,
                        "settings": json.dumps(config.additional_settings),
                        "updated_at": datetime.utcnow(),
                        "user": user.get('email', user.get('sub'))
                    }
                )
            else:
                # Insert new
                db.execute(
                    text("""
                    INSERT INTO oauth_app_configs 
                    (workspace_id, source, client_id, client_secret_encrypted, 
                     environment, settings, created_at, updated_at, created_by)
                    VALUES 
                    (:workspace_id, :source, :client_id, :secret, 
                     :env, :settings, :created_at, :updated_at, :user)
                    """),
                    {
                        "workspace_id": workspace_id,
                        "source": config.source,
                        "client_id": config.client_id,
                        "secret": encrypt(config.client_secret),
                        "env": config.environment,
                        "settings": json.dumps(config.additional_settings),
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "user": user.get('email', user.get('sub'))
                    }
                )
            
            db.commit()
        
        logger.info(f"OAuth config saved for {config.source} in workspace {workspace_id}")
        
        return {
            "status": "configured",
            "source": config.source,
            "message": f"OAuth credentials configured for {config.source}"
        }
        
    except Exception as e:
        logger.error(f"Error configuring OAuth for {config.source}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{workspace_id}/oauth/config/list", response_model=list[OAuthConfigResponse])
async def list_oauth_configs(
    workspace_id: str,
    user: dict = Depends(get_current_user)
):
    """
    List all OAuth configurations for a workspace
    """
    try:
        # Verify user has access to this workspace
        if workspace_id != user.get('workspace_id'):
            raise HTTPException(status_code=403, detail="Access denied to workspace")
        configs = []
        
        # Get configurations from database
        with get_db_session() as db:
            results = db.execute(
                text("""
                SELECT source, client_id, environment, updated_at
                FROM oauth_app_configs
                WHERE workspace_id = :workspace_id
                ORDER BY source
                """),
                {"workspace_id": workspace_id}
            ).fetchall()
            
            for row in results:
                configs.append(OAuthConfigResponse(
                    source=row[0],
                    client_id=row[1],
                    is_configured=True,
                    environment=row[2],
                    last_updated=row[3]
                ))
        
        # Add unconfigured sources
        configured_sources = {c.source for c in configs}
        for source in IntegrationSource:
            if source.value not in configured_sources:
                # Check if using environment variables
                env_client_id = None
                if source == IntegrationSource.QUICKBOOKS:
                    env_client_id = os.getenv('QB_CLIENT_ID')
                elif source == IntegrationSource.SALESFORCE:
                    env_client_id = os.getenv('SALESFORCE_CLIENT_ID')
                elif source == IntegrationSource.HUBSPOT:
                    env_client_id = os.getenv('HUBSPOT_CLIENT_ID')
                elif source == IntegrationSource.GUSTO:
                    env_client_id = os.getenv('GUSTO_CLIENT_ID')
                
                configs.append(OAuthConfigResponse(
                    source=source.value,
                    client_id=env_client_id[:10] + "..." if env_client_id else "",
                    is_configured=bool(env_client_id),
                    environment="env_variable" if env_client_id else "not_configured",
                    last_updated=None
                ))
        
        return configs
        
    except Exception as e:
        logger.error(f"Error listing OAuth configs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{workspace_id}/oauth/config/{source}")
async def delete_oauth_config(
    workspace_id: str,
    source: str,
    user: dict = Depends(get_current_user)
):
    """
    Delete OAuth configuration for a source
    """
    try:
        # Verify user has access to this workspace
        if workspace_id != user.get('workspace_id'):
            raise HTTPException(status_code=403, detail="Access denied to workspace")
        with get_db_session() as db:
            result = db.execute(
                text("""
                DELETE FROM oauth_app_configs
                WHERE workspace_id = :workspace_id AND source = :source
                """),
                {"workspace_id": workspace_id, "source": source}
            )
            db.commit()
            
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Configuration not found")
        
        return {"status": "deleted", "source": source}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting OAuth config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def get_oauth_credentials(workspace_id: str, source: str) -> Optional[tuple[str, str]]:
    """
    Get OAuth credentials for a workspace/source combination
    Returns (client_id, client_secret) or None
    """
    # First check database
    with get_db_session() as db:
        result = db.execute(
            text("""
            SELECT client_id, client_secret_encrypted
            FROM oauth_app_configs
            WHERE workspace_id = :workspace_id AND source = :source
            """),
            {"workspace_id": workspace_id, "source": source}
        ).fetchone()
        
        if result:
            return result[0], decrypt(result[1])
    
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