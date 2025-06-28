#!/usr/bin/env python3
"""
Check QuickBooks Integration Status
This script queries the database to show:
- Integration status for QuickBooks
- Last sync error messages
- Token expiry status
- Sync job records
- Stored metrics
"""

import os
import sys
from datetime import datetime, timezone
from sqlalchemy import text
import json

# Add backend to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import get_db_session, engine
from models.integration import IntegrationCredential, IntegrationSource, IntegrationStatus

def format_datetime(dt):
    """Format datetime for display"""
    if not dt:
        return "Never"
    if isinstance(dt, str):
        return dt
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")

def check_integration_credentials():
    """Check QuickBooks integration credentials"""
    print("\n" + "="*80)
    print("QUICKBOOKS INTEGRATION STATUS")
    print("="*80)
    
    with get_db_session() as db:
        # Query all QuickBooks integrations
        integrations = db.query(IntegrationCredential).filter(
            IntegrationCredential.source == IntegrationSource.QUICKBOOKS.value
        ).all()
        
        if not integrations:
            print("\n❌ No QuickBooks integrations found in database")
            return
        
        for intg in integrations:
            print(f"\n🏢 Workspace: {intg.workspace_id}")
            print(f"   ID: {intg.id}")
            print(f"   Status: {intg.status}")
            print(f"   Connected by: {intg.connected_by or 'Unknown'}")
            print(f"   Created: {format_datetime(intg.created_at)}")
            print(f"   Updated: {format_datetime(intg.updated_at)}")
            
            # Token status
            print(f"\n   📝 Token Information:")
            print(f"      Has Access Token: {'✅ Yes' if intg.access_token_encrypted else '❌ No'}")
            print(f"      Has Refresh Token: {'✅ Yes' if intg.refresh_token_encrypted else '❌ No'}")
            print(f"      Token Type: {intg.token_type}")
            print(f"      Expires At: {format_datetime(intg.expires_at)}")
            
            if intg.expires_at:
                if intg.is_expired():
                    print(f"      ⚠️  Token is EXPIRED!")
                elif intg.needs_refresh():
                    print(f"      ⚠️  Token needs refresh (expires soon)")
                else:
                    print(f"      ✅ Token is valid")
            
            # Sync information
            print(f"\n   🔄 Sync Information:")
            print(f"      Last Synced: {format_datetime(intg.last_synced_at)}")
            print(f"      Sync Frequency: {intg.sync_frequency_minutes} minutes")
            
            if intg.last_sync_error:
                print(f"      ❌ Last Error: {intg.last_sync_error}")
            else:
                print(f"      ✅ No sync errors")
            
            # Metadata
            if intg.metadata_encrypted:
                try:
                    metadata = intg.integration_metadata
                    print(f"\n   📋 Metadata:")
                    for key, value in metadata.items():
                        print(f"      {key}: {value}")
                except Exception as e:
                    print(f"      ⚠️  Error decrypting metadata: {e}")

def check_sync_logs():
    """Check sync log records"""
    print("\n" + "="*80)
    print("SYNC LOGS")
    print("="*80)
    
    with engine.connect() as conn:
        # Check if sync_logs table exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'sync_logs'
            )
        """))
        
        if not result.scalar():
            print("\n⚠️  sync_logs table does not exist")
            return
        
        # Get recent sync logs
        result = conn.execute(text("""
            SELECT * FROM sync_logs 
            ORDER BY created_at DESC 
            LIMIT 10
        """))
        
        logs = result.fetchall()
        
        if not logs:
            print("\n❌ No sync logs found")
            return
        
        print(f"\n📋 Found {len(logs)} recent sync logs:")
        
        for log in logs:
            print(f"\n   🔄 Sync ID: {log.id}")
            print(f"      Company: {log.company_id}")
            print(f"      Type: {log.sync_type}")
            print(f"      Status: {log.sync_status}")
            print(f"      Started: {format_datetime(log.started_at)}")
            print(f"      Completed: {format_datetime(log.completed_at)}")
            print(f"      Records Synced: {log.records_synced}")
            
            if log.error_message:
                print(f"      ❌ Error: {log.error_message}")
            
            if log.metadata:
                try:
                    metadata = json.loads(log.metadata) if isinstance(log.metadata, str) else log.metadata
                    print(f"      📋 Metadata: {json.dumps(metadata, indent=8)}")
                except:
                    print(f"      📋 Metadata: {log.metadata}")

def check_metrics():
    """Check stored metrics"""
    print("\n" + "="*80)
    print("STORED METRICS")
    print("="*80)
    
    with engine.connect() as conn:
        # Check if metrics table exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'metrics'
            )
        """))
        
        if result.scalar():
            # Get metrics count by type
            result = conn.execute(text("""
                SELECT metric_type, COUNT(*) as count,
                       MIN(timestamp) as earliest,
                       MAX(timestamp) as latest
                FROM metrics
                GROUP BY metric_type
                ORDER BY count DESC
            """))
            
            metrics = result.fetchall()
            
            if metrics:
                print("\n📊 Metrics Summary:")
                for metric in metrics:
                    print(f"   • {metric.metric_type}: {metric.count} records")
                    print(f"     From: {format_datetime(metric.earliest)}")
                    print(f"     To: {format_datetime(metric.latest)}")
            else:
                print("\n❌ No metrics found in metrics table")
        else:
            print("\n⚠️  metrics table does not exist")
        
        # Check KPI metrics table
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'kpi_metrics'
            )
        """))
        
        if result.scalar():
            result = conn.execute(text("""
                SELECT company_id, metric_name, COUNT(*) as count,
                       MIN(period_start) as earliest,
                       MAX(period_end) as latest
                FROM kpi_metrics
                GROUP BY company_id, metric_name
                ORDER BY company_id, metric_name
            """))
            
            kpis = result.fetchall()
            
            if kpis:
                print("\n📈 KPI Metrics Summary:")
                current_company = None
                for kpi in kpis:
                    if kpi.company_id != current_company:
                        current_company = kpi.company_id
                        print(f"\n   🏢 {kpi.company_id}:")
                    print(f"      • {kpi.metric_name}: {kpi.count} records")
                    print(f"        From: {format_datetime(kpi.earliest)}")
                    print(f"        To: {format_datetime(kpi.latest)}")
            else:
                print("\n❌ No KPI metrics found")
        else:
            print("\n⚠️  kpi_metrics table does not exist")

def check_quickbooks_data():
    """Check QuickBooks synced data"""
    print("\n" + "="*80)
    print("QUICKBOOKS DATA")
    print("="*80)
    
    tables = [
        ('qb_financial_statements', 'Financial Statements'),
        ('qb_account_balances', 'Account Balances'),
        ('qb_transactions', 'Transactions'),
        ('qb_customers', 'Customers'),
        ('qb_vendors', 'Vendors')
    ]
    
    with engine.connect() as conn:
        for table_name, display_name in tables:
            # Check if table exists
            result = conn.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = '{table_name}'
                )
            """))
            
            if not result.scalar():
                print(f"\n⚠️  {table_name} table does not exist")
                continue
            
            # Get record count
            result = conn.execute(text(f"SELECT COUNT(*) as count FROM {table_name}"))
            count = result.scalar()
            
            print(f"\n📊 {display_name}: {count} records")
            
            if count > 0:
                # Get sample data based on table type
                if table_name == 'qb_financial_statements':
                    result = conn.execute(text(f"""
                        SELECT company_id, statement_type, period_start, period_end
                        FROM {table_name}
                        ORDER BY period_end DESC
                        LIMIT 5
                    """))
                    
                    for row in result:
                        print(f"   • {row.company_id}: {row.statement_type} ({format_datetime(row.period_start)} to {format_datetime(row.period_end)})")
                
                elif table_name == 'qb_account_balances':
                    result = conn.execute(text(f"""
                        SELECT company_id, COUNT(DISTINCT account_id) as accounts, 
                               SUM(balance) as total_balance, MAX(as_of_date) as latest_date
                        FROM {table_name}
                        GROUP BY company_id
                    """))
                    
                    for row in result:
                        print(f"   • {row.company_id}: {row.accounts} accounts, Total: ${row.total_balance:,.2f}, As of: {format_datetime(row.latest_date)}")

def check_workspace_integrations():
    """Check workspace-level integration info"""
    print("\n" + "="*80)
    print("WORKSPACE INTEGRATION INFO")
    print("="*80)
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, name, qb_realm_id, qb_company_name, qb_last_sync
            FROM workspaces
            WHERE qb_realm_id IS NOT NULL
        """))
        
        workspaces = result.fetchall()
        
        if not workspaces:
            print("\n❌ No workspaces with QuickBooks integration found")
            return
        
        for ws in workspaces:
            print(f"\n🏢 {ws.name} ({ws.id})")
            print(f"   QB Realm ID: {ws.qb_realm_id}")
            print(f"   QB Company: {ws.qb_company_name}")
            print(f"   Last Sync: {format_datetime(ws.qb_last_sync)}")

def main():
    """Run all checks"""
    try:
        print("\n🔍 QUICKBOOKS INTEGRATION STATUS CHECK")
        print("=" * 80)
        print(f"Started at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Run all checks
        check_integration_credentials()
        check_sync_logs()
        check_metrics()
        check_quickbooks_data()
        check_workspace_integrations()
        
        print("\n" + "="*80)
        print("✅ Status check complete!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error running status check: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()