"""
Workspace model for multi-tenant isolation
Each workspace represents a company with its own QB realm, CRM org, and data
"""

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from sqlalchemy import Column, String, DateTime, JSON, Boolean, Integer
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from core.database import Base

class BillingStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"

class Workspace(Base):
    """
    SQLAlchemy model for workspace storage
    """
    __tablename__ = "workspaces"
    
    id = Column(String, primary_key=True)  # e.g., "acme-corp"
    name = Column(String, nullable=False)  # e.g., "Acme Corporation"
    
    # QuickBooks connection
    qb_realm_id = Column(String, nullable=True)
    qb_company_name = Column(String, nullable=True)
    qb_refresh_token = Column(String, nullable=True)  # Encrypted in production
    qb_last_sync = Column(DateTime, nullable=True)
    
    # CRM connection
    crm_type = Column(String, nullable=True)  # "salesforce" or "hubspot"
    crm_org_id = Column(String, nullable=True)
    crm_refresh_token = Column(String, nullable=True)  # Encrypted in production
    crm_last_sync = Column(DateTime, nullable=True)
    
    # Billing & subscription
    billing_status = Column(String, default=BillingStatus.TRIAL.value)
    trial_ends_at = Column(DateTime, nullable=True)
    seats_allowed = Column(Integer, default=5)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    settings = Column(JSON, default={})  # Flexible settings storage
    
    # Feature flags
    features_enabled = Column(JSON, default={
        "insights": True,
        "pdf_export": True,
        "api_access": True,
        "custom_templates": False
    })
    
    # Relationships for financial data - commented out to avoid circular imports
    # financial_statements = relationship("FinancialStatement", back_populates="workspace", cascade="all, delete-orphan")
    # account_balances = relationship("AccountBalance", back_populates="workspace", cascade="all, delete-orphan")
    # transactions = relationship("Transaction", back_populates="workspace", cascade="all, delete-orphan")
    # customers = relationship("Customer", back_populates="workspace", cascade="all, delete-orphan")
    # vendors = relationship("Vendor", back_populates="workspace", cascade="all, delete-orphan")
    # kpi_metrics = relationship("KPIMetric", back_populates="workspace", cascade="all, delete-orphan")
    # sync_logs = relationship("SyncLog", back_populates="workspace", cascade="all, delete-orphan")

class WorkspaceCreate(BaseModel):
    """
    Pydantic model for workspace creation
    """
    id: str = Field(..., description="Unique workspace ID (slug format)")
    name: str = Field(..., description="Display name of the company")
    qb_realm_id: Optional[str] = None
    crm_type: Optional[str] = "salesforce"
    billing_status: BillingStatus = BillingStatus.TRIAL
    settings: Dict[str, Any] = {}

class WorkspaceResponse(BaseModel):
    """
    Pydantic model for API responses
    """
    id: str
    name: str
    qb_connected: bool
    crm_connected: bool
    crm_type: Optional[str]
    billing_status: BillingStatus
    seats_allowed: int
    created_at: datetime
    features_enabled: Dict[str, bool]
    
    class Config:
        orm_mode = True
    
    @classmethod
    def from_orm(cls, workspace: Workspace) -> "WorkspaceResponse":
        return cls(
            id=workspace.id,
            name=workspace.name,
            qb_connected=bool(workspace.qb_realm_id),
            crm_connected=bool(workspace.crm_org_id),
            crm_type=workspace.crm_type,
            billing_status=workspace.billing_status,
            seats_allowed=workspace.seats_allowed,
            created_at=workspace.created_at,
            features_enabled=workspace.features_enabled or {}
        )

class WorkspaceContext(BaseModel):
    """
    Context passed through requests after auth
    """
    workspace_id: str
    user_id: str
    user_email: str
    permissions: list[str] = []
    
    @property
    def is_admin(self) -> bool:
        return "admin" in self.permissions