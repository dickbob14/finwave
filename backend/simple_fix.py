#!/usr/bin/env python3
"""
Simple fix for QuickBooks connection issue
"""
import os
import sqlite3
from datetime import datetime

# Create default workspace directly with SQLite
db_file = 'test_finwave.db'

print("🔧 Simple QuickBooks Fix")
print("=" * 30)

# Connect to database
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

try:
    # Check if workspaces table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='workspaces';")
    if not cursor.fetchone():
        print("Creating workspaces table...")
        cursor.execute("""
            CREATE TABLE workspaces (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
    
    # Check if default workspace exists
    cursor.execute("SELECT id FROM workspaces WHERE id = 'default'")
    if not cursor.fetchone():
        print("Creating 'default' workspace...")
        cursor.execute("""
            INSERT INTO workspaces (id, name, created_at, updated_at)
            VALUES ('default', 'Default Workspace', ?, ?)
        """, (datetime.utcnow(), datetime.utcnow()))
        conn.commit()
        print("✓ Created 'default' workspace")
    else:
        print("✓ 'default' workspace already exists")
    
    # Also check for demo workspace
    cursor.execute("SELECT id FROM workspaces WHERE id = 'demo'")
    if not cursor.fetchone():
        print("Creating 'demo' workspace...")
        cursor.execute("""
            INSERT INTO workspaces (id, name, created_at, updated_at)
            VALUES ('demo', 'Demo Workspace', ?, ?)
        """, (datetime.utcnow(), datetime.utcnow()))
        conn.commit()
        print("✓ Created 'demo' workspace")
    else:
        print("✓ 'demo' workspace already exists")
    
    print("\n✅ Done! QuickBooks connection should now work.")
    print("\nRestart the backend server and try connecting again.")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()