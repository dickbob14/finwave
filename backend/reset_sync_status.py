#!/usr/bin/env python3
"""
Reset sync status to force full sync
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import get_db_session
from models.integration import IntegrationCredential

def reset_sync_status():
    """Reset last sync timestamp"""
    
    with get_db_session() as db:
        integration = db.query(IntegrationCredential).filter_by(
            workspace_id='default',
            source='quickbooks'
        ).first()
        
        if integration:
            integration.last_synced_at = None
            integration.last_sync_error = None
            db.commit()
            print("✅ Sync status reset - next sync will be a full pull")
        else:
            print("❌ No QuickBooks integration found")


if __name__ == "__main__":
    reset_sync_status()