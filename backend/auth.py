"""
Authentication module for FinWave
Supports BYPASS_AUTH for demo mode
"""

import os
from typing import Optional, Dict
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict:
    """
    Get current user from JWT token or bypass in demo mode
    """
    if os.getenv("BYPASS_AUTH", "false").lower() == "true":
        # Demo mode - return a mock user
        return {
            "sub": "demo-user",
            "email": "demo@finwave.io",
            "workspace_id": "default"
        }
    
    # In production, you would verify the JWT token here
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    # For now, just return a mock user based on the token
    return {
        "sub": "user-123",
        "email": "user@example.com",
        "workspace_id": "default"
    }

def require_workspace(workspace_id: str, user: Dict = Depends(get_current_user)) -> str:
    """
    Verify user has access to the requested workspace
    Returns the workspace_id if access is granted
    """
    if os.getenv("BYPASS_AUTH", "false").lower() == "true":
        return workspace_id
    
    if user.get("workspace_id") != workspace_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied to workspace"
        )
    
    return workspace_id