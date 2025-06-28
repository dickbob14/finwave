#!/usr/bin/env python3
"""
Fix integration_credentials table schema
"""

import sqlite3
import os

db_path = "test_finwave.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Drop the existing table
cursor.execute("DROP TABLE IF EXISTS integration_credentials")

# Create table with all required columns from the model
cursor.execute("""
CREATE TABLE integration_credentials (
    id VARCHAR PRIMARY KEY,
    workspace_id VARCHAR NOT NULL,
    source VARCHAR NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'pending',
    access_token_encrypted TEXT,
    refresh_token_encrypted TEXT,
    expires_at TIMESTAMP,
    token_type VARCHAR DEFAULT 'Bearer',
    scope TEXT,
    metadata_encrypted TEXT,
    last_synced_at TIMESTAMP,
    last_sync_error TEXT,
    sync_frequency_minutes VARCHAR DEFAULT '60',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    connected_by VARCHAR
)
""")

# Create the required indexes
cursor.execute("""
CREATE UNIQUE INDEX ix_integration_workspace_source 
ON integration_credentials(workspace_id, source)
""")

cursor.execute("""
CREATE INDEX ix_integration_status 
ON integration_credentials(status)
""")

cursor.execute("""
CREATE INDEX ix_integration_sync 
ON integration_credentials(last_synced_at)
""")

conn.commit()
conn.close()

print("✅ integration_credentials table recreated with correct schema")