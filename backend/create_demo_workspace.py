#!/usr/bin/env python3
"""
Create a demo workspace for testing
"""
import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set SQLite database URL
os.environ['DATABASE_URL'] = 'sqlite:///finwave.db'

from core.database import get_db_session
from models.workspace import Workspace

with get_db_session() as db:
    # Check if demo workspace exists
    demo = db.query(Workspace).filter_by(id="demo").first()
    
    if not demo:
        # Create demo workspace
        demo = Workspace(
            id="demo",
            name="Demo Company",
            billing_status="active",
            features_enabled={
                "insights": True,
                "pdf_export": True,
                "api_access": True,
                "custom_templates": True
            }
        )
        db.add(demo)
        db.commit()
        print("✅ Created demo workspace")
    else:
        print("Demo workspace already exists")
        
    print(f"Workspace ID: {demo.id}")
    print(f"Workspace Name: {demo.name}")
    print(f"Created At: {demo.created_at}")