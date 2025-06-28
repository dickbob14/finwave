#!/usr/bin/env python3
"""
Fix missing OAuth tables
"""

import sqlite3
import os

db_path = "test_finwave.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create integration_credentials table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS integration_credentials (
    id VARCHAR PRIMARY KEY,
    workspace_id VARCHAR NOT NULL,
    source VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'pending',
    access_token_encrypted TEXT,
    refresh_token_encrypted TEXT,
    company_id VARCHAR,
    metadata JSON,
    last_synced_at TIMESTAMP,
    last_sync_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(workspace_id, source)
)
""")

# Create workspaces table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS workspaces (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    slug VARCHAR UNIQUE NOT NULL,
    billing_status VARCHAR DEFAULT 'trial',
    features_enabled JSON,
    settings JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Insert default workspace if it doesn't exist
cursor.execute("""
INSERT OR IGNORE INTO workspaces (id, name, slug) 
VALUES ('default', 'Default Workspace', 'default')
""")

conn.commit()
conn.close()

print("✅ Tables created successfully")