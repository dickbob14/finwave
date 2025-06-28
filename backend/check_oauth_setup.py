#!/usr/bin/env python3
"""
Check OAuth setup and create tables if needed
"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import after setting up path
import sqlite3
from core.crypto import encrypt

def check_oauth_setup():
    """Check and setup OAuth configuration"""
    
    # Connect to SQLite database
    db_path = os.getenv('DATABASE_URL', '').replace('sqlite:///', '')
    if not db_path:
        print("❌ No DATABASE_URL found")
        return
        
    print(f"📁 Database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if oauth_app_configs table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='oauth_app_configs'
        """)
        
        if not cursor.fetchone():
            print("❌ oauth_app_configs table NOT found")
            print("   Creating table...")
            
            # Create the table
            cursor.execute("""
                CREATE TABLE oauth_app_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workspace_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    client_id TEXT NOT NULL,
                    client_secret_encrypted TEXT NOT NULL,
                    environment TEXT DEFAULT 'production',
                    settings TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by TEXT,
                    UNIQUE(workspace_id, source)
                )
            """)
            conn.commit()
            print("   ✅ Table created successfully")
        else:
            print("✅ oauth_app_configs table exists")
            
            # Count configurations
            cursor.execute("SELECT COUNT(*) FROM oauth_app_configs")
            count = cursor.fetchone()[0]
            print(f"   Found {count} configurations")
            
            # List configurations
            cursor.execute("""
                SELECT workspace_id, source, client_id, environment 
                FROM oauth_app_configs
            """)
            for row in cursor.fetchall():
                print(f"   - {row[1]} for {row[0]}: {row[2][:10]}... ({row[3]})")
        
        # Check integration_credentials table
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='integration_credentials'
        """)
        
        if cursor.fetchone():
            print("\n✅ integration_credentials table exists")
            cursor.execute("SELECT COUNT(*) FROM integration_credentials")
            count = cursor.fetchone()[0]
            print(f"   Found {count} integrations")
        else:
            print("\n❌ integration_credentials table NOT found")
            
        # Check environment OAuth credentials
        print("\n🔑 Environment OAuth Credentials:")
        sources = [
            ('QuickBooks', 'QB_CLIENT_ID', 'QB_CLIENT_SECRET'),
            ('Salesforce', 'SALESFORCE_CLIENT_ID', 'SALESFORCE_CLIENT_SECRET'),
            ('HubSpot', 'HUBSPOT_CLIENT_ID', 'HUBSPOT_CLIENT_SECRET'),
            ('Gusto', 'GUSTO_CLIENT_ID', 'GUSTO_CLIENT_SECRET')
        ]
        
        for name, id_var, secret_var in sources:
            client_id = os.getenv(id_var)
            client_secret = os.getenv(secret_var)
            
            if client_id and client_secret:
                print(f"   ✅ {name}: {client_id[:10]}... (configured)")
            else:
                print(f"   ❌ {name}: Not configured")
                
        # Check auth bypass
        print(f"\n🔐 Auth bypass: {os.getenv('BYPASS_AUTH', 'false')}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_oauth_setup()