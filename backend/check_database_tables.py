#!/usr/bin/env python3
"""
Quick check of database tables related to QuickBooks integration
"""

import os
import sys
from sqlalchemy import text

# Add backend to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import engine

def main():
    """Check which tables exist"""
    print("\n🔍 DATABASE TABLE CHECK")
    print("=" * 80)
    
    # Tables to check
    tables_to_check = [
        # Core tables
        ('workspaces', 'Core workspace table'),
        ('integration_credentials', 'OAuth credentials storage'),
        
        # Metrics tables
        ('metrics', 'General metrics storage'),
        ('kpi_metrics', 'KPI calculations'),
        
        # QuickBooks sync tables
        ('qb_financial_statements', 'Financial statements from QB'),
        ('qb_account_balances', 'Account balances from QB'),
        ('qb_transactions', 'Transaction records from QB'),
        ('qb_customers', 'Customer data from QB'),
        ('qb_vendors', 'Vendor data from QB'),
        
        # Sync tracking
        ('sync_logs', 'Sync job history'),
        
        # Report tables
        ('report_history', 'Generated reports'),
        ('report_templates', 'Report templates')
    ]
    
    with engine.connect() as conn:
        print("\nChecking tables...")
        existing_tables = []
        missing_tables = []
        
        for table_name, description in tables_to_check:
            result = conn.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = '{table_name}'
                )
            """))
            
            exists = result.scalar()
            
            if exists:
                existing_tables.append((table_name, description))
                print(f"✅ {table_name:<30} - {description}")
            else:
                missing_tables.append((table_name, description))
                print(f"❌ {table_name:<30} - {description}")
        
        print(f"\n📊 Summary:")
        print(f"   Existing tables: {len(existing_tables)}")
        print(f"   Missing tables: {len(missing_tables)}")
        
        if missing_tables:
            print(f"\n⚠️  Missing tables might need migration scripts to be run:")
            for table, desc in missing_tables:
                print(f"   • {table} - {desc}")
            
            print(f"\n💡 To create missing tables, check the migrations/ directory")

if __name__ == "__main__":
    main()