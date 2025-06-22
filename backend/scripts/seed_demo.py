"""
Seed script to create demo workspace and trigger QuickBooks sync
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.database import get_db_session, init_db
from core.crypto import encrypt_value
from models.workspace import Workspace
from models.integration import IntegrationCredential
from integrations.quickbooks.sync import sync_quickbooks_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_demo_workspace():
    """Create demo workspace if it doesn't exist"""
    with get_db_session() as db:
        # Check if demo workspace exists
        workspace = db.query(Workspace).filter_by(slug='demo').first()
        
        if not workspace:
            logger.info("Creating demo workspace...")
            workspace = Workspace(
                id='demo-workspace-001',
                name="Craig's Design & Landscaping Services",
                slug='demo',
                billing_status='active',
                features_enabled={
                    'board_reports': True,
                    'variance_alerts': True,
                    'scenario_planning': True,
                    'ai_insights': True
                },
                settings={
                    'company_name': "Craig's Design & Landscaping Services",
                    'fiscal_year_start_month': 1,
                    'report_recipients': ['board@craigs-landscaping.com'],
                    'theme': {
                        'primary_color': '#4F46E5',  # Indigo
                        'secondary_color': '#10B981',  # Emerald
                        'company_name': "Craig's Design & Landscaping Services"
                    }
                }
            )
            db.add(workspace)
            db.commit()
            logger.info(f"Created workspace: {workspace.id}")
        else:
            logger.info(f"Demo workspace already exists: {workspace.id}")
        
        return workspace.id


def setup_quickbooks_credentials(workspace_id: str):
    """Set up QuickBooks sandbox credentials"""
    with get_db_session() as db:
        # Check if credentials exist
        existing = db.query(IntegrationCredential).filter_by(
            workspace_id=workspace_id,
            source='quickbooks'
        ).first()
        
        if existing:
            logger.info("QuickBooks credentials already exist")
            return
        
        # Create encrypted credentials
        logger.info("Setting up QuickBooks sandbox credentials...")
        
        # In a real OAuth flow, these would come from the OAuth callback
        # For demo/dev, we're using env vars
        access_token = os.getenv('QB_ACCESS_TOKEN', 'sandbox-token')
        refresh_token = os.getenv('QB_REFRESH_TOKEN', 'sandbox-refresh')
        
        credential = IntegrationCredential(
            workspace_id=workspace_id,
            source='quickbooks',
            status='active',
            access_token_encrypted=encrypt_value(access_token),
            refresh_token_encrypted=encrypt_value(refresh_token),
            company_id=os.getenv('QB_COMPANY_ID', '9341454888200521'),
            settings={
                'environment': 'sandbox',
                'company_name': "Craig's Design & Landscaping Services",
                'connected_by': 'admin@demo.finwave.io'
            }
        )
        db.add(credential)
        db.commit()
        logger.info("QuickBooks credentials saved")


def trigger_initial_sync(workspace_id: str):
    """Trigger initial QuickBooks data sync"""
    logger.info("Starting initial QuickBooks sync...")
    
    try:
        # This will fetch all data from QB API
        results = sync_quickbooks_data(workspace_id, initial=True)
        
        if results['status'] == 'completed':
            logger.info(f"✅ QuickBooks sync completed! Created {results['metrics_created']} metrics")
        else:
            logger.error(f"❌ QuickBooks sync failed: {results.get('errors', [])}")
    
    except Exception as e:
        logger.error(f"Failed to sync QuickBooks data: {e}")
        logger.info("Continuing with setup - you can manually sync later")


def main():
    """Main setup flow"""
    logger.info("🚀 Starting FinWave demo setup...")
    
    # Initialize database
    init_db()
    
    # Create demo workspace
    workspace_id = create_demo_workspace()
    
    # Set up QuickBooks credentials
    setup_quickbooks_credentials(workspace_id)
    
    # Trigger initial sync
    if os.getenv('QB_CLIENT_ID') and os.getenv('QB_CLIENT_SECRET'):
        trigger_initial_sync(workspace_id)
    else:
        logger.warning("⚠️  QuickBooks API credentials not found - skipping data sync")
        logger.info("Add QB_CLIENT_ID and QB_CLIENT_SECRET to .env to enable sync")
    
    logger.info("✅ Demo setup complete!")
    logger.info(f"Workspace ID: {workspace_id}")
    logger.info("You can now start the dev server and log in with admin@demo.finwave.io")


if __name__ == "__main__":
    main()