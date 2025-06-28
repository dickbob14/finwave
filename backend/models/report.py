"""
Report History Model

Tracks generated financial reports
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, JSON, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ReportHistory(Base):
    """
    Tracks all generated reports for audit and retrieval
    """
    __tablename__ = 'report_history'
    
    id = Column(String(36), primary_key=True)
    workspace_id = Column(String(36), nullable=False, index=True)
    report_type = Column(String(50), nullable=False, index=True)  # board_pack, investor_update, etc.
    period = Column(String(7), nullable=False, index=True)  # YYYY-MM format
    
    # File information
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)  # Local path
    s3_url = Column(String(500), nullable=True)  # S3 URL if uploaded
    size_bytes = Column(Integer, nullable=False)
    pages = Column(Integer, nullable=True)
    
    # Generation metadata
    generated_by = Column(String(255), nullable=False)  # User email
    generated_at = Column(DateTime, nullable=False, index=True)
    
    # Additional metadata
    metadata = Column(JSON, nullable=True)  # Flexible field for extra data
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<ReportHistory(id={self.id}, type={self.report_type}, period={self.period})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'report_type': self.report_type,
            'period': self.period,
            'filename': self.filename,
            'file_path': self.file_path,
            's3_url': self.s3_url,
            'size_bytes': self.size_bytes,
            'pages': self.pages,
            'generated_by': self.generated_by,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


def create_report_history(
    workspace_id: str,
    report_type: str,
    period: str,
    filename: str,
    size_bytes: int,
    generated_by: str,
    **kwargs
) -> ReportHistory:
    """
    Create a new report history record
    """
    from uuid import uuid4
    
    report = ReportHistory(
        id=str(uuid4()),
        workspace_id=workspace_id,
        report_type=report_type,
        period=period,
        filename=filename,
        size_bytes=size_bytes,
        generated_by=generated_by,
        generated_at=datetime.utcnow(),
        **kwargs
    )
    
    return report