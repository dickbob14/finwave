#!/usr/bin/env python3
"""
Fix QuickBooks realm_id for existing integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import get_db_session
from models.integration import IntegrationCredential

# QuickBooks sandbox realm ID - you'll need to replace with actual one
# This is just a placeholder - the real one comes from OAuth callback
SANDBOX_REALM_ID = "4620816365320497870"  # Example sandbox company ID

def fix_realm_id(workspace_id: str = 'default'):
    """Add realm_id to existing QuickBooks integration"""
    
    with get_db_session() as db:
        integration = db.query(IntegrationCredential).filter_by(
            workspace_id=workspace_id,
            source='quickbooks'
        ).first()
        
        if not integration:
            print("❌ No QuickBooks integration found")
            return
        
        print(f"Found integration for workspace: {workspace_id}")
        print(f"Current metadata: {integration.integration_metadata}")
        
        # Update metadata with realm_id
        metadata = integration.integration_metadata or {}
        if 'realm_id' not in metadata:
            print(f"\n⚠️  No realm_id found in metadata")
            print("Please provide the QuickBooks Company ID (realm_id) from your sandbox")
            print("You can find this in the QuickBooks URL after connecting")
            print("Example: https://sandbox.qbo.intuit.com/app/homepage?redir=%2Fapp%2Fhomepage&cid=1234567890")
            realm_id = input("Enter realm_id: ").strip()
            
            if realm_id:
                metadata['realm_id'] = realm_id
                integration.integration_metadata = metadata
                db.commit()
                print(f"✅ Updated realm_id to: {realm_id}")
            else:
                print("❌ No realm_id provided")
        else:
            print(f"✅ realm_id already set: {metadata['realm_id']}")


if __name__ == "__main__":
    fix_realm_id()