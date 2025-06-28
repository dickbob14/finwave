"""
Integration credential storage with encryption
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship

from core.database import Base
from core.crypto import encrypt, decrypt


class IntegrationSource(Enum):
    """Supported integration sources"""
    QUICKBOOKS = "quickbooks"
    SALESFORCE = "salesforce"
    HUBSPOT = "hubspot"
    GUSTO = "gusto"
    ADP = "adp"
    STRIPE = "stripe"
    GOOGLE_SHEETS = "google_sheets"


class IntegrationStatus(Enum):
    """Integration connection status"""
    PENDING = "pending"
    CONNECTED = "connected"
    ERROR = "error"
    EXPIRED = "expired"
    REFRESHING = "refreshing"


class IntegrationCredential(Base):
    """Encrypted storage for integration credentials"""
    __tablename__ = "integration_credentials"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: f"intg_{datetime.utcnow().timestamp()}")
    
    # Workspace relationship
    workspace_id = Column(String, nullable=False)
    # Note: Removed ForeignKey and relationship to avoid circular dependencies
    
    # Integration details
    source = Column(String, nullable=False)  # IntegrationSource enum value
    status = Column(String, nullable=False, default=IntegrationStatus.PENDING.value)
    
    # OAuth tokens (encrypted)
    access_token_encrypted = Column(Text, nullable=True)
    refresh_token_encrypted = Column(Text, nullable=True)
    
    # Token metadata
    expires_at = Column(DateTime, nullable=True)
    token_type = Column(String, default="Bearer")
    scope = Column(Text, nullable=True)
    
    # Integration-specific data (encrypted)
    metadata_encrypted = Column(Text, nullable=True)  # JSON string
    
    # Sync tracking
    last_synced_at = Column(DateTime, nullable=True)
    last_sync_error = Column(Text, nullable=True)
    sync_frequency_minutes = Column(String, default="60")
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # User who connected
    connected_by = Column(String, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('ix_integration_workspace_source', 'workspace_id', 'source', unique=True),
        Index('ix_integration_status', 'status'),
        Index('ix_integration_sync', 'last_synced_at'),
    )
    
    @property
    def access_token(self) -> Optional[str]:
        """Decrypt and return access token"""
        if self.access_token_encrypted:
            return decrypt(self.access_token_encrypted)
        return None
    
    @access_token.setter
    def access_token(self, value: Optional[str]):
        """Encrypt and store access token"""
        if value:
            self.access_token_encrypted = encrypt(value)
        else:
            self.access_token_encrypted = None
    
    @property
    def refresh_token(self) -> Optional[str]:
        """Decrypt and return refresh token"""
        if self.refresh_token_encrypted:
            return decrypt(self.refresh_token_encrypted)
        return None
    
    @refresh_token.setter
    def refresh_token(self, value: Optional[str]):
        """Encrypt and store refresh token"""
        if value:
            self.refresh_token_encrypted = encrypt(value)
        else:
            self.refresh_token_encrypted = None
    
    @property
    def integration_metadata(self) -> Optional[dict]:
        """Decrypt and parse metadata JSON"""
        if self.metadata_encrypted:
            import json
            decrypted = decrypt(self.metadata_encrypted)
            return json.loads(decrypted)
        return {}
    
    @integration_metadata.setter
    def integration_metadata(self, value: Optional[dict]):
        """Serialize and encrypt metadata"""
        if value:
            import json
            json_str = json.dumps(value)
            self.metadata_encrypted = encrypt(json_str)
        else:
            self.metadata_encrypted = None
    
    def is_expired(self) -> bool:
        """Check if token is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def needs_refresh(self) -> bool:
        """Check if token needs refresh (5 min buffer)"""
        if not self.expires_at:
            return False
        from datetime import timedelta
        return datetime.utcnow() > (self.expires_at - timedelta(minutes=5))


# CRUD Helper Functions
def create_integration(workspace_id: str, source: str, user_email: str = None) -> IntegrationCredential:
    """Create a new integration credential"""
    from core.database import get_db_session
    
    with get_db_session() as db:
        integration = IntegrationCredential(
            workspace_id=workspace_id,
            source=source,
            status=IntegrationStatus.PENDING.value,
            connected_by=user_email
        )
        db.add(integration)
        db.commit()
        db.refresh(integration)
        return integration


def get_integration(workspace_id: str, source: str) -> Optional[IntegrationCredential]:
    """Get integration by workspace and source"""
    from core.database import get_db_session
    
    with get_db_session() as db:
        return db.query(IntegrationCredential).filter_by(
            workspace_id=workspace_id,
            source=source
        ).first()


def update_integration_tokens(workspace_id: str, source: str, 
                            access_token: str, refresh_token: str = None,
                            expires_in: int = None, metadata: dict = None) -> IntegrationCredential:
    """Update integration tokens after OAuth"""
    from core.database import get_db_session
    from datetime import timedelta
    
    with get_db_session() as db:
        integration = db.query(IntegrationCredential).filter_by(
            workspace_id=workspace_id,
            source=source
        ).first()
        
        if not integration:
            raise ValueError(f"Integration not found for {workspace_id}/{source}")
        
        integration.access_token = access_token
        if refresh_token:
            integration.refresh_token = refresh_token
        
        if expires_in:
            integration.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        if metadata:
            integration.integration_metadata = metadata
        
        integration.status = IntegrationStatus.CONNECTED.value
        integration.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(integration)
        return integration


def list_workspace_integrations(workspace_id: str) -> list[IntegrationCredential]:
    """List all integrations for a workspace"""
    from core.database import get_db_session
    
    with get_db_session() as db:
        return db.query(IntegrationCredential).filter_by(
            workspace_id=workspace_id
        ).order_by(IntegrationCredential.source).all()


def mark_integration_synced(workspace_id: str, source: str, error: str = None):
    """Update integration sync status"""
    from core.database import get_db_session
    
    with get_db_session() as db:
        integration = db.query(IntegrationCredential).filter_by(
            workspace_id=workspace_id,
            source=source
        ).first()
        
        if integration:
            integration.last_synced_at = datetime.utcnow()
            if error:
                integration.last_sync_error = error
                integration.status = IntegrationStatus.ERROR.value
            else:
                integration.last_sync_error = None
                integration.status = IntegrationStatus.CONNECTED.value
            
            db.commit()