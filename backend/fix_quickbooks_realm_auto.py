#!/usr/bin/env python3
"""
Fix QuickBooks realm_id for testing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import get_db_session
from models.integration import IntegrationCredential

def fix_realm_id(workspace_id: str = 'default'):
    """Add test realm_id to existing QuickBooks integration"""
    
    with get_db_session() as db:
        integration = db.query(IntegrationCredential).filter_by(
            workspace_id=workspace_id,
            source='quickbooks'
        ).first()
        
        if not integration:
            print("❌ No QuickBooks integration found")
            return
        
        print(f"Found integration for workspace: {workspace_id}")
        
        # Set a test realm_id
        # In production, this comes from the OAuth callback realmId parameter
        TEST_REALM_ID = "4620816365320497870"  # QuickBooks sandbox company
        
        metadata = integration.integration_metadata or {}
        metadata['realm_id'] = TEST_REALM_ID
        metadata['company_name'] = "Sandbox Company_US_1"
        
        integration.integration_metadata = metadata
        db.commit()
        
        print(f"✅ Updated metadata: {metadata}")


if __name__ == "__main__":
    fix_realm_id()