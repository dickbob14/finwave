#!/usr/bin/env python3
"""
Quick database initialization for FinWave
"""
import sqlite3
from datetime import datetime

print("🔧 Quick Database Initialization")
print("=" * 35)

# Create/connect to database
conn = sqlite3.connect('test_finwave.db')
cursor = conn.cursor()

# Create minimal tables needed for OAuth
print("\n1. Creating tables...")

# Workspaces table
cursor.execute("""
CREATE TABLE IF NOT EXISTS workspaces (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Integration credentials table
cursor.execute("""
CREATE TABLE IF NOT EXISTS integration_credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id TEXT NOT NULL,
    source TEXT NOT NULL,
    status TEXT NOT NULL,
    access_token_encrypted TEXT,
    refresh_token_encrypted TEXT,
    expires_at TIMESTAMP,
    metadata_encrypted TEXT,
    connected_by TEXT,
    last_synced_at TIMESTAMP,
    last_sync_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(workspace_id, source)
)
""")

# Metrics table
cursor.execute("""
CREATE TABLE IF NOT EXISTS metrics (
    workspace_id TEXT NOT NULL,
    metric_id TEXT NOT NULL,
    period_date DATE NOT NULL,
    value REAL NOT NULL,
    source_template TEXT NOT NULL,
    currency TEXT DEFAULT 'USD',
    unit TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (workspace_id, metric_id, period_date)
)
""")

print("   ✓ Tables created")

# Create workspaces
print("\n2. Creating workspaces...")

# Check and create 'default' workspace
cursor.execute("SELECT id FROM workspaces WHERE id = 'default'")
if not cursor.fetchone():
    cursor.execute("""
        INSERT INTO workspaces (id, name, created_at, updated_at)
        VALUES ('default', 'Default Workspace', datetime('now'), datetime('now'))
    """)
    print("   ✓ Created 'default' workspace")
else:
    print("   ✓ 'default' workspace exists")

# Check and create 'demo' workspace  
cursor.execute("SELECT id FROM workspaces WHERE id = 'demo'")
if not cursor.fetchone():
    cursor.execute("""
        INSERT INTO workspaces (id, name, created_at, updated_at)
        VALUES ('demo', 'Demo Workspace', datetime('now'), datetime('now'))
    """)
    print("   ✓ Created 'demo' workspace")
else:
    print("   ✓ 'demo' workspace exists")

# Commit changes
conn.commit()

# Show summary
cursor.execute("SELECT COUNT(*) FROM workspaces")
workspace_count = cursor.fetchone()[0]
print(f"\n3. Summary:")
print(f"   Workspaces: {workspace_count}")
print(f"   Database: test_finwave.db")

conn.close()

print("\n✅ Database initialization complete!")
print("\nQuickBooks OAuth should now work:")
print("1. Restart the backend server (Ctrl+C and run ./quick_start.sh)")
print("2. Go to http://localhost:3000/settings")
print("3. Click 'Connect' on QuickBooks")