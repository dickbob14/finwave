#!/usr/bin/env python3
"""
CLI tool for workspace management
Usage: python manage_workspace.py [command] [options]
"""

import argparse
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_db_session, init_db
from models.workspace import Workspace, BillingStatus


def create_workspace(args):
    """Create a new workspace"""
    with get_db_session() as db:
        # Check if exists
        existing = db.query(Workspace).filter(Workspace.id == args.id).first()
        if existing:
            print(f"❌ Workspace '{args.id}' already exists")
            return False
        
        # Create workspace
        workspace = Workspace(
            id=args.id,
            name=args.name,
            billing_status=args.billing_status,
            trial_ends_at=datetime.utcnow() + timedelta(days=args.trial_days),
            seats_allowed=args.seats
        )
        
        # Set QuickBooks if provided
        if args.qb_realm:
            workspace.qb_realm_id = args.qb_realm
            workspace.qb_company_name = args.name
        
        # Set CRM if provided
        if args.crm_type:
            workspace.crm_type = args.crm_type
        
        db.add(workspace)
        db.commit()
        
        print(f"✅ Created workspace: {workspace.id}")
        print(f"   Name: {workspace.name}")
        print(f"   Status: {workspace.billing_status}")
        print(f"   Trial ends: {workspace.trial_ends_at.strftime('%Y-%m-%d')}")
        print(f"   Seats: {workspace.seats_allowed}")
        
        return True


def list_workspaces(args):
    """List all workspaces"""
    with get_db_session() as db:
        workspaces = db.query(Workspace).all()
        
        if not workspaces:
            print("No workspaces found")
            return
        
        print(f"\n{'ID':<20} {'Name':<30} {'Status':<10} {'QB':<5} {'CRM':<10}")
        print("-" * 80)
        
        for ws in workspaces:
            qb_status = "✓" if ws.qb_realm_id else "✗"
            crm_status = ws.crm_type if ws.crm_org_id else "-"
            
            print(f"{ws.id:<20} {ws.name:<30} {ws.billing_status:<10} {qb_status:<5} {crm_status:<10}")
        
        print(f"\nTotal: {len(workspaces)} workspaces")


def show_workspace(args):
    """Show detailed workspace info"""
    with get_db_session() as db:
        workspace = db.query(Workspace).filter(Workspace.id == args.id).first()
        
        if not workspace:
            print(f"❌ Workspace '{args.id}' not found")
            return False
        
        print(f"\n🏢 Workspace: {workspace.name}")
        print(f"   ID: {workspace.id}")
        print(f"   Created: {workspace.created_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Updated: {workspace.updated_at.strftime('%Y-%m-%d %H:%M')}")
        
        print(f"\n💳 Billing:")
        print(f"   Status: {workspace.billing_status}")
        if workspace.trial_ends_at:
            days_left = (workspace.trial_ends_at - datetime.utcnow()).days
            print(f"   Trial ends: {workspace.trial_ends_at.strftime('%Y-%m-%d')} ({days_left} days left)")
        print(f"   Seats: {workspace.seats_allowed}")
        
        print(f"\n🔌 Integrations:")
        print(f"   QuickBooks: {'Connected' if workspace.qb_realm_id else 'Not connected'}")
        if workspace.qb_realm_id:
            print(f"     - Realm ID: {workspace.qb_realm_id}")
            if workspace.qb_last_sync:
                print(f"     - Last sync: {workspace.qb_last_sync.strftime('%Y-%m-%d %H:%M')}")
        
        print(f"   CRM: {workspace.crm_type or 'Not connected'}")
        if workspace.crm_org_id:
            print(f"     - Org ID: {workspace.crm_org_id}")
            if workspace.crm_last_sync:
                print(f"     - Last sync: {workspace.crm_last_sync.strftime('%Y-%m-%d %H:%M')}")
        
        print(f"\n⚙️  Features:")
        for feature, enabled in (workspace.features_enabled or {}).items():
            status = "✓" if enabled else "✗"
            print(f"   {status} {feature}")
        
        return True


def update_workspace(args):
    """Update workspace settings"""
    with get_db_session() as db:
        workspace = db.query(Workspace).filter(Workspace.id == args.id).first()
        
        if not workspace:
            print(f"❌ Workspace '{args.id}' not found")
            return False
        
        # Update fields
        if args.name:
            workspace.name = args.name
            print(f"✓ Updated name: {args.name}")
        
        if args.billing_status:
            workspace.billing_status = args.billing_status
            print(f"✓ Updated billing status: {args.billing_status}")
        
        if args.seats:
            workspace.seats_allowed = args.seats
            print(f"✓ Updated seats: {args.seats}")
        
        if args.qb_realm:
            workspace.qb_realm_id = args.qb_realm
            print(f"✓ Updated QuickBooks realm: {args.qb_realm}")
        
        if args.crm_type:
            workspace.crm_type = args.crm_type
            print(f"✓ Updated CRM type: {args.crm_type}")
        
        workspace.updated_at = datetime.utcnow()
        db.commit()
        
        print(f"\n✅ Workspace '{args.id}' updated successfully")
        return True


def delete_workspace(args):
    """Delete a workspace"""
    with get_db_session() as db:
        workspace = db.query(Workspace).filter(Workspace.id == args.id).first()
        
        if not workspace:
            print(f"❌ Workspace '{args.id}' not found")
            return False
        
        # Confirm deletion
        if not args.force:
            confirm = input(f"⚠️  Delete workspace '{workspace.name}' ({workspace.id})? [y/N]: ")
            if confirm.lower() != 'y':
                print("Cancelled")
                return False
        
        db.delete(workspace)
        db.commit()
        
        print(f"✅ Deleted workspace: {workspace.id}")
        return True


def init_database(args):
    """Initialize database tables"""
    try:
        init_db()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='FinWave Workspace Management')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Create workspace
    create_parser = subparsers.add_parser('create', help='Create a new workspace')
    create_parser.add_argument('id', help='Workspace ID (slug format, e.g., acme-corp)')
    create_parser.add_argument('name', help='Display name (e.g., "Acme Corporation")')
    create_parser.add_argument('--billing-status', choices=['trial', 'active', 'suspended'], 
                             default='trial', help='Billing status')
    create_parser.add_argument('--trial-days', type=int, default=14, 
                             help='Trial period in days')
    create_parser.add_argument('--seats', type=int, default=5, 
                             help='Number of allowed seats')
    create_parser.add_argument('--qb-realm', help='QuickBooks realm ID')
    create_parser.add_argument('--crm-type', choices=['salesforce', 'hubspot'], 
                             help='CRM type')
    
    # List workspaces
    list_parser = subparsers.add_parser('list', help='List all workspaces')
    
    # Show workspace
    show_parser = subparsers.add_parser('show', help='Show workspace details')
    show_parser.add_argument('id', help='Workspace ID')
    
    # Update workspace
    update_parser = subparsers.add_parser('update', help='Update workspace')
    update_parser.add_argument('id', help='Workspace ID')
    update_parser.add_argument('--name', help='New display name')
    update_parser.add_argument('--billing-status', 
                             choices=['trial', 'active', 'suspended', 'cancelled'])
    update_parser.add_argument('--seats', type=int, help='Number of seats')
    update_parser.add_argument('--qb-realm', help='QuickBooks realm ID')
    update_parser.add_argument('--crm-type', choices=['salesforce', 'hubspot'])
    
    # Delete workspace
    delete_parser = subparsers.add_parser('delete', help='Delete a workspace')
    delete_parser.add_argument('id', help='Workspace ID')
    delete_parser.add_argument('--force', action='store_true', 
                             help='Skip confirmation')
    
    # Init database
    init_parser = subparsers.add_parser('init-db', help='Initialize database')
    
    args = parser.parse_args()
    
    # Map commands to functions
    commands = {
        'create': create_workspace,
        'list': list_workspaces,
        'show': show_workspace,
        'update': update_workspace,
        'delete': delete_workspace,
        'init-db': init_database
    }
    
    if args.command in commands:
        success = commands[args.command](args)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()