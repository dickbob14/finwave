#!/usr/bin/env python3
"""
Create default workspace for FinWave
"""
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set SQLite database URL
os.environ['DATABASE_URL'] = 'sqlite:///test_finwave.db'

from core.database import get_db_session
from models.workspace import Workspace

def create_default_workspace():
    """Create the default workspace"""
    print("Creating default workspace...")
    
    with get_db_session() as db:
        # Check if default workspace exists
        existing = db.query(Workspace).filter_by(id="default").first()
        if existing:
            print("✓ Default workspace already exists")
            return
        
        # Create default workspace
        workspace = Workspace(
            id="default",
            name="Default Workspace",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(workspace)
        db.commit()
        
        print("✓ Created default workspace")

if __name__ == "__main__":
    create_default_workspace()