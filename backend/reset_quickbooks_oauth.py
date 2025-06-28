#!/usr/bin/env python3
"""
Reset QuickBooks OAuth to force re-authentication
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import get_db_session
from models.integration import IntegrationCredential

def reset_quickbooks_oauth(workspace_id: str = 'default'):
    """Clear QuickBooks tokens to force re-authentication"""
    
    print("🔄 Resetting QuickBooks OAuth...")
    print("=" * 50)
    
    with get_db_session() as db:
        integration = db.query(IntegrationCredential).filter_by(
            workspace_id=workspace_id,
            source='quickbooks'
        ).first()
        
        if not integration:
            print("❌ No QuickBooks integration found")
            return
        
        # Clear tokens and metadata
        integration.access_token = None
        integration.refresh_token = None
        integration.expires_at = None
        integration.integration_metadata = {}
        integration.status = 'pending'
        integration.last_synced_at = None
        integration.last_sync_error = None
        
        db.commit()
        
        print("✅ QuickBooks tokens cleared")
        print("\nNext steps:")
        print("1. Go to http://localhost:3000/settings")
        print("2. Click 'Connect' for QuickBooks")
        print("3. Complete the OAuth flow")
        print("4. The sync should start automatically")
    
    # Also clear the token file
    token_file = 'qb_tokens.json'
    if os.path.exists(token_file):
        os.remove(token_file)
        print(f"\n✅ Removed {token_file}")


if __name__ == "__main__":
    reset_quickbooks_oauth()