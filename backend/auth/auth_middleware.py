"""
Auth0 authentication middleware for FastAPI
Validates JWT tokens and extracts workspace context
"""

import os
import logging
from typing import Optional, Dict, Any
from functools import wraps

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient

logger = logging.getLogger(__name__)

# Auth0 configuration from environment
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "finwave.auth0.com")
AUTH0_API_AUDIENCE = os.getenv("AUTH0_API_AUDIENCE", "https://api.finwave.io")
AUTH0_ALGORITHMS = ["RS256"]

# Initialize JWKS client for token validation
jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
jwks_client = PyJWKClient(jwks_url)

# Security scheme for Swagger UI
security = HTTPBearer()

class AuthError(Exception):
    """Custom auth exception"""
    def __init__(self, error: str, status_code: int):
        self.error = error
        self.status_code = status_code

def validate_token(token: str) -> Dict[str, Any]:
    """
    Validate Auth0 JWT token and return claims
    """
    try:
        # Get signing key from JWKS
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # Decode and validate token
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=AUTH0_ALGORITHMS,
            audience=AUTH0_API_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/"
        )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise AuthError("Token has expired", 401)
    except jwt.InvalidTokenError as e:
        raise AuthError(f"Invalid token: {str(e)}", 401)
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise AuthError("Unable to validate token", 401)

def get_workspace_from_token(payload: Dict[str, Any]) -> Optional[str]:
    """
    Extract workspace ID from token claims
    
    Auth0 custom claims format:
    - namespace/workspace_id
    - namespace/permissions
    """
    # Check custom namespace claims
    namespace = "https://finwave.io"
    workspace_claim = f"{namespace}/workspace_id"
    
    if workspace_claim in payload:
        return payload[workspace_claim]
    
    # Fallback to organization ID if using Auth0 Organizations
    if "org_id" in payload:
        return payload["org_id"]
    
    # For development/testing, check metadata
    if "app_metadata" in payload and "workspace_id" in payload["app_metadata"]:
        return payload["app_metadata"]["workspace_id"]
    
    return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user
    """
    token = credentials.credentials
    
    try:
        payload = validate_token(token)
        
        # Extract workspace
        workspace_id = get_workspace_from_token(payload)
        if not workspace_id:
            raise HTTPException(
                status_code=403,
                detail="No workspace associated with this user"
            )
        
        # Build user context
        user_context = {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "workspace_id": workspace_id,
            "permissions": payload.get(f"https://finwave.io/permissions", []),
            "token_payload": payload
        }
        
        return user_context
        
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.error)

async def require_workspace(
    request: Request,
    user: Dict[str, Any] = Depends(get_current_user)
) -> str:
    """
    Dependency that ensures workspace_id in path matches user's workspace
    """
    # Extract workspace_id from path
    path_parts = request.url.path.split("/")
    
    # Look for workspace_id in path (e.g., /api/workspaces/{workspace_id}/...)
    workspace_idx = None
    for i, part in enumerate(path_parts):
        if part == "workspaces" and i + 1 < len(path_parts):
            workspace_idx = i + 1
            break
    
    if workspace_idx is None:
        # No workspace in path, use user's default
        return user["workspace_id"]
    
    path_workspace = path_parts[workspace_idx]
    
    # Verify user has access to this workspace
    if path_workspace != user["workspace_id"]:
        # In future, check if user has access to multiple workspaces
        raise HTTPException(
            status_code=403,
            detail=f"Access denied to workspace {path_workspace}"
        )
    
    return path_workspace

def require_permission(permission: str):
    """
    Decorator to require specific permission
    """
    async def permission_checker(user: Dict[str, Any] = Depends(get_current_user)):
        user_permissions = user.get("permissions", [])
        
        if permission not in user_permissions and "admin" not in user_permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Permission '{permission}' required"
            )
        
        return user
    
    return permission_checker

# Convenience dependencies
require_admin = require_permission("admin")
require_write = require_permission("write")
require_read = require_permission("read")

# Development mode bypass (NEVER use in production)
BYPASS_AUTH = os.getenv("BYPASS_AUTH", "false").lower() == "true"

async def get_current_user_dev(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    Development mode auth bypass
    """
    if BYPASS_AUTH:
        logger.warning("AUTH BYPASSED - Development mode only!")
        return {
            "user_id": "dev-user",
            "email": "dev@finwave.io",
            "workspace_id": "demo-corp",
            "permissions": ["admin", "read", "write"]
        }
    
    # Fall back to real auth
    return await get_current_user(credentials)

# Use dev version if bypass is enabled
if BYPASS_AUTH:
    get_current_user = get_current_user_dev