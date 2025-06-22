"""
Workspace management API routes
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session

from core.database import get_db
from models.workspace import Workspace, WorkspaceCreate, WorkspaceResponse
from auth import get_current_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

@router.get("/current", response_model=WorkspaceResponse)
async def get_current_workspace(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's workspace details
    """
    workspace = db.query(Workspace).filter(
        Workspace.id == user["workspace_id"]
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    return WorkspaceResponse.from_orm(workspace)

@router.post("/", response_model=WorkspaceResponse)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new workspace (admin only)
    """
    # Check if workspace ID already exists
    existing = db.query(Workspace).filter(
        Workspace.id == workspace_data.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Workspace '{workspace_data.id}' already exists"
        )
    
    # Create workspace
    workspace = Workspace(
        id=workspace_data.id,
        name=workspace_data.name,
        qb_realm_id=workspace_data.qb_realm_id,
        crm_type=workspace_data.crm_type,
        billing_status=workspace_data.billing_status.value,
        settings=workspace_data.settings,
        trial_ends_at=datetime.utcnow() + timedelta(days=14)  # 14-day trial
    )
    
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    
    logger.info(f"Created workspace: {workspace.id}")
    
    return WorkspaceResponse.from_orm(workspace)

@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get workspace details by ID
    """
    # Check access
    if workspace_id != user["workspace_id"] and "admin" not in user.get("permissions", []):
        raise HTTPException(status_code=403, detail="Access denied")
    
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    return WorkspaceResponse.from_orm(workspace)

@router.patch("/{workspace_id}")
async def update_workspace(
    workspace_id: str,
    updates: dict,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update workspace settings
    """
    # Check access
    if workspace_id != user["workspace_id"] and "admin" not in user.get("permissions", []):
        raise HTTPException(status_code=403, detail="Access denied")
    
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Update allowed fields
    allowed_fields = ["name", "settings", "qb_realm_id", "crm_type", "crm_org_id"]
    
    for field, value in updates.items():
        if field in allowed_fields:
            setattr(workspace, field, value)
    
    workspace.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(workspace)
    
    return {"status": "updated", "workspace_id": workspace_id}

@router.post("/{workspace_id}/connect-quickbooks")
async def connect_quickbooks(
    workspace_id: str,
    auth_code: str,
    realm_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Connect QuickBooks to workspace using OAuth callback data
    """
    # Check access
    if workspace_id != user["workspace_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    try:
        # Exchange auth code for tokens
        from integrations.quickbooks.client import QuickBooksClient
        
        # This would normally exchange the auth code for tokens
        # For now, we'll just store the realm ID
        workspace.qb_realm_id = realm_id
        workspace.qb_last_sync = datetime.utcnow()
        
        db.commit()
        
        return {
            "status": "connected",
            "realm_id": realm_id,
            "workspace_id": workspace_id
        }
        
    except Exception as e:
        logger.error(f"QuickBooks connection failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{workspace_id}/connect-crm")
async def connect_crm(
    workspace_id: str,
    crm_type: str,
    auth_data: dict,  # Contains either auth_code or api_key
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Connect CRM (Salesforce/HubSpot) to workspace
    """
    # Check access
    if workspace_id != user["workspace_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    try:
        # Test CRM connection
        from integrations.crm.client import test_crm_connection
        
        if test_crm_connection(crm_type):
            workspace.crm_type = crm_type
            workspace.crm_org_id = auth_data.get("org_id", "default")
            workspace.crm_last_sync = datetime.utcnow()
            
            db.commit()
            
            return {
                "status": "connected",
                "crm_type": crm_type,
                "workspace_id": workspace_id
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to connect to CRM")
            
    except Exception as e:
        logger.error(f"CRM connection failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{workspace_id}/integrations")
async def get_integrations_status(
    workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get status of all integrations for a workspace
    """
    # Check access
    if workspace_id != user["workspace_id"] and "admin" not in user.get("permissions", []):
        raise HTTPException(status_code=403, detail="Access denied")
    
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    return {
        "quickbooks": {
            "connected": bool(workspace.qb_realm_id),
            "realm_id": workspace.qb_realm_id,
            "last_sync": workspace.qb_last_sync.isoformat() if workspace.qb_last_sync else None
        },
        "crm": {
            "connected": bool(workspace.crm_org_id),
            "type": workspace.crm_type,
            "org_id": workspace.crm_org_id,
            "last_sync": workspace.crm_last_sync.isoformat() if workspace.crm_last_sync else None
        },
        "features": workspace.features_enabled
    }

@router.get("/current/theme")
async def get_current_theme(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current workspace's theme settings
    """
    workspace = db.query(Workspace).filter(
        Workspace.id == user["workspace_id"]
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Get theme from workspace settings or return defaults
    theme = workspace.settings.get("theme", {}) if workspace.settings else {}
    
    # Return theme with defaults
    return {
        "company_name": theme.get("company_name", workspace.name),
        "logo_url": theme.get("logo_url", ""),
        "primary_color": theme.get("primary_color", "#4F46E5"),
        "secondary_color": theme.get("secondary_color", "#7C3AED")
    }

@router.put("/current/theme")
async def update_current_theme(
    theme_data: dict,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current workspace's theme settings
    """
    workspace = db.query(Workspace).filter(
        Workspace.id == user["workspace_id"]
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Update theme in settings
    if not workspace.settings:
        workspace.settings = {}
    
    workspace.settings["theme"] = {
        "company_name": theme_data.get("company_name", workspace.name),
        "logo_url": theme_data.get("logo_url", ""),
        "primary_color": theme_data.get("primary_color", "#4F46E5"),
        "secondary_color": theme_data.get("secondary_color", "#7C3AED")
    }
    
    # Also save to theme.json file for backward compatibility
    import json
    import os
    
    theme_file_path = os.path.join("static", f"theme_{workspace.id}.json")
    os.makedirs("static", exist_ok=True)
    
    full_theme = {
        "brand": {
            "company_name": workspace.settings["theme"]["company_name"],
            "logo_url": workspace.settings["theme"]["logo_url"],
            "contact_email": f"finance@{workspace.id}.com"
        },
        "colors": {
            "primary_color": workspace.settings["theme"]["primary_color"],
            "secondary_color": workspace.settings["theme"]["secondary_color"],
            "success_color": "#10B981",
            "warning_color": "#F59E0B",
            "danger_color": "#EF4444",
            "info_color": "#3B82F6",
            "text_primary": "#111827",
            "text_secondary": "#6B7280",
            "background_accent": "#F9FAFB",
            "background_hover": "#F3F4F6",
            "border_color": "#E5E7EB",
            "success_bg": "#F0FDF4",
            "warning_bg": "#FFFBEB",
            "danger_bg": "#FEF2F2",
            "info_bg": "#EFF6FF"
        },
        "charts": {
            "palette": [
                workspace.settings["theme"]["primary_color"],
                workspace.settings["theme"]["secondary_color"],
                "#EC4899", "#F59E0B", "#10B981", "#3B82F6"
            ],
            "font_family": "Inter",
            "grid_color": "#E5E7EB",
            "text_color": "#6B7280"
        },
        "pdf": {
            "page_size": "A4",
            "orientation": "portrait",
            "margins": {
                "top": "2.5cm",
                "right": "2cm",
                "bottom": "2.5cm",
                "left": "2cm"
            }
        }
    }
    
    with open(theme_file_path, 'w') as f:
        json.dump(full_theme, f, indent=2)
    
    workspace.updated_at = datetime.utcnow()
    db.commit()
    
    logger.info(f"Updated theme for workspace: {workspace.id}")
    
    return {"status": "success", "message": "Theme updated successfully"}

@router.post("/current/upload-logo")
async def upload_logo(
    logo: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a logo for the current workspace
    """
    import os
    import uuid
    from fastapi import UploadFile, File
    
    workspace = db.query(Workspace).filter(
        Workspace.id == user["workspace_id"]
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/svg+xml"]
    if logo.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Only PNG, JPG, and SVG are allowed."
        )
    
    # Validate file size (max 2MB)
    contents = await logo.read()
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 2MB."
        )
    
    # Save file
    file_extension = logo.filename.split(".")[-1]
    filename = f"{workspace.id}_logo_{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join("static", "logos", filename)
    
    os.makedirs(os.path.join("static", "logos"), exist_ok=True)
    
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Return the URL path
    logo_url = f"/static/logos/{filename}"
    
    return {"logo_url": logo_url, "filename": filename}

# Admin-only routes
@router.get("/", response_model=List[WorkspaceResponse])
async def list_workspaces(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    List all workspaces (admin only)
    """
    workspaces = db.query(Workspace).offset(skip).limit(limit).all()
    return [WorkspaceResponse.from_orm(ws) for ws in workspaces]